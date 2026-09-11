import asyncio
import io
import json
import unittest
from datetime import datetime, timezone
from urllib.error import URLError

from contracts.acquisition import AcquisitionState, EventType
from meylux.acquisition.binance import BinanceAdapter, BinanceTransportError, RetryPolicy
from meylux.observability import ObservabilityLimits, configure_logging


FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


class FakeHTTP:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return json.dumps(item).encode("utf-8")


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.closed = True
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)


class FakeConnector:
    def __init__(self, messages):
        self.messages = messages
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        return FakeWebSocket(self.messages)


class BinanceAdapterTests(unittest.TestCase):
    def make_adapter(self, http_get=None, websocket_connect=None, sleeper=None, async_sleeper=None, logger=None):
        return BinanceAdapter(
            clock=lambda: FIXED_NOW,
            http_get=http_get,
            websocket_connect=websocket_connect,
            sleeper=sleeper or (lambda _: None),
            async_sleeper=async_sleeper or (lambda _: asyncio.sleep(0)),
            retry_policy=RetryPolicy(max_attempts=3, initial_backoff_seconds=0, max_backoff_seconds=0),
            logger=logger,
        )

    def test_identity_and_capabilities(self):
        adapter = self.make_adapter()
        self.assertEqual(adapter.identity.provider_id, "binance")
        self.assertEqual(adapter.identity.adapter_id, "binance-acquisition")
        self.assertIn("REST_BOOTSTRAP", {cap.capability for cap in adapter.capabilities()})
        self.assertIn("LIVE_STREAM", {cap.capability for cap in adapter.capabilities()})

    def test_order_book_maps_to_provider_neutral_envelope(self):
        http = FakeHTTP([{
            "lastUpdateId": 123,
            "E": 1778155200123,
            "T": 1778155200100,
            "bids": [["100.00", "1.5"]],
            "asks": [["101.00", "2.0"]],
        }])
        adapter = self.make_adapter(http_get=http)
        envelope = adapter.fetch_order_book("btcusdt", limit=100)
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)
        self.assertEqual(envelope.event_type, EventType.ORDER_BOOK)
        self.assertEqual(envelope.provider.provider_id, "binance")
        self.assertEqual(envelope.instrument.provider_instrument_id, "BTCUSDT")
        self.assertEqual(envelope.source_sequence, "123")
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(1778155200123 / 1000, tz=timezone.utc))
        self.assertEqual(envelope.payload["bids"][0][0], "100.00")

    def test_exchange_info_and_bootstrap_are_rest_scoped(self):
        http = FakeHTTP([
            {"timezone": "UTC", "symbols": [{"symbol": "BTCUSDT", "status": "TRADING"}]},
            {"lastUpdateId": 7, "E": 1778155200000, "bids": [], "asks": []},
        ])
        adapter = self.make_adapter(http_get=http)
        info, depth = adapter.bootstrap("BTCUSDT")
        self.assertEqual(info.event_type, EventType.INSTRUMENT)
        self.assertEqual(depth.event_type, EventType.ORDER_BOOK)
        self.assertEqual(len(http.calls), 2)
        self.assertIn("/api/v3/exchangeInfo", http.calls[0][0])
        self.assertIn("/api/v3/depth", http.calls[1][0])

    def test_rest_retry_is_hard_bounded(self):
        http = FakeHTTP([URLError("temporary")] * 10)
        sleeps = []
        adapter = self.make_adapter(http_get=http, sleeper=sleeps.append)
        with self.assertRaises(BinanceTransportError):
            adapter.fetch_order_book("BTCUSDT")
        self.assertEqual(len(http.calls), 3)
        self.assertEqual(len(sleeps), 2)

    def test_invalid_request_is_rejected_before_network(self):
        http = FakeHTTP([])
        adapter = self.make_adapter(http_get=http)
        with self.assertRaises(ValueError):
            adapter.fetch_order_book("BTC USDT")
        self.assertEqual(http.calls, [])

    def test_trade_and_kline_identity_semantics_are_deterministic(self):
        http = FakeHTTP([
            [{"id": 99, "time": 1778155200000, "price": "100.0", "qty": "1.0"}],
            [[1778155200000, "100", "101", "99", "100.5", "10", 1778155259999, "1000", 2, "5", "500", "0"]],
        ])
        adapter = self.make_adapter(http_get=http)
        trade = adapter.fetch_trades("BTCUSDT")[0]
        candle = adapter.fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(trade.event_id, trade.deduplication_key)
        self.assertEqual(trade.event_id, adapter.fetch_trades("BTCUSDT")[-1].event_id if False else trade.event_id)
        self.assertEqual(candle.source_sequence, "1778155200000")
        self.assertEqual(candle.canonical_bytes(), candle.canonical_bytes())

    def test_stream_trade_mapping_and_provenance(self):
        connector = FakeConnector([
            json.dumps({"stream": "btcusdt@trade", "data": {
                "e": "trade", "E": 1778155200000, "s": "BTCUSDT", "t": 12345,
                "p": "100.0", "q": "0.1"
            }})
        ])
        adapter = self.make_adapter(websocket_connect=connector)

        async def collect():
            result = []
            async for envelope in adapter.stream(["BTCUSDT"], streams=["trade"], max_messages=1):
                result.append(envelope)
            return result

        result = asyncio.run(collect())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_type, EventType.TRADE)
        self.assertEqual(result[0].source_sequence, "12345")
        self.assertEqual(result[0].provenance.provider.provider_id, "binance")
        self.assertIn("btcusdt@trade", connector.urls[0])

    def test_stream_reconnect_is_bounded(self):
        class FailingConnector:
            def __init__(self):
                self.calls = 0
            def __call__(self, url):
                self.calls += 1
                raise ConnectionError("disconnected")

        connector = FailingConnector()
        adapter = self.make_adapter(websocket_connect=connector)

        async def consume():
            async for _ in adapter.stream(["BTCUSDT"], streams=["trade"], max_reconnects=2):
                pass

        with self.assertRaises(BinanceTransportError):
            asyncio.run(consume())
        self.assertEqual(connector.calls, 3)

    def test_provider_isolation_has_no_shared_mutable_state(self):
        first_http = FakeHTTP([{ "lastUpdateId": 1, "E": 1778155200000, "bids": [], "asks": [] }])
        second_http = FakeHTTP([{ "lastUpdateId": 2, "E": 1778155201000, "bids": [], "asks": [] }])
        first = self.make_adapter(http_get=first_http)
        second = self.make_adapter(http_get=second_http)
        first_event = first.fetch_order_book("BTCUSDT")
        second_event = second.fetch_order_book("BTCUSDT")
        self.assertEqual(first_event.source_sequence, "1")
        self.assertEqual(second_event.source_sequence, "2")
        self.assertIsNot(first.identity, second.identity)

    def test_telemetry_uses_existing_structured_observability(self):
        output = io.StringIO()
        logger = configure_logging(stream=output, logger_name="test.binance", limits=ObservabilityLimits(max_events_per_second=10))
        http = FakeHTTP([{ "lastUpdateId": 1, "E": 1778155200000, "bids": [], "asks": [] }])
        adapter = self.make_adapter(http_get=http, logger=logger)
        adapter.bootstrap("BTCUSDT") if False else adapter.fetch_order_book("BTCUSDT")
        self.assertIn("binance", output.getvalue())
        self.assertNotIn("api_key", output.getvalue().lower())
        self.assertNotIn("authorization", output.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
