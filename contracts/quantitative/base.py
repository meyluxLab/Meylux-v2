"""Shared Phase-4 quantitative result semantics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping


class CalculationStatus(str, Enum):
    VALID = "valid"
    INSUFFICIENT_HISTORY = "insufficient_history"
    INVALID_INPUT = "invalid_input"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class QuantitativeContext:
    """Optional provenance/context carried with a deterministic quantitative fact."""
    source_ref: str | None = None
    timestamp: datetime | None = None
    timeframe: str | None = None
    symbol: str | None = None
    venue_context: str | None = None
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in ("source_ref", "timeframe", "symbol", "venue_context", "version"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be a non-empty string when supplied")
        if self.timestamp is not None:
            if not isinstance(self.timestamp, datetime):
                raise TypeError("timestamp must be datetime")
            if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
                raise ValueError("timestamp must be timezone-aware UTC")
            if self.timestamp.utcoffset() != timezone.utc.utcoffset(self.timestamp):
                raise ValueError("timestamp must use UTC")


@dataclass(frozen=True, slots=True)
class CalculationResult:
    """Deterministic calculation result; absent values are represented explicitly."""
    value: Decimal | None
    status: CalculationStatus
    reason: str
    context: QuantitativeContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, CalculationStatus):
            raise TypeError("status must be CalculationStatus")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be a non-empty string")
        if self.value is not None:
            if isinstance(self.value, float) or not isinstance(self.value, Decimal):
                raise TypeError("value must be Decimal or None")
            if not self.value.is_finite():
                raise ValueError("value must be finite")
            if self.status is not CalculationStatus.VALID:
                raise ValueError("non-null value requires VALID status")
        elif self.status is CalculationStatus.VALID:
            raise ValueError("VALID result requires a numeric value")

    @property
    def valid(self) -> bool:
        return self.status is CalculationStatus.VALID
