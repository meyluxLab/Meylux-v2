import json
import unittest
from datetime import datetime, timedelta, timezone

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
)
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
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        return json.dumps(self.response).encode("utf-8")


class BinanceFinalityTests(unittest.TestCase):
    def make_adapter(self, http_get=None, clock=None):
        return BinanceAdapter(
            clock=clock or (lambda: NOW),
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

    def assert_provider_error(self, message, code):
        with self.assertRaises(BinanceTransportError) as raised:
            self.make_adapter().parse_stream_message(message)
        self.assertIsNotNone(raised.exception.provider_error)
        self.assertEqual(raised.exception.provider_error.code, code)
        self.assertEqual(raised.exception.state, AcquisitionState.INVALID)

    def test_rest_historical_kline_never_synthesizes_finality(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        envelope = self.make_adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]

        self.assertIsNone(envelope.payload["k"]["x"])
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(OPEN_MS / 1000, tz=UTC))
        self.assertEqual(envelope.received_at, NOW)
        self.assertNotIn("knowledge_time", envelope.payload)

        outcome = normalize(envelope)
        self.assertFalse(outcome.valid)
        self.assertTrue(any(issue.field == "is_closed" for issue in outcome.issues))

    def test_rest_close_time_does_not_depend_on_receipt_time(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        late = NOW + timedelta(hours=24)
        early = NOW - timedelta(days=24)

        for clock in (early, late):
            with self.subTest(clock=clock):
                envelope = self.make_adapter(
                    http_get=FakeHTTP([row]),
                    clock=lambda clock=clock: clock,
                ).fetch_klines("BTCUSDT", "1m")[0]
                self.assertIsNone(envelope.payload["k"]["x"])
                self.assertEqual(envelope.payload["k"]["T"], CLOSE_MS)
                self.assertEqual(envelope.received_at, clock)

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
        self.assert_provider_error(json.dumps(message), "BINANCE_INVALID_KLINE_FINALITY")

    def test_non_boolean_finality_flag_is_rejected(self):
        self.assert_provider_error(
            self.stream_message("true"),
            "BINANCE_INVALID_KLINE_FINALITY",
        )

    def test_missing_open_time_is_rejected(self):
        message = json.loads(self.stream_message(True))
        del message["k"]["t"]
        self.assert_provider_error(json.dumps(message), "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_malformed_open_time_is_rejected(self):
        self.assert_provider_error(
            self.stream_message(True, k={"t": "not-an-epoch"}),
            "BINANCE_INVALID_KLINE_CLOSE_TIME",
        )

    def test_missing_close_time_is_rejected(self):
        message = json.loads(self.stream_message(True))
        del message["k"]["T"]
        self.assert_provider_error(json.dumps(message), "BINANCE_INVALID_KLINE_CLOSE_TIME")

    def test_malformed_close_time_is_rejected(self):
        self.assert_provider_error(
            self.stream_message(True, k={"T": "not-an-epoch"}),
            "BINANCE_INVALID_KLINE_CLOSE_TIME",
        )

    def test_close_time_not_after_open_time_is_rejected(self):
        self.assert_provider_error(
            self.stream_message(True, k={"T": OPEN_MS}),
            "BINANCE_INVALID_KLINE_CLOSE_TIME",
        )

    def test_provider_metadata_and_embedded_kline_symbol_mismatch_is_rejected(self):
        self.assert_provider_error(
            self.stream_message(True, k={"s": "ETHUSDT"}),
            "BINANCE_KLINE_SYMBOL_MISMATCH",
        )

    def test_empty_embedded_kline_interval_is_rejected_as_provider_payload_mismatch(self):
        self.assert_provider_error(
            self.stream_message(True, k={"i": ""}),
            "BINANCE_INVALID_KLINE_INTERVAL",
        )

    def test_event_time_close_time_and_receipt_time_remain_distinct(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(False))
        self.assertEqual(envelope.event_time, datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC))
        self.assertEqual(
            datetime.fromtimestamp(envelope.payload["k"]["T"] / 1000, tz=UTC),
            datetime.fromtimestamp(CLOSE_MS / 1000, tz=UTC),
        )
        self.assertEqual(envelope.received_at, NOW)
        self.assertNotEqual(envelope.event_time, envelope.received_at)

    def test_finality_is_not_promoted_by_close_time_event_time_or_local_clock(self):
        before_close = datetime.fromtimestamp((CLOSE_MS - 1) / 1000, tz=UTC)
        after_close = datetime.fromtimestamp((CLOSE_MS + 1) / 1000, tz=UTC)

        for closed, clock in ((True, before_close), (True, after_close), (False, before_close), (False, after_close)):
            with self.subTest(closed=closed, clock=clock):
                envelope = self.make_adapter(clock=lambda clock=clock: clock).parse_stream_message(
                    self.stream_message(closed)
                )
                self.assertEqual(envelope.payload["k"]["x"], closed)
                self.assertEqual(envelope.payload["k"]["T"], CLOSE_MS)
                self.assertEqual(envelope.event_time, datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC))
                self.assertEqual(envelope.received_at, clock)

    def test_contradictory_temporal_observation_preserves_authoritative_x(self):
        # x=True is the provider's explicit finality signal even when the
        # operational receipt clock is before the kline close boundary. The
        # adapter does not invent a second contradiction state or override x.
        receipt_before_close = datetime.fromtimestamp((CLOSE_MS - 1) / 1000, tz=UTC)
        envelope = self.make_adapter(clock=lambda: receipt_before_close).parse_stream_message(
            self.stream_message(True)
        )
        self.assertTrue(envelope.payload["k"]["x"])
        self.assertLess(envelope.received_at, datetime.fromtimestamp(CLOSE_MS / 1000, tz=UTC))

    def test_non_final_to_final_is_explicit_and_identity_distinct(self):
        adapter = self.make_adapter()
        non_final = adapter.parse_stream_message(self.stream_message(False))
        final = adapter.parse_stream_message(self.stream_message(True))

        self.assertNotEqual(non_final.event_id, final.event_id)
        self.assertNotEqual(non_final.identity_bytes(), final.identity_bytes())
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
        self.assertEqual(first.identity_bytes(), replay.identity_bytes())
        self.assertEqual(first.canonical_bytes(), replay.canonical_bytes())

    def test_canonical_serialization_is_deterministic_for_same_observation(self):
        adapter = self.make_adapter()
        first = adapter.parse_stream_message(self.stream_message(True))
        second = adapter.parse_stream_message(self.stream_message(True))

        self.assertEqual(first.canonical_bytes(), second.canonical_bytes())
        self.assertEqual(first.event_id, second.event_id)

    def test_identity_material_includes_finality_payload_deterministically(self):
        adapter = self.make_adapter()
        open_observation = adapter.parse_stream_message(self.stream_message(False))
        final_observation = adapter.parse_stream_message(self.stream_message(True))

        self.assertIn(b'"x":false', open_observation.identity_bytes())
        self.assertIn(b'"x":true', final_observation.identity_bytes())
        self.assertNotEqual(open_observation.identity_bytes(), final_observation.identity_bytes())

    def test_stream_finality_does_not_change_canonical_contract_identity_shape(self):
        envelope = self.make_adapter().parse_stream_message(self.stream_message(True))
        outcome = normalize(envelope)
        self.assertTrue(outcome.valid)
        self.assertEqual(outcome.value.instrument_id, "BINANCE:BTCUSDT")
        self.assertEqual(outcome.value.timeframe, "1m")
        self.assertEqual(outcome.value.close_time, datetime.fromtimestamp(CLOSE_MS / 1000, tz=UTC))

    def test_historical_row_preserves_full_binance_wire_row(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        envelope = self.make_adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(tuple(envelope.payload["row"]), tuple(row))
        self.assertEqual(envelope.payload["k"]["T"], CLOSE_MS)
        self.assertIsNone(envelope.payload["k"]["x"])

    def test_seven_field_historical_row_is_accepted_by_existing_minimum_shape_policy(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS]
        envelope = self.make_adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)
        self.assertIsNone(envelope.payload["k"]["x"])

    def test_short_historical_row_is_rejected_as_malformed_response_shape(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10"]
        envelope = self.make_adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.state, AcquisitionState.INVALID)
        self.assertEqual(envelope.provider_error.code, "BINANCE_INVALID_KLINE_ROW")

    def test_malformed_historical_close_time_is_rejected_by_normalization(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", "not-an-epoch", "1005", 100, "5", "502.5", "0"]
        envelope = self.make_adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)
        self.assertIsNone(envelope.payload["k"]["x"])

        outcome = normalize(envelope)
        self.assertFalse(outcome.valid)
        self.assertTrue(any(issue.field == "close_time" for issue in outcome.issues))

    def test_historical_missing_finality_never_becomes_closed_even_after_long_delay(self):
        row = [OPEN_MS, "100", "102", "99", "101", "10", CLOSE_MS, "1005", 100, "5", "502.5", "0"]
        very_late = datetime.fromtimestamp((CLOSE_MS + 10 * 365 * 24 * 3600 * 1000) / 1000, tz=UTC)
        envelope = self.make_adapter(
            http_get=FakeHTTP([row]),
            clock=lambda: very_late,
        ).fetch_klines("BTCUSDT", "1m")[0]

        self.assertIsNone(envelope.payload["k"]["x"])
        outcome = normalize(envelope)
        self.assertFalse(outcome.valid)

    def test_unsupported_provider_is_rejected_at_normalization_mapping_boundary(self):
        provider = ProviderIdentity("unsupported-provider", "unsupported-adapter", "1.0.0")
        instrument = InstrumentIdentity("UNSUPPORTED:BTCUSDT", "BTCUSDT")
        provenance = Provenance("unsupported-provenance", provider, "TEST")
        envelope = AcquisitionEnvelope(
            provider=provider,
            instrument=instrument,
            provenance=provenance,
            event_type=EventType.CANDLE,
            event_time=datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC),
            received_at=NOW,
            state=AcquisitionState.AVAILABLE,
            payload={
                "k": {
                    "t": OPEN_MS,
                    "T": CLOSE_MS,
                    "i": "1m",
                    "o": "100",
                    "h": "102",
                    "l": "99",
                    "c": "101",
                    "v": "10",
                    "x": True,
                }
            },
        )

        outcome = normalize(envelope)
        self.assertFalse(outcome.valid)
        self.assertTrue(any(issue.field == "timeframe" for issue in outcome.issues))
        self.assertTrue(any("unsupported provider mapping" in issue.message for issue in outcome.issues))

    def test_existing_valid_binance_acquisition_behavior_remains_available(self):
        http = FakeHTTP([{
            "lastUpdateId": 123,
            "E": EVENT_MS,
            "T": EVENT_MS,
            "bids": [["100.00", "1.5"]],
            "asks": [["101.00", "2.0"]],
        }])
        envelope = self.make_adapter(http_get=http).fetch_order_book("BTCUSDT", limit=100)
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)
        self.assertEqual(envelope.event_type, EventType.ORDER_BOOK)
        self.assertEqual(envelope.provider.provider_id, "binance")
        self.assertEqual(envelope.source_sequence, "123")

    def test_no_mexc_implementation_or_semantic_path_is_introduced_here(self):
        self.assertEqual(self.make_adapter().identity.provider_id, "binance")
        self.assertEqual(self.make_adapter().identity.adapter_id, "binance-acquisition")


if __name__ == "__main__":
    unittest.main()
