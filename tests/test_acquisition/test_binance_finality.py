import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from contracts.acquisition import AcquisitionState, ProviderIdentity, Provenance
from contracts.normalization import normalize
from meylux.acquisition.binance import BinanceAdapter, BinanceTransportError, RetryPolicy


UTC = timezone.utc
NOW = datetime(2026, 9, 25, 12, 0, 10, tzinfo=UTC)
OPEN_MS = 1780056000000
CLOSE_MS = OPEN_MS + 59999
EVENT_MS = OPEN_MS + 30000


class FakeHTTP:
    def __init__(self, response):
        self.response = response

    def __call__(self, url, timeout):
        return json.dumps(self.response).encode("utf-8")


class BinanceFinalityTests(unittest.TestCase):
    def make_adapter(self, http_get=None):
        return BinanceAdapter(
            clock=lambda: NOW,
            http_get=http_get,
            sleeper=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        )

    def stream_message(self, closed=True, **overrides):
        kline = {
            "t": OPEN_MS,
            "T": CLOSE_MS,
            "s": "BTCUSDT",
            "i": "1m",
            "f": 100,
            "L": 200,
            "o": "100",
            "c": "101",
            "h": "102",
            "l": "99",
            "v": "10",
            "n": 100,
            "x": closed,
            "q": "1005",
        }
        kline.update(overrides.pop("k", {}))
        payload = {
            "e": "kline",
            "E": EVENT_MS,
            "s": "BTCUSDT",
            "k": kline,
        }
        payload.update(overrides)
        return json.dumps(payload)

    def test_rest_historical_kline_never_synthesizes_finality(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        envelope = self.make_adapter(http_get=FakeHTTP([[row]])).fetch_klines("BTCUSDT", "1m")[0]

        self.assertIsNone(envelope.payload["k"]["x"])
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(OPEN_MS / 1000, tz=UTC))
        self.assertEqual(envelope.received_at, NOW)

        outcome = normalize(envelope)
        self.assertFalse(outcome.valid)
        self.assertTrue(any(issue.field == "is_closed" for issue in outcome.issues))

    def test_rest_close_time_does_not_depend_on_receipt_time(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        late = NOW + timedelta(hours=24)
        adapter = BinanceAdapter(
            clock=lambda: late,
            http_get=FakeHTTP([[row]]),
            sleeper=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        )
        envelope = adapter.fetch_klines("BTCUSDT", "1m")[0]
        self.assertIsNone(envelope.payload["k"]["x"])
        self.assertEqual(envelope.received_at, late)

    def test_websocket_explicit_false_is_preserved(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(False))
        self.assertIsNotNone(envelope)
        self.assertEqual(envelope.payload["k"]["x"], False)
        self.assertEqual(envelope.payload["k"]["T"], CLOSE_MS)
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC))

        outcome = normalize(envelope)
        self.assertTrue(outcome.valid)
        self.assertFalse(outcome.value.is_closed)

    def test_websocket_explicit_true_is_preserved(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(True))
        self.assertIsNotNone(envelope)
        self.assertEqual(envelope.payload["k"]["x"], True)

        outcome = normalize(envelope)
        self.assertTrue(outcome.valid)
        self.assertTrue(outcome.value.is_closed)

    def test_missing_finality_flag_is_rejected(self):
        message = json.loads(self.stream_message(True))
        del message["k"]["x"]
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(json.dumps(message))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_FINALITY")

    def test_non_boolean_finality_flag_is_rejected(self):
        with self.assertRaises(Exception) as raised:
            self.make_adapter().parse_stream_message(self.stream_message("true"))
        self.assertIn("BINANCE_INVALID_KLINE_FINALITY", str(raised.exception))

    def test_malformed_close_time_is_rejected(self):
        with self.assertRaises(Exception) as raised:
            self.make_adapter().parse_stream_message(self.stream_message(True, k={"T": OPEN_MS}))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_missing_open_time_is_rejected(self):
        message = json.loads(self.stream_message(True))
        del message["k"]["t"]
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(json.dumps(message))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_OPEN_TIME")

    def test_malformed_open_time_is_rejected(self):
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(self.stream_message(True, k={"t": "bad"}))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_OPEN_TIME")

    def test_missing_close_time_is_rejected(self):
        message = json.loads(self.stream_message(True))
        del message["k"]["T"]
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(json.dumps(message))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_malformed_close_time_is_rejected(self):
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(self.stream_message(True, k={"T": "bad"}))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_close_time_before_or_equal_open_time_is_rejected_as_temporal_contradiction(self):
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(self.stream_message(True, k={"T": OPEN_MS}))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_symbol_mismatch_is_rejected(self):
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(self.stream_message(True, k={"s": "ETHUSDT"}))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_KLINE_SYMBOL_MISMATCH")

    def test_event_time_close_time_and_receipt_time_remain_distinct(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(False))
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC))
        self.assertEqual(
            datetime.fromtimestamp(envelope.payload["k"]["T"] / 1000, tz=UTC),
            datetime.fromtimestamp(CLOSE_MS / 1000, tz=UTC),
        )
        self.assertEqual(envelope.received_at, NOW)
        self.assertNotEqual(envelope.event_time, envelope.received_at)

    def test_non_final_to_final_is_explicit_and_identity_distinct(self):
        adapter = self.make_adapter()
        non_final = adapter.parse_stream_message(self.stream_message(False))
        final = adapter.parse_stream_message(self.stream_message(True))

        self.assertNotEqual(non_final.event_id, final.event_id)
        self.assertNotEqual(non_final.canonical_bytes(), final.canonical_bytes())
        self.assertFalse(normalize(non_final).value.is_closed)
        self.assertTrue(normalize(final).value.is_closed)

    def test_final_then_conflicting_non_final_remains_explicit(self):
        adapter = self.make_adapter()
        final = adapter.parse_stream_message(self.stream_message(True))
        conflicting = adapter.parse_stream_message(self.stream_message(False))

        self.assertTrue(normalize(final).value.is_closed)
        self.assertFalse(normalize(conflicting).value.is_closed)
        self.assertNotEqual(final.event_id, conflicting.event_id)

    def test_replay_is_idempotent_for_same_provider_observation(self):
        adapter = self.make_adapter()
        first = adapter.parse_stream_message(self.stream_message(True))
        replay = adapter.parse_stream_message(self.stream_message(True))

        self.assertEqual(first.event_id, replay.event_id)
        self.assertEqual(first.deduplication_key, replay.deduplication_key)
        self.assertEqual(first.canonical_bytes(), replay.canonical_bytes())

    def test_provider_metadata_and_embedded_kline_symbol_mismatch_is_rejected(self):
        message = json.loads(self.stream_message(True))
        message["s"] = "ETHUSDT"
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(json.dumps(message))
        self.assertEqual(raised.exception.provider_error.code, "BINANCE_KLINE_SYMBOL_MISMATCH")

    def test_unsupported_provider_is_rejected_at_normalization_boundary(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(True))
        unsupported_identity = ProviderIdentity("unsupported", "unsupported-adapter", "1.0.0")
        unsupported = replace(
            envelope,
            provider=unsupported_identity,
            provenance=Provenance(
                envelope.provenance.provenance_id,
                unsupported_identity,
                envelope.provenance.acquisition_method,
            ),
        )
        outcome = normalize(unsupported)
        self.assertFalse(outcome.valid)
        self.assertTrue(any(issue.field == "provider" for issue in outcome.issues))

    def test_finality_is_not_promoted_by_close_time_or_receipt_time(self):
        late_non_final = self.make_adapter().parse_stream_message(
            self.stream_message(False, k={"T": OPEN_MS + 1})
        )
        self.assertFalse(normalize(late_non_final).value.is_closed)
        early_received_final = BinanceAdapter(
            clock=lambda: datetime.fromtimestamp((CLOSE_MS - 1000) / 1000, tz=UTC),
            sleeper=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        ).parse_stream_message(self.stream_message(True))
        self.assertTrue(normalize(early_received_final).value.is_closed)

    def test_finality_is_independent_of_local_clock(self):
        before_close = BinanceAdapter(
            clock=lambda: datetime.fromtimestamp((CLOSE_MS - 1000) / 1000, tz=UTC),
            sleeper=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        ).parse_stream_message(self.stream_message(True))
        after_close = BinanceAdapter(
            clock=lambda: datetime.fromtimestamp((CLOSE_MS + 3600000) / 1000, tz=UTC),
            sleeper=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        ).parse_stream_message(self.stream_message(True))
        self.assertTrue(normalize(before_close).value.is_closed)
        self.assertTrue(normalize(after_close).value.is_closed)
        self.assertEqual(before_close.event_id, after_close.event_id)
        self.assertNotEqual(before_close.received_at, after_close.received_at)

    def test_knowledge_time_is_not_created_or_inferred(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(True))
        self.assertFalse(hasattr(envelope, "knowledge_time"))
        self.assertNotIn("knowledge_time", envelope.payload)
        self.assertFalse(hasattr(normalize(envelope).value, "knowledge_time"))

    def test_canonical_serialization_is_deterministic_across_equivalent_adapters(self):
        first = self.make_adapter().parse_stream_message(self.stream_message(True))
        second = self.make_adapter().parse_stream_message(self.stream_message(True))
        self.assertEqual(first.canonical_bytes(), second.canonical_bytes())
        self.assertEqual(first.event_id, second.event_id)

    def test_historical_row_with_seven_fields_remains_supported_by_existing_adapter_policy(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS]
        envelope = self.make_adapter(http_get=FakeHTTP([[row]])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertIsNone(envelope.payload["k"]["x"])
        self.assertEqual(tuple(envelope.payload["row"]), tuple(row))

    def test_historical_row_shorter_than_minimum_is_rejected(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10"]
        envelope = self.make_adapter(http_get=FakeHTTP([[row]])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.state, AcquisitionState.INVALID)
        self.assertEqual(envelope.provider_error.code, "BINANCE_INVALID_KLINE_ROW")

    def test_historical_row_with_malformed_close_time_is_rejected(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", "bad"]
        envelope = self.make_adapter(http_get=FakeHTTP([[row]])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.state, AcquisitionState.INVALID)
        self.assertEqual(envelope.provider_error.code, "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_stream_finality_does_not_change_canonical_contract_identity_shape(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(True))
        outcome = normalize(envelope)
        self.assertTrue(outcome.valid)
        self.assertEqual(outcome.value.instrument_id, "BINANCE:BTCUSDT")
        self.assertEqual(outcome.value.timeframe, "1m")
        self.assertEqual(outcome.value.close_time, datetime.fromtimestamp(CLOSE_MS / 1000, tz=UTC))

    def test_binance_provider_isolation_is_explicit(self):
        adapter = self.make_adapter()
        self.assertEqual(adapter.identity.provider_id, "binance")
        self.assertEqual(adapter.identity.adapter_id, "binance-acquisition")
        self.assertFalse(any("mexc" in name.lower() for name in dir(adapter)))


if __name__ == "__main__":
    unittest.main()
