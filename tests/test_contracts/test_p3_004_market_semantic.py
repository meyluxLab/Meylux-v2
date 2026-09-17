from decimal import Decimal

from contracts.canonical.foundation import ValidationCode, ValidationResult
from contracts.market_semantic import (
    validate_market_semantics,
    validate_ohlc,
    validate_precision,
    validate_spread,
    validate_quantity,
    validate_volume,
)


def test_positive_price_is_valid() -> None:
    outcome = validate_market_semantics({"price": Decimal("100.25")})
    assert outcome.result is ValidationResult.VALID
    assert outcome.issues == ()


def test_non_positive_price_is_rejected() -> None:
    outcome = validate_market_semantics({"price": Decimal("0")})
    assert outcome.result is ValidationResult.REJECTED
    assert outcome.issues[0].code is ValidationCode.INVALID_VALUE


def test_ohlc_valid_relationships_are_accepted() -> None:
    issues = validate_ohlc(
        {
            "open": Decimal("100"),
            "high": Decimal("110"),
            "low": Decimal("90"),
            "close": Decimal("105"),
        }
    )
    assert issues == ()


def test_ohlc_high_low_violation_is_detected() -> None:
    issues = validate_ohlc(
        {"open": Decimal("100"), "high": Decimal("90"), "low": Decimal("95"), "close": Decimal("98")}
    )
    assert any(issue.field == "high" and "high must be >= low" in issue.message for issue in issues)


def test_ohlc_high_open_violation_is_detected() -> None:
    issues = validate_ohlc(
        {"open": Decimal("100"), "high": Decimal("99"), "low": Decimal("90"), "close": Decimal("95")}
    )
    assert any(issue.field == "high" and "high must be >= open" in issue.message for issue in issues)


def test_ohlc_high_close_violation_is_detected() -> None:
    issues = validate_ohlc(
        {"open": Decimal("100"), "high": Decimal("105"), "low": Decimal("90"), "close": Decimal("110")}
    )
    assert any(issue.field == "high" and "high must be >= close" in issue.message for issue in issues)


def test_ohlc_low_open_violation_is_detected() -> None:
    issues = validate_ohlc(
        {"open": Decimal("100"), "high": Decimal("110"), "low": Decimal("101"), "close": Decimal("105")}
    )
    assert any(issue.field == "low" and "low must be <= open" in issue.message for issue in issues)


def test_ohlc_low_close_violation_is_detected() -> None:
    issues = validate_ohlc(
        {"open": Decimal("100"), "high": Decimal("110"), "low": Decimal("106"), "close": Decimal("105")}
    )
    assert any(issue.field == "low" and "low must be <= close" in issue.message for issue in issues)


def test_positive_quantity_and_non_negative_volume_are_valid() -> None:
    assert validate_quantity(Decimal("2")) is None
    assert validate_volume(Decimal("0")) is None


def test_invalid_quantity_and_volume_are_detected() -> None:
    assert validate_quantity(Decimal("0")) is not None
    assert validate_volume(Decimal("-1")) is not None


def test_bid_ask_and_exact_spread_are_valid() -> None:
    assert validate_spread(Decimal("100"), Decimal("101"), Decimal("1")) == ()


def test_invalid_spread_relationship_is_detected() -> None:
    issues = validate_spread(Decimal("100"), Decimal("101"), Decimal("2"))
    assert issues
    assert issues[0].code is ValidationCode.INVALID_VALUE


def test_bid_must_be_lower_than_ask() -> None:
    issues = validate_spread(Decimal("101"), Decimal("100"))
    assert issues
    assert issues[0].field == "ask"


def test_authoritative_decimal_scale_is_enforced_without_rounding() -> None:
    assert validate_precision(Decimal("1.23"), 2) is None
    issue = validate_precision(Decimal("1.234"), 2)
    assert issue is not None
    assert issue.code is ValidationCode.PRECISION_INVALID


def test_float_is_not_accepted_as_authoritative_numeric_input() -> None:
    outcome = validate_market_semantics({"price": 1.25})
    assert outcome.result is ValidationResult.REJECTED
    assert outcome.issues[0].code is ValidationCode.FLOAT_NOT_ALLOWED


def test_missing_market_specific_precision_parameter_is_not_invented() -> None:
    outcome = validate_market_semantics({"price": Decimal("1.2345")})
    assert outcome.result is ValidationResult.VALID


def test_precision_is_applied_only_when_caller_supplies_authoritative_scale() -> None:
    outcome = validate_market_semantics(
        {"price": Decimal("1.2345")},
        precision_scales={"price": 4},
    )
    assert outcome.result is ValidationResult.VALID


def test_regression_validation_outcome_taxonomy_is_reused() -> None:
    valid = validate_market_semantics({"quantity": Decimal("2")})
    invalid = validate_market_semantics({"quantity": Decimal("0")})
    assert valid.result is ValidationResult.VALID
    assert invalid.result is ValidationResult.REJECTED
