from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Iterable

from contracts.canonical import CanonicalCandle
from contracts.quantitative.base import CalculationResult, CalculationStatus
from contracts.quantitative.structure import MarketStructureResult

SEMANTIC_VERSION = "1.0.0"
_STATE_NEUTRAL = "NEUTRAL"
_STATE_UP = "TRENDING_UP"
_STATE_DOWN = "TRENDING_DOWN"
_STATE_RANGE = "RANGE"
_STATE_UNCONFIRMED = "UNCONFIRMED"
_INTERVALS = {"1m": timedelta(minutes=1), "5m": timedelta(minutes=5), "15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}

@dataclass(frozen=True, slots=True)
class StructuralEvent:
    event_type: str
    event_location: datetime
    confirmation_time: datetime
    knowledge_time: datetime
    identity: str
    direction: str | None = None
    level: Decimal | None = None
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    lifecycle: str | None = None
    structural_state: str | None = None
    source_event_identity: str | None = None
    prior_structural_state: str | None = None
    reason: str = ""
    def result(self) -> MarketStructureResult:
        numeric = self.level
        status = CalculationStatus.VALID if numeric is not None else CalculationStatus.UNAVAILABLE
        return MarketStructureResult(self.event_type, CalculationResult(numeric, status, self.reason or self.event_type), SEMANTIC_VERSION,
            event_location=self.event_location, confirmation_time=self.confirmation_time, knowledge_time=self.knowledge_time,
            level=self.level, lower_bound=self.lower_bound, upper_bound=self.upper_bound, direction=self.direction,
            lifecycle=self.lifecycle, structural_state=self.structural_state, identity=self.identity,
            source_event_identity=self.source_event_identity)

@dataclass(frozen=True, slots=True)
class BarState:
    index: int
    event_location: datetime
    knowledge_time: datetime
    state: str
    events: tuple[StructuralEvent, ...]
    processing_order: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class MarketStructureAnalysis:
    bars: tuple[CanonicalCandle, ...]
    events: tuple[StructuralEvent, ...]
    states: tuple[BarState, ...]
    calculation_version: str = SEMANTIC_VERSION
    @property
    def results(self) -> tuple[MarketStructureResult, ...]:
        return tuple(e.result() for e in self.events)

class MarketStructureEngine:
    calculation_version = SEMANTIC_VERSION

    def analyze(self, candles: Iterable[CanonicalCandle]) -> MarketStructureAnalysis:
        xs = self._validate(candles)
        events=[]; states=[]; highs=[]; lows=[]; high_class={}; low_class={}
        boundary=0; state=_STATE_NEUTRAL; pending=None; quarantine=False
        active_fvgs=[]; fvg_lifecycle={}; active_obs=[]; active_breakers=[]; pools_high={}; pools_low={}; active_pools=[]
        seen=set(); broken_levels=set(); active_break_facts={}
        for i,candle in enumerate(xs):
            bar_events=[]; phase_trace=[]; pre_highs=list(highs); pre_lows=list(lows); pre_state=state
            phase_trace.append("continuity")
            if i and self._expected_open(xs[i-1]) != candle.open_time:
                boundary=i; state=_STATE_UNCONFIRMED; pending=None; quarantine=True
                highs=[x for x in highs if x[0]>=boundary]; lows=[x for x in lows if x[0]>=boundary]
                high_class.clear(); low_class.clear(); active_fvgs=[]; active_obs=[]; active_breakers=[]
                pools_high={}; pools_low={}; active_pools=[]; broken_levels=set()
            phase_trace.append("swing")
            cand=i-5
            if cand>=boundary and cand>=5 and self._window_continuous(xs,cand,i):
                candidate=xs[cand]; window=xs[cand-5:cand+6]
                if all(x.is_closed for x in window):
                    if all(candidate.high>x.high for j,x in enumerate(window) if j!=5):
                        ev=self._event("SWING_HIGH",candidate,candle.close_time,level=candidate.high,reason="strict_5_5_swing_high",index=cand)
                        if ev.identity not in seen:
                            seen.add(ev.identity); bar_events.append(ev); highs.append((cand,candidate.high,ev))
                            if len(highs)>=2:
                                previous=highs[-2][1]
                                high_class[cand]="HH" if candidate.high>previous else "LH" if candidate.high<previous else None
                                if high_class[cand]:
                                    ce=self._event(high_class[cand],candidate,candle.close_time,level=candidate.high,reason="swing_high_classification",index=cand)
                                    if ce.identity not in seen: seen.add(ce.identity); bar_events.append(ce)
                            else: high_class[cand]=None
                    if all(candidate.low<x.low for j,x in enumerate(window) if j!=5):
                        ev=self._event("SWING_LOW",candidate,candle.close_time,level=candidate.low,reason="strict_5_5_swing_low",index=cand)
                        if ev.identity not in seen:
                            seen.add(ev.identity); bar_events.append(ev); lows.append((cand,candidate.low,ev))
                            if len(lows)>=2:
                                previous=lows[-2][1]
                                low_class[cand]="HL" if candidate.low>previous else "LL" if candidate.low<previous else None
                                if low_class[cand]:
                                    ce=self._event(low_class[cand],candidate,candle.close_time,level=candidate.low,reason="swing_low_classification",index=cand)
                                    if ce.identity not in seen: seen.add(ce.identity); bar_events.append(ce)
                            else: low_class[cand]=None
            phase_trace.append("classification")
            if boundary==i or pending is not None or quarantine:
                derived=self._derive_state(highs,lows,high_class,low_class)
                if quarantine and derived in (_STATE_UP,_STATE_DOWN,_STATE_RANGE):
                    state=derived; quarantine=False
                else: state=_STATE_UNCONFIRMED
            else:
                state=self._derive_state(highs,lows,high_class,low_class)
            phase_trace.append("state")
            if i>=boundary:
                break_state=pre_state; choch_emitted=False
                if break_state==_STATE_UP and pre_lows and candle.close<pre_lows[-1][1]:
                    protected=pre_lows[-1]
                    ev=self._event("CHOCH",candle,candle.close_time,level=protected[1],direction="bearish",prior_state=_STATE_UP,reason="close_below_protected_swing_low",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev)
                    pending={"direction":"bearish","event":ev,"boundary":boundary,"index":i,"new_low":False,"new_high":False}; state=_STATE_UNCONFIRMED; choch_emitted=True
                elif break_state==_STATE_DOWN and pre_highs and candle.close>pre_highs[-1][1]:
                    protected=pre_highs[-1]
                    ev=self._event("CHOCH",candle,candle.close_time,level=protected[1],direction="bullish",prior_state=_STATE_DOWN,reason="close_above_protected_swing_high",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev)
                    pending={"direction":"bullish","event":ev,"boundary":boundary,"index":i,"new_low":False,"new_high":False}; state=_STATE_UNCONFIRMED; choch_emitted=True
                if pending is None and not choch_emitted:
                    if break_state==_STATE_UP and pre_highs:
                        level=pre_highs[-1][1]
                        if candle.close>level and ("bullish",level,boundary) not in broken_levels:
                            ev=self._event("BOS",candle,candle.close_time,level=level,direction="bullish",prior_state=break_state,reason="close_above_confirmed_swing_high",index=i)
                            if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); broken_levels.add(("bullish",level,boundary)); active_break_facts[ev.identity]=ev
                    elif break_state==_STATE_DOWN and pre_lows:
                        level=pre_lows[-1][1]
                        if candle.close<level and ("bearish",level,boundary) not in broken_levels:
                            ev=self._event("BOS",candle,candle.close_time,level=level,direction="bearish",prior_state=break_state,reason="close_below_confirmed_swing_low",index=i)
                            if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); broken_levels.add(("bearish",level,boundary)); active_break_facts[ev.identity]=ev
                if pending is not None and not choch_emitted:
                    for pe in bar_events:
                        if pe.event_type=="LL" and pending["direction"]=="bearish": pending["new_low"]=True
                        if pe.event_type=="LH" and pending["direction"]=="bearish": pending["new_high"]=True
                        if pe.event_type=="HH" and pending["direction"]=="bullish": pending["new_high"]=True
                        if pe.event_type=="HL" and pending["direction"]=="bullish": pending["new_low"]=True
                    direction=pending["direction"]
                    if direction=="bearish" and pending["new_low"] and pending["new_high"] and lows and any(c>pending["index"] for c,_,_ in lows):
                        protected=pre_lows[-1]
                        if candle.close<protected[1] and protected[0]>pending["index"]:
                            ev=self._event("MSS",candle,candle.close_time,level=protected[1],direction="bearish",prior_state=_STATE_UNCONFIRMED,reason="post_choch_bearish_structural_transition",index=i)
                            if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); broken_levels.add(("bearish",protected[1],boundary)); active_break_facts[ev.identity]=ev; state=_STATE_DOWN; pending=None
                    elif direction=="bullish" and pending["new_high"] and pending["new_low"] and highs and any(c>pending["index"] for c,_,_ in highs):
                        protected=pre_highs[-1]
                        if candle.close>protected[1] and protected[0]>pending["index"]:
                            ev=self._event("MSS",candle,candle.close_time,level=protected[1],direction="bullish",prior_state=_STATE_UNCONFIRMED,reason="post_choch_bullish_structural_transition",index=i)
                            if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); broken_levels.add(("bullish",protected[1],boundary)); active_break_facts[ev.identity]=ev; state=_STATE_UP; pending=None
            phase_trace.append("structural_breaks")
            for e in list(bar_events):
                if e.event_type not in ("BOS","CHOCH","MSS") or e.direction is None: continue
                source=self._source_body(xs,i,e.direction,boundary)
                if source is None: continue
                sidx,sc=source
                ob=self._event("ORDER_BLOCK",sc,e.knowledge_time,lower=sc.low,upper=sc.high,direction=e.direction,lifecycle="ACTIVE",source=e.identity,reason="nearest_preceding_opposite_body",index=sidx,location_override=sc.open_time)
                if ob.identity not in seen: seen.add(ob.identity); bar_events.append(ob); active_obs.append(ob)
            phase_trace.append("ob_breaker")
            for ob in list(active_obs):
                if ob.direction=="bullish" and candle.close<ob.lower_bound:
                    inv=self._event("ORDER_BLOCK_INVALIDATION",candle,candle.close_time,lower=ob.lower_bound,upper=ob.upper_bound,direction="bearish",lifecycle="INVALIDATED",source=ob.identity,reason="close_below_bullish_order_block",index=i)
                    if inv.identity not in seen: seen.add(inv.identity); bar_events.append(inv)
                    br=self._event("BREAKER",candle,candle.close_time,lower=ob.lower_bound,upper=ob.upper_bound,direction="bearish",lifecycle="ACTIVE",source=ob.identity,reason="bullish_order_block_flipped_to_bearish_breaker",index=i)
                    if br.identity not in seen: seen.add(br.identity); bar_events.append(br); active_breakers.append(br); active_obs.remove(ob)
                elif ob.direction=="bearish" and candle.close>ob.upper_bound:
                    inv=self._event("ORDER_BLOCK_INVALIDATION",candle,candle.close_time,lower=ob.lower_bound,upper=ob.upper_bound,direction="bullish",lifecycle="INVALIDATED",source=ob.identity,reason="close_above_bearish_order_block",index=i)
                    if inv.identity not in seen: seen.add(inv.identity); bar_events.append(inv)
                    br=self._event("BREAKER",candle,candle.close_time,lower=ob.lower_bound,upper=ob.upper_bound,direction="bullish",lifecycle="ACTIVE",source=ob.identity,reason="bearish_order_block_flipped_to_bullish_breaker",index=i)
                    if br.identity not in seen: seen.add(br.identity); bar_events.append(br); active_breakers.append(br); active_obs.remove(ob)
            for br in list(active_breakers):
                if (br.direction=="bearish" and candle.close>br.upper_bound) or (br.direction=="bullish" and candle.close<br.lower_bound):
                    ev=self._event("BREAKER_INVALIDATION",candle,candle.close_time,lower=br.lower_bound,upper=br.upper_bound,direction=br.direction,lifecycle="INVALIDATED",source=br.identity,reason="close_through_opposite_breaker_boundary",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); active_breakers.remove(br)
            phase_trace.append("fvg")
            if i>=2 and i>=boundary and self._window_continuous(xs,i-2,i):
                a,b,c=xs[i-2],xs[i-1],candle
                if c.low>a.high:
                    ev=self._event("FVG",c,c.close_time,lower=a.high,upper=c.low,direction="bullish",lifecycle="ACTIVE",reason="bullish_three_candle_gap",index=i)
                    if ev.identity not in seen:
                        seen.add(ev); bar_events.append(ev); active_fvgs.append(ev); fvg_lifecycle[ev.identity]="ACTIVE"
                elif c.high<a.low:
                    ev=self._event("FVG",c,c.close_time,lower=c.high,upper=a.low,direction="bearish",lifecycle="ACTIVE",reason="bearish_three_candle_gap",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); active_fvgs.append(ev); fvg_lifecycle[ev.identity]="ACTIVE"
            if i>boundary:
                for fvg in list(active_fvgs):
                    current=fvg_lifecycle.get(fvg.identity,"ACTIVE")
                    if fvg.event_location==candle.open_time or current=="FULLY_MITIGATED": continue
                    hit=None
                    if fvg.direction=="bullish" and candle.low<=fvg.upper_bound:
                        hit="FULLY_MITIGATED" if candle.low<=fvg.lower_bound else "PARTIALLY_MITIGATED"
                    elif fvg.direction=="bearish" and candle.high>=fvg.lower_bound:
                        hit="FULLY_MITIGATED" if candle.high>=fvg.upper_bound else "PARTIALLY_MITIGATED"
                    if hit is None: continue
                    if current=="ACTIVE":
                        part=self._event("FVG_LIFECYCLE",candle,candle.close_time,lower=fvg.lower_bound,upper=fvg.upper_bound,direction=fvg.direction,lifecycle="PARTIALLY_MITIGATED",source=fvg.identity,reason="wick_based_mitigation",index=i)
                        if part.identity not in seen: seen.add(part.identity); bar_events.append(part)
                        fvg_lifecycle[fvg.identity]="PARTIALLY_MITIGATED"; current="PARTIALLY_MITIGATED"
                    if current=="PARTIALLY_MITIGATED" and hit=="FULLY_MITIGATED":
                        full=self._event("FVG_LIFECYCLE",candle,candle.close_time,lower=fvg.lower_bound,upper=fvg.upper_bound,direction=fvg.direction,lifecycle="FULLY_MITIGATED",source=fvg.identity,reason="wick_based_full_mitigation",index=i)
                        if full.identity not in seen: seen.add(full.identity); bar_events.append(full)
                        fvg_lifecycle[fvg.identity]="FULLY_MITIGATED"; active_fvgs.remove(fvg)
            phase_trace.append("liquidity")
            for e in bar_events:
                if e.event_type=="SWING_HIGH":
                    members=pools_high.setdefault(e.level,[]); members.append(e)
                    if len(members)==2:
                        pool=self._event("LIQUIDITY_POOL",candle,candle.close_time,level=e.level,direction="bullish",lifecycle="ACTIVE",reason="two_exactly_equal_confirmed_swing_highs",index=i,source=",".join(m.identity for m in members))
                        if pool.identity not in seen: seen.add(pool.identity); bar_events.append(pool); active_pools.append(pool)
                elif e.event_type=="SWING_LOW":
                    members=pools_low.setdefault(e.level,[]); members.append(e)
                    if len(members)==2:
                        pool=self._event("LIQUIDITY_POOL",candle,candle.close_time,level=e.level,direction="bearish",lifecycle="ACTIVE",reason="two_exactly_equal_confirmed_swing_lows",index=i,source=",".join(m.identity for m in members))
                        if pool.identity not in seen: seen.add(pool.identity); bar_events.append(pool); active_pools.append(pool)
            for pool in list(active_pools):
                if pool.direction=="bullish" and candle.close>pool.level:
                    ev=self._event("LIQUIDITY_POOL_SWEEP",candle,candle.close_time,level=pool.level,direction=pool.direction,lifecycle="INVALIDATED",source=pool.identity,reason="close_beyond_bullish_side_pool_level",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); active_pools.remove(pool)
                elif pool.direction=="bearish" and candle.close<pool.level:
                    ev=self._event("LIQUIDITY_POOL_SWEEP",candle,candle.close_time,level=pool.level,direction=pool.direction,lifecycle="INVALIDATED",source=pool.identity,reason="close_beyond_bearish_side_pool_level",index=i)
                    if ev.identity not in seen: seen.add(ev.identity); bar_events.append(ev); active_pools.remove(pool)
            for original in list(active_break_facts.values()):
                if original.direction=="bullish" and candle.close<original.level and original.knowledge_time<candle.close_time:
                    inv=self._event("STRUCTURAL_INVALIDATION",candle,candle.close_time,level=original.level,direction="bearish",lifecycle="INVALIDATED",source=original.identity,reason="later_close_contradicts_bullish_structural_fact",index=i)
                    if inv.identity not in seen: seen.add(inv.identity); bar_events.append(inv)
                    active_break_facts.pop(original.identity,None)
                elif original.direction=="bearish" and candle.close>original.level and original.knowledge_time<candle.close_time:
                    inv=self._event("STRUCTURAL_INVALIDATION",candle,candle.close_time,level=original.level,direction="bullish",lifecycle="INVALIDATED",source=original.identity,reason="later_close_contradicts_bearish_structural_fact",index=i)
                    if inv.identity not in seen: seen.add(inv.identity); bar_events.append(inv)
                    active_break_facts.pop(original.identity,None)

            if boundary==i or pending is not None: state=_STATE_UNCONFIRMED
            elif state==_STATE_UNCONFIRMED and not quarantine: state=self._derive_state(highs,lows,high_class,low_class)
            phase_trace.append("official_post_bar_state")
            state_event=self._event("STRUCTURE_STATE",candle,candle.close_time,structural_state=state,reason="official_post_bar_structure_state",index=i)
            if state_event.identity not in seen: seen.add(state_event.identity); bar_events.append(state_event)
            bar_events=self._dedupe(bar_events); events.extend(bar_events); states.append(BarState(i,candle.open_time,candle.close_time,state,tuple(bar_events),tuple(phase_trace)))
        return MarketStructureAnalysis(tuple(xs),tuple(events),tuple(states))

    def _validate(self,candles):
        try: xs=tuple(candles)
        except TypeError as exc: raise TypeError("candles must be iterable") from exc
        for i,c in enumerate(xs):
            if not isinstance(c,CanonicalCandle): raise TypeError(f"candles[{i}] must be CanonicalCandle")
            if not c.is_closed: raise ValueError(f"candles[{i}] must be closed")
            if i and (c.instrument_id!=xs[i-1].instrument_id or c.timeframe!=xs[i-1].timeframe): raise ValueError("instrument_id and timeframe must remain constant")
            if i and c.open_time<=xs[i-1].open_time: raise ValueError("candles must be strictly increasing by open_time")
        return xs
    def _expected_open(self,c): return c.open_time+_INTERVALS[c.timeframe] if c.timeframe in _INTERVALS else None
    def _window_continuous(self,xs,a,b):
        return all(xs[j].timeframe in _INTERVALS and xs[j].open_time==self._expected_open(xs[j-1]) for j in range(a+1,b+1))
    def _derive_state(self,highs,lows,hc,lc):
        if not highs or not lows: return _STATE_NEUTRAL
        h=hc.get(highs[-1][0]); l=lc.get(lows[-1][0])
        if h is None or l is None: return _STATE_UNCONFIRMED
        if h=="HH" and l=="HL": return _STATE_UP
        if h=="LH" and l=="LL": return _STATE_DOWN
        return _STATE_RANGE
    def _source_body(self,xs,i,direction,boundary):
        for j in range(i-1,boundary-1,-1):
            c=xs[j]
            if direction=="bullish" and c.close<c.open: return j,c
            if direction=="bearish" and c.close>c.open: return j,c
        return None
    def _event(self,event_type,c,knowledge,level=None,lower=None,upper=None,direction=None,lifecycle=None,source=None,prior_state=None,reason="",index=0,location_override=None,structural_state=None):
        loc=location_override or c.open_time
        payload=(c.instrument_id,c.timeframe,SEMANTIC_VERSION,event_type,loc.isoformat(),knowledge.isoformat(),direction or "",self._dec(level),self._dec(lower),self._dec(upper),lifecycle or "",source or "")
        ident=sha256("|".join(payload).encode()).hexdigest()
        return StructuralEvent(event_type,loc,knowledge,knowledge,ident,direction,level,lower,upper,lifecycle,structural_state,source,prior_state,reason)
    @staticmethod
    def _dec(x): return "" if x is None else format(x,"f")
    @staticmethod
    def _dedupe(events):
        out=[]; ids=set()
        for e in events:
            if e.identity not in ids: ids.add(e.identity); out.append(e)
        return out
