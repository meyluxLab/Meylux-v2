from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from contracts.canonical.derivatives import CanonicalDerivatives
from contracts.canonical.orderbook import CanonicalOrderBook
from contracts.canonical.trade import CanonicalTrade
from contracts.quantitative.base import CalculationStatus
from meylux.quantitative.volume_orderflow_derivatives import (
    ClosedBar,
    DerivativesEngine,
    OrderFlowConfig,
    OrderFlowEngine,
    VolumeProfileConfig,
    VolumeProfileEngine,
)


UTC = timezone.utc
T0 = datetime(2026, 9, 19, 0, 0, tzinfo=UTC)


def trade(i, price, qty, side="BUY", minute=0):
    return CanonicalTrade(
        f"t{i}", "BTCUSDT", T0 + timedelta(minutes=minute),
        Decimal(str(price)), Decimal(str(qty)), side, None, f"prov-{i}"
    )


def deriv(i, minute, **kwargs):
    return CanonicalDerivatives(
        "BTCUSDT", T0 + timedelta(minutes=minute), provenance_id=f"d-{i}", **kwargs
    )


class VolumeProfileTests(unittest.TestCase):
    def setUp(self):
        self.engine = VolumeProfileEngine()
        self.config = VolumeProfileConfig(Decimal("1"), Decimal("0.75"), Decimal("0.25"))

    def analyze(self, trades, end_minutes=10, config=None):
        return self.engine.analyze(
            trades, T0, T0 + timedelta(minutes=end_minutes),
            config or self.config
        )

    def test_empty_profile_is_explicit(self):
        result = self.analyze(())
        self.assertEqual(result.poc.result.status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertIsNone(result.poc.result.value)
        self.assertEqual(result.bins, ())

    def test_one_trade_profile(self):
        result = self.analyze((trade(1, "100.25", "2"),))
        self.assertEqual(result.bins, ((Decimal("100"), Decimal("2")),))
        self.assertEqual(result.poc.result.value, Decimal("100"))
        self.assertEqual(result.value_area_low.result.value, Decimal("100"))
        self.assertEqual(result.value_area_high.result.value, Decimal("101"))

    def test_exact_poc_tie_chooses_lowest_price(self):
        result = self.analyze((trade(1, "101", "5"), trade(2, "100", "5")))
        self.assertEqual(result.poc.result.value, Decimal("100"))

    def test_exact_seventy_percent_boundary_stops_immediately(self):
        trades = (
            trade(1, "1", "4"), trade(2, "2", "3"), trade(3, "3", "3")
        )
        result = self.analyze(trades)
        self.assertEqual(result.selected_value_area_bins, (Decimal("1"), Decimal("2")))
        self.assertEqual(result.value_area_low.result.value, Decimal("1"))
        self.assertEqual(result.value_area_high.result.value, Decimal("3"))

    def test_value_area_expansion_exact_tie_chooses_lower_side(self):
        trades = (
            trade(1, "10", "4"), trade(2, "9", "3"), trade(3, "11", "3")
        )
        result = self.analyze(trades)
        self.assertEqual(result.selected_value_area_bins[:2], (Decimal("9"), Decimal("10")))

    def test_exact_bin_boundaries_are_deterministic(self):
        result = self.analyze((trade(1, "1", "1"), trade(2, "1.999", "1"), trade(3, "2", "1")))
        self.assertEqual(
            result.bins,
            ((Decimal("1"), Decimal("2")), (Decimal("2"), Decimal("1")))
        )

    def test_invalid_bin_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            VolumeProfileConfig(Decimal("0"))
        with self.assertRaises(ValueError):
            VolumeProfileConfig(Decimal("-1"))

    def test_hvn_lvn_threshold_equality_qualifies(self):
        config = VolumeProfileConfig(Decimal("1"), Decimal("0.5"), Decimal("0.5"))
        result = self.analyze(
            (trade(1, "1", "10"), trade(2, "2", "5"), trade(3, "3", "5")),
            config=config,
        )
        self.assertIn(Decimal("2"), result.hvn_bins)
        self.assertIn(Decimal("2"), result.lvn_bins)
        self.assertNotIn(Decimal("1"), result.lvn_bins)

    def test_missing_hvn_lvn_configuration_is_unavailable(self):
        result = self.analyze(
            (trade(1, "1", "1"),),
            config=VolumeProfileConfig(Decimal("1"))
        )
        self.assertEqual(result.hvn.result.status, CalculationStatus.UNAVAILABLE)
        self.assertEqual(result.lvn.result.status, CalculationStatus.UNAVAILABLE)

    def test_no_lookahead_excludes_future_trade(self):
        result = self.engine.analyze(
            (trade(1, "10", "1", minute=1), trade(2, "99", "100", minute=20)),
            T0, T0 + timedelta(minutes=10), self.config
        )
        self.assertEqual(result.poc.result.value, Decimal("10"))

    def test_large_and_small_decimal_values(self):
        config = VolumeProfileConfig(Decimal("0.000000000000000001"))
        result = self.engine.analyze(
            (trade(1, "0.000000000000000002", "1000000000000000000000000"),),
            T0, T0 + timedelta(minutes=1), config
        )
        self.assertEqual(result.poc.result.value, Decimal("0.000000000000000002"))

    def test_malformed_trade_input_is_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.analyze((object(),), T0, T0 + timedelta(minutes=1), self.config)

    def test_repeated_profile_replay_is_equal(self):
        trades = (trade(1, "100", "2"), trade(2, "101", "3"))
        a = self.analyze(trades)
        b = self.analyze(trades)
        self.assertEqual(a, b)


class OrderFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = OrderFlowEngine()
        self.config = OrderFlowConfig(Decimal("2"), Decimal("5"), Decimal("0.5"))

    def test_missing_aggressor_is_unavailable(self):
        result = self.engine.bar_delta((trade(1, "100", "2", None),))
        self.assertEqual(result.result.status, CalculationStatus.UNAVAILABLE)

    def test_bar_delta_buy_positive_sell_negative(self):
        result = self.engine.bar_delta(
            (trade(1, "100", "7", "BUY"), trade(2, "100", "3", "SELL"))
        )
        self.assertEqual(result.result.value, Decimal("4"))

    def test_cvd_replay_and_missing_delta_does_not_become_zero(self):
        bars = (
            ClosedBar(T0, T0 + timedelta(minutes=1), (trade(1, "100", "5", "BUY"),)),
            ClosedBar(T0 + timedelta(minutes=1), T0 + timedelta(minutes=2), (trade(2, "101", "1", None),)),
            ClosedBar(T0 + timedelta(minutes=2), T0 + timedelta(minutes=3), (trade(3, "102", "2", "SELL"),)),
        )
        a = self.engine.cvd(bars)
        b = self.engine.cvd(bars)
        self.assertEqual(a, b)
        self.assertEqual(a[0].result.value, Decimal("5"))
        self.assertEqual(a[1].result.status, CalculationStatus.UNAVAILABLE)
        self.assertEqual(a[2].result.value, Decimal("3"))

    def test_cvd_rejects_out_of_order_bars(self):
        bars = (
            ClosedBar(T0 + timedelta(minutes=1), T0 + timedelta(minutes=2), (trade(1, "100", "1"),)),
            ClosedBar(T0, T0 + timedelta(minutes=1), (trade(2, "100", "1"),)),
        )
        with self.assertRaises(ValueError):
            self.engine.cvd(bars)

    def test_imbalance_below_equal_above_threshold(self):
        below = self.engine.imbalance(Decimal("19"), Decimal("10"), self.config)
        equal = self.engine.imbalance(Decimal("20"), Decimal("10"), self.config)
        above = self.engine.imbalance(Decimal("21"), Decimal("10"), self.config)
        self.assertEqual(below.result.reason, "threshold_not_qualified")
        self.assertEqual(equal.result.reason, "threshold_qualified")
        self.assertEqual(above.result.reason, "threshold_qualified")

    def test_zero_opposing_volume_never_becomes_infinity(self):
        result = self.engine.imbalance(Decimal("100"), Decimal("0"), self.config)
        self.assertEqual(result.result.status, CalculationStatus.UNAVAILABLE)
        self.assertIsNone(result.result.value)

    def test_invalid_imbalance_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            OrderFlowConfig(Decimal("1"), Decimal("1"), Decimal("0"))

    def test_absorption_requires_order_book_evidence(self):
        result = self.engine.absorption(
            (trade(1, "100", "10", "BUY"),), (), T0, T0 + timedelta(minutes=1),
            Decimal("100"), "BUY", self.config
        )
        self.assertEqual(result.result.status, CalculationStatus.UNAVAILABLE)

    def test_absorption_requires_opposite_resting_quantity(self):
        book = CanonicalOrderBook(
            "BTCUSDT", T0, ((Decimal("99"), Decimal("20")),),
            ((Decimal("101"), Decimal("20")),), "book-1"
        )
        result = self.engine.absorption(
            (trade(1, "100", "10", "BUY"),), (book,), T0, T0 + timedelta(minutes=1),
            Decimal("100"), "BUY", self.config
        )
        self.assertEqual(result.result.status, CalculationStatus.UNAVAILABLE)

    def test_absorption_with_trade_and_book_evidence(self):
        book = CanonicalOrderBook(
            "BTCUSDT", T0, ((Decimal("99"), Decimal("20")),),
            ((Decimal("100"), Decimal("20")),), "book-1"
        )
        result = self.engine.absorption(
            (trade(1, "100", "10", "BUY"),), (book,), T0, T0 + timedelta(minutes=1),
            Decimal("100"), "BUY", self.config
        )
        self.assertEqual(result.result.value, Decimal("1"))

    def test_absorption_rejects_traversal_beyond_displacement(self):
        book = CanonicalOrderBook(
            "BTCUSDT", T0, ((Decimal("99"), Decimal("20")),),
            ((Decimal("100"), Decimal("20")),), "book-1"
        )
        result = self.engine.absorption(
            (trade(1, "100", "10", "BUY"), trade(2, "101", "1", "BUY")),
            (book,), T0, T0 + timedelta(minutes=1),
            Decimal("100"), "BUY", self.config
        )
        self.assertEqual(result.result.reason, "price_traversal_exceeded_configured_displacement")


class DerivativesTests(unittest.TestCase):
    def setUp(self):
        self.engine = DerivativesEngine()

    def test_missing_derivatives_fields_are_explicit(self):
        result = self.engine.analyze(deriv(1, 0))
        self.assertEqual(result["FUNDING_RATE"].status, CalculationStatus.UNAVAILABLE)
        self.assertEqual(result["OPEN_INTEREST"].status, CalculationStatus.UNAVAILABLE)
        self.assertEqual(result["BASIS"].status, CalculationStatus.UNAVAILABLE)

    def test_first_observation_velocity_and_oi_delta_are_insufficient(self):
        result = self.engine.analyze(
            deriv(1, 0, funding_rate=Decimal("0.001"), open_interest=Decimal("100"))
        )
        self.assertEqual(result["FUNDING_VELOCITY"].status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertEqual(result["OI_DELTA"].status, CalculationStatus.INSUFFICIENT_HISTORY)

    def test_velocity_and_oi_delta_use_only_canonical_observations(self):
        previous = deriv(1, 0, funding_rate=Decimal("0.001"), open_interest=Decimal("100"))
        current = deriv(2, 60, funding_rate=Decimal("0.003"), open_interest=Decimal("125"), basis=Decimal("2"))
        result = self.engine.analyze(current, previous)
        self.assertEqual(result["FUNDING_VELOCITY"].value, Decimal("0.00003333333333333333333333333333"))
        self.assertEqual(result["OI_DELTA"].value, Decimal("25"))
        self.assertEqual(result["BASIS"].value, Decimal("2"))

    def test_zero_and_negative_elapsed_time_are_invalid(self):
        previous = deriv(1, 0, funding_rate=Decimal("0.001"), open_interest=Decimal("100"))
        same_time = deriv(2, 0, funding_rate=Decimal("0.002"), open_interest=Decimal("110"))
        result = self.engine.analyze(same_time, previous)
        self.assertEqual(result["FUNDING_VELOCITY"].status, CalculationStatus.INVALID_INPUT)
        earlier = deriv(3, -1, funding_rate=Decimal("0.002"), open_interest=Decimal("110"))
        result2 = self.engine.analyze(earlier, previous)
        self.assertEqual(result2["FUNDING_VELOCITY"].status, CalculationStatus.INVALID_INPUT)

    def test_canonical_velocity_and_oi_delta_are_exposed_exactly(self):
        current = deriv(
            1, 1, funding_rate=Decimal("0.003"),
            funding_velocity=Decimal("0.0001"),
            open_interest=Decimal("100"),
            open_interest_delta=Decimal("-5"),
            funding_change=Decimal("0.001"),
        )
        result = self.engine.analyze(current)
        self.assertEqual(result["FUNDING_VELOCITY"].value, Decimal("0.0001"))
        self.assertEqual(result["OI_DELTA"].value, Decimal("-5"))
        self.assertEqual(result["FUNDING_CHANGE"].value, Decimal("0.001"))

    def test_acceleration_requires_prior_velocity(self):
        previous = deriv(1, 0, funding_rate=Decimal("0.001"), open_interest=Decimal("100"))
        current = deriv(2, 60, funding_rate=Decimal("0.002"), open_interest=Decimal("100"))
        result = self.engine.analyze(current, previous)
        self.assertEqual(result["FUNDING_ACCELERATION"].status, CalculationStatus.INSUFFICIENT_HISTORY)

    def test_malformed_and_nonfinite_derivatives_are_rejected_by_canonical_contract(self):
        with self.assertRaises((TypeError, ValueError)):
            CanonicalDerivatives(
                "BTCUSDT", T0, funding_rate=float("nan"), provenance_id="bad"
            )

    def test_deterministic_derivatives_replay(self):
        previous = deriv(1, 0, funding_rate=Decimal("0.001"), open_interest=Decimal("100"))
        current = deriv(2, 60, funding_rate=Decimal("0.003"), open_interest=Decimal("125"))
        self.assertEqual(self.engine.analyze(current, previous), self.engine.analyze(current, previous))


if __name__ == "__main__":
    unittest.main()
