"""Evidence tests for TO-P3-001 canonical contract foundation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from contracts.canonical.candle import CanonicalCandle
from contracts.canonical.derivatives import CanonicalDerivatives
from contracts.canonical.foundation import (
    LineageRef,
    ProvenanceRef,
    ValidationCode,
    ValidationResult,
    deterministic_identity,
    require_decimal,
    validate_allowed,
    validate_decimal_scale,
    validate_provenance,
    validate_required_fields,
    validate_timestamp,
    validation_outcome,
)
from contracts.canonical.instrument import CanonicalInstrument
from contracts.canonical.orderbook import CanonicalOrderBook
from contracts.canonical.trade import CanonicalTrade


UTC = timezone.utc
NOW = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


class CanonicalFoundationTests(unittest.TestCase):
    def test_all_existing_canonical_contracts_construct_with_semantic_values(self):
        instrument = CanonicalInstrument(
            instrument_id="BTC-USD-SPOT",
            base_asset="BTC",
            quote_asset="USD",
            market_type="spot",
            contract_type="spot",
            unit="asset",
            as_of=NOW,
            price_precision=2,
            quantity_precision=6,
            contract_multiplier=Decimal("1"),
            provenance_id="source:fixture/instrument",
        )
        self.assertEqual(instrument.instrument_id, "BTC-USD-SPOT")

        candle = CanonicalCandle(
            instrument_id=instrument.instrument_id,
            timeframe="1m",
            open_time=NOW,
            close_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100.5"),
            volume=Decimal("2"),
            provenance_id="source:fixture/candle",
        )
        trade = CanonicalTrade(
            trade_id="trade-1",
            instrument_id=instrument.instrument_id,
            timestamp=NOW,
            price=Decimal("100.5"),
            quantity=Decimal("0.1"),
            aggressor_side="BUY",
            provenance_id="source:fixture/trade",
        )
        book = CanonicalOrderBook(
            instrument_id=instrument.instrument_id,
            timestamp=NOW,
            bids=((Decimal("100"), Decimal("1")),),
            asks=((Decimal("101"), Decimal("1")),),
            provenance_id="source:fixture/orderbook",
        )
        derivatives = CanonicalDerivatives(
            instrument_id=instrument.instrument_id,
            timestamp=NOW,
            funding_rate=Decimal("0.0001"),
            open_interest=Decimal("10"),
            provenance_id="source:fixture/derivatives",
        )
        self.assertEqual(candle.close, Decimal("100.5"))
        self.assertEqual(trade.quantity, Decimal("0.1"))
        self.assertEqual(book.bids[0][0], Decimal("100"))
        self.assertEqual(derivatives.open_interest, Decimal("10"))

    def test_required_optional_and_null_semantics(self):
        issues = validate_required_fields(
            {"venue": "binance", "symbol": None, "market_type": "spot"},
            ("venue", "symbol", "market_type", "contract_type"),
        )
        self.assertEqual(
            [issue.code for issue in issues],
            [ValidationCode.NULL_NOT_ALLOWED, ValidationCode.REQUIRED_MISSING],
        )
        outcome = validation_outcome(issues)
        self.assertEqual(outcome.result, ValidationResult.INCOMPLETE)
        self.assertFalse(outcome.valid)

    def test_decimal_is_authoritative_and_float_is_rejected(self):
        self.assertEqual(require_decimal(Decimal("1.20"), "price"), Decimal("1.20"))
        with self.assertRaises(TypeError):
            require_decimal(1.2, "price")
        with self.assertRaises(ValueError):
            require_decimal(Decimal("NaN"), "price")
        with self.assertRaises(ValueError):
            require_decimal(Decimal("Infinity"), "price")

    def test_scale_rejects_without_rounding(self):
        self.assertEqual(validate_decimal_scale(Decimal("1.20"), "price", 2), Decimal("1.20"))
        with self.assertRaises(ValueError):
            validate_decimal_scale(Decimal("1.201"), "price", 2)

    def test_timestamp_requires_aware_utc(self):
        self.assertEqual(validate_timestamp(NOW), NOW)
        with self.assertRaises(ValueError):
            validate_timestamp(datetime(2026, 1, 1), "timestamp")
        with self.assertRaises(ValueError):
            validate_timestamp(datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=2))), "timestamp")

    def test_governed_vocabulary_is_explicit_and_provider_neutral(self):
        allowed = ("spot", "futures")
        self.assertIsNone(validate_allowed("spot", "market_type", allowed))
        issue = validate_allowed("unknown", "market_type", allowed)
        self.assertIsNotNone(issue)
        self.assertEqual(issue.code, ValidationCode.INVALID_VALUE)
        self.assertEqual(validation_outcome((issue,)).result, ValidationResult.REJECTED)

    def test_deterministic_identity_is_order_independent(self):
        left = deterministic_identity({"venue": "binance", "symbol": "BTCUSDT", "market": "spot"})
        right = deterministic_identity({"market": "spot", "symbol": "BTCUSDT", "venue": "binance"})
        self.assertEqual(left, right)
        self.assertEqual(len(left), 64)

    def test_provenance_and_lineage_are_required_and_immutable(self):
        provenance = ProvenanceRef("prov:fixture/1", "fixture", "test")
        lineage = LineageRef("raw:fixture/1", "validation")
        self.assertEqual(provenance.provenance_id, "prov:fixture/1")
        self.assertEqual(lineage.parent_id, "raw:fixture/1")
        self.assertIsNone(validate_provenance(provenance))
        with self.assertRaises((AttributeError, TypeError)):
            provenance.source = "other"  # type: ignore[misc]

    def test_missing_provenance_is_rejected_by_canonical_validation_boundary(self):
        issue = validate_provenance(None)
        self.assertIsNotNone(issue)
        self.assertEqual(issue.code, ValidationCode.PROVENANCE_MISSING)
        outcome = validation_outcome((issue,))
        self.assertEqual(outcome.result, ValidationResult.INCOMPLETE)
        self.assertFalse(outcome.valid)

    def test_invalid_empty_provenance_is_rejected(self):
        with self.assertRaises(ValueError):
            ProvenanceRef("", "fixture", "test")
        issue = validate_provenance("not-a-provenance-ref")
        self.assertIsNotNone(issue)
        self.assertEqual(issue.code, ValidationCode.INVALID_TYPE)
        self.assertEqual(validation_outcome((issue,)).result, ValidationResult.REJECTED)

    def test_validation_result_taxonomy_and_outcome_mapping_are_authoritative(self):
        expected = {
            ValidationResult.VALID,
            ValidationResult.DEGRADED,
            ValidationResult.STALE,
            ValidationResult.INCOMPLETE,
            ValidationResult.CONTRADICTORY,
            ValidationResult.REJECTED,
            ValidationResult.UNAVAILABLE,
        }
        self.assertEqual(set(ValidationResult), expected)
        self.assertEqual(validation_outcome(()).result, ValidationResult.VALID)
        self.assertEqual(
            validation_outcome((ValidationCodeIssue := None,) if False else ()).result,
            ValidationResult.VALID,
        )


if __name__ == "__main__":
    unittest.main()
