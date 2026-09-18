"""Deterministic Phase-4 quantitative foundation."""
from .numeric import quantize, serialize_decimal
from .primitives import (
    rolling_mean, average, weighted_average, exponential_smoothing,
    standard_deviation, percentile, accumulate, normalize_min_max,
)
from .golden import run_golden_vectors, load_golden_vectors

__all__ = [
    "quantize", "serialize_decimal",
    "rolling_mean", "average", "weighted_average", "exponential_smoothing",
    "standard_deviation", "percentile", "accumulate", "normalize_min_max",
    "run_golden_vectors", "load_golden_vectors",
]
