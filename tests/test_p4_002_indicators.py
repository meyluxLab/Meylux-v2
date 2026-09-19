import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical import CanonicalCandle
from contracts.quantitative import CalculationStatus
from meylux.quantitative.indicators import (
    adx, anchored_vwap, atr, atr_percentile, bollinger_bandwidth, bollinger_bands,
    ema, ema_candles, historical_volatility, hma, macd, rsi, sma, supertrend,
    volume_climax, volume_sma, volume_spike, vwap, volatility_expansion_ratio, wma,
)
from meylux.quantitative.numeric import serialize_decimal


def candles(closes, highs=None, lows=None, volumes=None, closed=True):
    closes = [Decimal(str(x)) for x in closes]
    highs = [Decimal(str(x)) for x in (highs or [x + Decimal("0.5") for x in closes])]
    lows = [Decimal(str(x)) for x in (lows or [x - Decimal("0.5") for x in closes])]
    volumes = [Decimal(str(x)) for x in (volumes or [100] * len(closes))]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        CanonicalCandle(
            instrument_id="TEST",
            timeframe="1h",
            open_time=start + timedelta(hours=i),
            close_time=start + timedelta(hours=i + 1),
            open=closes[i],
            high=highs[i],
            low=lows[i],
            close=closes[i],
            volume=volumes[i],
            is_closed=closed,
            provenance_id=f"prov-{i}",
        )
        for i in range(len(closes))
    )


class MovingAverageTests(unittest.TestCase):
    def test_ema_sma_wma_and_hma_warmup_and_exact_values(self):
        xs = [1, 2, 3, 4, 5, 6]
        self.assertEqual([r.status for r in ema(xs, 3)[:2]], [CalculationStatus.INSUFFICIENT_HISTORY] * 2)
        self.assertEqual([serialize_decimal(r.value) for r in ema(xs, 3)[2:]], ["2", "3.0000000000000000000000000000000000000000000000000000000000000000000000000000000", "4.0000000000000000000000000000000000000000000000000000000000000000000000000000000", "5.0000000000000000000000000000000000000000000000000000000000000000000000000000000"])
        self.assertEqual(serialize_decimal(sma(xs, 3)[2].value), "2")
        self.assertEqual(serialize_decimal(wma(xs, 3)[2].value), "2.3333333333333333333333333333333333333333333333333333333333333333333333333333333")
        self.assertEqual(serialize_decimal(hma(xs, 4)[4].value), "5.00000000000000000000000000000000000000000000000000000000000000000000000000000006666666666666666666666666666666666666667")

    def test_moving_average_parameter_validation(self):
        for fn in (ema, sma, wma):
            with self.assertRaises(ValueError):
                fn([1, 2], 0)
            with self.assertRaises(TypeError):
                fn([1.0, 2], 2)
        with self.assertRaises(ValueError):
            hma([1, 2, 3], 1)

    def test_hma_does_not_mutate_input(self):
        xs = [1, 2, 3, 4, 5]
        before = xs[:]
        hma(xs, 4)
        self.assertEqual(xs, before)


class MomentumTests(unittest.TestCase):
    def test_rsi_wilder_seed_and_flat_market(self):
        cs = candles([10, 11, 12, 11, 13, 14])
        values = rsi(cs, 2)
        self.assertEqual(values[1].status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertEqual(serialize_decimal(values[2].value), "100")
        self.assertEqual(serialize_decimal(values[3].value), "50")
        flat = rsi(candles([10, 10, 10]), 2)
        self.assertEqual(flat[2].value, Decimal("50"))

    def test_macd_signal_alignment(self):
        cs = candles([10, 11, 12, 13, 14, 15, 16, 17])
        points = macd(cs, fast_period=2, slow_period=3, signal_period=2)
        self.assertFalse(points[1].macd.valid)
        self.assertTrue(points[2].macd.valid)
        self.assertFalse(points[2].signal.valid)
        self.assertTrue(points[3].signal.valid)
        self.assertTrue(points[3].histogram.valid)
        self.assertEqual(points[3].histogram.value, Decimal("5E-29"))


class VolatilityTests(unittest.TestCase):
    def test_atr_and_adx_warmup(self):
        cs = candles([10, 11, 12, 11, 13, 14], [11, 12, 13, 12, 14, 15], [9, 10, 11, 10, 12, 13])
        av = atr(cs, 2)
        self.assertEqual(serialize_decimal(av[1].value), "2")
        self.assertEqual(serialize_decimal(av[4].value), "2.5")
        dx = adx(cs, 2)
        self.assertEqual(dx[2].status, CalculationStatus.VALID)
        self.assertEqual(dx[2].value, Decimal("100"))

    def test_bollinger_band_and_bandwidth(self):
        cs = candles([1, 2, 3, 4])
        bands = bollinger_bands(cs, 3, "2")
        self.assertFalse(bands[1].middle.valid)
        self.assertEqual(serialize_decimal(bands[2].middle.value), "2")
        self.assertEqual(serialize_decimal(bands[2].upper.value), "3.63299316185545206546485604980392759464396498710444675228846171150064025163821")
        bandwidth = bollinger_bandwidth(cs, 3, "2")
        self.assertEqual(serialize_decimal(bandwidth[2].value), "1.63299316185545206546485604980392759464396498710444675228846171150064025163821")

    def test_historical_volatility_and_atr_features(self):
        cs = candles([100, 101, 102, 104, 103, 105], [101,102,103,105,104,106], [99,100,101,103,102,104])
        hv = historical_volatility(cs, window=2, periods_per_year=4)
        self.assertEqual(hv[2].status, CalculationStatus.VALID)
        self.assertTrue(hv[2].value > 0)
        ap = atr_percentile(cs, atr_period=2, lookback=2)
        self.assertEqual(ap[2].value, Decimal("100"))
        ex = volatility_expansion_ratio(cs, atr_period=2, baseline_window=2)
        self.assertEqual(ex[2].value, Decimal("1"))


class VolumeAndVWAPTests(unittest.TestCase):
    def test_volume_features_use_prior_window_for_rvol(self):
        cs = candles([10, 11, 12, 13], volumes=[100, 100, 100, 300])
        vs = volume_sma(cs, 2)
        self.assertEqual(vs[1].value, Decimal("100"))
        rv = __import__("meylux.quantitative.indicators", fromlist=["rvol"]).rvol(cs, 2)
        self.assertEqual(rv[2].value, Decimal("1"))
        self.assertEqual(rv[3].value, Decimal("3"))
        self.assertEqual(volume_spike(cs, 2, "2")[3].value, Decimal("1"))
        self.assertEqual(volume_climax(cs, 2, "4")[3].value, Decimal("0"))

    def test_vwap_and_explicit_anchor(self):
        cs = candles([10, 11, 12], highs=[11,12,13], lows=[9,10,11], volumes=[100,200,300])
        vw = vwap(cs)
        self.assertEqual(serialize_decimal(vw[0].value), "10")
        self.assertEqual(serialize_decimal(vw[2].value), "11.333333333333333333333333333333333333333333333333333333333333333333333333333333")
        av = anchored_vwap(cs, 1)
        self.assertEqual(av[0].status, CalculationStatus.INSUFFICIENT_HISTORY)
        self.assertEqual(serialize_decimal(av[1].value), "11")
        self.assertEqual(serialize_decimal(av[2].value), "11.6")
        with self.assertRaises(ValueError):
            anchored_vwap(cs, 3)

    def test_zero_volume_is_explicitly_invalid(self):
        cs = candles([10, 11], volumes=[0, 0])
        self.assertEqual(vwap(cs)[0].status, CalculationStatus.INVALID_INPUT)
        self.assertEqual(anchored_vwap(cs, 0)[0].status, CalculationStatus.INVALID_INPUT)

    def test_closed_state_and_temporal_order_are_enforced(self):
        with self.assertRaises(ValueError):
            ema_candles(candles([1,2], closed=False), 2)
        cs = list(candles([1,2,3]))
        cs[1] = CanonicalCandle(
            instrument_id="TEST", timeframe="1h",
            open_time=cs[0].open_time, close_time=cs[1].close_time,
            open=Decimal("2"), high=Decimal("3"), low=Decimal("1"), close=Decimal("2"),
            volume=Decimal("100"), provenance_id="dup"
        )
        with self.assertRaises(ValueError):
            ema_candles(cs, 2)


class IntegrityTests(unittest.TestCase):
    def test_malformed_and_nonfinite_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            ema([1.0, 2], 2)
        with self.assertRaises(TypeError):
            sma([None, 2], 2)
        with self.assertRaises(ValueError):
            wma(["NaN", "2"], 2)
        with self.assertRaises(ValueError):
            historical_volatility(candles([1,2,3]), 2, "0")


    def test_indicator_invariants_hold_on_valid_sequences(self):
        cs = candles([10, 11, 12, 11, 13, 14, 15, 14])
        av = atr(cs, 2)
        self.assertTrue(all((not x.valid) or x.value >= 0 for x in av))
        rv = __import__("meylux.quantitative.indicators", fromlist=["rvol"]).rvol(
            candles([10, 11, 12, 13], volumes=[100, 100, 100, 300]), 2
        )
        self.assertTrue(all((not x.valid) or x.value >= 0 for x in rv))
        bands = bollinger_bands(cs, 3, "2")
        for point in bands:
            if point.middle.valid:
                self.assertLessEqual(point.lower.value, point.middle.value)
                self.assertLessEqual(point.middle.value, point.upper.value)
        rs = rsi(cs, 2)
        self.assertTrue(all((not x.valid) or Decimal("0") <= x.value <= Decimal("100") for x in rs))
        st = supertrend(cs, 2, "3")
        self.assertTrue(all((not x.value.valid) or x.direction.value in (Decimal("-1"), Decimal("1")) for x in st))

    def test_missing_required_canonical_fields_are_rejected_at_boundary(self):
        with self.assertRaises(TypeError):
            CanonicalCandle(
                instrument_id="TEST", timeframe="1h",
                open_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
                close_time=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
                open=Decimal("1"), high=Decimal("2"), low=Decimal("1"),
                close=Decimal("1"), volume=None, provenance_id="missing-volume"
            )

    def test_no_lookahead_for_already_emitted_values(self):
        base = candles([10, 11, 12, 13, 14])
        extended = candles([10, 11, 12, 13, 14, 1000])
        a = ema_candles(base, 3)
        b = ema_candles(extended, 3)
        self.assertEqual([r.value for r in a], [r.value for r in b[:len(a)]])
        va = vwap(base)
        vb = vwap(extended)
        self.assertEqual([r.value for r in va], [r.value for r in vb[:len(va)]])

    def test_deterministic_recalculation(self):
        cs = candles([10,11,12,11,13,14,15,16])
        self.assertEqual(atr(cs, 3), atr(cs, 3))
        self.assertEqual(macd(cs, 2, 3, 2), macd(cs, 2, 3, 2))


if __name__ == "__main__":
    unittest.main()
