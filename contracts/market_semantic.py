"""Deterministic market-semantic validation for STEP-P3-004.

This module consumes existing P3 validation and Decimal semantics. It is
provider-neutral, side-effect free, and does not define market-specific
thresholds, tick sizes, lot sizes, or normalization policies.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from contracts.canonical.foundation import (
    ValidationCode,
    ValidationIssue,
    ValidationOutcome,
    validate_decimal_scale,
    validation_outcome,
)


def _decimal_issue(value: object, field: str) -> ValidationIssue | None:
    """Validate an exact finite Decimal without inventing conversion rules."""

    if isinstance(value, float):
        return ValidationIssue(ValidationCode.FLOAT_NOT_ALLOWED, field, f"{field} must be Decimal; float is forbidden")
    if not isinstance(value, Decimal):
        return ValidationIssue(ValidationCode.INVALID_TYPE, field, f"{field} must be Decimal")
    if not value.is_finite():
        return ValidationIssue(ValidationCode.NON_FINITE_DECIMAL, field, f"{field} must be finite")
    return None


def validate_price(value: object, field: str = "price") -> ValidationIssue | None:
    """Validate a market price as a finite, strictly positive Decimal."""

    issue = _decimal_issue(value, field)
    if issue is not None:
        return issue
    assert isinstance(value, Decimal)
    if value <= 0:
        return ValidationIssue(ValidationCode.INVALID_VALUE, field, f"{field} must be positive")
    return None


def validate_ohlc(values: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    """Validate positive OHLC values and deterministic internal ordering."""

    issues: list[ValidationIssue] = []
    required = ("open", "high", "low", "close")
    for field in required:
        if field not in values:
            issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, field, f"{field} is required"))
            continue
        issue = validate_price(values[field], field)
        if issue is not None:
            issues.append(issue)

    if issues:
        return tuple(issues)

    open_value = values["open"]
    high_value = values["high"]
    low_value = values["low"]
    close_value = values["close"]
    assert all(isinstance(value, Decimal) for value in (open_value, high_value, low_value, close_value))

    relationships = (
        (high_value >= low_value, "high", "high must be >= low"),
        (high_value >= open_value, "high", "high must be >= open"),
        (high_value >= close_value, "high", "high must be >= close"),
        (low_value <= open_value, "low", "low must be <= open"),
        (low_value <= close_value, "low", "low must be <= close"),
    )
    for valid, field, message in relationships:
        if not valid:
            issues.append(ValidationIssue(ValidationCode.INVALID_VALUE, field, message))
    return tuple(issues)


def validate_quantity(value: object, field: str = "quantity") -> ValidationIssue | None:
    """Validate quantity using existing positive canonical quantity semantics."""

    issue = _decimal_issue(value, field)
    if issue is not None:
        return issue
    assert isinstance(value, Decimal)
    if value <= 0:
        return ValidationIssue(ValidationCode.INVALID_VALUE, field, f"{field} must be positive")
    return None


def validate_volume(value: object, field: str = "volume") -> ValidationIssue | None:
    """Validate volume using existing canonical candle non-negative semantics."""

    issue = _decimal_issue(value, field)
    if issue is not None:
        return issue
    assert isinstance(value, Decimal)
    if value < 0:
        return ValidationIssue(ValidationCode.INVALID_VALUE, field, f"{field} must be non-negative")
    return None


def validate_bid_ask(
    bid: object,
    ask: object,
    bid_field: str = "bid",
    ask_field: str = "ask",
) -> tuple[ValidationIssue, ...]:
    """Validate positive bid/ask prices and the existing best-bid/best-ask relation."""

    issues: list[ValidationIssue] = []
    bid_issue = validate_price(bid, bid_field)
    ask_issue = validate_price(ask, ask_field)
    if bid_issue is not None:
        issues.append(bid_issue)
    if ask_issue is not None:
        issues.append(ask_issue)
    if issues:
        return tuple(issues)

    assert isinstance(bid, Decimal) and isinstance(ask, Decimal)
    if bid >= ask:
        issues.append(
            ValidationIssue(
                ValidationCode.INVALID_VALUE,
                ask_field,
                f"{ask_field} must be greater than {bid_field}",
            )
        )
    return tuple(issues)


def validate_spread(
    bid: object,
    ask: object,
    spread: object | None = None,
) -> tuple[ValidationIssue, ...]:
    """Validate bid/ask integrity and, when supplied, exact spread equality."""

    issues = list(validate_bid_ask(bid, ask))
    if issues:
        return tuple(issues)

    assert isinstance(bid, Decimal) and isinstance(ask, Decimal)
    expected = ask - bid
    if spread is not None:
        spread_issue = _decimal_issue(spread, "spread")
        if spread_issue is not None:
            issues.append(spread_issue)
        elif isinstance(spread, Decimal) and spread != expected:
            issues.append(
                ValidationIssue(
                    ValidationCode.INVALID_VALUE,
                    "spread",
                    "spread must equal ask - bid",
                )
            )
    return tuple(issues)


def validate_precision(
    value: object,
    scale: int,
    field: str = "value",
) -> ValidationIssue | None:
    """Validate Decimal scale using the existing P3-001 no-rounding doctrine."""

    decimal_issue = _decimal_issue(value, field)
    if decimal_issue is not None:
        return decimal_issue
    try:
        validate_decimal_scale(value, field, scale)
    except ValueError as exc:
        message = str(exc)
        code = ValidationCode.SCALE_INVALID if message == "scale must be a non-negative integer" else ValidationCode.PRECISION_INVALID
        return ValidationIssue(code, field, message)
    return None


def validate_market_semantics(
    values: Mapping[str, Any],
    *,
    precision_scales: Mapping[str, int] | None = None,
) -> ValidationOutcome:
    """Validate supplied market-semantic fields without inventing absent policy.

    Fields are validated only when supplied. Market-specific precision/scale
    parameters are caller-supplied and are enforced only when explicitly
    provided by an authoritative contract/configuration.
    """

    if not isinstance(values, Mapping):
        issue = ValidationIssue(ValidationCode.INVALID_TYPE, "record", "record must be a mapping")
        return validation_outcome((issue,))

    issues: list[ValidationIssue] = []

    if "price" in values:
        issue = validate_price(values["price"], "price")
        if issue is not None:
            issues.append(issue)

    if any(field in values for field in ("open", "high", "low", "close")):
        issues.extend(validate_ohlc(values))

    if "quantity" in values:
        issue = validate_quantity(values["quantity"])
        if issue is not None:
            issues.append(issue)

    if "volume" in values:
        issue = validate_volume(values["volume"])
        if issue is not None:
            issues.append(issue)

    if "bid" in values or "ask" in values:
        if "bid" not in values:
            issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, "bid", "bid is required when ask is supplied"))
        elif "ask" not in values:
            issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, "ask", "ask is required when bid is supplied"))
        else:
            issues.extend(validate_spread(values["bid"], values["ask"], values.get("spread")))
    elif "spread" in values:
        issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, "bid", "bid and ask are required to validate spread"))
        issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, "ask", "bid and ask are required to validate spread"))

    if precision_scales is not None:
        for field, scale in precision_scales.items():
            if field in values:
                issue = validate_precision(values[field], scale, field)
                if issue is not None:
                    issues.append(issue)

    return validation_outcome(issues)
