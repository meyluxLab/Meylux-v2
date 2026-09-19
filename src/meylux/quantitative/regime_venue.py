"""Deterministic market-regime and venue-aware quantitative evidence engine.

Pure Phase-4 computation. No network, filesystem, database, wall-clock,
provider-runtime, mutable-global or intelligence-layer dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Sequence

from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationResult, CalculationStatus, QuantitativeContext
from contracts.quantitative.regime import RegimeResult

SEMANTIC_VERSION = "1.0.0"

BULLISH = "BULLISH"
BEARISH = "BEARISH"
RANGE = "RANGE"
INSUFFICIENT = "INSUFFICIENT"

COMPARABLE = "COMPARABLE"
INCOMPATIBLE = "INCOMPATIBLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def _decimal(value: object, field: str, *, positive: bool = False, non_negative: bool = False) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field} must not be bool or float")
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{field} must be positive")
    if non_negative and value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _context(
    candles: Sequence[CanonicalCandle],
    explicit: QuantitativeContext | None,
    *,
    version: str,
) -> QuantitativeContext | None:
    if explicit is not None:
        if not isinstance(explicit, QuantitativeContext):
            raise TypeError("context must be QuantitativeContext or None")
        return explicit
    if not candles:
        return None
    provenance = "|".join(c.provenance_id for c in candles)
    return QuantitativeContext(
        source_ref=f"canonical-provenance:{provenance}",
        timestamp=max(c.close_time for c in candles),
        timeframe=candles[-1].timeframe,
        symbol=candles[0].instrument_id,
        version=version,
    )


@dataclass(frozen=True, slots=True)
class RegimeConfig:
    trend_lookback: int
    momentum_lookback: int
    trend_entry_threshold: Decimal
    trend_exit_threshold: Decimal
    momentum_entry_threshold: Decimal
    momentum_exit_threshold: Decimal
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in ("trend_lookback", "momentum_lookback"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be int")
            if value < 1:
                raise ValueError(f"{name} must be >= 1")
        for name in (
            "trend_entry_threshold", "trend_exit_threshold",
            "momentum_entry_threshold", "momentum_exit_threshold",
        ):
            _decimal(getattr(self, name), name, non_negative=True)
        if self.trend_exit_threshold > self.trend_entry_threshold:
            raise ValueError("trend_exit_threshold must be <= trend_entry_threshold")
        if self.momentum_exit_threshold > self.momentum_entry_threshold:
            raise ValueError("momentum_exit_threshold must be <= momentum_entry_threshold")
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("version must be non-empty")


@dataclass(frozen=True, slots=True)
class RegimeFactor:
    name: str
    value: Decimal | None
    direction: str
    status: CalculationStatus
    reason: str

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("factor name must be non-empty")
        if self.value is not None:
            _decimal(self.value, "factor value")
        if self.direction not in {BULLISH, BEARISH, RANGE, INSUFFICIENT}:
            raise ValueError("invalid factor direction")
        if not self.reason:
            raise ValueError("factor reason must be non-empty")


@dataclass(frozen=True, slots=True)
class RegimeAnalysis:
    result: RegimeResult
    factors: tuple[RegimeFactor, ...]
    previous_state: str | None
    transition: str
    configuration_version: str
    context: QuantitativeContext | None


class MarketRegimeEngine:
    calculation_version = SEMANTIC_VERSION

    def classify(
        self,
        candles: Iterable[CanonicalCandle],
        config: RegimeConfig,
        previous_state: str | None = None,
        context: QuantitativeContext | None = None,
    ) -> RegimeAnalysis:
        if not isinstance(config, RegimeConfig):
            raise TypeError("config must be RegimeConfig")
        if previous_state is not None and previous_state not in {BULLISH, BEARISH, RANGE, INSUFFICIENT}:
            raise ValueError("previous_state is invalid")
        xs = tuple(candles)
        self._validate(xs)
        ctx = _context(xs, context, version=config.version)
        required = max(config.trend_lookback, config.momentum_lookback)
        if len(xs) <= required:
            factors = self._insufficient_factors()
            return self._analysis(INSUFFICIENT, factors, previous_state, "INSUFFICIENT_HISTORY", config, ctx)

        trend = self._trend_factor(xs, config)
        momentum = self._momentum_factor(xs, config)
        factors = (trend, momentum)

        candidate = self._candidate_state(trend, momentum)
        state = self._apply_hysteresis(candidate, trend, momentum, previous_state, config)
        transition = "INITIAL" if previous_state is None else (
            "UNCHANGED" if state == previous_state else f"{previous_state}->{state}"
        )
        return self._analysis(state, factors, previous_state, transition, config, ctx)

    def _validate(self, xs: tuple[CanonicalCandle, ...]) -> None:
        for i, candle in enumerate(xs):
            if not isinstance(candle, CanonicalCandle):
                raise TypeError(f"candles[{i}] must be CanonicalCandle")
            if not candle.is_closed:
                raise ValueError("all candles must be closed")
            if i:
                prev = xs[i - 1]
                if candle.instrument_id != prev.instrument_id:
                    raise ValueError("instrument_id must remain constant")
                if candle.timeframe != prev.timeframe:
                    raise ValueError("timeframe must remain constant")
                if candle.open_time <= prev.open_time:
                    raise ValueError("candles must be strictly increasing by open_time")
                if candle.open_time < prev.close_time:
                    raise ValueError("candle intervals must not overlap")

    @staticmethod
    def _insufficient_factors() -> tuple[RegimeFactor, ...]:
        return (
            RegimeFactor("trend", None, INSUFFICIENT, CalculationStatus.INSUFFICIENT_HISTORY, "insufficient_history"),
            RegimeFactor("momentum", None, INSUFFICIENT, CalculationStatus.INSUFFICIENT_HISTORY, "insufficient_history"),
        )

    @staticmethod
    def _trend_factor(xs: tuple[CanonicalCandle, ...], config: RegimeConfig) -> RegimeFactor:
        current = xs[-1].close
        baseline = sum((c.close for c in xs[-1-config.trend_lookback:-1]), Decimal("0")) / Decimal(config.trend_lookback)
        if baseline <= 0:
            raise ValueError("trend baseline must be positive")
        value = (current - baseline) / baseline
        if value >= config.trend_entry_threshold:
            direction = BULLISH
        elif value <= -config.trend_entry_threshold:
            direction = BEARISH
        else:
            direction = RANGE
        return RegimeFactor("trend", value, direction, CalculationStatus.VALID, "close_vs_prior_close_mean")

    @staticmethod
    def _momentum_factor(xs: tuple[CanonicalCandle, ...], config: RegimeConfig) -> RegimeFactor:
        prior = xs[-1-config.momentum_lookback].close
        current = xs[-1].close
        if prior <= 0:
            raise ValueError("momentum reference must be positive")
        value = (current - prior) / prior
        if value >= config.momentum_entry_threshold:
            direction = BULLISH
        elif value <= -config.momentum_entry_threshold:
            direction = BEARISH
        else:
            direction = RANGE
        return RegimeFactor("momentum", value, direction, CalculationStatus.VALID, "close_return_over_lookback")

    @staticmethod
    def _candidate_state(trend: RegimeFactor, momentum: RegimeFactor) -> str:
        if trend.direction == BULLISH and momentum.direction == BULLISH:
            return BULLISH
        if trend.direction == BEARISH and momentum.direction == BEARISH:
            return BEARISH
        return RANGE

    @staticmethod
    def _apply_hysteresis(
        candidate: str,
        trend: RegimeFactor,
        momentum: RegimeFactor,
        previous: str | None,
        config: RegimeConfig,
    ) -> str:
        if previous is None or previous == RANGE or previous == INSUFFICIENT:
            return candidate
        if previous == BULLISH:
            trend_holds = trend.value is not None and trend.value > config.trend_exit_threshold
            momentum_holds = momentum.value is not None and momentum.value > config.momentum_exit_threshold
            if trend_holds and momentum_holds:
                return BULLISH
            if candidate == BEARISH:
                return BEARISH
            return RANGE
        if previous == BEARISH:
            trend_holds = trend.value is not None and trend.value < -config.trend_exit_threshold
            momentum_holds = momentum.value is not None and momentum.value < -config.momentum_exit_threshold
            if trend_holds and momentum_holds:
                return BEARISH
            if candidate == BULLISH:
                return BULLISH
            return RANGE
        return candidate

    @staticmethod
    def _analysis(
        state: str,
        factors: tuple[RegimeFactor, ...],
        previous: str | None,
        transition: str,
        config: RegimeConfig,
        context: QuantitativeContext | None,
    ) -> RegimeAnalysis:
        score = Decimal("1") if state == BULLISH else Decimal("-1") if state == BEARISH else Decimal("0")
        status = CalculationStatus.VALID if state != INSUFFICIENT else CalculationStatus.INSUFFICIENT_HISTORY
        result = RegimeResult(
            state,
            CalculationResult(score if status is CalculationStatus.VALID else None, status, transition.lower(), context),
            SEMANTIC_VERSION,
        )
        return RegimeAnalysis(result, factors, previous, transition, config.version, context)


@dataclass(frozen=True, slots=True)
class VenueEvidence:
    metric: str
    value: Decimal | None
    status: CalculationStatus
    context: QuantitativeContext | None
    semantics_version: str = SEMANTIC_VERSION

    def __post_init__(self) -> None:
        if not self.metric:
            raise ValueError("metric must be non-empty")
        if self.value is not None:
            _decimal(self.value, "value")
            if self.status is not CalculationStatus.VALID:
                raise ValueError("non-null venue evidence value requires VALID status")
        if self.value is None and self.status is CalculationStatus.VALID:
            raise ValueError("VALID venue evidence requires value")


@dataclass(frozen=True, slots=True)
class VenueComparison:
    classification: str
    result: CalculationResult
    left: VenueEvidence
    right: VenueEvidence
    reason: str

    def __post_init__(self) -> None:
        if self.classification not in {COMPARABLE, INCOMPATIBLE, INSUFFICIENT_EVIDENCE}:
            raise ValueError("invalid comparison classification")
        if not self.reason:
            raise ValueError("reason must be non-empty")


class VenueEvidenceEngine:
    calculation_version = SEMANTIC_VERSION

    def compare(self, left: VenueEvidence, right: VenueEvidence) -> VenueComparison:
        if not isinstance(left, VenueEvidence) or not isinstance(right, VenueEvidence):
            raise TypeError("left and right must be VenueEvidence")
        if left.status is not CalculationStatus.VALID or right.status is not CalculationStatus.VALID:
            return VenueComparison(
                INSUFFICIENT_EVIDENCE,
                CalculationResult(None, CalculationStatus.INSUFFICIENT_HISTORY, "input_evidence_not_valid", left.context),
                left, right, "input_evidence_not_valid",
            )
        lc, rc = left.context, right.context
        if lc is None or rc is None:
            return self._incompatible(left, right, "missing_context")
        if left.metric != right.metric:
            return self._incompatible(left, right, "metric_mismatch")
        if lc.symbol != rc.symbol:
            return self._incompatible(left, right, "instrument_mismatch")
        if lc.timeframe != rc.timeframe:
            return self._incompatible(left, right, "timeframe_mismatch")
        if lc.venue_context is None or rc.venue_context is None:
            return self._insufficient(left, right, "missing_venue_context")
        if lc.venue_context == rc.venue_context:
            return self._incompatible(left, right, "same_venue_not_cross_venue")
        if lc.timestamp is None or rc.timestamp is None:
            return self._insufficient(left, right, "missing_timestamp")
        if lc.timestamp != rc.timestamp:
            return self._incompatible(left, right, "timestamp_mismatch")
        difference = right.value - left.value
        ctx = QuantitativeContext(
            source_ref=f"venue-compare:{lc.source_ref or 'left'}|{rc.source_ref or 'right'}",
            timestamp=lc.timestamp,
            timeframe=lc.timeframe,
            symbol=lc.symbol,
            venue_context=f"{lc.venue_context}|{rc.venue_context}",
            version=SEMANTIC_VERSION,
        )
        return VenueComparison(
            COMPARABLE,
            CalculationResult(difference, CalculationStatus.VALID, "right_minus_left", ctx),
            left, right, "compatible_cross_venue_evidence",
        )

    @staticmethod
    def _incompatible(left: VenueEvidence, right: VenueEvidence, reason: str) -> VenueComparison:
        return VenueComparison(
            INCOMPATIBLE,
            CalculationResult(None, CalculationStatus.INVALID_INPUT, reason, left.context),
            left, right, reason,
        )

    @staticmethod
    def _insufficient(left: VenueEvidence, right: VenueEvidence, reason: str) -> VenueComparison:
        return VenueComparison(
            INSUFFICIENT_EVIDENCE,
            CalculationResult(None, CalculationStatus.INSUFFICIENT_HISTORY, reason, left.context),
            left, right, reason,
        )
