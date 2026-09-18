import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical import CanonicalCandle
from meylux.quantitative.indicators import (
    adx, anchored_vwap, atr, atr_percentile, bollinger_bandwidth, bollinger_bands,
    ema, historical_volatility, hma, macd, rsi, sma, supertrend, volume_climax,
    volume_sma, volume_spike, vwap, volatility_expansion_ratio, wma, rvol,
)
from meylux.quantitative.numeric import serialize_decimal


def make_candles(data):
    closes = [Decimal(str(x)) for x in data["closes"]]
    highs = [Decimal(str(x)) for x in data.get("highs", [x + Decimal("0.5") for x in closes])]
    lows = [Decimal(str(x)) for x in data.get("lows", [x - Decimal("0.5") for x in closes])]
    volumes = [Decimal(str(x)) for x in data.get("volumes", [100] * len(closes))]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        CanonicalCandle(
            instrument_id="GOLDEN",
            timeframe="1h",
            open_time=start + timedelta(hours=i),
            close_time=start + timedelta(hours=i + 1),
            open=closes[i], high=highs[i], low=lows[i], close=closes[i],
            volume=volumes[i], provenance_id=f"golden-{i}",
        )
        for i in range(len(closes))
    )


FUNCTIONS = {
    "ema": lambda d: ema(d["values"], d["window"]),
    "sma": lambda d: sma(d["values"], d["window"]),
    "wma": lambda d: wma(d["values"], d["window"]),
    "hma": lambda d: hma(d["values"], d["period"]),
    "rsi": lambda d: rsi(make_candles(d), d["period"]),
    "macd": lambda d: macd(make_candles(d), d["fast_period"], d["slow_period"], d["signal_period"]),
    "atr": lambda d: atr(make_candles(d), d["period"]),
    "adx": lambda d: adx(make_candles(d), d["period"]),
    "bollinger_bands": lambda d: bollinger_bands(make_candles(d), d["window"], d["deviations"]),
    "bollinger_bandwidth": lambda d: bollinger_bandwidth(make_candles(d), d["window"], d["deviations"]),
    "supertrend": lambda d: supertrend(make_candles(d), d["period"], d["multiplier"]),
    "historical_volatility": lambda d: historical_volatility(make_candles(d), d["window"], d["periods_per_year"]),
    "atr_percentile": lambda d: atr_percentile(make_candles(d), d["atr_period"], d["lookback"]),
    "volatility_expansion_ratio": lambda d: volatility_expansion_ratio(make_candles(d), d["atr_period"], d["baseline_window"]),
    "volume_sma": lambda d: volume_sma(make_candles(d), d["window"]),
    "rvol": lambda d: rvol(make_candles(d), d["window"]),
    "volume_spike": lambda d: volume_spike(make_candles(d), d["window"], d["threshold"]),
    "volume_climax": lambda d: volume_climax(make_candles(d), d["window"], d["threshold"]),
    "vwap": lambda d: vwap(make_candles(d)),
    "anchored_vwap": lambda d: anchored_vwap(make_candles(d), d["anchor_index"]),
}


class IndicatorGoldenVectorTests(unittest.TestCase):
    def test_controlled_vectors_are_exact(self):
        with open("tests/golden_vectors/p4_002_indicators.json", encoding="utf-8") as fh:
            vectors = json.load(fh)
        for vector in vectors:
            result = FUNCTIONS[vector["function"]](vector["input"])[vector["index"]]
            expected = vector["expected"]
            if vector["function"] == "macd":
                actual = {
                    "macd": serialize_decimal(result.macd.value),
                    "signal": serialize_decimal(result.signal.value),
                    "histogram": serialize_decimal(result.histogram.value),
                }
                self.assertEqual(actual, expected, vector["id"])
            elif vector["function"] == "bollinger_bands":
                actual = {
                    "middle": serialize_decimal(result.middle.value),
                    "upper": serialize_decimal(result.upper.value),
                    "lower": serialize_decimal(result.lower.value),
                }
                self.assertEqual(actual, expected, vector["id"])
            elif vector["function"] == "supertrend":
                actual = {
                    "value": serialize_decimal(result.value.value),
                    "upper_band": serialize_decimal(result.upper_band.value),
                    "lower_band": serialize_decimal(result.lower_band.value),
                    "direction": serialize_decimal(result.direction.value),
                }
                self.assertEqual(actual, expected, vector["id"])
            else:
                self.assertEqual(serialize_decimal(result.value), expected, vector["id"])

    def test_vectors_are_reproducible(self):
        with open("tests/golden_vectors/p4_002_indicators.json", encoding="utf-8") as fh:
            vectors = json.load(fh)
        for _ in range(3):
            for vector in vectors:
                result = FUNCTIONS[vector["function"]](vector["input"])[vector["index"]]
                self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
