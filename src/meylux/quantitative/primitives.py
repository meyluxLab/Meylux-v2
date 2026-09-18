"""Pure deterministic quantitative primitives for STEP-P4-001."""
from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Iterable, Sequence

from contracts.quantitative.base import CalculationResult, CalculationStatus
from .numeric import to_decimal


def _values(values: Iterable[object], field: str = "values") -> tuple[Decimal, ...]:
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field} must be iterable") from exc
    return tuple(to_decimal(value, f"{field}[{i}]") for i, value in enumerate(raw))


def _valid(value: Decimal, reason: str = "ok") -> CalculationResult:
    return CalculationResult(value=value, status=CalculationStatus.VALID, reason=reason)


def _insufficient(required: int, actual: int) -> CalculationResult:
    return CalculationResult(
        value=None,
        status=CalculationStatus.INSUFFICIENT_HISTORY,
        reason=f"requires_at_least_{required}_values; received_{actual}",
    )


def _invalid(reason: str) -> CalculationResult:
    return CalculationResult(value=None, status=CalculationStatus.INVALID_INPUT, reason=reason)


def average(values: Iterable[object]) -> CalculationResult:
    xs = _values(values)
    if not xs:
        return _insufficient(1, 0)
    return _valid(sum(xs, Decimal(0)) / Decimal(len(xs)))


def weighted_average(values: Iterable[object], weights: Iterable[object]) -> CalculationResult:
    xs = _values(values, "values")
    ws = _values(weights, "weights")
    if not xs:
        return _insufficient(1, 0)
    if len(xs) != len(ws):
        return _invalid("values_and_weights_length_mismatch")
    denominator = sum(ws, Decimal(0))
    if denominator == 0:
        return _invalid("weights_sum_must_not_be_zero")
    return _valid(sum((x * w for x, w in zip(xs, ws)), Decimal(0)) / denominator)


def rolling_mean(values: Iterable[object], window: int) -> tuple[CalculationResult, ...]:
    xs = _values(values)
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")
    out: list[CalculationResult] = []
    for i in range(len(xs)):
        if i + 1 < window:
            out.append(_insufficient(window, i + 1))
        else:
            sample = xs[i + 1 - window : i + 1]
            out.append(_valid(sum(sample, Decimal(0)) / Decimal(window)))
    return tuple(out)


def exponential_smoothing(values: Iterable[object], alpha: object) -> tuple[CalculationResult, ...]:
    xs = _values(values)
    a = to_decimal(alpha, "alpha")
    if not Decimal("0") < a <= Decimal("1"):
        raise ValueError("alpha must be in (0, 1]")
    if not xs:
        return ()
    out: list[CalculationResult] = [_valid(xs[0])]
    previous = xs[0]
    for current in xs[1:]:
        previous = a * current + (Decimal(1) - a) * previous
        out.append(_valid(previous))
    return tuple(out)


def standard_deviation(values: Iterable[object], ddof: int = 0) -> CalculationResult:
    xs = _values(values)
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof not in (0, 1):
        raise ValueError("ddof must be 0 or 1")
    if len(xs) <= ddof:
        return _insufficient(ddof + 1, len(xs))
    with localcontext() as context:
        context.prec = max(50, max((len(x.as_tuple().digits) for x in xs), default=1) + 20)
        mean = sum(xs, Decimal(0)) / Decimal(len(xs))
        variance = sum((x - mean) ** 2 for x in xs) / Decimal(len(xs) - ddof)
        return _valid(variance.sqrt())


def percentile(values: Iterable[object], rank: object) -> CalculationResult:
    xs = _values(values)
    if not xs:
        return _insufficient(1, 0)
    p = to_decimal(rank, "rank")
    if p < 0 or p > 100:
        return _invalid("rank_must_be_between_0_and_100")
    ordered = tuple(sorted(xs))
    if len(ordered) == 1:
        return _valid(ordered[0])
    position = (p / Decimal(100)) * Decimal(len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - Decimal(lower)
    return _valid(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


def accumulate(values: Iterable[object], start: object = Decimal(0)) -> tuple[CalculationResult, ...]:
    xs = _values(values)
    total = to_decimal(start, "start")
    out: list[CalculationResult] = []
    for value in xs:
        total += value
        out.append(_valid(total))
    return tuple(out)


def normalize_min_max(values: Iterable[object]) -> tuple[CalculationResult, ...]:
    xs = _values(values)
    if not xs:
        return ()
    low, high = min(xs), max(xs)
    if low == high:
        return tuple(_invalid("normalization_range_must_not_be_zero") for _ in xs)
    span = high - low
    return tuple(_valid((x - low) / span) for x in xs)
