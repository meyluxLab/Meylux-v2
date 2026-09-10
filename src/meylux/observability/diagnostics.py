"""Deterministic operational health classification for P1 observability."""
from __future__ import annotations
from .core import HealthState

def classify_health(*, backlog: int, max_backlog: int, dependency_available: bool = True, capability_available: bool = True) -> HealthState:
    if backlog < 0 or max_backlog <= 0: raise ValueError("invalid backlog bounds")
    if not capability_available: return HealthState.UNAVAILABLE
    if not dependency_available: return HealthState.DEPENDENCY_FAILURE
    if backlog >= max_backlog: return HealthState.OVERLOAD
    if backlog * 100 >= max_backlog * 80: return HealthState.DEGRADED
    return HealthState.NORMAL