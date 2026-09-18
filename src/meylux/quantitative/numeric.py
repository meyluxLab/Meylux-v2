"""Authoritative deterministic numeric policy for Phase 4.

The implementation uses Decimal throughout the public mathematical boundary
and internal primitive calculations. This is an implementation choice made
within TO-P4-001: it avoids binary floating-point drift while retaining an
explicit Decimal boundary compatible with P3 canonical numeric contracts.

No implicit rounding is performed. Quantization is explicit and uses
ROUND_HALF_EVEN. Golden vectors compare canonical Decimal serialization
exactly, not by tolerance.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Any


ROUNDING = ROUND_HALF_EVEN
SERIALIZATION = "plain_decimal"
DEFAULT_QUANTUM = Decimal("0.000000000001")


def to_decimal(value: Any, field: str = "value") -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field} must not be bool or float")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, str):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{field} is not a valid decimal") from exc
    else:
        raise TypeError(f"{field} must be Decimal, int, or str")
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def quantize(value: Any, quantum: Any) -> Decimal:
    """Explicitly quantize a finite numeric value; never silently repair input."""
    number = to_decimal(value)
    q = to_decimal(quantum, "quantum")
    if q <= 0:
        raise ValueError("quantum must be positive")
    return number.quantize(q, rounding=ROUNDING)


def serialize_decimal(value: Any) -> str:
    """Canonical non-exponent decimal string used by golden-vector comparison."""
    number = to_decimal(value)
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"
