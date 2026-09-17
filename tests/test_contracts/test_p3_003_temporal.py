"""Evidence tests for TO-P3-003 temporal, sequence, and completeness validation."""

from datetime import datetime, timedelta, timezone
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
)
from contracts.canonical.foundation import ValidationCode, ValidationResult
from contracts.temporal import (
    validate_completeness,
    validate_sequence,
    validate_temporal_evidence,
    validate_temporal_order,
    validate_temporal_sequence_completeness,
)


UTC = timezone.utc
BASE = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


def envelope(
    offset_seconds: int,
    *,
    sequence: str | None = None,
    payload_value: str | None = None,
) -> AcquisitionEnvelope:
    provider = ProviderIdentity("binance", "binance-spot", "1.0.0")
    instrument = InstrumentIdentity("BTC-USD-SPOT", "BTCUSDT")
    provenance = Provenance("prov:fixture/1", provider, "websocket")
    event_time = BASE + timedelta(seconds=offset_seconds)
    return AcquisitionEnvelope(
        provider=provider,
        instrument=instrument,
        provenance=provenance,
        event_type=EventType.TRADE,
        event_time=event_time,
        received_at=event_time + timedelta(seconds=1),
        state=AcquisitionState.AVAILABLE,
        payload={"value": payload_value or str(offset_seconds)},
        source_sequence=sequence,
    )


class TemporalSequenceCompletenessTests(unittest.TestCase):
    def test_valid_timestamp_and_event_receive_order_are_accepted(self):
        result = validate_temporal_evidence(envelope(0), reference_time=BASE + timedelta(seconds=2))
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_event_time_after_received_at_is_rejected(self):
        item = envelope(0)
        bad = AcquisitionEnvelope(
            provider=item.provider,
            instrument=item.instrument,
            provenance=item.provenance,
            event_type=item.event_type,
            event_time=item.received_at + timedelta(seconds=1),
            received_at=item.received_at,
            state=item.state,
            payload=item.payload,
            source_sequence=item.source_sequence,
        )
        result = validate_temporal_evidence(bad)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(issue.field == "event_time" for issue in result.outcome.issues))

    def test_future_event_is_checked_only_against_explicit_reference(self):
        result = validate_temporal_evidence(envelope(10), reference_time=BASE)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(issue.code is ValidationCode.INVALID_VALUE for issue in result.outcome.issues))

    def test_chronological_order_accepts_monotonic_sequence(self):
        result = validate_temporal_order((envelope(0, sequence="1"), envelope(1, sequence="2")))
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_out_of_order_temporal_evidence_is_rejected(self):
        result = validate_temporal_order((envelope(1, sequence="2"), envelope(0, sequence="1")))
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any("chronological" in issue.message for issue in result.outcome.issues))

    def test_duplicate_sequence_is_rejected_within_provider_instrument_stream(self):
        result = validate_sequence((envelope(0, sequence="7"), envelope(1, sequence="7")))
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any("duplicate" in issue.message for issue in result.outcome.issues))

    def test_contiguous_sequence_requires_explicit_authoritative_successor(self):
        result = validate_sequence(
            (envelope(0, sequence="7"), envelope(1, sequence="8")),
            sequence_successor=lambda value: str(int(value) + 1),
        )
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_sequence_gap_is_rejected_when_authoritative_successor_is_supplied(self):
        result = validate_sequence(
            (envelope(0, sequence="7"), envelope(1, sequence="9")),
            sequence_successor=lambda value: str(int(value) + 1),
        )
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any("discontinuous" in issue.message for issue in result.outcome.issues))

    def test_opaque_sequence_does_not_invent_numeric_gap_semantics(self):
        result = validate_sequence((envelope(0, sequence="A-1"), envelope(1, sequence="A-3")))
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_missing_sequence_is_tolerated_when_contract_does_not_require_it(self):
        result = validate_sequence((envelope(0), envelope(1)))
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_cadence_gap_is_rejected_only_with_authoritative_cadence(self):
        result = validate_completeness(
            (envelope(0), envelope(2)),
            cadence_successor=lambda value: value + timedelta(seconds=1),
        )
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any("cadence-continuous" in issue.message for issue in result.outcome.issues))

    def test_complete_boundary_is_deterministic(self):
        items = (envelope(0, sequence="1"), envelope(1, sequence="2"))
        first = validate_temporal_sequence_completeness(
            items,
            reference_time=BASE + timedelta(seconds=3),
            sequence_successor=lambda value: str(int(value) + 1),
            cadence_successor=lambda value: value + timedelta(seconds=1),
        )
        second = validate_temporal_sequence_completeness(
            items,
            reference_time=BASE + timedelta(seconds=3),
            sequence_successor=lambda value: str(int(value) + 1),
            cadence_successor=lambda value: value + timedelta(seconds=1),
        )
        self.assertEqual(first.outcome.result, ValidationResult.VALID)
        self.assertEqual(first.outcome, second.outcome)

    def test_provider_neutral_identity_is_not_rebuilt_or_modified(self):
        first = envelope(0, sequence="1")
        second = envelope(1, sequence="2")
        self.assertNotEqual(first.event_id, second.event_id)
        result = validate_temporal_sequence_completeness((first, second))
        self.assertEqual(result.outcome.result, ValidationResult.VALID)


if __name__ == "__main__":
    unittest.main()
