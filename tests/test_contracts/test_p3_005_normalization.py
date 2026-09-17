from datetime import datetime, timezone
from decimal import Decimal
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
)
from contracts.canonical import CanonicalCandle, CanonicalOrderBook, CanonicalTrade
from contracts.normalization import SID, VERSION, normalize

UTC = timezone.utc
NOW = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


def envelope(provider, event_type, payload, *, instrument=None, method="TEST", state=AcquisitionState.AVAILABLE):
    identity = InstrumentIdentity(instrument or f"{provider.upper()}:BTCUSDT", "BTCUSDT")
    p = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
    provenance = Provenance(f"{provider}:test", p, method)
    return AcquisitionEnvelope(
        provider=p,
        instrument=identity,
        provenance=provenance,
        event_type=event_type,
        event_time=NOW,
        received_at=NOW,
        state=state,
        payload=payload,
        source_sequence="42",
    )


class P3005NormalizationTests(unittest.TestCase):
    def test_identity_and_version(self):
        self.assertEqual(SID, "STEP-P3-005")
        self.assertEqual(VERSION, "1.0.0")

    def test_valid_binance_trade_maps_to_canonical(self):
        env = envelope("binance", EventType.TRADE, {
            "e": "trade", "s": "BTCUSDT", "t": 7, "T": 1757592000000,
            "p": "100.25", "q": "2", "m": False, "Y": "200.50",
            "transportField": "must-not-leak",
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertIsInstance(result.value, CanonicalTrade)
        self.assertEqual(result.value.trade_id, "7")
        self.assertEqual(result.value.price, Decimal("100.25"))
        self.assertEqual(result.value.quantity, Decimal("2"))
        self.assertEqual(result.value.aggressor_side, "BUY")
        self.assertEqual(result.value.quote_quantity, Decimal("200.50"))
        self.assertFalse(hasattr(result.value, "transportField"))

    def test_valid_mexc_trade_maps_without_unsupported_side_guess(self):
        env = envelope("mexc", EventType.TRADE, {
            "price": "100", "qty": "2", "time": 1757592000000,
            "tradeId": "trade-7", "eventtype": "deal",
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertIsInstance(result.value, CanonicalTrade)
        self.assertEqual(result.value.trade_id, "trade-7")
        self.assertIsNone(result.value.aggressor_side)

    def test_valid_binance_stream_candle_maps_timeframe_and_ohlcv(self):
        env = envelope("binance", EventType.CANDLE, {
            "e": "kline", "s": "BTCUSDT", "k": {
                "i": "1m", "t": 1757592000000, "T": 1757592059999,
                "o": "100", "h": "110", "l": "90", "c": "105",
                "v": "12", "q": "1250", "n": 10, "x": True,
                "providerOnly": "x",
            }
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertIsInstance(result.value, CanonicalCandle)
        self.assertEqual(result.value.timeframe, "1m")
        self.assertEqual(result.value.open, Decimal("100"))
        self.assertEqual(result.value.volume, Decimal("12"))
        self.assertTrue(result.value.is_closed)

    def test_valid_mexc_stream_candle_maps_protobuf_semantics(self):
        env = envelope("mexc", EventType.CANDLE, {
            "channel": "spot@public.kline.v3.api.pb@BTCUSDT@Min1",
            "symbol": "BTCUSDT", "sendtime": 1757592000001,
            "data": {
                "interval": "Min1", "windowStart": 1757592000,
                "windowEnd": 1757592059, "openingPrice": "100",
                "closingPrice": "105", "highestPrice": "110",
                "lowestPrice": "90", "volume": "12", "amount": "1250",
            },
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertEqual(result.value.timeframe, "Min1")
        self.assertEqual(result.value.close, Decimal("105"))

    def test_valid_binance_order_book_maps_snapshot(self):
        env = envelope("binance", EventType.ORDER_BOOK, {
            "lastUpdateId": 123,
            "bids": [["100", "2"], ["99", "1"]],
            "asks": [["101", "1"], ["102", "2"]],
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertIsInstance(result.value, CanonicalOrderBook)
        self.assertEqual(result.value.bids[0], (Decimal("100"), Decimal("2")))
        self.assertEqual(result.value.asks[0], (Decimal("101"), Decimal("1")))

    def test_valid_mexc_order_book_maps_snapshot_lists(self):
        env = envelope("mexc", EventType.ORDER_BOOK, {
            "lastUpdateId": 9,
            "bids": [["100", "2"]],
            "asks": [["101", "1"]],
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertEqual(result.value.instrument_id, "MEXC:BTCUSDT")

    def test_instrument_mapping_preserves_identity_and_provenance(self):
        env = envelope("binance", EventType.INSTRUMENT, {
            "symbols": [{
                "symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT",
                "status": "TRADING", "pricePrecision": 2, "quantityPrecision": 6,
                "providerOnly": "wire",
            }]
        }, instrument="BINANCE:BTCUSDT")
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertEqual(result.value.instrument_id, "BINANCE:BTCUSDT")
        self.assertEqual(result.value.market_type, "SPOT")
        self.assertEqual(result.value.contract_type, "SPOT")
        self.assertEqual(result.value.unit, "BTC")
        self.assertEqual(result.value.provenance_id, "binance:test")

    def test_provider_specific_alias_is_only_translated_when_supported(self):
        env = envelope("binance", EventType.TRADE, {
            "price": "100", "qty": "2", "id": 9, "time": 1757592000000,
            "isBuyerMaker": True,
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertEqual(result.value.aggressor_side, "SELL")

    def test_ambiguous_mexc_trade_type_is_not_guessed(self):
        env = envelope("mexc", EventType.TRADE, {
            "price": "100", "quantity": "2", "tradeId": "7", "time": 1757592000000,
            "tradeType": 1,
        })
        result = normalize(env)
        self.assertTrue(result.valid)
        self.assertIsNone(result.value.aggressor_side)

    def test_unsupported_event_is_explicitly_rejected(self):
        env = envelope("binance", EventType.UPDATE, {"foo": "bar"})
        result = normalize(env)
        self.assertFalse(result.valid)
        self.assertEqual(result.result.value, "rejected")
        self.assertEqual(result.issues[0].field, "event_type")

    def test_non_available_input_cannot_be_promoted(self):
        env = envelope("binance", EventType.TRADE, {}, state=AcquisitionState.INVALID)
        result = normalize(env)
        self.assertFalse(result.valid)
        self.assertIsNone(result.value)

    def test_malformed_trade_is_rejected_without_fallback(self):
        env = envelope("binance", EventType.TRADE, {"p": "not-a-price", "q": "2", "t": 1, "T": 1757592000000})
        result = normalize(env)
        self.assertFalse(result.valid)
        self.assertIsNone(result.value)

    def test_float_market_value_is_rejected(self):
        env = envelope("binance", EventType.TRADE, {"p": 100.25, "q": "2", "t": 1, "T": 1757592000000})
        result = normalize(env)
        self.assertFalse(result.valid)

    def test_zero_order_book_quantity_is_rejected_not_promoted(self):
        env = envelope("mexc", EventType.ORDER_BOOK, {"bids": [["100", "0"]], "asks": [["101", "1"]]})
        result = normalize(env)
        self.assertFalse(result.valid)
        self.assertIsNone(result.value)

    def test_missing_candle_timeframe_is_rejected(self):
        env = envelope("binance", EventType.CANDLE, {"o": "100", "h": "110", "l": "90", "c": "105", "v": "1"})
        result = normalize(env)
        self.assertFalse(result.valid)

    def test_deterministic_repeated_mapping(self):
        env = envelope("binance", EventType.TRADE, {"p": "100", "q": "2", "t": 1, "T": 1757592000000})
        first = normalize(env)
        second = normalize(env)
        self.assertTrue(first.valid)
        self.assertEqual(first.value, second.value)

    def test_provenance_is_preserved_for_supported_mapping_types(self):
        cases = [
            (EventType.TRADE, {"p": "100", "q": "2", "t": 1, "T": 1757592000000}),
            (EventType.ORDER_BOOK, {"bids": [["100", "2"]], "asks": [["101", "1"]]}),
            (EventType.CANDLE, {"k": {"i": "1m", "t": 1757592000000, "T": 1757592059999, "o": "100", "h": "110", "l": "90", "c": "105", "v": "1"}}),
        ]
        for event_type, payload in cases:
            with self.subTest(event_type=event_type):
                result = normalize(envelope("binance", event_type, payload))
                self.assertTrue(result.valid)
                self.assertEqual(result.value.provenance_id, "binance:test")


if __name__ == "__main__":
    unittest.main()
