"""Market-structure domain contract foundation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from .base import CalculationResult

@dataclass(frozen=True, slots=True)
class MarketStructureResult:
    """One deterministic market-structure fact or state value."""
    event_type: str
    result: CalculationResult
    calculation_version: str = "1.0.0"
    event_location: datetime | None = None
    confirmation_time: datetime | None = None
    knowledge_time: datetime | None = None
    level: Decimal | None = None
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    direction: str | None = None
    lifecycle: str | None = None
    structural_state: str | None = None
    identity: str | None = None
    source_event_identity: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not self.event_type:
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(self.result, CalculationResult):
            raise TypeError("result must be CalculationResult")
        if not isinstance(self.calculation_version, str) or not self.calculation_version:
            raise ValueError("calculation_version must be non-empty")
        for name in ("event_location", "confirmation_time", "knowledge_time"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, datetime):
                    raise TypeError(f"{name} must be datetime")
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError(f"{name} must be timezone-aware UTC")
                if value.utcoffset() != timezone.utc.utcoffset(value):
                    raise ValueError(f"{name} must use UTC")
        for name in ("level", "lower_bound", "upper_bound"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, Decimal):
                    raise TypeError(f"{name} must be Decimal")
                if not value.is_finite():
                    raise ValueError(f"{name} must be finite")
        for name in ("direction", "lifecycle", "structural_state", "identity", "source_event_identity"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be non-empty when supplied")
