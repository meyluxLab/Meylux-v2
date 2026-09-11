from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    CapabilityState,
    EventType,
    InstrumentIdentity,
    ProviderCapability,
    ProviderError,
    ProviderIdentity,
    Provenance,
    SID,
    VERSION,
)


UTC = timezone.utc
EVENT_TIME = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
RECEIVED_AT = datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)


class FloatPayloadEnum(Enum):
    PRICE = 100.25


class MutablePayloadEnum(Enum):
    VALUE = {"nested": [1, 2]}


class NonFiniteDecimalEnum(Enum):
    PRICE = Decimal("NaN")


class DecimalPayloadEnum(Enum):
    PRICE = Decimal("100.25")


class AcquisitionContractTests(unittest.TestCase):
    def setUp(self):
        self.provider = ProviderIdentity("provider-a", "adapter-a", "1.0.0")
        self.instrument = InstrumentIdentity("BTC-USDT-SPOT", "BTCUSDT")
        self.provenance = Provenance("prov-001", self.provider, "stream")

    def make_envelope(self, **overrides):
        values = {
            "provider": self.provider,
            "instrument": self.instrument,
            "provenance": self.provenance,
            "event_type": EventType.TRADE,
            "event_time": EVENT_TIME,
            "received_at": RECEIVED_AT,
            "state": AcquisitionState.AVAILABLE,
            "payload": {"price": Decimal("100.25"), "quantity": Decimal("2.0")},
            "source_sequence": "42",
        }
        values.update(overrides)
        return AcquisitionEnvelope(**values)

    def test_identity_and_version_are_explicit(self):
        self.assertEqual(SID, "CTR-P2-001")
        self.assertEqual(VERSION, "1.0.0")

    def test_valid_acquisition_envelope(self):
        envelope = self.make_envelope()
        self.assertEqual(envelope.provider.provider_id, "provider-a")
        self.assertEqual(envelope.instrument.canonical_instrument_id, "BTC-USDT-SPOT")
        self.assertEqual(envelope.event_type, EventType.TRADE)
        self.assertEqual(envelope.state, AcquisitionState.AVAILABLE)

    def test_payload_is_immutable_and_float_is_rejected(self):
        envelope = self.make_envelope()
        with self.assertRaises(TypeError):
            envelope.payload["price"] = Decimal("101")
        with self.assertRaises(TypeError):
            self.make_envelope(payload={"price": 100.25})

    def test_float_valued_enum_payload_is_rejected(self):
        with self.assertRaises(TypeError):
            self.make_envelope(payload={"price": FloatPayloadEnum.PRICE})

    def test_mutable_enum_payload_is_rejected_at_construction(self):
        with self.assertRaises(TypeError):
            self.make_envelope(payload={"value": MutablePayloadEnum.VALUE})

    def test_non_finite_decimal_inside_enum_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            self.make_envelope(payload={"price": NonFiniteDecimalEnum.PRICE})

    def test_valid_decimal_enum_has_deterministic_serialization_and_identity(self):
        first = self.make_envelope(payload={"price": DecimalPayloadEnum.PRICE})
        second = self.make_envelope(payload={"price": DecimalPayloadEnum.PRICE})
        self.assertEqual(first.canonical_bytes(), second.canonical_bytes())
        self.assertEqual(first.event_id, second.event_id)
        self.assertEqual(first.deduplication_key, second.deduplication_key)

    def test_missing_identity_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            ProviderIdentity("", "adapter-a", "1.0.0")
        with self.assertRaises(ValueError):
            InstrumentIdentity("", "BTCUSDT")
        with self.assertRaises(ValueError):
            Provenance("", self.provider, "stream")

    def test_invalid_data_and_timestamp_are_rejected(self):
        with self.assertRaises(ValueError):
            self.make_envelope(event_time=datetime(2026, 1, 1, 0, 0))
        with self.assertRaises(ValueError):
            self.make_envelope(received_at=datetime(2026, 1, 1, 0, 0))
        with self.assertRaises(TypeError):
            self.make_envelope(event_type="TRADE")

    def test_degraded_state_requires_structured_error(self):
        error = ProviderError("DEGRADED", "transport", "provider degraded", retryable=True)
        envelope = self.make_envelope(
            state=AcquisitionState.DEGRADED,
            provider_error=error,
            capability=ProviderCapability("trades", CapabilityState.DEGRADED),
        )
        self.assertEqual(envelope.state, AcquisitionState.DEGRADED)
        self.assertTrue(envelope.provider_error.retryable)

    def test_required_failure_states_cannot_be_synthetic_success(self):
        failure_states = (
            AcquisitionState.UNAVAILABLE,
            AcquisitionState.STALE,
            AcquisitionState.INVALID,
            AcquisitionState.DISCONNECTED,
            AcquisitionState.RATE_LIMITED,
            AcquisitionState.SEQUENCE_GAP,
            AcquisitionState.INSUFFICIENT_DATA,
        )
        for state in failure_states:
            with self.subTest(state=state):
                with self.assertRaises(ValueError):
                    self.make_envelope(state=state)

    def test_available_state_cannot_carry_provider_error(self):
        error = ProviderError("X", "transport", "failure")
        with self.assertRaises(ValueError):
            self.make_envelope(provider_error=error)

    def test_provenance_provider_must_match_envelope_provider(self):
        other = ProviderIdentity("provider-b", "adapter-b", "1.0.0")
        with self.assertRaises(ValueError):
            self.make_envelope(provenance=Provenance("prov-002", other, "stream"))

    def test_deterministic_serialization_is_order_independent(self):
        first = self.make_envelope(payload={"b": Decimal("2"), "a": Decimal("1")})
        second = self.make_envelope(payload={"a": Decimal("1"), "b": Decimal("2")})
        self.assertEqual(first.canonical_bytes(), second.canonical_bytes())
        self.assertEqual(first.event_id, second.event_id)
        self.assertEqual(first.deduplication_key, second.deduplication_key)

    def test_replay_identity_excludes_receive_time(self):
        original = self.make_envelope(received_at=RECEIVED_AT)
        replay = self.make_envelope(
            received_at=RECEIVED_AT + timedelta(seconds=30),
        )
        self.assertNotEqual(original.canonical_bytes(), replay.canonical_bytes())
        self.assertEqual(original.event_id, replay.event_id)

    def test_provider_isolation_is_part_of_identity(self):
        other = ProviderIdentity("provider-b", "adapter-b", "1.0.0")
        other_provenance = Provenance("prov-b", other, "stream")
        other_event = self.make_envelope(
            provider=other,
            provenance=other_provenance,
        )
        self.assertNotEqual(self.make_envelope().event_id, other_event.event_id)

    def test_source_sequence_and_capability_are_explicit(self):
        envelope = self.make_envelope(
            source_sequence="seq-7",
            capability=ProviderCapability("trades", CapabilityState.SUPPORTED),
        )
        self.assertEqual(envelope.source_sequence, "seq-7")
        self.assertEqual(envelope.capability.state, CapabilityState.SUPPORTED)

    def test_non_finite_decimal_is_rejected_during_serialization(self):
        with self.assertRaises(ValueError):
            self.make_envelope(payload={"price": Decimal("NaN")})


if __name__ == "__main__":
    unittest.main()
