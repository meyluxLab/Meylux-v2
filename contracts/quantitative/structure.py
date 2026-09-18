"""Market-structure domain contract foundation."""
from __future__ import annotations
from dataclasses import dataclass
from .base import CalculationResult


@dataclass(frozen=True, slots=True)
class MarketStructureResult:
    """One deterministic market-structure fact or state value."""
    event_type: str
    result: CalculationResult
    calculation_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not self.event_type:
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(self.result, CalculationResult):
            raise TypeError("result must be CalculationResult")
        if not isinstance(self.calculation_version, str) or not self.calculation_version:
            raise ValueError("calculation_version must be non-empty")
