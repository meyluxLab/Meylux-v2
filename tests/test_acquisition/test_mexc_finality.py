import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from contracts.acquisition import AcquisitionState, EventType, InstrumentIdentity, AcquisitionEnvelope, ProviderIdentity, Provenance
from contracts.canonical.foundation import ValidationCode, ValidationResult
from contracts.normalization import normalize
from meylux.acquisition.mexc import MEXCAdapter, RetryPolicy


UTC = timezone.utc
NOW = datetime(2026, 9, 25, 12, 0, 10, tzinfo=UTC)
OPEN_MS = 1780056000000
CLOSE_MS = OPEN_MS + 59999
EVENT_MS = OPEN_MS + 30000


class FakeHTTP:
    def __init__(self, response):
        self.response = response

    def __call__(self, _url, _timeout):
        return json.dumps(self.response).encode("utf-8")


def adapter(clock=lambda: NOW, http_get=None):
    return MEXCAdapter(
        clock=clock,
        http_get=http_get,
        sleeper=lambda _: None,
        retry_policy=RetryPolicy(max_attempts=1),
    )


def kline_payload(**overrides):
    data = {
        "interval": "Min1",
        "windowStart": OPEN_MS // 1000,
        "windowEnd": CLOSE_MS // 1000,
        "openingPrice": "100",
        "closingPrice": "105",
        "highestPrice": "110",
        "lowestPrice": "90",
        "volume": "12",
        "amount": "1250",
    }
    data.update(overrides)
    return {"data": data}


def envelope(payload, *, received_at=NOW):
    provider = ProviderIdentity("mexc", "mexc-acquisition", "1.1.0")
    instrument = InstrumentIdentity("BTCUSDT", "BTCUSDT")
    provenance = Provenance("mexc:test", provider, "TEST")
    return AcquisitionEnvelope(
        provider,
        instrument,
        provenance,
        EventType.CANDLE,
        datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC),
        received_at,
        AcquisitionState.AVAILABLE,
        payload,
        "kline-1",
    )


class MEXCFinalityCorrectionTests(unittest.TestCase):
    def assert_unavailable_finality(self, outcome):
        self.assertFalse(outcome.valid)
        self.assertIsNone(outcome.value)
        self.assertEqual(outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(
            issue.code is ValidationCode.REQUIRED_MISSING and issue.field == "is_closed"
            for issue in outcome.issues
        ))

    def test_valid_websocket_shape_is_rejected_before_canonical_candle_construction(self):
        outcome = normalize(envelope(kline_payload()))
        self.assert_unavailable_finality(outcome)

    def test_valid_rest_row_is_preserved_at_acquisition_and_rejected_at_normalization(self):
        row = [OPEN_MS, "100", "110", "90", "105", "12", CLOSE_MS, "1250"]
        received = NOW
        acquired = adapter(http_get=FakeHTTP([row])).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(acquired.state, AcquisitionState.AVAILABLE)
        self.assertEqual(acquired.payload["row"], row)
        self.assertEqual(acquired.provenance.acquisition_method, "REST_KLINES")
        self.assertEqual(acquired.received_at, received)
        self.assert_unavailable_finality(normalize(acquired))

    def test_mexc_finality_unavailable_precedes_malformed_window_start(self):
        outcome = normalize(envelope(kline_payload(windowStart="bad")))
        self.assert_unavailable_finality(outcome)

    def test_mexc_finality_unavailable_precedes_malformed_window_end(self):
        outcome = normalize(envelope(kline_payload(windowEnd="bad")))
        self.assert_unavailable_finality(outcome)

    def test_mexc_finality_unavailable_precedes_non_increasing_window(self):
        outcome = normalize(envelope(kline_payload(windowEnd=OPEN_MS // 1000)))
        self.assert_unavailable_finality(outcome)

    def test_mexc_finality_unavailable_precedes_malformed_ohlcv(self):
        outcome = normalize(envelope(kline_payload(closingPrice="not-a-decimal")))
        self.assert_unavailable_finality(outcome)

    def test_mexc_finality_unavailable_precedes_contradictory_provider_metadata(self):
        payload = kline_payload()
        payload["symbol"] = "ETHUSDT"
        outcome = normalize(envelope(payload))
        self.assert_unavailable_finality(outcome)

    def test_missing_required_kline_shape_remains_explicitly_rejected(self):
        outcome = normalize(envelope({"data": {}}))
        self.assertFalse(outcome.valid)
        self.assertIsNone(outcome.value)
        self.assertTrue(any(issue.field == "timeframe" for issue in outcome.issues))

    def test_malicious_non_authoritative_finality_fields_do_not_create_canonical_truth(self):
        payload = kline_payload()
        payload["data"]["closed"] = True
        payload["data"]["isClosed"] = True
        payload["data"]["finalized"] = True
        outcome = normalize(envelope(payload))
        self.assert_unavailable_finality(outcome)

    def test_receipt_time_cannot_promote_mexc_finality(self):
        early = normalize(envelope(kline_payload(), received_at=datetime(2026, 9, 25, 11, 0, tzinfo=UTC)))
        late = normalize(envelope(kline_payload(), received_at=datetime(2026, 9, 26, 11, 0, tzinfo=UTC)))
        self.assert_unavailable_finality(early)
        self.assert_unavailable_finality(late)

    def test_repeated_observations_remain_non_canonical(self):
        first = envelope(kline_payload())
        replay = envelope(kline_payload())
        self.assertEqual(first.event_id, replay.event_id)
        self.assertEqual(first.deduplication_key, replay.deduplication_key)
        self.assert_unavailable_finality(normalize(first))
        self.assert_unavailable_finality(normalize(replay))

    def test_rejection_does_not_mutate_acquisition_identity(self):
        source = envelope(kline_payload())
        event_id = source.event_id
        canonical_bytes = source.canonical_bytes()
        outcome = normalize(source)
        self.assert_unavailable_finality(outcome)
        self.assertEqual(source.event_id, event_id)
        self.assertEqual(source.canonical_bytes(), canonical_bytes)
        self.assertEqual(source.provenance.acquisition_method, "TEST")

    def test_rest_close_time_is_evidence_only(self):
        row = [OPEN_MS, "100", "110", "90", "105", "12", CLOSE_MS, "1250"]
        envelope_a = adapter(
            clock=lambda: datetime(2026, 9, 25, 12, 0, tzinfo=UTC),
            http_get=FakeHTTP([row]),
        ).fetch_klines("BTCUSDT", "1m")[0]
        envelope_b = adapter(
            clock=lambda: datetime(2026, 9, 27, 12, 0, tzinfo=UTC),
            http_get=FakeHTTP([row]),
        ).fetch_klines("BTCUSDT", "1m")[0]
        self.assertEqual(envelope_a.payload["row"][6], CLOSE_MS)
        self.assertEqual(envelope_b.payload["row"][6], CLOSE_MS)
        self.assert_unavailable_finality(normalize(envelope_a))
        self.assert_unavailable_finality(normalize(envelope_b))

    def test_binance_finality_path_remains_provider_specific(self):
        provider = ProviderIdentity("binance", "binance-acquisition", "1.0.0")
        instrument = InstrumentIdentity("BINANCE:BTCUSDT", "BTCUSDT")
        provenance = Provenance("binance:test", provider, "TEST")
        payload = {
            "k": {
                "i": "1m", "t": OPEN_MS, "T": CLOSE_MS, "o": "100",
                "h": "110", "l": "90", "c": "105", "v": "12", "x": True,
            }
        }
        e = AcquisitionEnvelope(
            provider, instrument, provenance, EventType.CANDLE,
            datetime.fromtimestamp(EVENT_MS / 1000, tz=UTC), NOW,
            AcquisitionState.AVAILABLE, payload, "binance-1",
        )
        outcome = normalize(e)
        self.assertTrue(outcome.valid)
        self.assertTrue(outcome.value.is_closed)

    def test_unsupported_provider_still_rejected(self):
        source = envelope(kline_payload())
        unsupported = replace(
            source,
            provider=ProviderIdentity("unsupported", "unsupported-adapter", "1.0.0"),
        )
        outcome = normalize(unsupported)
        self.assertFalse(outcome.valid)
        self.assertIsNone(outcome.value)
        self.assertTrue(any(issue.field == "provider" for issue in outcome.issues))


if __name__ == "__main__":
    unittest.main()
