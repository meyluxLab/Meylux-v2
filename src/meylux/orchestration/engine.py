"""Deterministic composition boundary for verified Phase-4 engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
from meylux.quantitative.market_structure import MarketStructureEngine
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
        if not isinstance(self.indicators, Mapping):
            raise TypeError("indicators must be a mapping")
        if not isinstance(self.source_provenance, tuple) or not self.source_provenance:
            raise ValueError("source_provenance must be a non-empty tuple")


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
    return MTFAlignment(primary.close_time, timeframe, last, None if last is None else last.close_time)


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
        if self.macd_fast_period >= self.macd_slow_period:
            raise ValueError("macd_fast_period must be less than macd_slow_period")
        if self.historical_volatility_window < 2:
            raise ValueError("historical_volatility_window must be at least 2")
        if not isinstance(self.bollinger_deviations, str) or not self.bollinger_deviations:
            raise ValueError("bollinger_deviations must be a non-empty decimal string")
        if not isinstance(self.historical_volatility_periods_per_year, str) or not self.historical_volatility_periods_per_year:
            raise ValueError("historical_volatility_periods_per_year must be a non-empty decimal string")
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
    facts = {
        "EMA": ema_candles(candles, config.ema_period)[-1],
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
        indicators = _indicator_facts(xs, config)
        htf: dict[str, MTFAlignment] = {}
        htf_facts: dict[str, TimeframeQuantitativeFacts] = {}
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
        )
