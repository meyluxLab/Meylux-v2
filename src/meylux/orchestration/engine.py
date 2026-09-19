"""Deterministic composition boundary for verified Phase-4 engines."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping
from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationResult
from contracts.quantitative.regime import RegimeResult
from meylux.quantitative.indicators import ema_candles, rsi, atr
from meylux.quantitative.market_structure import MarketStructureEngine
from meylux.quantitative.regime_venue import MarketRegimeEngine, RegimeConfig

def _utc(v:datetime,n:str)->datetime:
    if not isinstance(v,datetime): raise TypeError(f"{n} must be datetime")
    if v.tzinfo is None or v.utcoffset() is None or v.utcoffset()!=timezone.utc.utcoffset(v): raise ValueError(f"{n} must use UTC")
    return v

@dataclass(frozen=True,slots=True)
class MTFAlignment:
    primary_close:datetime
    timeframe:str
    candle:CanonicalCandle|None
    available_at:datetime|None
    def __post_init__(self):
        _utc(self.primary_close,"primary_close")
        if self.candle is not None:
            if not self.candle.is_closed: raise ValueError("aligned candle must be closed")
            if self.candle.close_time>self.primary_close: raise ValueError("aligned candle closes after primary knowledge boundary")
            if self.available_at!=self.candle.close_time: raise ValueError("available_at must equal aligned candle close_time")

def align_higher_timeframe(primary:CanonicalCandle,higher:Iterable[CanonicalCandle])->MTFAlignment:
    if not isinstance(primary,CanonicalCandle): raise TypeError("primary must be CanonicalCandle")
    if not primary.is_closed: raise ValueError("primary candle must be closed")
    last=None; previous=None
    for i,c in enumerate(tuple(higher)):
        if not isinstance(c,CanonicalCandle): raise TypeError(f"higher[{i}] must be CanonicalCandle")
        if not c.is_closed: raise ValueError(f"higher[{i}] is incomplete")
        if c.instrument_id!=primary.instrument_id: raise ValueError("higher timeframe instrument must match primary")
        if previous is not None and c.open_time<=previous: raise ValueError("higher timeframe candles must be strictly ordered")
        previous=c.open_time
        if c.close_time<=primary.close_time: last=c
        else: break
    return MTFAlignment(primary.close_time,primary.timeframe,last,None if last is None else last.close_time)

@dataclass(frozen=True,slots=True)
class QuantOrchestrationConfig:
    regime:RegimeConfig
    ema_period:int=20
    rsi_period:int=14
    atr_period:int=14
    version:str="1.0.0"
    def __post_init__(self):
        if not isinstance(self.regime,RegimeConfig): raise TypeError("regime must be RegimeConfig")
        for n in ("ema_period","rsi_period","atr_period"):
            v=getattr(self,n)
            if isinstance(v,bool) or not isinstance(v,int) or v<1: raise ValueError(f"{n} must be positive")
        if not isinstance(self.version,str) or not self.version: raise ValueError("version must be non-empty")

@dataclass(frozen=True,slots=True)
class QuantOrchestrationResult:
    symbol:str
    timeframe:str
    as_of:datetime
    configuration_version:str
    regime:RegimeResult
    regime_transition:str
    indicators:Mapping[str,CalculationResult]
    structure_event_count:int
    structure_state:str
    htf:Mapping[str,MTFAlignment]
    source_provenance:tuple[str,...]

class QuantitativeOrchestrator:
    def __init__(self):
        self._regime=MarketRegimeEngine()
        self._structure=MarketStructureEngine()
    def process(self,candles:Iterable[CanonicalCandle],config:QuantOrchestrationConfig,*,previous_regime:str|None=None,higher_timeframes:Mapping[str,Iterable[CanonicalCandle]]|None=None)->QuantOrchestrationResult:
        if not isinstance(config,QuantOrchestrationConfig): raise TypeError("config must be QuantOrchestrationConfig")
        xs=tuple(candles)
        if not xs: raise ValueError("candles must contain at least one closed candle")
        for i,c in enumerate(xs):
            if not isinstance(c,CanonicalCandle): raise TypeError(f"candles[{i}] must be CanonicalCandle")
            if not c.is_closed: raise ValueError(f"candles[{i}] is incomplete")
            if i and c.instrument_id!=xs[i-1].instrument_id: raise ValueError("instrument_id must remain constant")
            if i and c.timeframe!=xs[i-1].timeframe: raise ValueError("timeframe must remain constant")
            if i and c.open_time<=xs[i-1].open_time: raise ValueError("candles must be strictly increasing by open_time")
            if i and c.open_time<xs[i-1].close_time: raise ValueError("candle intervals must not overlap")
        regime=self._regime.classify(xs,config.regime,previous_state=previous_regime)
        structure=self._structure.analyze(xs)
        indicators={"EMA":ema_candles(xs,config.ema_period)[-1],"RSI":rsi(xs,config.rsi_period)[-1],"ATR":atr(xs,config.atr_period)[-1]}
        htf={}
        for tf,series in (higher_timeframes or {}).items():
            if not isinstance(tf,str) or not tf: raise ValueError("higher timeframe key must be non-empty")
            normalized=tuple(series)
            for i,c in enumerate(normalized):
                if not isinstance(c,CanonicalCandle): raise TypeError(f"higher_timeframes[{tf}][{i}] must be CanonicalCandle")
                if c.timeframe!=tf: raise ValueError(f"higher_timeframes[{tf}] contains candle with timeframe {c.timeframe!r}")
            htf[tf]=align_higher_timeframe(xs[-1],normalized)
        return QuantOrchestrationResult(xs[-1].instrument_id,xs[-1].timeframe,xs[-1].close_time,config.version,regime.result,regime.transition,indicators,len(structure.events),structure.states[-1].state if structure.states else "NEUTRAL",htf,tuple(c.provenance_id for c in xs))
