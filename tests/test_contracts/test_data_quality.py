import unittest

from contracts.data_quality import (
    DataLifecycleState,
    DataQuality,
    DataQualityState,
    validate_quality_lifecycle,
)


class DataQualityTests(unittest.TestCase):
    def test_architecture_quality_outcomes_are_explicit(self):
        self.assertEqual(
            {state.value for state in DataQualityState},
            {
                "VALID",
                "DEGRADED",
                "STALE",
                "INCOMPLETE",
                "CONTRADICTORY",
                "REJECTED",
                "UNAVAILABLE",
            },
        )

    def test_architecture_lifecycle_states_are_explicit(self):
        self.assertEqual(
            {state.value for state in DataLifecycleState},
            {
                "RAW",
                "STAGED",
                "VALIDATING",
                "NORMALIZED",
                "CANONICAL",
                "QUALITY_DEGRADED",
                "REJECTED",
                "QUARANTINED",
                "EXPIRED",
                "ARCHIVED",
            },
        )

    def test_quality_is_immutable_and_reason_codes_are_deterministic(self):
        quality = DataQuality(DataQualityState.DEGRADED, ("MISSING_FIELD", "STALE_FEED"))
        with self.assertRaises(Exception):
            quality.quality_state = DataQualityState.VALID
        with self.assertRaises(ValueError):
            DataQuality(DataQualityState.VALID, ("DUPLICATE", "DUPLICATE"))
        with self.assertRaises(TypeError):
            DataQuality(DataQualityState.VALID, ["DUPLICATE"])

    def test_invalid_quality_state_type_is_rejected(self):
        with self.assertRaises(TypeError):
            DataQuality("VALID")

    def test_empty_reason_code_is_rejected(self):
        with self.assertRaises(ValueError):
            DataQuality(DataQualityState.DEGRADED, ("",))

    def test_rejected_and_unavailable_are_not_authoritative(self):
        self.assertTrue(DataQuality(DataQualityState.REJECTED).blocks_canonical_promotion)
        self.assertTrue(DataQuality(DataQualityState.UNAVAILABLE).blocks_canonical_promotion)
        self.assertFalse(DataQuality(DataQualityState.STALE).blocks_canonical_promotion)

    def test_canonical_promotion_guard_is_explicit(self):
        valid = DataQuality(DataQualityState.VALID)
        rejected = DataQuality(DataQualityState.REJECTED)
        unavailable = DataQuality(DataQualityState.UNAVAILABLE)

        self.assertFalse(valid.blocks_canonical_promotion)
        self.assertTrue(rejected.blocks_canonical_promotion)
        self.assertTrue(unavailable.blocks_canonical_promotion)

    def test_cross_state_validation_rejects_silent_promotion(self):
        validate_quality_lifecycle(
            DataQuality(DataQualityState.VALID), DataLifecycleState.CANONICAL
        )
        with self.assertRaises(ValueError):
            validate_quality_lifecycle(
                DataQuality(DataQualityState.REJECTED), DataLifecycleState.CANONICAL
            )
        with self.assertRaises(ValueError):
            validate_quality_lifecycle(
                DataQuality(DataQualityState.UNAVAILABLE), DataLifecycleState.CANONICAL
            )

    def test_cross_state_validation_does_not_invent_extra_policy(self):
        validate_quality_lifecycle(
            DataQuality(DataQualityState.STALE), DataLifecycleState.NORMALIZED
        )
        validate_quality_lifecycle(
            DataQuality(DataQualityState.CONTRADICTORY), DataLifecycleState.QUALITY_DEGRADED
        )

    def test_invalid_lifecycle_type_is_rejected(self):
        quality = DataQuality(DataQualityState.VALID)
        with self.assertRaises(TypeError):
            validate_quality_lifecycle(quality, "CANONICAL")


if __name__ == "__main__":
    unittest.main()
