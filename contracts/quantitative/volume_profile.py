"""Volume-profile domain contract foundation."""
from __future__ import annotations
from dataclasses import dataclass
from .base import CalculationResult


@dataclass(frozen=True, slots=True)
class VolumeProfileResult:
    """One deterministic volume-profile fact."""
    metric: str
    result: CalculationResult
    calculation_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not isinstance(self.metric, str) or not self.metric:
            raise ValueError("metric must be a non-empty string")
        if not isinstance(self.result, CalculationResult):
            raise TypeError("result must be CalculationResult")
        if not isinstance(self.calculation_version, str) or not self.calculation_version:
            raise ValueError("calculation_version must be non-empty")
