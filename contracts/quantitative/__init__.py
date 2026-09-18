"""Authoritative Phase-4 quantitative foundation contracts.

Pure, provider-neutral contracts. No network, database, filesystem, clock,
mutable global state, or AI dependency is permitted here.
"""
from .base import CalculationResult, CalculationStatus, QuantitativeContext
from .indicators import IndicatorResult
from .structure import MarketStructureResult
from .volume_profile import VolumeProfileResult
from .order_flow import OrderFlowResult
from .regime import RegimeResult

__all__ = [
    "CalculationResult", "CalculationStatus", "QuantitativeContext",
    "IndicatorResult", "MarketStructureResult", "VolumeProfileResult",
    "OrderFlowResult", "RegimeResult",
]
