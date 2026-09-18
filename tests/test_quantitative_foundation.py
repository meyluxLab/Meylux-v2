import unittest
from decimal import Decimal

from contracts.quantitative import (
    CalculationResult, CalculationStatus, IndicatorResult, MarketStructureResult,
    VolumeProfileResult, OrderFlowResult, RegimeResult,
)
from contracts.quantitative.base import QuantitativeContext
from meylux.quantitative.numeric import quantize, serialize_decimal
from meylux.quantitative.primitives import (
    average, weighted_average, rolling_mean, exponential_smoothing,
    standard_deviation, percentile, accumulate, normalize_min_max,
)
from meylux.quantitative.golden import load_golden_vectors, run_golden_vectors


class QuantitativeContractTests(unittest.TestCase):
    def test_result_requires_explicit_status_and_reason(self):
        result = CalculationResult(Decimal("1.25"), CalculationStatus.VALID, "ok")
        self.assertTrue(result.valid)

    def test_invalid_status_cannot_carry_numeric_value(self):
        with self.assertRaises(ValueError):
            CalculationResult(Decimal("0"), CalculationStatus.INSUFFICIENT_HISTORY, "missing")

    def test_context_rejects_non_utc_timestamp(self):
        from datetime import datetime, timezone, timedelta
        with self.assertRaises(ValueError):
            QuantitativeContext(timestamp=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))))

    def test_domain_contracts_are_immutable_and_typed(self):
        result = CalculationResult(Decimal("1"), CalculationStatus.VALID, "ok")
        for obj in (
            IndicatorResult("EMA", result),
            MarketStructureResult("BOS", result),
            VolumeProfileResult("POC", result),
            OrderFlowResult("DELTA", result),
            RegimeResult("TREND", result),
        ):
            with self.assertRaises(Exception):
                obj.result = result


class QuantitativePrimitiveTests(unittest.TestCase):
    def test_average_negative_zero_and_large_values(self):
        result = average(["-1000000000000000000000", "0", "1000000000000000000000"])
        self.assertEqual(result.value, Decimal("0"))

    def test_float_and_nonfinite_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            average([1.0, 2])
        with self.assertRaises(ValueError):
            average(["NaN", "1"])
        with self.assertRaises(ValueError):
            average(["Infinity", "1"])

    def test_empty_and_warmup_are_explicit(self):
        self.assertEqual(average([]).status, CalculationStatus.INSUFFICIENT_HISTORY)
        results = rolling_mean([1, 2, 3], 3)
        self.assertEqual(results[0].status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertEqual(results[1].status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertEqual(results[2].value, Decimal("2"))

    def test_weighted_zero_denominator_is_invalid(self):
        result = weighted_average([1, 2], [1, -1])
        self.assertEqual(result.status, CalculationStatus.INVALID_INPUT)
        self.assertIsNone(result.value)

    def test_smoothing_is_deterministic(self):
        a = exponential_smoothing([1, 2, 4], "0.5")
        b = exponential_smoothing([1, 2, 4], "0.5")
        self.assertEqual(a, b)
        self.assertEqual(a[-1].value, Decimal("2.75"))

    def test_standard_deviation_population_and_sample(self):
        self.assertEqual(
            serialize_decimal(standard_deviation([1, 2, 3]).value),
            "0.81649658092772603273242802490196379732198249355223",
        )
        self.assertEqual(serialize_decimal(standard_deviation([1, 2, 3], 1).value), "1")

    def test_percentile_boundaries_and_input_order(self):
        values = [3, 1, 2]
        self.assertEqual(percentile(values, 50).value, Decimal("2"))
        self.assertEqual(values, [3, 1, 2])
        self.assertEqual(percentile(values, 0).value, Decimal("1"))
        self.assertEqual(percentile(values, 100).value, Decimal("3"))
        self.assertEqual(percentile([], 50).status, CalculationStatus.INSUFFICIENT_HISTORY)

    def test_accumulate_and_normalize(self):
        accumulated = accumulate([1, 2, 3], start="10")
        self.assertEqual([x.value for x in accumulated], [Decimal("11"), Decimal("13"), Decimal("16")])
        normalized = normalize_min_max([1, 2, 3])
        self.assertEqual([x.value for x in normalized], [Decimal("0"), Decimal("0.5"), Decimal("1")])
        self.assertTrue(all(x.status is CalculationStatus.INVALID_INPUT for x in normalize_min_max([5, 5])))

    def test_explicit_rounding_is_half_even(self):
        self.assertEqual(quantize("1.2345", "0.001"), Decimal("1.234"))
        self.assertEqual(quantize("1.2355", "0.001"), Decimal("1.236"))
        with self.assertRaises(ValueError):
            quantize("1.2", "0")


class GoldenVectorTests(unittest.TestCase):
    FUNCTIONS = {
        "average": average,
        "weighted_average": weighted_average,
        "standard_deviation": standard_deviation,
        "percentile": percentile,
        "exponential_smoothing": exponential_smoothing,
    }

    def test_all_golden_vectors_pass_exactly(self):
        vectors = load_golden_vectors("tests/golden_vectors/p4_001_primitives.json")
        run_golden_vectors(vectors, self.FUNCTIONS)

    def test_golden_vectors_are_reproducible(self):
        vectors = load_golden_vectors("tests/golden_vectors/p4_001_primitives.json")
        for _ in range(3):
            run_golden_vectors(vectors, self.FUNCTIONS)


if __name__ == "__main__":
    unittest.main()
