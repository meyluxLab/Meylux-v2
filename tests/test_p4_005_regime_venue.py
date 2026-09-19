from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationStatus, QuantitativeContext
from meylux.quantitative.regime_venue import (
    BEARISH, BULLISH, RANGE, INSUFFICIENT,
    COMPARABLE, INCOMPATIBLE, INSUFFICIENT_EVIDENCE,
    MarketRegimeEngine, RegimeConfig, RegimeFactor, VenueEvidence, VenueEvidenceEngine,
)


UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def candle(i: int, close: str, *, volume: str = "10", instrument: str = "BTCUSDT",
           timeframe: str = "1m", provenance: str | None = None) -> CanonicalCandle:
    ts = T0 + timedelta(minutes=i)
    c = Decimal(close)
    return CanonicalCandle(
        instrument_id=instrument, timeframe=timeframe,
        open_time=ts, close_time=ts + timedelta(minutes=1),
        open=c, high=c, low=c, close=c, volume=Decimal(volume),
        provenance_id=provenance or f"p-{i}",
    )


def cfg(**kw) -> RegimeConfig:
    base = dict(
        trend_lookback=2, momentum_lookback=2,
        trend_entry_threshold=Decimal("0.10"),
        trend_exit_threshold=Decimal("0.05"),
        momentum_entry_threshold=Decimal("0.10"),
        momentum_exit_threshold=Decimal("0.05"),
    )
    base.update(kw)
    return RegimeConfig(**base)


class TestMarketRegimeEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MarketRegimeEngine()

    def test_bullish_nominal_and_factor_agreement(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        out = self.engine.classify(xs, cfg())
        self.assertEqual(out.result.state, BULLISH)
        self.assertEqual(out.result.result.value, Decimal("1"))
        self.assertEqual([f.direction for f in out.factors], [BULLISH, BULLISH])
        self.assertEqual(out.transition, "INITIAL")

    def test_bearish_nominal(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "80"]))
        out = self.engine.classify(xs, cfg())
        self.assertEqual(out.result.state, BEARISH)
        self.assertEqual(out.result.result.value, Decimal("-1"))

    def test_conflicting_factors_are_range(self):
        c = cfg(trend_lookback=3, momentum_lookback=1)
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "100", "115"]))
        out = self.engine.classify(xs, c)
        self.assertEqual(out.factors[0].direction, BULLISH)
        self.assertEqual(out.factors[1].direction, BULLISH)
        self.assertEqual(out.result.state, BULLISH)
        c2 = cfg(trend_lookback=3, momentum_lookback=1, trend_entry_threshold=Decimal("0.20"))
        out2 = self.engine.classify(xs, c2)
        self.assertEqual(out2.factors[0].direction, RANGE)
        self.assertEqual(out2.factors[1].direction, BULLISH)
        self.assertEqual(out2.result.state, RANGE)

    def test_stable_state_persistence_and_hysteresis(self):
        first = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        held = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120", "126"]))
        a = self.engine.classify(first, cfg())
        b = self.engine.classify(held, cfg(), previous_state=a.result.state)
        self.assertEqual(a.result.state, BULLISH)
        self.assertEqual(b.result.state, BULLISH)

    def test_bearish_state_persistence(self):
        first = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "80"]))
        held = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "80", "74"]))
        a = self.engine.classify(first, cfg())
        b = self.engine.classify(held, cfg(), previous_state=a.result.state)
        self.assertEqual(a.result.state, BEARISH)
        self.assertEqual(b.result.state, BEARISH)
        self.assertEqual(b.transition, "UNCHANGED")

    def test_direct_opposite_transition_from_bullish_to_bearish(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "80"]))
        out = self.engine.classify(xs, cfg(), previous_state=BULLISH)
        self.assertEqual(out.result.state, BEARISH)
        self.assertEqual(out.transition, "BULLISH->BEARISH")

    def test_direct_opposite_transition_from_bearish_to_bullish(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        out = self.engine.classify(xs, cfg(), previous_state=BEARISH)
        self.assertEqual(out.result.state, BULLISH)
        self.assertEqual(out.transition, "BEARISH->BULLISH")

    def test_exact_entry_threshold_qualifies(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "110"]))
        out = self.engine.classify(xs, cfg())
        self.assertEqual(out.result.state, BULLISH)

    def test_exact_exit_threshold_exits(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "105"]))
        out = self.engine.classify(xs, cfg(), previous_state=BULLISH)
        self.assertEqual(out.result.state, RANGE)
        self.assertEqual(out.transition, "BULLISH->RANGE")

    def test_bearish_hysteresis_and_exact_exit(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "95"]))
        out = self.engine.classify(xs, cfg(), previous_state=BEARISH)
        self.assertEqual(out.result.state, RANGE)
        self.assertEqual(out.transition, "BEARISH->RANGE")

    def test_range_previous_state_reenters_directional_state(self):
        bullish = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        bearish = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "80"]))
        self.assertEqual(self.engine.classify(bullish, cfg(), previous_state=RANGE).result.state, BULLISH)
        self.assertEqual(self.engine.classify(bearish, cfg(), previous_state=RANGE).result.state, BEARISH)

    def test_insufficient_previous_state_matrix_is_explicit(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "101"]))
        for previous in (None, RANGE, INSUFFICIENT, BULLISH, BEARISH):
            with self.subTest(previous_state=previous):
                out = self.engine.classify(xs, cfg(), previous_state=previous)
                self.assertEqual(out.result.state, INSUFFICIENT)
                self.assertEqual(out.result.result.status, CalculationStatus.INSUFFICIENT_HISTORY)
                self.assertIsNone(out.result.result.value)
                self.assertEqual([f.direction for f in out.factors], [INSUFFICIENT, INSUFFICIENT])

    def test_empty_input_is_deterministically_insufficient(self):
        a = self.engine.classify((), cfg())
        b = self.engine.classify((), cfg())
        self.assertEqual(a, b)
        self.assertEqual(a.result.state, INSUFFICIENT)
        self.assertIsNone(a.context)
        self.assertEqual(a.transition, "INSUFFICIENT_HISTORY")

    def test_previous_state_validation(self):
        with self.assertRaises(ValueError):
            self.engine.classify(tuple(candle(i, "100") for i in range(4)), cfg(), previous_state="INVALID")

    def test_malformed_candle_type_rejected(self):
        with self.assertRaisesRegex(TypeError, "candles\[1\] must be CanonicalCandle"):
            self.engine.classify((candle(0, "100"), object(), candle(2, "102"), candle(3, "103")), cfg())

    def test_cross_instrument_rejected(self):
        xs = (candle(0, "100"), candle(1, "101", instrument="ETHUSDT"),
              candle(2, "102"), candle(3, "103"))
        with self.assertRaises(ValueError):
            self.engine.classify(xs, cfg())

    def test_timeframe_mismatch_rejected(self):
        xs = (candle(0, "100"), candle(1, "101"), candle(2, "102"),
              candle(3, "103", timeframe="5m"))
        with self.assertRaises(ValueError):
            self.engine.classify(xs, cfg())

    def test_temporal_overlap_rejected(self):
        a = candle(0, "100")
        b = CanonicalCandle("BTCUSDT", "1m", a.open_time + timedelta(seconds=30),
                            a.close_time + timedelta(seconds=30), Decimal("101"),
                            Decimal("101"), Decimal("101"), Decimal("101"),
                            Decimal("10"), provenance_id="overlap")
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            self.engine.classify((a, b), cfg())

    def test_non_increasing_temporal_input_rejected_separately(self):
        a = candle(0, "100")
        b = CanonicalCandle("BTCUSDT", "1m", a.open_time, a.close_time,
                            Decimal("101"), Decimal("101"), Decimal("101"), Decimal("101"),
                            Decimal("10"), provenance_id="duplicate-open")
        with self.assertRaisesRegex(ValueError, "strictly increasing by open_time"):
            self.engine.classify((a, b), cfg())

    def test_no_lookahead(self):
        prefix = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        future = prefix + (candle(4, "50"),)
        a = self.engine.classify(prefix, cfg())
        b = self.engine.classify(future, cfg())
        self.assertEqual(a.result.state, BULLISH)
        self.assertEqual(a.context.timestamp, prefix[-1].close_time)
        self.assertEqual(b.context.timestamp, future[-1].close_time)

    def test_provenance_and_version_are_preserved(self):
        xs = tuple(candle(i, v, provenance=f"prov-{i}") for i, v in enumerate(["100", "100", "100", "120"]))
        out = self.engine.classify(xs, cfg())
        self.assertEqual(out.context.source_ref, "canonical-provenance:prov-0|prov-1|prov-2|prov-3")
        self.assertEqual(out.context.symbol, "BTCUSDT")
        self.assertEqual(out.context.timeframe, "1m")
        self.assertEqual(out.configuration_version, "1.0.0")

    def test_configuration_and_version_change_are_explicit_and_deterministic(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        baseline = self.engine.classify(xs, cfg(version="1.0.0"))
        replay = self.engine.classify(xs, cfg(version="1.0.0"))
        changed = self.engine.classify(
            xs,
            cfg(
                trend_entry_threshold=Decimal("0.20"),
                momentum_entry_threshold=Decimal("0.20"),
                version="2.0.0",
            ),
        )
        self.assertEqual(baseline, replay)
        self.assertEqual(baseline.result.state, BULLISH)
        self.assertEqual(changed.result.state, RANGE)
        self.assertEqual(changed.configuration_version, "2.0.0")
        self.assertEqual(changed.context.version, "2.0.0")
        self.assertNotEqual(baseline.configuration_version, changed.configuration_version)

    def test_explicit_context_is_authoritative(self):
        ctx = QuantitativeContext(source_ref="explicit", timestamp=T0, timeframe="5m",
                                  symbol="X", venue_context="venue-a", version="9.0.0")
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        out = self.engine.classify(xs, cfg(version="2.0.0"), context=ctx)
        self.assertEqual(out.context, ctx)

    def test_malformed_and_nonfinite_config_rejected(self):
        with self.assertRaises(TypeError):
            RegimeConfig(2, 2, 0.1, Decimal("0.05"), Decimal("0.1"), Decimal("0.05"))
        with self.assertRaises(ValueError):
            RegimeConfig(2, 2, Decimal("NaN"), Decimal("0.05"), Decimal("0.1"), Decimal("0.05"))

    def test_deterministic_replay(self):
        xs = tuple(candle(i, v) for i, v in enumerate(["100", "100", "100", "120"]))
        a = self.engine.classify(xs, cfg())
        b = self.engine.classify(xs, cfg())
        self.assertEqual(a, b)


class TestVenueEvidenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VenueEvidenceEngine()
        self.left = QuantitativeContext("left-source", T0, "1m", "BTCUSDT", "VENUE-A", "1.0.0")
        self.right = QuantitativeContext("right-source", T0, "1m", "BTCUSDT", "VENUE-B", "1.0.0")

    def evidence(self, value, ctx, metric="mid_price", status=CalculationStatus.VALID):
        return VenueEvidence(metric, Decimal(value) if value is not None else None, status, ctx)

    def test_comparable_cross_venue_evidence(self):
        out = self.engine.compare(self.evidence("100", self.left), self.evidence("101", self.right))
        self.assertEqual(out.classification, COMPARABLE)
        self.assertEqual(out.result.status, CalculationStatus.VALID)
        self.assertEqual(out.result.value, Decimal("1"))
        self.assertEqual(out.result.context.venue_context, "VENUE-A|VENUE-B")

    def test_instrument_mismatch_is_incompatible(self):
        right = QuantitativeContext("r", T0, "1m", "ETHUSDT", "VENUE-B", "1.0.0")
        out = self.engine.compare(self.evidence("101", self.left), self.evidence("101", right))
        self.assertEqual(out.classification, INCOMPATIBLE)
        self.assertEqual(out.result.status, CalculationStatus.INVALID_INPUT)

    def test_timeframe_mismatch_is_incompatible(self):
        right = QuantitativeContext("r", T0, "5m", "BTCUSDT", "VENUE-B", "1.0.0")
        out = self.engine.compare(self.evidence("101", self.left), self.evidence("101", right))
        self.assertEqual(out.classification, INCOMPATIBLE)

    def test_timestamp_mismatch_is_incompatible(self):
        right = QuantitativeContext("r", T0 + timedelta(minutes=1), "1m", "BTCUSDT", "VENUE-B", "1.0.0")
        out = self.engine.compare(self.evidence("101", self.left), self.evidence("101", right))
        self.assertEqual(out.classification, INCOMPATIBLE)

    def test_same_venue_is_not_cross_venue_comparison(self):
        right = QuantitativeContext("r", T0, "1m", "BTCUSDT", "VENUE-A", "1.0.0")
        out = self.engine.compare(self.evidence("101", self.left), self.evidence("101", right))
        self.assertEqual(out.classification, INCOMPATIBLE)

    def test_missing_venue_context_is_insufficient(self):
        right = QuantitativeContext("r", T0, "1m", "BTCUSDT", None, "1.0.0")
        out = self.engine.compare(self.evidence("101", self.left), self.evidence("101", right))
        self.assertEqual(out.classification, INSUFFICIENT_EVIDENCE)

    def test_unavailable_evidence_is_insufficient(self):
        unavailable = self.evidence(None, self.left, status=CalculationStatus.UNAVAILABLE)
        out = self.engine.compare(unavailable, self.evidence("101", self.right))
        self.assertEqual(out.classification, INSUFFICIENT_EVIDENCE)
        self.assertEqual(out.result.status, CalculationStatus.INSUFFICIENT_HISTORY)

    def test_venue_evidence_validity_boundaries(self):
        with self.assertRaises(ValueError):
            VenueEvidence("mid_price", Decimal("100"), CalculationStatus.UNAVAILABLE, self.left)
        with self.assertRaises(ValueError):
            VenueEvidence("mid_price", None, CalculationStatus.VALID, self.left)
        with self.assertRaises(TypeError):
            VenueEvidence("mid_price", 100.0, CalculationStatus.VALID, self.left)

    def test_invalid_comparison_operands_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.compare(object(), self.evidence("101", self.right))
        with self.assertRaises(TypeError):
            self.engine.compare(self.evidence("100", self.left), None)

    def test_metric_mismatch_is_incompatible(self):
        out = self.engine.compare(self.evidence("100", self.left, "funding_rate"),
                                  self.evidence("101", self.right, "mid_price"))
        self.assertEqual(out.classification, INCOMPATIBLE)

    def test_deterministic_replay(self):
        a = self.engine.compare(self.evidence("100", self.left), self.evidence("101", self.right))
        b = self.engine.compare(self.evidence("100", self.left), self.evidence("101", self.right))
        self.assertEqual(a, b)

    def test_decimal_extremes(self):
        out = self.engine.compare(self.evidence("0.000000000001", self.left),
                                  self.evidence("1000000000000", self.right))
        self.assertEqual(out.result.value, Decimal("999999999999.999999999999"))


if __name__ == "__main__":
    unittest.main()
