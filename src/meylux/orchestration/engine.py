"""Deterministic composition boundary for verified Phase-4 engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping

from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationResult, QuantitativeContext
from contracts.quantitative.regime import RegimeResult
from meylux.quantitative.indicators import (
    adx,
    atr,
    atr_percentile,
    bollinger_bandwidth,
    bollinger_bands,
    ema_candles,
    historical_volatility,
    macd,
    rsi,
    volatility_expansion_ratio,
)
from meylux.quantitative.market_structure import MarketStructureEngine, StructuralEvent, _INTERVALS
from meylux.quantitative.regime_venue import MarketRegimeEngine, RegimeConfig


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{name} must use UTC")
    return value


@dataclass(frozen=True, slots=True)
class MTFAlignment:
    primary_close: datetime
    timeframe: str
    candle: CanonicalCandle | None
    available_at: datetime | None

    def __post_init__(self) -> None:
        _utc(self.primary_close, "primary_close")
        if not isinstance(self.timeframe, str) or not self.timeframe:
            raise ValueError("timeframe must be non-empty")
        if self.candle is not None:
            if not self.candle.is_closed:
                raise ValueError("aligned candle must be closed")
            if self.candle.close_time > self.primary_close:
                raise ValueError("aligned candle closes after primary knowledge boundary")
            if self.available_at != self.candle.close_time:
                raise ValueError("available_at must equal aligned candle close_time")


@dataclass(frozen=True, slots=True)
class TimeframeQuantitativeFacts:
    """Latest eligible deterministic fact set for one independently persisted timeframe."""
    symbol: str
    timeframe: str
    event_time: datetime
    knowledge_time: datetime
    configuration_version: str
    indicators: Mapping[str, CalculationResult]
    source_provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be non-empty")
        if not isinstance(self.timeframe, str) or not self.timeframe:
            raise ValueError("timeframe must be non-empty")
        _utc(self.event_time, "event_time")
        _utc(self.knowledge_time, "knowledge_time")
        if self.knowledge_time != self.event_time:
            raise ValueError("timeframe fact knowledge_time must equal its authoritative closed-candle event_time")
        if not isinstance(self.configuration_version, str) or not self.configuration_version:
            raise ValueError("configuration_version must be non-empty")
        if not isinstance(self.indicators, Mapping) or not self.indicators:
            raise TypeError("indicators must be a non-empty mapping")
        if any(not isinstance(name, str) or not name or not isinstance(value, CalculationResult)
               for name, value in self.indicators.items()):
            raise TypeError("indicators must map non-empty names to CalculationResult values")
        if not isinstance(self.source_provenance, tuple) or not self.source_provenance:
            raise ValueError("source_provenance must be a non-empty tuple")
        if any(not isinstance(value, str) or not value for value in self.source_provenance):
            raise ValueError("source_provenance entries must be non-empty strings")


def align_higher_timeframe(primary: CanonicalCandle, higher: Iterable[CanonicalCandle]) -> MTFAlignment:
    """Validate the complete supplied HTF sequence and select its latest eligible close."""
    if not isinstance(primary, CanonicalCandle):
        raise TypeError("primary must be CanonicalCandle")
    if not primary.is_closed:
        raise ValueError("primary candle must be closed")
    xs = tuple(higher)
    last = None
    previous = None
    expected_timeframe = None
    for index, candle in enumerate(xs):
        if not isinstance(candle, CanonicalCandle):
            raise TypeError(f"higher[{index}] must be CanonicalCandle")
        if not candle.is_closed:
            raise ValueError(f"higher[{index}] is incomplete")
        if candle.instrument_id != primary.instrument_id:
            raise ValueError("higher timeframe instrument must match primary")
        if candle.timeframe == primary.timeframe:
            raise ValueError("higher timeframe must differ from primary timeframe")
        if expected_timeframe is None:
            expected_timeframe = candle.timeframe
        elif candle.timeframe != expected_timeframe:
            raise ValueError("higher timeframe candles must use one consistent timeframe")
        if previous is not None:
            if candle.open_time <= previous.open_time:
                raise ValueError("higher timeframe candles must be strictly ordered")
            if candle.open_time < previous.close_time:
                raise ValueError("higher timeframe candle intervals must not overlap")
        if candle.close_time > primary.close_time:
            raise ValueError("higher timeframe candle closes after primary knowledge boundary")
        previous = candle
        last = candle
    timeframe = expected_timeframe or primary.timeframe
    return MTFAlignment(primary.close_time, primary.timeframe, last, None if last is None else last.close_time)


@dataclass(frozen=True, slots=True)
class QuantOrchestrationConfig:
    regime: RegimeConfig
    ema_period: int = 20
    rsi_period: int = 14
    atr_period: int = 14
    version: str = "1.0.0"
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    adx_period: int = 14
    bollinger_window: int = 20
    bollinger_deviations: str = "2"
    historical_volatility_window: int = 20
    historical_volatility_periods_per_year: str = "365"
    atr_percentile_lookback: int = 100
    volatility_expansion_baseline_window: int = 20
    # Additional configured periods use the existing deterministic EMA engine.
    # The legacy "EMA" fact below remains for existing P4 consumers.
    ema_periods: tuple[int, ...] = (9, 20, 21, 50, 200)

    def __post_init__(self) -> None:
        if not isinstance(self.regime, RegimeConfig):
            raise TypeError("regime must be RegimeConfig")
        for name in (
            "ema_period", "rsi_period", "atr_period", "macd_fast_period",
            "macd_slow_period", "macd_signal_period", "adx_period",
            "bollinger_window", "historical_volatility_window",
            "atr_percentile_lookback", "volatility_expansion_baseline_window",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be positive")
        if not isinstance(self.ema_periods, tuple) or not self.ema_periods:
            raise ValueError("ema_periods must be a non-empty tuple of positive integers")
        if any(isinstance(period, bool) or not isinstance(period, int) or period < 1 for period in self.ema_periods):
            raise ValueError("ema_periods must contain only positive integers")
        if len(set(self.ema_periods)) != len(self.ema_periods):
            raise ValueError("ema_periods must not contain duplicates")
        if self.macd_fast_period >= self.macd_slow_period:
            raise ValueError("macd_fast_period must be less than macd_slow_period")
        if self.historical_volatility_window < 2:
            raise ValueError("historical_volatility_window must be at least 2")
        if not isinstance(self.bollinger_deviations, str) or not self.bollinger_deviations:
            raise ValueError("bollinger_deviations must be a non-empty decimal string")
        if not isinstance(self.historical_volatility_periods_per_year, str) or not self.historical_volatility_periods_per_year:
            raise ValueError("historical_volatility_periods_per_year must be a non-empty decimal string")
        try:
            deviations = Decimal(self.bollinger_deviations)
            annual_periods = Decimal(self.historical_volatility_periods_per_year)
        except InvalidOperation as exc:
            raise ValueError("decimal configuration values must be valid decimals") from exc
        if not deviations.is_finite() or deviations < 0:
            raise ValueError("bollinger_deviations must be finite and non-negative")
        if not annual_periods.is_finite() or annual_periods <= 0:
            raise ValueError("historical_volatility_periods_per_year must be finite and positive")
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("version must be non-empty")


@dataclass(frozen=True, slots=True)
class QuantOrchestrationResult:
    symbol: str
    timeframe: str
    as_of: datetime
    knowledge_time: datetime
    configuration_version: str
    regime: RegimeResult
    regime_transition: str
    indicators: Mapping[str, CalculationResult]
    structure_event_count: int
    structure_state: str
    htf: Mapping[str, MTFAlignment]
    source_provenance: tuple[str, ...]
    higher_timeframe_facts: Mapping[str, TimeframeQuantitativeFacts] = field(default_factory=dict)
    structure_events: tuple[StructuralEvent, ...] = ()
    structure_event_provenance: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    higher_timeframe_structure_events: Mapping[str, tuple[StructuralEvent, ...]] = field(default_factory=dict)
    higher_timeframe_structure_event_provenance: Mapping[str, Mapping[str, tuple[str, ...]]] = field(default_factory=dict)
    structure_event_history: Mapping[str, tuple[int, str, str]] = field(default_factory=dict)
    higher_timeframe_structure_event_history: Mapping[str, Mapping[str, tuple[int, str, str]]] = field(default_factory=dict)


def _contextualize(result: CalculationResult, candle: CanonicalCandle) -> CalculationResult:
    """Fill provenance context only when an existing pure calculation omits it."""
    if result.context is not None:
        return result
    return CalculationResult(
        result.value,
        result.status,
        result.reason,
        QuantitativeContext(
            source_ref=candle.provenance_id,
            timestamp=candle.close_time,
            timeframe=candle.timeframe,
            symbol=candle.instrument_id,
            version="1.0.0",
        ),
    )


def _indicator_facts(candles: tuple[CanonicalCandle, ...], config: QuantOrchestrationConfig) -> dict[str, CalculationResult]:
    if not candles:
        raise ValueError("indicator facts require at least one candle")
    last = candles[-1]
    macd_point = macd(candles, config.macd_fast_period, config.macd_slow_period, config.macd_signal_period)[-1]
    bands = bollinger_bands(candles, config.bollinger_window, config.bollinger_deviations)[-1]
    # Calculate each distinct configured period once through the established
    # EMA implementation. "EMA" remains the backward-compatible legacy fact.
    ema_periods = tuple(dict.fromkeys((config.ema_period, *config.ema_periods)))
    ema_results = {period: ema_candles(candles, period)[-1] for period in ema_periods}
    facts = {
        "EMA": ema_results[config.ema_period],
        **{f"EMA_{period}": ema_results[period] for period in config.ema_periods},
        "RSI": rsi(candles, config.rsi_period)[-1],
        "MACD": macd_point.macd,
        "MACD_SIGNAL": macd_point.signal,
        "MACD_HISTOGRAM": macd_point.histogram,
        "ATR": atr(candles, config.atr_period)[-1],
        "ADX": adx(candles, config.adx_period)[-1],
        "BOLLINGER_MIDDLE": bands.middle,
        "BOLLINGER_UPPER": bands.upper,
        "BOLLINGER_LOWER": bands.lower,
        "BOLLINGER_BANDWIDTH": _contextualize(
            bollinger_bandwidth(candles, config.bollinger_window, config.bollinger_deviations)[-1], last
        ),
        "HISTORICAL_VOLATILITY": historical_volatility(
            candles, config.historical_volatility_window, config.historical_volatility_periods_per_year
        )[-1],
        "ATR_PERCENTILE": atr_percentile(
            candles, config.atr_period, config.atr_percentile_lookback
        )[-1],
        "VOLATILITY_EXPANSION_RATIO": volatility_expansion_ratio(
            candles, config.atr_period, config.volatility_expansion_baseline_window
        )[-1],
    }
    return facts


def _structure_event_provenance(
    candles: tuple[CanonicalCandle, ...],
    events: tuple[StructuralEvent, ...],
) -> dict[str, tuple[str, ...]]:
    """Map facts to canonical candles that establish them, including source chains."""
    by_open = {candle.open_time: index for index, candle in enumerate(candles)}
    by_close = {candle.close_time: index for index, candle in enumerate(candles)}
    by_provenance = {candle.provenance_id: index for index, candle in enumerate(candles)}
    if len(by_provenance) != len(candles):
        raise ValueError("canonical candle provenance identifiers must be unique within a timeframe")
    event_by_id = {event.identity: event for event in events}
    swing_types = {"SWING_HIGH", "SWING_LOW", "HH", "HL", "LH", "LL"}
    out: dict[str, tuple[str, ...]] = {}
    for event in events:
        if not event.identity or event.event_location not in by_open or event.confirmation_time not in by_close:
            raise ValueError("structural event must map to canonical event-location and confirmation candles")
        location_index = by_open[event.event_location]
        confirmation_index = by_close[event.confirmation_time]
        if location_index > confirmation_index:
            raise ValueError("structural event location cannot follow its confirmation candle")
        indices = {location_index, confirmation_index}
        if event.event_type in swing_types:
            # DOC-P4-002 confirms a 5/5 pivot only after its full eleven-candle window.
            if confirmation_index != location_index + 5 or location_index < 5:
                raise ValueError("confirmed swing lineage must contain its complete 5/5 window")
            indices.update(range(location_index - 5, confirmation_index + 1))
        elif event.event_type == "FVG":
            if location_index < 2:
                raise ValueError("FVG lineage must contain its complete three-candle window")
            indices.update(range(location_index - 2, location_index + 1))

        source_ids = tuple(token for token in (event.source_event_identity or "").split(",") if token)
        for source_id in source_ids:
            if source_id not in event_by_id or source_id not in out:
                raise ValueError("structural source/member identity must resolve to an earlier event")
            for ref in out[source_id]:
                if ref not in by_provenance:
                    raise ValueError("source event provenance must resolve to canonical candle input")
                indices.add(by_provenance[ref])

        # DOC-P4-002 classifies a new swing relative to the immediately previous
        # confirmed swing of the same side. Preserve that support lineage without
        # changing the ratified engine's deterministic event identity.
        if event.event_type in {"HH", "LH", "HL", "LL"}:
            required_type = "SWING_HIGH" if event.event_type in {"HH", "LH"} else "SWING_LOW"
            prior = [
                candidate for candidate in events
                if candidate.event_type == required_type
                and candidate.event_location < event.event_location
                and candidate.knowledge_time < event.knowledge_time
                and candidate.identity in out
            ]
            if prior:
                source = max(prior, key=lambda candidate: (candidate.knowledge_time, candidate.event_location))
                indices.update(by_provenance[ref] for ref in out[source.identity])

        # Break facts are level-based in the existing P4 engine. Link the latest
        # previously knowable exact-level swing for provenance, without rewriting
        # the engine event identity or adding alternative break mathematics.
        if event.event_type in {"BOS", "CHOCH", "MSS"} and event.level is not None:
            required_type = "SWING_HIGH" if event.direction == "bullish" else "SWING_LOW"
            prior = [
                candidate for candidate in events
                if candidate.event_type == required_type
                and candidate.level == event.level
                and candidate.event_location < event.event_location
                and candidate.knowledge_time < event.knowledge_time
                and candidate.identity in out
            ]
            if not prior:
                raise ValueError("structural break must resolve its exact-level supporting swing identity")
            source = max(prior, key=lambda candidate: (candidate.knowledge_time, candidate.event_location))
            indices.update(by_provenance[ref] for ref in out[source.identity])

        refs = tuple(dict.fromkeys(candles[index].provenance_id for index in sorted(indices)))
        if not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError("structural event requires explicit canonical candle provenance")
        if event.identity in out:
            raise ValueError("structural event identities must be unique within a timeframe")
        out[event.identity] = refs
    return out


def _structure_event_history(
    candles: tuple[CanonicalCandle, ...],
    events: tuple[StructuralEvent, ...],
) -> dict[str, tuple[int, str, str]]:
    """Describe 5/5 swing-history availability using only candles knowable at each fact."""
    by_close = {candle.close_time: index for index, candle in enumerate(candles)}
    out: dict[str, tuple[int, str, str]] = {}
    for event in events:
        end = by_close.get(event.knowledge_time)
        if end is None:
            raise ValueError("structural event knowledge_time must map to a closed canonical candle")
        start = end
        while start > 0:
            interval = _INTERVALS.get(candles[start - 1].timeframe)
            if interval is None or candles[start - 1].open_time + interval != candles[start].open_time:
                break
            start -= 1
        contiguous_count = end - start + 1
        if contiguous_count < 11:
            status = "INSUFFICIENT_HISTORY"
            reason = "requires_11_contiguous_closed_candles_for_5_5_swing_confirmation"
        else:
            status = "AVAILABLE"
            reason = "minimum_5_5_swing_history_available"
        if event.identity in out:
            raise ValueError("structural event history identities must be unique within a timeframe")
        out[event.identity] = (contiguous_count, status, reason)
    return out


class QuantitativeOrchestrator:
    def __init__(self) -> None:
        self._regime = MarketRegimeEngine()
        self._structure = MarketStructureEngine()

    def process(
        self,
        candles: Iterable[CanonicalCandle],
        config: QuantOrchestrationConfig,
        *,
        previous_regime: str | None = None,
        higher_timeframes: Mapping[str, Iterable[CanonicalCandle]] | None = None,
    ) -> QuantOrchestrationResult:
        if not isinstance(config, QuantOrchestrationConfig):
            raise TypeError("config must be QuantOrchestrationConfig")
        xs = tuple(candles)
        if not xs:
            raise ValueError("candles must contain at least one closed candle")
        for index, candle in enumerate(xs):
            if not isinstance(candle, CanonicalCandle):
                raise TypeError(f"candles[{index}] must be CanonicalCandle")
            if not candle.is_closed:
                raise ValueError(f"candles[{index}] is incomplete")
            if index and candle.instrument_id != xs[index - 1].instrument_id:
                raise ValueError("instrument_id must remain constant")
            if index and candle.timeframe != xs[index - 1].timeframe:
                raise ValueError("timeframe must remain constant")
            if index and candle.open_time <= xs[index - 1].open_time:
                raise ValueError("candles must be strictly increasing by open_time")
            if index and candle.open_time < xs[index - 1].close_time:
                raise ValueError("candle intervals must not overlap")

        regime = self._regime.classify(xs, config.regime, previous_state=previous_regime)
        structure = self._structure.analyze(xs)
        structure_events = structure.events
        structure_event_provenance = _structure_event_provenance(xs, structure_events)
        structure_event_history = _structure_event_history(xs, structure_events)
        indicators = _indicator_facts(xs, config)
        htf: dict[str, MTFAlignment] = {}
        htf_facts: dict[str, TimeframeQuantitativeFacts] = {}
        htf_structure_events: dict[str, tuple[StructuralEvent, ...]] = {}
        htf_structure_provenance: dict[str, Mapping[str, tuple[str, ...]]] = {}
        htf_structure_history: dict[str, Mapping[str, tuple[int, str, str]]] = {}
        for timeframe, series in (higher_timeframes or {}).items():
            if not isinstance(timeframe, str) or not timeframe:
                raise ValueError("higher timeframe key must be non-empty")
            if timeframe == xs[-1].timeframe:
                raise ValueError("higher timeframe key must differ from primary timeframe")
            normalized = tuple(series)
            for index, candle in enumerate(normalized):
                if not isinstance(candle, CanonicalCandle):
                    raise TypeError(f"higher_timeframes[{timeframe}][{index}] must be CanonicalCandle")
                if candle.timeframe != timeframe:
                    raise ValueError(
                        f"higher_timeframes[{timeframe}] contains candle with timeframe {candle.timeframe!r}"
                    )
            alignment = align_higher_timeframe(xs[-1], normalized)
            htf[timeframe] = alignment
            if normalized:
                # align_higher_timeframe rejects post-boundary, malformed, overlapping,
                # mixed-instrument and incomplete candles before calculation.
                selected = tuple(c for c in normalized if c.close_time <= xs[-1].close_time)
                if selected:
                    latest = selected[-1]
                    htf_facts[timeframe] = TimeframeQuantitativeFacts(
                        symbol=latest.instrument_id,
                        timeframe=timeframe,
                        event_time=latest.close_time,
                        knowledge_time=latest.close_time,
                        configuration_version=config.version,
                        indicators=_indicator_facts(selected, config),
                        source_provenance=tuple(c.provenance_id for c in selected),
                    )
                    htf_structure = self._structure.analyze(selected)
                    htf_structure_events[timeframe] = htf_structure.events
                    htf_structure_provenance[timeframe] = _structure_event_provenance(
                        selected, htf_structure.events
                    )
                    htf_structure_history[timeframe] = _structure_event_history(
                        selected, htf_structure.events
                    )

        knowledge_time = xs[-1].close_time
        return QuantOrchestrationResult(
            xs[-1].instrument_id,
            xs[-1].timeframe,
            xs[-1].close_time,
            knowledge_time,
            config.version,
            regime.result,
            regime.transition,
            indicators,
            len(structure.events),
            structure.states[-1].state if structure.states else "NEUTRAL",
            htf,
            tuple(c.provenance_id for c in xs),
            htf_facts,
            structure_events,
            structure_event_provenance,
            htf_structure_events,
            htf_structure_provenance,
            structure_event_history,
            htf_structure_history,
        )
