"""Evidence tests for TO-P3-002 structural/schema/identity validation."""

from datetime import datetime, timezone
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
from contracts.validation import validate_acquisition_envelope, validate_acquisition_structure


UTC = timezone.utc
NOW = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


def valid_record() -> dict[str, object]:
    provider = ProviderIdentity("binance", "binance-spot", "1.0.0")
    instrument = InstrumentIdentity("BTC-USD-SPOT", "BTCUSDT")
    provenance = Provenance("prov:fixture/1", provider, "websocket")
    return {
        "provider": provider,
        "instrument": instrument,
        "provenance": provenance,
        "event_type": EventType.TRADE,
        "event_time": NOW,
        "received_at": NOW,
        "state": AcquisitionState.AVAILABLE,
        "payload": {"price": "100", "quantity": "1"},
        "source_sequence": "42",
        "provider_error": None,
        "capability": None,
    }


class StructuralSchemaIdentityTests(unittest.TestCase):
    def test_valid_acquisition_structure_is_accepted_and_has_deterministic_identity(self):
        first = validate_acquisition_structure(valid_record())
        second = validate_acquisition_structure(valid_record())
        self.assertEqual(first.outcome.result, ValidationResult.VALID)
        self.assertIsNotNone(first.identity)
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(len(first.identity), 64)

    def test_missing_required_field_is_incomplete(self):
        record = valid_record()
        del record["event_type"]
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.INCOMPLETE)
        self.assertEqual(result.outcome.issues[0].code, ValidationCode.REQUIRED_MISSING)

    def test_explicit_null_required_field_is_incomplete(self):
        record = valid_record()
        record["payload"] = None
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.INCOMPLETE)
        self.assertIn(ValidationCode.NULL_NOT_ALLOWED, {issue.code for issue in result.outcome.issues})

    def test_nullable_optional_fields_are_structurally_permitted(self):
        record = valid_record()
        record["source_sequence"] = None
        record["provider_error"] = None
        record["capability"] = None
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.VALID)

    def test_unknown_field_is_rejected(self):
        record = valid_record()
        record["provider_private_alias"] = "BTCUSDT"
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(issue.field == "provider_private_alias" for issue in result.outcome.issues))

    def test_invalid_field_type_is_rejected(self):
        record = valid_record()
        record["event_time"] = "2026-01-01T00:00:00Z"
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(issue.code is ValidationCode.INVALID_TYPE for issue in result.outcome.issues))

    def test_malformed_top_level_structure_is_rejected(self):
        result = validate_acquisition_structure([("provider", "binance")])  # type: ignore[arg-type]
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertEqual(result.outcome.issues[0].code, ValidationCode.INVALID_TYPE)

    def test_initial_identity_validation_rejects_invalid_identity_token(self):
        record = valid_record()
        record["instrument"] = InstrumentIdentity("BTC USD", "BTCUSDT")
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertEqual(result.outcome.issues[0].code, ValidationCode.IDENTITY_INVALID)

    def test_provider_specific_wire_alias_is_not_accepted_as_canonical_field(self):
        record = valid_record()
        record["symbol"] = "BTCUSDT"
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.REJECTED)
        self.assertTrue(any(issue.field == "symbol" for issue in result.outcome.issues))

    def test_existing_acquisition_envelope_is_accepted_without_reconstruction(self):
        record = valid_record()
        envelope = AcquisitionEnvelope(**record)  # type: ignore[arg-type]
        result = validate_acquisition_envelope(envelope)
        self.assertEqual(result.outcome.result, ValidationResult.VALID)
        self.assertEqual(result.identity, envelope.event_id)

    def test_existing_envelope_semantic_rules_are_not_reimplemented(self):
        record = valid_record()
        record["event_type"] = EventType.TRADE
        record["payload"] = {"provider_wire_field": "allowed as opaque payload"}
        result = validate_acquisition_structure(record)
        self.assertEqual(result.outcome.result, ValidationResult.VALID)


if __name__ == "__main__":
    unittest.main()
