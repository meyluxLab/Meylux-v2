"""Bounded structured observability foundation for Meylux V2."""
from .diagnostics import classify_health
from .core import HealthState, ObservabilityLimits, Severity, clear_context, configure_logging, emit, get_context, new_correlation_id, scrub, set_context
__all__=["HealthState","ObservabilityLimits","Severity","clear_context","configure_logging","emit","get_context","new_correlation_id","scrub","set_context", "classify_health"]