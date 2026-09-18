"""Indicator-domain contract foundation."""
from __future__ import annotations
from dataclasses import dataclass
from .base import CalculationResult


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    """One deterministic indicator value with explicit calculation semantics."""
    name: str
    result: CalculationResult
    calculation_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.result, CalculationResult):
            raise TypeError("result must be CalculationResult")
        if not isinstance(self.calculation_version, str) or not self.calculation_version:
            raise ValueError("calculation_version must be non-empty")
