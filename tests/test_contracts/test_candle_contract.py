from datetime import datetime, timezone
from decimal import Decimal
import unittest

from contracts.canonical.candle import CanonicalCandle, SID, VERSION


class CanonicalCandleContractTests(unittest.TestCase):
    def make_candle(self, **overrides):
        values = {
            "instrument_id": "BTCUSDT",
            "timeframe": "1m",
            "open_time": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            "close_time": datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
            "open": Decimal("100.00"),
            "high": Decimal("105.00"),
            "low": Decimal("99.00"),
            "close": Decimal("103.00"),
            "volume": Decimal("12.50"),
            "quote_volume": Decimal("1287.50"),
            "trade_count": 42,
            "is_closed": True,
            "provenance_id": "fixture-001",
        }
        values.update(overrides)
        return CanonicalCandle(**values)

    def test_identity_and_version_are_explicit(self):
        self.assertEqual(SID, "CTR-V2-CANONICAL-CANDLE")
        self.assertEqual(VERSION, "1.0.0")

    def test_valid_candle_is_constructed(self):
        candle = self.make_candle()
        self.assertEqual(candle.open, Decimal("100.00"))
        self.assertEqual(candle.close_time.tzinfo, timezone.utc)

    def test_contract_is_immutable(self):
        candle = self.make_candle()
        with self.assertRaises(Exception):
            candle.close = Decimal("104.00")

    def test_float_is_rejected_at_numeric_boundary(self):
        with self.assertRaises(TypeError):
            self.make_candle(close=103.0)

    def test_non_finite_decimal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_candle(close=Decimal("NaN"))
        with self.assertRaises(ValueError):
            self.make_candle(close=Decimal("Infinity"))

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_candle(open_time=datetime(2026, 1, 1, 0, 0))

    def test_non_utc_timestamp_is_rejected(self):
        from datetime import timedelta, timezone

        local = timezone(timedelta(hours=3))
        with self.assertRaises(ValueError):
            self.make_candle(open_time=datetime(2026, 1, 1, 3, 0, tzinfo=local))

    def test_invalid_ohlc_relationship_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_candle(high=Decimal("102.00"))
        with self.assertRaises(ValueError):
            self.make_candle(low=Decimal("104.00"))

    def test_negative_volume_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_candle(volume=Decimal("-1"))

    def test_invalid_temporal_order_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_candle(
                close_time=datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)
            )

    def test_provenance_is_required(self):
        with self.assertRaises(ValueError):
            self.make_candle(provenance_id="")

    def test_optional_numeric_fields_follow_decimal_and_integer_rules(self):
        with self.assertRaises(TypeError):
            self.make_candle(quote_volume=1287.5)
        with self.assertRaises(TypeError):
            self.make_candle(trade_count=True)
        with self.assertRaises(ValueError):
            self.make_candle(trade_count=-1)


if __name__ == "__main__":
    unittest.main()
