from decimal import Decimal
import unittest

from contracts.acquisition import CapabilityState
from contracts.canonical.foundation import (
    ProvenanceRef,
    ValidationCode,
    ValidationIssue,
    ValidationOutcome,
    ValidationResult,
)
from contracts.data_quality import DataQualityState
from contracts.quality import (
    BoundedQuarantine,
    QUALITY_DIMENSIONS,
    QualityInput,
    QualitySignals,
    assess_quality,
    fingerprint_payload,
    quarantine_record,
    route_assessment,
)

ALL_SCORES = {name: Decimal("1.00") for name in QUALITY_DIMENSIONS}
PROVENANCE = ProvenanceRef("binance:test", "binance", "WS")


def quality_input(
    result: ValidationResult = ValidationResult.VALID, **kwargs
) -> QualityInput:
    return QualityInput(
        ValidationOutcome(result),
        QualitySignals(**ALL_SCORES),
        PROVENANCE,
        "raw:event:1",
        "staging:event:1",
        **kwargs,
    )


class P3007QualityTests(unittest.TestCase):
    def test_all_authoritative_quality_states_are_explicit(self):
        expected = {
            ValidationResult.VALID: DataQualityState.VALID,
            ValidationResult.DEGRADED: DataQualityState.DEGRADED,
            ValidationResult.STALE: DataQualityState.STALE,
            ValidationResult.INCOMPLETE: DataQualityState.INCOMPLETE,
            ValidationResult.CONTRADICTORY: DataQualityState.CONTRADICTORY,
            ValidationResult.REJECTED: DataQualityState.REJECTED,
            ValidationResult.UNAVAILABLE: DataQualityState.UNAVAILABLE,
        }
        for validation, quality in expected.items():
            with self.subTest(validation=validation):
                result = assess_quality(quality_input(validation))
                self.assertEqual(result.quality.quality_state, quality)
                self.assertFalse(result.canonical_eligible if quality is not DataQualityState.VALID else False)

    def test_valid_requires_available_lineage_evidence(self):
        result = assess_quality(quality_input())
        self.assertTrue(result.canonical_eligible)
        self.assertEqual(result.quality.quality_state, DataQualityState.VALID)
        self.assertEqual(result.lineage.source_record_id, "raw:event:1")
        self.assertEqual(result.lineage.lineage_parent_id, "staging:event:1")
        self.assertEqual(result.lineage.provenance_id, "binance:test")

    def test_missing_lineage_is_incomplete_not_fabricated(self):
        result = assess_quality(
            QualityInput(
                ValidationOutcome(ValidationResult.VALID),
                QualitySignals(**ALL_SCORES),
                PROVENANCE,
            )
        )
        self.assertEqual(result.quality.quality_state, DataQualityState.INCOMPLETE)
        self.assertIn("lineage_missing", result.quality.reason_codes)
        self.assertFalse(result.canonical_eligible)
        self.assertIsNone(result.lineage)

    def test_missing_validation_is_incomplete(self):
        result = assess_quality(QualityInput(None, QualitySignals(**ALL_SCORES), PROVENANCE, "raw:1", "stage:1"))
        self.assertEqual(result.quality.quality_state, DataQualityState.INCOMPLETE)
        self.assertIn("required_evidence_missing", result.quality.reason_codes)

    def test_validation_precedence_over_degraded_capability(self):
        cases = (
            (ValidationResult.REJECTED, DataQualityState.REJECTED),
            (ValidationResult.INCOMPLETE, DataQualityState.INCOMPLETE),
            (ValidationResult.CONTRADICTORY, DataQualityState.CONTRADICTORY),
        )
        for validation, expected in cases:
            with self.subTest(validation=validation):
                result = assess_quality(
                    quality_input(validation, capability_state=CapabilityState.DEGRADED)
                )
                self.assertEqual(result.quality.quality_state, expected)
                self.assertFalse(result.canonical_eligible)
                self.assertEqual(
                    route_assessment(result, {"id": "bad"}, BoundedQuarantine(2)),
                    "QUARANTINED",
                )

    def test_valid_evidence_can_be_degraded_by_degraded_capability(self):
        result = assess_quality(
            quality_input(
                ValidationResult.VALID,
                capability_state=CapabilityState.DEGRADED,
            )
        )
        self.assertEqual(result.quality.quality_state, DataQualityState.DEGRADED)
        self.assertFalse(result.canonical_eligible)

    def test_unavailable_and_unsupported_capability_remain_explicit(self):
        for capability in (CapabilityState.UNAVAILABLE, CapabilityState.UNSUPPORTED):
            with self.subTest(capability=capability):
                result = assess_quality(
                    quality_input(
                        ValidationResult.VALID,
                        capability_state=capability,
                    )
                )
                self.assertEqual(result.quality.quality_state, DataQualityState.UNAVAILABLE)
                self.assertFalse(result.canonical_eligible)

    def test_capability_unavailable_and_unsupported_are_not_canonical(self):
        for capability, expected in (
            (CapabilityState.UNAVAILABLE, DataQualityState.UNAVAILABLE),
            (CapabilityState.UNSUPPORTED, DataQualityState.UNAVAILABLE),
            (CapabilityState.DEGRADED, DataQualityState.DEGRADED),
        ):
            with self.subTest(capability=capability):
                result = assess_quality(quality_input(capability_state=capability))
                self.assertEqual(result.quality.quality_state, expected)
                self.assertFalse(result.canonical_eligible)

    def test_record_unavailable_has_explicit_outcome(self):
        result = assess_quality(quality_input(record_available=False))
        self.assertEqual(result.quality.quality_state, DataQualityState.UNAVAILABLE)
        self.assertIn("provider_unavailable", result.quality.reason_codes)
        self.assertFalse(result.canonical_eligible)

    def test_validation_findings_are_preserved_as_deterministic_reasons(self):
        issue = ValidationIssue(
            ValidationCode.INVALID_VALUE, "price", "price is invalid"
        )
        result = assess_quality(
            QualityInput(
                ValidationOutcome(ValidationResult.REJECTED, (issue,)),
                QualitySignals(**ALL_SCORES),
                PROVENANCE,
                "raw:2",
                "stage:2",
            )
        )
        self.assertEqual(result.quality.reason_codes[0], "validation_rejected")
        self.assertIn("validation_invalid_value:price", result.quality.reason_codes)

    def test_score_is_bounded_and_only_emitted_when_all_dimensions_exist(self):
        result = assess_quality(quality_input())
        self.assertEqual(result.explanation.score, Decimal("1.00"))
        partial = assess_quality(
            QualityInput(
                ValidationOutcome(ValidationResult.VALID),
                QualitySignals(freshness=Decimal("0.75")),
                PROVENANCE,
                "raw:3",
                "stage:3",
            )
        )
        self.assertIsNone(partial.explanation.score)

    def test_quarantine_preserves_partial_upstream_evidence_without_fabrication(self):
        cases = (
            (PROVENANCE, "raw:partial:1", None),
            (PROVENANCE, None, "stage:partial:2"),
            (None, "raw:partial:3", "stage:partial:3"),
        )
        for provenance, source_id, parent_id in cases:
            with self.subTest(
                provenance=provenance,
                source_id=source_id,
                parent_id=parent_id,
            ):
                result = assess_quality(
                    QualityInput(
                        ValidationOutcome(ValidationResult.REJECTED),
                        QualitySignals(**ALL_SCORES),
                        provenance,
                        source_id,
                        parent_id,
                    )
                )
                record = quarantine_record(result, {"case": "partial"})
                self.assertEqual(
                    record.provenance_id,
                    provenance.provenance_id if provenance else None,
                )
                self.assertEqual(record.source_record_id, source_id)
                self.assertEqual(record.lineage_parent_id, parent_id)

    def test_incomplete_evidence_preserves_partial_upstream_identity(self):
        result = assess_quality(
            QualityInput(
                ValidationOutcome(ValidationResult.INCOMPLETE),
                QualitySignals(**ALL_SCORES),
                PROVENANCE,
                "raw:incomplete",
                None,
            )
        )
        record = quarantine_record(result, {"case": "incomplete"})
        self.assertEqual(record.provenance_id, PROVENANCE.provenance_id)
        self.assertEqual(record.source_record_id, "raw:incomplete")
        self.assertIsNone(record.lineage_parent_id)

    def test_invalid_score_types_and_bounds_are_rejected(self):
        with self.assertRaises(TypeError):
            QualitySignals(freshness=1.0)
        with self.assertRaises(ValueError):
            QualitySignals(freshness=Decimal("1.01"))
        with self.assertRaises(ValueError):
            QualitySignals(freshness=Decimal("-0.01"))
        with self.assertRaises(ValueError):
            QualitySignals(freshness=Decimal("NaN"))

    def test_score_vector_order_is_governed_and_reproducible(self):
        result = assess_quality(quality_input())
        self.assertEqual(
            tuple(name for name, _ in result.explanation.components),
            QUALITY_DIMENSIONS,
        )
        self.assertEqual(result, assess_quality(quality_input()))

    def test_degraded_and_stale_are_explicit_noncanonical_quality_routes(self):
        quarantine = BoundedQuarantine(4)
        degraded = assess_quality(quality_input(ValidationResult.DEGRADED))
        stale = assess_quality(quality_input(ValidationResult.STALE))
        self.assertEqual(route_assessment(degraded, {"id": 1}, quarantine), "QUALITY_DEGRADED")
        self.assertEqual(route_assessment(stale, {"id": 2}, quarantine), "QUALITY_DEGRADED")
        self.assertEqual(quarantine.size, 0)

    def test_rejected_routes_to_bounded_normalization_dlq(self):
        quarantine = BoundedQuarantine(2)
        assessment = assess_quality(quality_input(ValidationResult.REJECTED))
        self.assertEqual(route_assessment(assessment, {"bad": "record"}, quarantine), "QUARANTINED")
        self.assertEqual(quarantine.size, 1)
        stored = quarantine.snapshot()[0]
        self.assertEqual(stored.quality_state, DataQualityState.REJECTED)
        self.assertEqual(stored.provenance_id, "binance:test")
        self.assertTrue(stored.payload_fingerprint)

    def test_retry_is_idempotent_and_does_not_duplicate_dlq_evidence(self):
        quarantine = BoundedQuarantine(1)
        assessment = assess_quality(quality_input(ValidationResult.REJECTED))
        payload = {"bad": "record"}
        first = quarantine_record(assessment, payload, attempt=1)
        retry = quarantine_record(assessment, payload, attempt=2)
        self.assertEqual(first.deduplication_key, retry.deduplication_key)
        self.assertEqual(quarantine.enqueue(first), "ENQUEUED")
        self.assertEqual(quarantine.enqueue(retry), "DUPLICATE")
        self.assertEqual(quarantine.size, 1)

    def test_dlq_capacity_is_bounded_and_exhaustion_is_explicit(self):
        quarantine = BoundedQuarantine(1)
        assessment = assess_quality(quality_input(ValidationResult.REJECTED))
        quarantine.enqueue(quarantine_record(assessment, {"id": 1}))
        with self.assertRaises(OverflowError):
            quarantine.enqueue(quarantine_record(assessment, {"id": 2}))

    def test_valid_data_cannot_be_quarantined(self):
        with self.assertRaises(ValueError):
            quarantine_record(assess_quality(quality_input()), {"id": 1})

    def test_fingerprint_is_deterministic_for_semantically_equal_mappings(self):
        left = {"b": Decimal("1.0"), "a": [2, "x"]}
        right = {"a": [2, "x"], "b": Decimal("1.0")}
        self.assertEqual(fingerprint_payload(left), fingerprint_payload(right))

    def test_malformed_input_is_explicitly_rejected_at_quality_boundary(self):
        with self.assertRaises(TypeError):
            QualityInput("malformed", QualitySignals(**ALL_SCORES), PROVENANCE, "raw:4", "stage:4")
        with self.assertRaises(TypeError):
            QualityInput(
                ValidationOutcome(ValidationResult.VALID),
                "malformed",
                PROVENANCE,
                "raw:4",
                "stage:4",
            )

    def test_no_opportunity_or_trading_semantics_exist_in_assessment(self):
        assessment = assess_quality(quality_input())
        self.assertFalse(hasattr(assessment, "opportunity"))
        self.assertFalse(hasattr(assessment, "trade_idea"))


if __name__ == "__main__":
    unittest.main()