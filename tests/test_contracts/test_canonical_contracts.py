from datetime import datetime, timezone
from decimal import Decimal
import unittest

from contracts.canonical.derivatives import CanonicalDerivatives, SID as DERIVATIVES_SID
from contracts.canonical.instrument import CanonicalInstrument, SID as INSTRUMENT_SID
from contracts.canonical.orderbook import CanonicalOrderBook, SID as ORDERBOOK_SID
from contracts.canonical.trade import CanonicalTrade, SID as TRADE_SID


TS = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


class CanonicalInstrumentTests(unittest.TestCase):
    def make_instrument(self, **overrides):
        values = {
            "instrument_id": "BTCUSDT-SPOT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "market_type": "SPOT",
            "contract_type": "SPOT",
            "unit": "BTC",
            "as_of": TS,
            "price_precision": 2,
            "quantity_precision": 6,
            "contract_multiplier": None,
            "active": True,
            "provenance_id": "fixture-instrument-001",
        }
        values.update(overrides)
        return CanonicalInstrument(**values)

    def test_identity_and_valid_instance(self):
        self.assertEqual(INSTRUMENT_SID, "CTR-V2-CANONICAL-INSTRUMENT")
        self.assertEqual(self.make_instrument().base_asset, "BTC")

    def test_immutable(self):
        with self.assertRaises(Exception):
            self.make_instrument().active = False

    def test_precision_and_multiplier_are_deterministic(self):
        with self.assertRaises(TypeError):
            self.make_instrument(price_precision=2.0)
        with self.assertRaises(ValueError):
            self.make_instrument(quantity_precision=-1)
        with self.assertRaises(TypeError):
            self.make_instrument(contract_multiplier=1.0)
        with self.assertRaises(ValueError):
            self.make_instrument(contract_multiplier=Decimal("0"))

    def test_timestamp_and_provenance_are_required(self):
        with self.assertRaises(ValueError):
            self.make_instrument(as_of=datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            self.make_instrument(provenance_id="")


class CanonicalTradeTests(unittest.TestCase):
    def make_trade(self, **overrides):
        values = {
            "trade_id": "canonical-trade-001",
            "instrument_id": "BTCUSDT-SPOT",
            "timestamp": TS,
            "price": Decimal("100.25"),
            "quantity": Decimal("0.50"),
            "aggressor_side": "BUY",
            "quote_quantity": Decimal("50.125"),
            "provenance_id": "fixture-trade-001",
        }
        values.update(overrides)
        return CanonicalTrade(**values)

    def test_identity_and_valid_instance(self):
        self.assertEqual(TRADE_SID, "CTR-V2-CANONICAL-TRADE")
        self.assertEqual(self.make_trade().price, Decimal("100.25"))

    def test_decimal_and_positive_numeric_boundary(self):
        with self.assertRaises(TypeError):
            self.make_trade(price=100.25)
        with self.assertRaises(ValueError):
            self.make_trade(quantity=Decimal("0"))
        with self.assertRaises(ValueError):
            self.make_trade(quote_quantity=Decimal("-1"))

    def test_side_and_timestamp_validation(self):
        with self.assertRaises(ValueError):
            self.make_trade(aggressor_side="LONG")
        with self.assertRaises(ValueError):
            self.make_trade(timestamp=datetime(2026, 1, 1))

    def test_immutable(self):
        with self.assertRaises(Exception):
            self.make_trade().price = Decimal("101")


class CanonicalOrderBookTests(unittest.TestCase):
    def make_book(self, **overrides):
        values = {
            "instrument_id": "BTCUSDT-SPOT",
            "timestamp": TS,
            "bids": (
                (Decimal("99"), Decimal("2")),
                (Decimal("98"), Decimal("3")),
            ),
            "asks": (
                (Decimal("101"), Decimal("1")),
                (Decimal("102"), Decimal("4")),
            ),
            "provenance_id": "fixture-book-001",
        }
        values.update(overrides)
        return CanonicalOrderBook(**values)

    def test_identity_and_valid_instance(self):
        self.assertEqual(ORDERBOOK_SID, "CTR-V2-CANONICAL-ORDERBOOK")
        self.assertEqual(self.make_book().bids[0][0], Decimal("99"))

    def test_levels_require_decimal_positive_values(self):
        with self.assertRaises(TypeError):
            self.make_book(bids=((99.0, Decimal("2")),))
        with self.assertRaises(ValueError):
            self.make_book(asks=((Decimal("101"), Decimal("0")),))

    def test_levels_are_ordered_and_unique(self):
        with self.assertRaises(ValueError):
            self.make_book(bids=((Decimal("98"), Decimal("1")), (Decimal("99"), Decimal("1"))))
        with self.assertRaises(ValueError):
            self.make_book(asks=((Decimal("101"), Decimal("1")), (Decimal("101"), Decimal("2"))))

    def test_book_cannot_be_crossed_or_empty(self):
        with self.assertRaises(ValueError):
            self.make_book(bids=((Decimal("101"), Decimal("1")),))
        with self.assertRaises(ValueError):
            self.make_book(bids=(), asks=())

    def test_immutable(self):
        with self.assertRaises(Exception):
            self.make_book().bids = ()


class CanonicalDerivativesTests(unittest.TestCase):
    def make_derivatives(self, **overrides):
        values = {
            "instrument_id": "BTCUSDT-PERP",
            "timestamp": TS,
            "funding_rate": Decimal("0.0001"),
            "funding_change": Decimal("0.00002"),
            "funding_velocity": Decimal("0.000005"),
            "open_interest": Decimal("1000"),
            "open_interest_delta": Decimal("25"),
            "basis": Decimal("12.5"),
            "provenance_id": "fixture-derivatives-001",
        }
        values.update(overrides)
        return CanonicalDerivatives(**values)

    def test_identity_and_valid_instance(self):
        self.assertEqual(DERIVATIVES_SID, "CTR-V2-CANONICAL-DERIVATIVES")
        self.assertEqual(self.make_derivatives().open_interest, Decimal("1000"))

    def test_signed_rates_and_basis_are_allowed(self):
        result = self.make_derivatives(
            funding_rate=Decimal("-0.0001"),
            funding_change=Decimal("-0.00002"),
            funding_velocity=Decimal("-0.000005"),
            open_interest_delta=Decimal("-25"),
            basis=Decimal("-12.5"),
        )
        self.assertEqual(result.funding_rate, Decimal("-0.0001"))

    def test_decimal_and_open_interest_validation(self):
        with self.assertRaises(TypeError):
            self.make_derivatives(open_interest=1000.0)
        with self.assertRaises(ValueError):
            self.make_derivatives(open_interest=Decimal("-1"))
        with self.assertRaises(ValueError):
            self.make_derivatives(funding_rate=Decimal("NaN"))

    def test_missing_optional_evidence_is_none_not_fabricated(self):
        result = self.make_derivatives(
            funding_rate=None,
            funding_change=None,
            funding_velocity=None,
            open_interest=None,
            open_interest_delta=None,
            basis=None,
        )
        self.assertIsNone(result.basis)

    def test_immutable(self):
        with self.assertRaises(Exception):
            self.make_derivatives().basis = Decimal("13")


if __name__ == "__main__":
    unittest.main()
