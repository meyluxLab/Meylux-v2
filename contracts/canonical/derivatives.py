"""Canonical derivatives-market-data contract for Meylux V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


SID = "CTR-V2-CANONICAL-DERIVATIVES"
VERSION = "1.0.0"


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _decimal(value: Decimal, field: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    return value


@dataclass(frozen=True, slots=True)
class CanonicalDerivatives:
    """Validated immutable derivatives evidence snapshot.

    Rates may be signed. Open interest is a non-negative quantity. Basis is a
    signed price-difference value when available; missing optional evidence is
    represented by ``None`` rather than fabricated values.
    """

    instrument_id: str
    timestamp: datetime
    funding_rate: Optional[Decimal] = None
    funding_change: Optional[Decimal] = None
    funding_velocity: Optional[Decimal] = None
    open_interest: Optional[Decimal] = None
    open_interest_delta: Optional[Decimal] = None
    basis: Optional[Decimal] = None
    provenance_id: str = ""

    def __post_init__(self) -> None:
        _text(self.instrument_id, "instrument_id")
        _text(self.provenance_id, "provenance_id")
        _utc(self.timestamp, "timestamp")

        for field in (
            "funding_rate",
            "funding_change",
            "funding_velocity",
            "open_interest",
            "open_interest_delta",
            "basis",
        ):
            value = getattr(self, field)
            if value is not None:
                _decimal(value, field)

        if self.open_interest is not None and self.open_interest < 0:
            raise ValueError("open_interest must be non-negative")
