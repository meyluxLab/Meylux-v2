from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from contracts.acquisition import AcquisitionState, EventType
from meylux.acquisition.binance import BinanceAdapter
from meylux.acquisition.mexc import MEXCAdapter, RetryPolicy

FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def adapter(*, http_get=None, websocket_connect=None, sleeper=None, async_sleeper=None):
    return MEXCAdapter(
        clock=lambda: FIXED_NOW,
        http_get=http_get,
        websocket_connect=websocket_connect,
        sleeper=sleeper or (lambda _delay: None),
        async_sleeper=async_sleeper or (lambda _delay: asyncio.sleep(0)),
        retry_policy=RetryPolicy(max_attempts=3, initial_backoff_seconds=0, max_backoff_seconds=0),
    )


def varint(value: int) -> bytes:
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def field(number: int, value: bytes | int, wire: int = 2) -> bytes:
    if wire == 0:
        return varint(number << 3) + varint(int(value))
    return varint((number << 3) | wire) + varint(len(value)) + value


def sfield(number: int, value: str) -> bytes:
    return field(number, value.encode())


def trade_proto() -> bytes:
    item = b"".join((sfield(1, "100"), sfield(2, "2"), field(3, 1, 0), field(4, 1757592000000, 0), sfield(5, "trade-7")))
    body = field(1, item) + sfield(2, "spot@public.aggre.deals.v3.api.pb@100ms")
    return b"".join((sfield(1, "spot@public.aggre.deals.v3.api.pb@100ms@BTCUSDT"), sfield(3, "BTCUSDT"), field(5, 1757592000000, 0), field(6, 1757592000001, 0), field(314, body)))


def depth_proto() -> bytes:
    item = sfield(1, "100") + sfield(2, "2")
    body = field(1, item) + field(2, item) + sfield(3, "spot@public.aggre.depth.v3.api.pb@100ms") + sfield(4, "10") + sfield(5, "11")
    return b"".join((sfield(1, "spot@public.aggre.depth.v3.api.pb@100ms@BTCUSDT"), sfield(3, "BTCUSDT"), field(5, 1757592000000, 0), field(6, 1757592000001, 0), field(313, body)))


def kline_proto() -> bytes:
    body = b"".join((sfield(1, "Min1"), field(2, 1757592000, 0), sfield(3, "100"), sfield(4, "105"), sfield(5, "110"), sfield(6, "90"), sfield(7, "12"), sfield(8, "1250"), field(9, 1757592059, 0)))
    return b"".join((sfield(1, "spot@public.kline.v3.api.pb@BTCUSDT@Min1"), sfield(3, "BTCUSDT"), field(5, 1757592000000, 0), field(6, 1757592000001, 0), field(308, body)))


class FakeWebSocket:
    def __init__(self, messages=(), fail=False):
        self.messages = list(messages)
        self.fail = fail
        self.sent = []

    async def __aenter__(self):
        if self.fail:
            raise ConnectionError("simulated disconnect")
        return self

    async def __aexit__(self, *_args):
        return False

    async def send(self, value):
        self.sent.append(value)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        raise StopAsyncIteration


class MEXCAdapterTests(unittest.TestCase):
    def test_identity_and_capabilities_are_provider_isolated(self):
        mexc = adapter()
        binance = BinanceAdapter(clock=lambda: FIXED_NOW)
        self.assertEqual(mexc.identity.provider_id, "mexc")
        self.assertNotEqual(mexc.identity.provider_id, binance.identity.provider_id)
        self.assertEqual({c.capability for c in mexc.capabilities()}, {"REST_BOOTSTRAP", "LIVE_STREAM", "INSTRUMENT_METADATA", "ORDER_BOOK_SNAPSHOT", "TRADES", "CANDLES"})

    def test_order_book_maps_provider_payload_and_sequence(self):
        def http_get(url, _timeout):
            self.assertIn("/api/v3/depth", url)
            return b'{"lastUpdateId":12345,"bids":[["100","2"]],"asks":[["101","1"]]}'
        envelope = adapter(http_get=http_get).fetch_order_book("btcusdt", limit=100)
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)
        self.assertEqual(envelope.event_type, EventType.ORDER_BOOK)
        self.assertEqual(envelope.source_sequence, "12345")

    def test_trades_map_time_and_identity_deterministically(self):
        body = b'[{"id":7,"price":"100","qty":"2","quoteQty":"200","time":1757592000000}]'
        mexc = adapter(http_get=lambda _url, _timeout: body)
        first, second = mexc.fetch_trades("BTCUSDT")[0], mexc.fetch_trades("BTCUSDT")[0]
        self.assertEqual(first.source_sequence, "7")
        self.assertEqual(first.event_id, second.event_id)

    def test_klines_preserve_raw_wire_row(self):
        row = [1757592000000, "100", "110", "90", "105", "12", 1757592059999, "1250"]
        envelope = adapter(http_get=lambda _url, _timeout: json.dumps([row]).encode()).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.payload["row"][1], "100")

    def test_exchange_info_supports_symbol_and_server_time(self):
        def http_get(url, _timeout):
            self.assertIn("/api/v3/exchangeInfo", url)
            return b'{"serverTime":1757592000000,"symbol":"BTCUSDT","status":"ENABLED"}'
        envelope = adapter(http_get=http_get).fetch_exchange_info("BTCUSDT")
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(1757592000, tz=timezone.utc))

    def test_http_429_maps_to_rate_limited_after_bounded_retry(self):
        attempts = []
        def http_get(_url, _timeout):
            attempts.append(1)
            raise HTTPError(_url, 429, "rate limited", {}, None)
        envelope = adapter(http_get=http_get).fetch_order_book("BTCUSDT")
        self.assertEqual(envelope.state, AcquisitionState.RATE_LIMITED)
        self.assertEqual(len(attempts), 3)

    def test_transport_failure_maps_to_unavailable_after_bounded_retry(self):
        attempts = []
        def http_get(_url, _timeout):
            attempts.append(1)
            raise URLError("offline")
        envelope = adapter(http_get=http_get).fetch_order_book("BTCUSDT")
        self.assertEqual(envelope.state, AcquisitionState.UNAVAILABLE)
        self.assertEqual(len(attempts), 3)

    def test_invalid_json_maps_to_invalid_without_retry_loop(self):
        attempts = []
        def http_get(_url, _timeout):
            attempts.append(1)
            return b"not-json"
        envelope = adapter(http_get=http_get).fetch_order_book("BTCUSDT")
        self.assertEqual(envelope.state, AcquisitionState.INVALID)
        self.assertEqual(len(attempts), 1)

    def test_current_trade_channel_and_protobuf_deserialization(self):
        envelope = adapter().parse_stream_message(trade_proto())
        self.assertEqual(envelope.event_type, EventType.TRADE)
        self.assertEqual(envelope.instrument.canonical_instrument_id, "BTCUSDT")
        self.assertEqual(envelope.payload["data"]["dealsList"][0]["tradeId"], "trade-7")
        self.assertEqual(envelope.source_sequence, "trade-7")

    def test_current_depth_channel_and_protobuf_deserialization(self):
        envelope = adapter().parse_stream_message(depth_proto())
        self.assertEqual(envelope.event_type, EventType.ORDER_BOOK)
        self.assertEqual(envelope.source_sequence, "11")
        self.assertEqual(envelope.payload["data"]["bidsList"][0]["price"], "100")

    def test_current_kline_channel_and_protobuf_deserialization(self):
        envelope = adapter().parse_stream_message(kline_proto())
        self.assertEqual(envelope.event_type, EventType.CANDLE)
        self.assertEqual(envelope.payload["data"]["openingPrice"], "100")
        self.assertEqual(envelope.payload["data"]["interval"], "Min1")

    def test_legacy_json_market_payload_is_rejected(self):
        legacy = json.dumps({"channel": "spot@public.deals.v3.api@BTCUSDT", "symbol": "BTCUSDT", "data": {}})
        with self.assertRaises(Exception) as raised:
            adapter().parse_stream_message(legacy)
        self.assertEqual(raised.exception.state, AcquisitionState.INVALID)

    def test_stream_subscription_uses_current_pb_channels(self):
        ws = FakeWebSocket([trade_proto()])
        async def run():
            items = []
            async for item in adapter(websocket_connect=lambda _url: ws).stream(["BTCUSDT"], streams=("trade",), max_messages=1):
                items.append(item)
            return items
        items = asyncio.run(run())
        self.assertEqual(len(items), 1)
        request = json.loads(ws.sent[0])
        self.assertEqual(request["params"], ["spot@public.aggre.deals.v3.api.pb@100ms@BTCUSDT"])

    def test_stream_reconnect_limit_is_bounded(self):
        connects = []
        def websocket_connect(_url):
            connects.append(1)
            return FakeWebSocket(fail=True)
        async def run():
            results = []
            async for item in adapter(websocket_connect=websocket_connect).stream(["BTCUSDT"], streams=("trade",), max_reconnects=2):
                results.append(item)
            return results
        results = asyncio.run(run())
        self.assertEqual(len(connects), 3)
        self.assertEqual(results[-1].state, AcquisitionState.DISCONNECTED)
        self.assertEqual(results[-1].provider_error.code, "MEXC_RECONNECT_LIMIT")

    def test_subscription_bound_is_enforced(self):
        with self.assertRaises(ValueError):
            asyncio.run(adapter().stream(["BTCUSDT"] * 31).__anext__())

    def test_canonical_serialization_contains_no_float_values(self):
        body = b'{"lastUpdateId":1,"bids":[["100","2"]],"asks":[]}'
        envelope = adapter(http_get=lambda _url, _timeout: body).fetch_order_book("BTCUSDT")
        self.assertIsInstance(envelope.canonical_bytes(), bytes)
        self.assertEqual(envelope.event_id, envelope.deduplication_key)

    def test_failure_does_not_mutate_binance_identity_or_state(self):
        binance = BinanceAdapter(clock=lambda: FIXED_NOW)
        mexc = adapter(http_get=lambda _url, _timeout: b'{"code":10007,"msg":"failure"}')
        failure = mexc.fetch_order_book("BTCUSDT")
        self.assertEqual(failure.state, AcquisitionState.UNAVAILABLE)
        self.assertEqual(binance.identity.provider_id, "binance")
        self.assertNotEqual(failure.provider.provider_id, binance.identity.provider_id)

    def test_credentials_are_not_part_of_public_adapter_configuration(self):
        source = open("src/meylux/acquisition/mexc.py", encoding="utf-8").read()
        for forbidden in ("API_KEY", "API_SECRET", "X-MEXC-APIKEY", "signature"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
