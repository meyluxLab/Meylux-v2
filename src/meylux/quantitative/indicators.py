"""Deterministic technical-indicator, statistical and volatility engine for P4-002.

Pure computation over validated canonical candles or explicit numeric series.
No I/O, provider access, database access, filesystem access, wall-clock reads,
mutable global state, randomness, or trading capability is permitted here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from math import isqrt
from typing import Iterable, Sequence

from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationResult, CalculationStatus, QuantitativeContext
from .numeric import to_decimal


_PRECISION_FLOOR = 80


@dataclass(frozen=True, slots=True)
class BandPoint:
    middle: CalculationResult
    upper: CalculationResult
    lower: CalculationResult


@dataclass(frozen=True, slots=True)
class MACDPoint:
    macd: CalculationResult
    signal: CalculationResult
    histogram: CalculationResult


@dataclass(frozen=True, slots=True)
class SupertrendPoint:
    value: CalculationResult
    upper_band: CalculationResult
    lower_band: CalculationResult
    direction: CalculationResult  # +1 = up, -1 = down


@dataclass(frozen=True, slots=True)
class VolumeActivityPoint:
    volume_sma: CalculationResult
    rvol: CalculationResult
    spike: CalculationResult  # 1 when rvol >= spike_threshold, else 0
    climax: CalculationResult  # 1 when rvol >= climax_threshold, else 0


def _precision(values: Iterable[Decimal]) -> int:
    digits = max((len(v.as_tuple().digits) for v in values), default=1)
    return max(_PRECISION_FLOOR, digits + 40)


def _valid(value: Decimal, candle: CanonicalCandle | None = None, reason: str = "ok") -> CalculationResult:
    context = _context(candle) if candle is not None else None
    return CalculationResult(value=value, status=CalculationStatus.VALID, reason=reason, context=context)


def _insufficient(required: int, actual: int, candle: CanonicalCandle | None = None) -> CalculationResult:
    context = _context(candle) if candle is not None else None
    return CalculationResult(
        value=None,
        status=CalculationStatus.INSUFFICIENT_HISTORY,
        reason=f"requires_at_least_{required}_observations; received_{actual}",
        context=context,
    )


def _invalid(reason: str, candle: CanonicalCandle | None = None) -> CalculationResult:
    context = _context(candle) if candle is not None else None
    return CalculationResult(value=None, status=CalculationStatus.INVALID_INPUT, reason=reason, context=context)


def _context(candle: CanonicalCandle) -> QuantitativeContext:
    return QuantitativeContext(
        source_ref=candle.provenance_id,
        timestamp=candle.close_time,
        timeframe=candle.timeframe,
        symbol=candle.instrument_id,
        version="1.0.0",
    )


def _series(values: Iterable[object], field: str = "values") -> tuple[Decimal, ...]:
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field} must be iterable") from exc
    return tuple(to_decimal(v, f"{field}[{i}]") for i, v in enumerate(raw))


def _positive_period(period: object, name: str = "period") -> int:
    if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return period


def _nonnegative_decimal(value: object, name: str) -> Decimal:
    number = to_decimal(value, name)
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _validate_candles(candles: Iterable[CanonicalCandle]) -> tuple[CanonicalCandle, ...]:
    try:
        xs = tuple(candles)
    except TypeError as exc:
        raise TypeError("candles must be iterable") from exc
    for i, candle in enumerate(xs):
        if not isinstance(candle, CanonicalCandle):
            raise TypeError(f"candles[{i}] must be CanonicalCandle")
        if i:
            previous = xs[i - 1]
            if candle.instrument_id != previous.instrument_id:
                raise ValueError("candle instrument_id must remain constant")
            if candle.timeframe != previous.timeframe:
                raise ValueError("candle timeframe must remain constant")
            if candle.open_time <= previous.open_time:
                raise ValueError("candles must be strictly increasing by open_time; sorting is not permitted")
    return xs


def _require_closed(candles: Sequence[CanonicalCandle], allow_incomplete: bool) -> None:
    if not allow_incomplete:
        for i, candle in enumerate(candles):
            if not candle.is_closed:
                raise ValueError(f"candles[{i}] is incomplete; set allow_incomplete=True to compute provisional values")


def _numeric_series_from_candles(
    candles: Sequence[CanonicalCandle],
    field: str,
) -> tuple[Decimal, ...]:
    return tuple(getattr(candle, field) for candle in candles)


def _sma_series(xs: Sequence[Decimal], window: int, candles: Sequence[CanonicalCandle] | None = None) -> tuple[CalculationResult, ...]:
    out: list[CalculationResult] = []
    for i in range(len(xs)):
        candle = candles[i] if candles is not None else None
        if i + 1 < window:
            out.append(_insufficient(window, i + 1, candle))
        else:
            with localcontext() as ctx:
                ctx.prec = _precision(xs[i + 1 - window : i + 1])
                value = sum(xs[i + 1 - window : i + 1], Decimal(0)) / Decimal(window)
            out.append(_valid(value, candle))
    return tuple(out)


def _wma_window(sample: Sequence[Decimal]) -> Decimal:
    weights = range(1, len(sample) + 1)
    denominator = Decimal(sum(weights))
    return sum((x * Decimal(w) for x, w in zip(sample, weights)), Decimal(0)) / denominator


def _wma_series(xs: Sequence[Decimal], window: int, candles: Sequence[CanonicalCandle] | None = None) -> tuple[CalculationResult, ...]:
    out: list[CalculationResult] = []
    for i in range(len(xs)):
        candle = candles[i] if candles is not None else None
        if i + 1 < window:
            out.append(_insufficient(window, i + 1, candle))
        else:
            sample = xs[i + 1 - window : i + 1]
            with localcontext() as ctx:
                ctx.prec = _precision(sample)
                value = _wma_window(sample)
            out.append(_valid(value, candle))
    return tuple(out)


def _ema_series(xs: Sequence[Decimal], window: int, candles: Sequence[CanonicalCandle] | None = None) -> tuple[CalculationResult, ...]:
    out: list[CalculationResult] = []
    if not xs:
        return ()
    alpha = Decimal(2) / Decimal(window + 1)
    seed = _sma_series(xs, window, candles)
    previous: Decimal | None = None
    for i, candle in enumerate(candles if candles is not None else [None] * len(xs)):
        if i + 1 < window:
            out.append(seed[i])
            continue
        if previous is None:
            seed_values = xs[:window]
            if all(value == seed_values[0] for value in seed_values):
                previous = seed_values[0]
            else:
                previous = seed[i].value
                assert previous is not None
            out.append(_valid(previous, candle, reason="seed_sma"))
            continue
        with localcontext() as ctx:
            ctx.prec = _precision((previous, xs[i]))
            previous = alpha * xs[i] + (Decimal(1) - alpha) * previous
        out.append(_valid(previous, candle))
    return tuple(out)


def sma(values: Iterable[object], window: int) -> tuple[CalculationResult, ...]:
    """Simple moving average; first window-1 observations are insufficient."""
    xs = _series(values)
    n = _positive_period(window, "window")
    return _sma_series(xs, n)


def wma(values: Iterable[object], window: int) -> tuple[CalculationResult, ...]:
    """Linearly weighted moving average with weights 1..window."""
    xs = _series(values)
    n = _positive_period(window, "window")
    return _wma_series(xs, n)


def hma(values: Iterable[object], period: int) -> tuple[CalculationResult, ...]:
    """Hull moving average using floor(period/2) and floor(sqrt(period))."""
    xs = _series(values)
    n = _positive_period(period, "period")
    if n < 2:
        raise ValueError("period must be at least 2 for HMA")
    half = n // 2
    root = isqrt(n)
    fast = _wma_series(xs, half)
    slow = _wma_series(xs, n)
    raw: list[Decimal | None] = []
    for i in range(len(xs)):
        if fast[i].valid and slow[i].valid:
            assert fast[i].value is not None and slow[i].value is not None
            with localcontext() as ctx:
                ctx.prec = _precision((fast[i].value, slow[i].value))
                raw.append(Decimal(2) * fast[i].value - slow[i].value)
        else:
            raw.append(None)
    out: list[CalculationResult] = []
    for i in range(len(xs)):
        if raw[i] is None:
            out.append(_insufficient(n + root - 1, i + 1))
        else:
            sample_start = i + 1 - root
            if sample_start < 0 or any(v is None for v in raw[sample_start : i + 1]):
                out.append(_insufficient(n + root - 1, i + 1))
                continue
            sample = tuple(v for v in raw[sample_start : i + 1] if v is not None)
            with localcontext() as ctx:
                ctx.prec = _precision(sample)
                value = _wma_window(sample)
            out.append(_valid(value))
    return tuple(out)


def ema(values: Iterable[object], window: int) -> tuple[CalculationResult, ...]:
    """Exponential moving average seeded by the SMA of the first window observations."""
    xs = _series(values)
    n = _positive_period(window, "window")
    return _ema_series(xs, n)


def ema_candles(candles: Iterable[CanonicalCandle], window: int, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    return _ema_series(_numeric_series_from_candles(xs, "close"), _positive_period(window, "window"), xs)


def sma_candles(candles: Iterable[CanonicalCandle], window: int, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    return _sma_series(_numeric_series_from_candles(xs, "close"), _positive_period(window, "window"), xs)


def wma_candles(candles: Iterable[CanonicalCandle], window: int, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    return _wma_series(_numeric_series_from_candles(xs, "close"), _positive_period(window, "window"), xs)


def hma_candles(candles: Iterable[CanonicalCandle], period: int, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    values = _numeric_series_from_candles(xs, "close")
    # HMA's public numeric implementation has no candle context, so reconstruct
    # the exact same calculation while attaching per-observation provenance.
    numeric = hma(values, period)
    return tuple(
        _valid(r.value, xs[i], r.reason) if r.valid else (
            _insufficient(period + isqrt(period) - 1, i + 1, xs[i])
        )
        for i, r in enumerate(numeric)
    )


def rsi(candles: Iterable[CanonicalCandle], period: int = 14, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(period, "period")
    closes = _numeric_series_from_candles(xs, "close")
    if not closes:
        return ()
    out = [_insufficient(n + 1, i + 1, xs[i]) for i in range(len(xs))]
    if len(xs) <= n:
        return tuple(out)
    gains = [max(closes[i] - closes[i - 1], Decimal(0)) for i in range(1, len(xs))]
    losses = [max(closes[i - 1] - closes[i], Decimal(0)) for i in range(1, len(xs))]
    with localcontext() as ctx:
        ctx.prec = _precision(closes)
        avg_gain = sum(gains[:n], Decimal(0)) / Decimal(n)
        avg_loss = sum(losses[:n], Decimal(0)) / Decimal(n)
        for i in range(n, len(xs)):
            if i > n:
                avg_gain = (avg_gain * Decimal(n - 1) + gains[i - 1]) / Decimal(n)
                avg_loss = (avg_loss * Decimal(n - 1) + losses[i - 1]) / Decimal(n)
            if avg_loss == 0:
                value = Decimal(50) if avg_gain == 0 else Decimal(100)
            else:
                rs = avg_gain / avg_loss
                value = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))
            out[i] = _valid(value, xs[i], reason="wilder_rsi")
    return tuple(out)


def macd(
    candles: Iterable[CanonicalCandle],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    allow_incomplete: bool = False,
) -> tuple[MACDPoint, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    fast_n = _positive_period(fast_period, "fast_period")
    slow_n = _positive_period(slow_period, "slow_period")
    signal_n = _positive_period(signal_period, "signal_period")
    if fast_n >= slow_n:
        raise ValueError("fast_period must be less than slow_period")
    closes = _numeric_series_from_candles(xs, "close")
    fast = _ema_series(closes, fast_n, xs)
    slow = _ema_series(closes, slow_n, xs)
    macd_values: list[Decimal | None] = [None] * len(xs)
    for i in range(len(xs)):
        if fast[i].valid and slow[i].valid:
            assert fast[i].value is not None and slow[i].value is not None
            macd_values[i] = fast[i].value - slow[i].value
    signal_input = tuple(v for v in macd_values if v is not None)
    signal_series = _ema_series(signal_input, signal_n)
    signal_iter = iter(signal_series)
    points: list[MACDPoint] = []
    available_macd = 0
    available_signal = 0
    for i, candle in enumerate(xs):
        if macd_values[i] is None:
            points.append(MACDPoint(
                _insufficient(slow_n, i + 1, candle),
                _insufficient(slow_n + signal_n - 1, i + 1, candle),
                _insufficient(slow_n + signal_n - 1, i + 1, candle),
            ))
            continue
        available_macd += 1
        m = _valid(macd_values[i], candle)
        s = next(signal_iter)
        if s.valid:
            available_signal += 1
            assert s.value is not None
            signal = _valid(s.value, candle)
            histogram = _valid(macd_values[i] - s.value, candle)
        else:
            signal = _insufficient(slow_n + signal_n - 1, i + 1, candle)
            histogram = _insufficient(slow_n + signal_n - 1, i + 1, candle)
        points.append(MACDPoint(m, signal, histogram))
    return tuple(points)


def atr(candles: Iterable[CanonicalCandle], period: int = 14, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(period, "period")
    if not xs:
        return ()
    tr: list[Decimal] = [xs[0].high - xs[0].low]
    for i in range(1, len(xs)):
        tr.append(max(xs[i].high - xs[i].low, abs(xs[i].high - xs[i - 1].close), abs(xs[i].low - xs[i - 1].close)))
    out = [_insufficient(n, i + 1, xs[i]) for i in range(len(xs))]
    if len(xs) < n:
        return tuple(out)
    with localcontext() as ctx:
        ctx.prec = _precision(tr)
        value = sum(tr[:n], Decimal(0)) / Decimal(n)
        out[n - 1] = _valid(value, xs[n - 1], reason="wilder_atr_seed")
        for i in range(n, len(xs)):
            value = (value * Decimal(n - 1) + tr[i]) / Decimal(n)
            out[i] = _valid(value, xs[i])
    return tuple(out)


def adx(candles: Iterable[CanonicalCandle], period: int = 14, allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(period, "period")
    if len(xs) <= n:
        return tuple(_insufficient(2 * n - 1, i + 1, xs[i]) for i in range(len(xs)))
    tr: list[Decimal] = [xs[0].high - xs[0].low]
    plus_dm: list[Decimal] = [Decimal(0)]
    minus_dm: list[Decimal] = [Decimal(0)]
    for i in range(1, len(xs)):
        up = xs[i].high - xs[i - 1].high
        down = xs[i - 1].low - xs[i].low
        plus_dm.append(up if up > down and up > 0 else Decimal(0))
        minus_dm.append(down if down > up and down > 0 else Decimal(0))
        tr.append(max(xs[i].high - xs[i].low, abs(xs[i].high - xs[i - 1].close), abs(xs[i].low - xs[i - 1].close)))
    out = [_insufficient(2 * n - 1, i + 1, xs[i]) for i in range(len(xs))]
    with localcontext() as ctx:
        ctx.prec = _precision(tuple(tr) + tuple(plus_dm) + tuple(minus_dm))
        atr_s = sum(tr[:n], Decimal(0))
        plus_s = sum(plus_dm[:n], Decimal(0))
        minus_s = sum(minus_dm[:n], Decimal(0))
        dx: list[Decimal | None] = [None] * len(xs)
        for i in range(n - 1, len(xs)):
            if i >= n:
                atr_s = atr_s - atr_s / Decimal(n) + tr[i]
                plus_s = plus_s - plus_s / Decimal(n) + plus_dm[i]
                minus_s = minus_s - minus_s / Decimal(n) + minus_dm[i]
            if atr_s == 0:
                dx[i] = Decimal(0)
                continue
            plus_di = Decimal(100) * plus_s / atr_s
            minus_di = Decimal(100) * minus_s / atr_s
            denominator = plus_di + minus_di
            dx[i] = Decimal(0) if denominator == 0 else Decimal(100) * abs(plus_di - minus_di) / denominator
        valid_dx = [i for i, v in enumerate(dx) if v is not None]
        if len(valid_dx) >= n:
            first = valid_dx[n - 1]
            adx_value = sum((dx[i] for i in valid_dx[:n] if dx[i] is not None), Decimal(0)) / Decimal(n)
            out[first] = _valid(adx_value, xs[first], reason="wilder_adx_seed")
            for j in valid_dx[n:]:
                assert dx[j] is not None
                adx_value = (adx_value * Decimal(n - 1) + dx[j]) / Decimal(n)
                out[j] = _valid(adx_value, xs[j])
    return tuple(out)


def bollinger_bands(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    deviations: object = "2",
    allow_incomplete: bool = False,
) -> tuple[BandPoint, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(window, "window")
    k = _nonnegative_decimal(deviations, "deviations")
    closes = _numeric_series_from_candles(xs, "close")
    out: list[BandPoint] = []
    for i, candle in enumerate(xs):
        if i + 1 < n:
            r = _insufficient(n, i + 1, candle)
            out.append(BandPoint(r, r, r))
            continue
        sample = closes[i + 1 - n : i + 1]
        with localcontext() as ctx:
            ctx.prec = _precision(sample)
            mean = sum(sample, Decimal(0)) / Decimal(n)
            variance = sum((x - mean) ** 2 for x in sample) / Decimal(n)
            std = variance.sqrt()
            delta = k * std
        out.append(BandPoint(_valid(mean, candle), _valid(mean + delta, candle), _valid(mean - delta, candle)))
    return tuple(out)


def supertrend(
    candles: Iterable[CanonicalCandle],
    period: int = 10,
    multiplier: object = "3",
    allow_incomplete: bool = False,
) -> tuple[SupertrendPoint, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(period, "period")
    m = _nonnegative_decimal(multiplier, "multiplier")
    atr_values = atr(xs, n, allow_incomplete=True)
    out: list[SupertrendPoint] = []
    final_upper: Decimal | None = None
    final_lower: Decimal | None = None
    previous_value: Decimal | None = None
    previous_direction = 1
    for i, candle in enumerate(xs):
        if not atr_values[i].valid:
            r = _insufficient(n, i + 1, candle)
            out.append(SupertrendPoint(r, r, r, r))
            continue
        assert atr_values[i].value is not None
        with localcontext() as ctx:
            ctx.prec = _precision((candle.high, candle.low, atr_values[i].value))
            hl2 = (candle.high + candle.low) / Decimal(2)
            basic_upper = hl2 + m * atr_values[i].value
            basic_lower = hl2 - m * atr_values[i].value
            if final_upper is None or final_lower is None:
                final_upper, final_lower = basic_upper, basic_lower
                direction = 1
                value = final_lower
            else:
                assert previous_value is not None
                final_upper = basic_upper if basic_upper < final_upper or xs[i - 1].close > final_upper else final_upper
                final_lower = basic_lower if basic_lower > final_lower or xs[i - 1].close < final_lower else final_lower
                if previous_direction == -1:
                    if candle.close <= final_upper:
                        direction = -1
                        value = final_upper
                    else:
                        direction = 1
                        value = final_lower
                else:
                    if candle.close >= final_lower:
                        direction = 1
                        value = final_lower
                    else:
                        direction = -1
                        value = final_upper
        previous_value = value
        previous_direction = direction
        out.append(SupertrendPoint(
            _valid(value, candle),
            _valid(final_upper, candle),
            _valid(final_lower, candle),
            _valid(Decimal(direction), candle),
        ))
    return tuple(out)


def historical_volatility(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    periods_per_year: object = "365",
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(window, "window")
    annual_periods = _nonnegative_decimal(periods_per_year, "periods_per_year")
    if annual_periods <= 0:
        raise ValueError("periods_per_year must be positive")
    closes = _numeric_series_from_candles(xs, "close")
    returns: list[Decimal] = []
    out = [_insufficient(n + 1, i + 1, xs[i]) for i in range(len(xs))]
    with localcontext() as ctx:
        ctx.prec = _precision(closes)
        for i in range(1, len(closes)):
            returns.append((closes[i] / closes[i - 1]).ln())
        for i in range(n, len(closes)):
            sample = returns[i - n : i]
            mean = sum(sample, Decimal(0)) / Decimal(n)
            variance = sum((r - mean) ** 2 for r in sample) / Decimal(n - 1)
            value = variance.sqrt() * annual_periods.sqrt()
            out[i] = _valid(value, xs[i], reason="annualized_sample_log_return_volatility")
    return tuple(out)


def atr_percentile(
    candles: Iterable[CanonicalCandle],
    atr_period: int = 14,
    lookback: int = 100,
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    a_n = _positive_period(atr_period, "atr_period")
    l_n = _positive_period(lookback, "lookback")
    values = atr(xs, a_n, allow_incomplete=True)
    out: list[CalculationResult] = []
    for i, candle in enumerate(xs):
        if not values[i].valid:
            out.append(_insufficient(a_n + l_n - 1, i + 1, candle))
            continue
        available = [r.value for r in values[max(0, i - l_n + 1) : i + 1] if r.valid and r.value is not None]
        if len(available) < l_n:
            out.append(_insufficient(a_n + l_n - 1, i + 1, candle))
            continue
        current = available[-1]
        ordered = sorted(available)
        count = sum(1 for x in ordered if x <= current)
        rank = Decimal(count - 1) / Decimal(len(ordered) - 1) * Decimal(100) if len(ordered) > 1 else Decimal(100)
        out.append(_valid(rank, candle, reason="atr_lookback_percentile_rank"))
    return tuple(out)


def volatility_expansion_ratio(
    candles: Iterable[CanonicalCandle],
    atr_period: int = 14,
    baseline_window: int = 20,
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    a_n = _positive_period(atr_period, "atr_period")
    b_n = _positive_period(baseline_window, "baseline_window")
    atr_values = atr(xs, a_n, allow_incomplete=True)
    out: list[CalculationResult] = []
    for i, candle in enumerate(xs):
        if not atr_values[i].valid:
            out.append(_insufficient(a_n + b_n - 1, i + 1, candle))
            continue
        available = [r.value for r in atr_values[max(0, i - b_n + 1) : i + 1] if r.valid and r.value is not None]
        if len(available) < b_n:
            out.append(_insufficient(a_n + b_n - 1, i + 1, candle))
            continue
        baseline = sum(available, Decimal(0)) / Decimal(len(available))
        if baseline == 0:
            out.append(_invalid("atr_baseline_must_not_be_zero", candle))
        else:
            out.append(_valid(atr_values[i].value / baseline, candle, reason="current_atr_over_rolling_atr_mean"))
    return tuple(out)


def bollinger_bandwidth(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    deviations: object = "2",
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    bands = bollinger_bands(candles, window, deviations, allow_incomplete)
    out: list[CalculationResult] = []
    for point in bands:
        if not point.middle.valid:
            out.append(point.middle)
            continue
        assert point.middle.value is not None and point.upper.value is not None and point.lower.value is not None
        if point.middle.value == 0:
            out.append(_invalid("bollinger_middle_must_not_be_zero"))
        else:
            out.append(_valid((point.upper.value - point.lower.value) / point.middle.value, reason="bandwidth"))
    return tuple(out)


def volume_sma(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(window, "window")
    return _sma_series(_numeric_series_from_candles(xs, "volume"), n, xs)


def rvol(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    n = _positive_period(window, "window")
    volumes = _numeric_series_from_candles(xs, "volume")
    out: list[CalculationResult] = []
    for i, candle in enumerate(xs):
        if i < n:
            out.append(_insufficient(n + 1, i + 1, candle))
            continue
        baseline = sum(volumes[i - n : i], Decimal(0)) / Decimal(n)
        if baseline == 0:
            out.append(_invalid("prior_volume_baseline_must_not_be_zero", candle))
        else:
            out.append(_valid(volumes[i] / baseline, candle, reason="current_volume_over_prior_window_mean"))
    return tuple(out)


def volume_activity(
    candles: Iterable[CanonicalCandle],
    window: int = 20,
    spike_threshold: object = "2",
    climax_threshold: object = "4",
    allow_incomplete: bool = False,
) -> tuple[VolumeActivityPoint, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    spike = _nonnegative_decimal(spike_threshold, "spike_threshold")
    climax = _nonnegative_decimal(climax_threshold, "climax_threshold")
    if climax < spike:
        raise ValueError("climax_threshold must be >= spike_threshold")
    ratios = rvol(xs, window, allow_incomplete=True)
    volume_means = volume_sma(xs, window, allow_incomplete=True)
    out: list[VolumeActivityPoint] = []
    for i, candle in enumerate(xs):
        if not ratios[i].valid:
            out.append(VolumeActivityPoint(ratios[i] if not volume_means[i].valid else volume_means[i], ratios[i], ratios[i], ratios[i]))
            continue
        assert ratios[i].value is not None
        spike_value = Decimal(1) if ratios[i].value >= spike else Decimal(0)
        climax_value = Decimal(1) if ratios[i].value >= climax else Decimal(0)
        out.append(VolumeActivityPoint(
            volume_means[i],
            ratios[i],
            _valid(spike_value, candle, reason="rvol_spike_threshold"),
            _valid(climax_value, candle, reason="rvol_climax_threshold"),
        ))
    return tuple(out)


def volume_spike(candles: Iterable[CanonicalCandle], window: int = 20, threshold: object = "2", allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    return tuple(point.spike for point in volume_activity(candles, window, threshold, max(_nonnegative_decimal(threshold, "threshold"), Decimal("4")), allow_incomplete))


def volume_climax(candles: Iterable[CanonicalCandle], window: int = 20, threshold: object = "4", allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    t = _nonnegative_decimal(threshold, "threshold")
    return tuple(point.climax for point in volume_activity(candles, window, t, t, allow_incomplete))


def vwap(candles: Iterable[CanonicalCandle], allow_incomplete: bool = False) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    out: list[CalculationResult] = []
    cumulative_volume = Decimal(0)
    cumulative_value = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = _precision(tuple(c.close for c in xs) + tuple(c.volume for c in xs))
        for candle in xs:
            typical = (candle.high + candle.low + candle.close) / Decimal(3)
            cumulative_volume += candle.volume
            cumulative_value += typical * candle.volume
            if cumulative_volume == 0:
                out.append(_invalid("cumulative_volume_must_not_be_zero", candle))
            else:
                out.append(_valid(cumulative_value / cumulative_volume, candle))
    return tuple(out)


def anchored_vwap(
    candles: Iterable[CanonicalCandle],
    anchor_index: int,
    allow_incomplete: bool = False,
) -> tuple[CalculationResult, ...]:
    xs = _validate_candles(candles)
    _require_closed(xs, allow_incomplete)
    if isinstance(anchor_index, bool) or not isinstance(anchor_index, int):
        raise TypeError("anchor_index must be int")
    if anchor_index < 0 or anchor_index >= len(xs):
        raise ValueError("anchor_index must identify an observation in candles")
    out: list[CalculationResult] = [_insufficient(1, i + 1, c) for i, c in enumerate(xs)]
    cumulative_volume = Decimal(0)
    cumulative_value = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = _precision(tuple(c.close for c in xs[anchor_index:]) + tuple(c.volume for c in xs[anchor_index:]))
        for i in range(anchor_index, len(xs)):
            candle = xs[i]
            typical = (candle.high + candle.low + candle.close) / Decimal(3)
            cumulative_volume += candle.volume
            cumulative_value += typical * candle.volume
            if cumulative_volume == 0:
                out[i] = _invalid("anchored_cumulative_volume_must_not_be_zero", candle)
            else:
                out[i] = _valid(cumulative_value / cumulative_volume, candle)
    return tuple(out)


# Canonical aliases used by the Task Order vocabulary.
EMA = ema
SMA = sma
WMA = wma
HMA = hma
RSI = rsi
MACD = macd
ATR = atr
ADX = adx
BollingerBands = bollinger_bands
Supertrend = supertrend
HistoricalVolatility = historical_volatility
ATRPercentile = atr_percentile
VolumeSMA = volume_sma
RVOL = rvol
VWAP = vwap
AnchoredVWAP = anchored_vwap
