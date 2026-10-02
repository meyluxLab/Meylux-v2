"""Deterministic Stage-1 Group-A specialists: S-01, S-06 and S-08.

This module interprets persisted authoritative Snapshot facts only. It does not
calculate indicators or import another specialist's output.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from contracts.specialist import (
    FactStatus, InputSnapshot, EvidenceRef, SpecialistFinding, SpecialistOutput,
    SpecialistStatus, canonical_json,
)
from meylux.queue import NonRetryableProcessingError


class GroupASemanticError(NonRetryableProcessingError):
    """Malformed Group-A input or violated authoritative evidence contract."""


@dataclass(frozen=True, slots=True)
class Metric:
    state: str
    value: Decimal | None
    refs: tuple[EvidenceRef, ...]
    reason: str
    facts: tuple[Any, ...] = ()


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float) or value is None:
        raise InvalidOperation("value must be a finite decimal-compatible scalar")
    result = value if isinstance(value, Decimal) else Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite quantitative input")
    return result


def _tf(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GroupASemanticError("authoritative fact timeframe is missing")
    return value.strip().lower()


def _symbol(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GroupASemanticError("authoritative fact symbol is missing")
    return value.strip().upper()


def _refs(facts) -> tuple[EvidenceRef, ...]:
    unique = {}
    for fact in facts:
        for ref in fact.evidence_refs:
            if not ref.record_id or not ref.source_family or not ref.timeframe or not ref.venue:
                raise GroupASemanticError("Group-A EvidenceRef lacks source record/timeframe/venue context")
            unique[ref.evidence_id] = ref
    return tuple(unique[k] for k in sorted(unique))


def _name(fact) -> str | None:
    value = fact.value
    if isinstance(value, Mapping):
        candidate = value.get("fact_name") or value.get("indicator_name") or value.get("name")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().upper()
    metadata = fact.metadata or {}
    candidate = metadata.get("fact_name") or metadata.get("indicator_name")
    return candidate.strip().upper() if isinstance(candidate, str) and candidate.strip() else None


def _source_table(fact) -> str:
    value = (fact.metadata or {}).get("source_table", "")
    return value.strip().lower() if isinstance(value, str) else ""


def _context_matches(fact, symbol: str, timeframe: str) -> bool:
    metadata = fact.metadata or {}
    if _symbol(metadata.get("symbol")) != symbol or _tf(metadata.get("timeframe")) != timeframe:
        return False
    meta_knowledge = metadata.get("knowledge_time", fact.knowledge_time)
    if meta_knowledge != fact.knowledge_time:
        raise GroupASemanticError("metadata knowledge_time conflicts with SnapshotFact knowledge_time")
    if meta_knowledge > fact.knowledge_time:
        raise GroupASemanticError("metadata knowledge_time exceeds SnapshotFact knowledge_time")
    return True


def _metric(snapshot: InputSnapshot, symbol: str, timeframe: str, names: tuple[str, ...],
            *, source: str = "meylux.calculated_indicator_vectors", boundary=None) -> Metric:
    matched = []
    for fact in snapshot.facts:
        if _source_table(fact) != source or _name(fact) not in names:
            continue
        metadata = fact.metadata or {}
        if not metadata.get("symbol") or not metadata.get("timeframe"):
            raise GroupASemanticError("authoritative indicator fact lacks symbol/timeframe context")
        if not _context_matches(fact, symbol, timeframe):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupASemanticError("post-boundary Group-A evidence reached specialist execution")
        if boundary is not None and fact.knowledge_time > boundary:
            continue
        event_time = (fact.metadata or {}).get("event_time")
        if event_time is None:
            raise GroupASemanticError("authoritative Group-A fact lacks event_time")
        matched.append((fact, event_time))
    if not matched:
        return Metric("MISSING", None, (), "required authoritative Group-A fact is missing")
    post_boundary = tuple(fact for fact, event_time in matched if event_time > snapshot.as_of)
    if post_boundary:
        return Metric("POST_BOUNDARY", None, _refs(post_boundary),
            "authoritative event_time is after snapshot.as_of", post_boundary)
    latest_time = max(event_time for _, event_time in matched)
    latest = tuple(fact for fact, event_time in matched if event_time == latest_time)
    if len(latest) > 1:
        # Different records at the same authoritative event time are ambiguous even
        # when their numeric payload happens to agree.
        return Metric("CONTRADICTORY", None, _refs(latest),
            "multiple authoritative records exist for the same logical fact and event time", latest)
    fact = latest[0]
    if fact.status is not FactStatus.VALID:
        state = {
            FactStatus.CONTRADICTORY: "CONTRADICTORY",
            FactStatus.STALE: "STALE",
            FactStatus.INVALID: "INVALID",
            FactStatus.UNAVAILABLE: "UNAVAILABLE",
            FactStatus.INSUFFICIENT_DATA: "INSUFFICIENT_DATA",
            FactStatus.PARTIAL: "INSUFFICIENT_DATA",
        }.get(fact.status, "INSUFFICIENT_DATA")
        return Metric(state, None, _refs((fact,)), fact.reason or "authoritative fact is non-VALID", (fact,))
    value = fact.value
    if not isinstance(value, Mapping) or "value" not in value:
        return Metric("INVALID", None, _refs((fact,)), "authoritative indicator payload lacks a value", (fact,))
    calculation_status = str(value.get("status", "VALID")).upper()
    if calculation_status not in {"VALID", "SUCCESS", "OK"}:
        status_text = str(value.get("status", "")).upper()
        state = "INSUFFICIENT_DATA" if "INSUFFICIENT" in status_text or "HISTORY" in status_text else "INVALID"
        return Metric(state, None, _refs((fact,)), str(value.get("reason") or "authoritative calculation is non-valid"), (fact,))
    try:
        number = _decimal(value["value"])
    except (InvalidOperation, ValueError, TypeError):
        return Metric("INVALID", None, _refs((fact,)), "authoritative numeric value is invalid or non-finite", (fact,))
    return Metric("VALID", number, _refs((fact,)), "latest authoritative persisted fact resolved", (fact,))

def _price(snapshot: InputSnapshot, symbol: str, timeframe: str, *, boundary=None) -> Metric:
    matched = []
    for fact in snapshot.facts:
        if _source_table(fact) != "meylux.canonical_candles":
            continue
        metadata = fact.metadata or {}
        if not metadata.get("symbol") or not metadata.get("timeframe"):
            raise GroupASemanticError("authoritative candle fact lacks symbol/timeframe context")
        if not _context_matches(fact, symbol, timeframe):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupASemanticError("post-boundary price evidence reached specialist execution")
        if boundary is not None and fact.knowledge_time > boundary:
            continue
        event_time = (fact.metadata or {}).get("event_time")
        if event_time is None:
            raise GroupASemanticError("authoritative closed candle lacks event_time")
        matched.append((fact, event_time))
    if not matched:
        return Metric("MISSING", None, (), "authoritative closed-candle close is missing")
    post_boundary = tuple(fact for fact, event_time in matched if event_time > snapshot.as_of)
    if post_boundary:
        return Metric("POST_BOUNDARY", None, _refs(post_boundary),
            "closed-candle event_time is after snapshot.as_of", post_boundary)
    latest_time = max(event_time for _, event_time in matched)
    latest = tuple(fact for fact, event_time in matched if event_time == latest_time)
    if len(latest) > 1:
        return Metric("CONTRADICTORY", None, _refs(latest), "multiple candle records share the latest event time", latest)
    fact = latest[0]
    if fact.status is not FactStatus.VALID:
        return Metric("INVALID", None, _refs((fact,)), "latest authoritative candle is non-VALID", (fact,))
    value = fact.value
    if not isinstance(value, Mapping) or "close" not in value:
        return Metric("INVALID", None, _refs((fact,)), "authoritative candle payload lacks close", (fact,))
    try:
        number = _decimal(value["close"])
    except (InvalidOperation, ValueError, TypeError):
        return Metric("INVALID", None, _refs((fact,)), "authoritative close is invalid or non-finite", (fact,))
    return Metric("VALID", number, _refs((fact,)), "latest persisted closed-candle close resolved", (fact,))

def _ema_names(period: int, primary_period: int) -> tuple[str, ...]:
    names = [f"EMA_{period}", f"EMA{period}"]
    if period == primary_period:
        names.append("EMA")
    return tuple(names)


def _same_event_time(*metrics: Metric) -> bool:
    times = {
        fact.metadata.get("event_time")
        for metric in metrics if metric.state == "VALID"
        for fact in metric.facts
    }
    return len(times) <= 1


def _metric_state_status(metric: Metric) -> SpecialistStatus:
    if metric.state == "VALID":
        return SpecialistStatus.SUCCESS
    if metric.state in {"INSUFFICIENT_DATA", "MISSING"}:
        return SpecialistStatus.INSUFFICIENT_DATA
    if metric.state in {"POST_BOUNDARY", "CONTRADICTORY"}:
        return SpecialistStatus.PARTIAL
    if metric.state == "UNAVAILABLE":
        return SpecialistStatus.UNAVAILABLE_INPUT
    return SpecialistStatus.PARTIAL


def _finding(code: str, value: Any, reason: str, refs: tuple[EvidenceRef, ...],
             status: SpecialistStatus = SpecialistStatus.SUCCESS) -> SpecialistFinding:
    return SpecialistFinding(code, status, value, reason, evidence_refs=refs)


def _output_status(findings: list[SpecialistFinding], all_refs: tuple[EvidenceRef, ...]) -> tuple[SpecialistStatus, str]:
    if not all_refs:
        return SpecialistStatus.INSUFFICIENT_DATA, "no resolvable authoritative Group-A evidence in Snapshot"
    statuses = {finding.status for finding in findings}
    if statuses <= {SpecialistStatus.SUCCESS}:
        return SpecialistStatus.SUCCESS, "all configured Group-A interpretations resolved deterministically"
    if statuses <= {SpecialistStatus.INSUFFICIENT_DATA}:
        return SpecialistStatus.INSUFFICIENT_DATA, "required Group-A facts are missing or insufficient"
    if SpecialistStatus.UNAVAILABLE_INPUT in statuses and statuses <= {SpecialistStatus.UNAVAILABLE_INPUT, SpecialistStatus.INSUFFICIENT_DATA}:
        return SpecialistStatus.UNAVAILABLE_INPUT, "authoritative Group-A inputs are unavailable"
    return SpecialistStatus.PARTIAL, "some Group-A interpretations are unavailable, invalid, stale or insufficient"


def _config_csv(config: Any, key: str, converter):
    raw = config.parameter(key)
    if not isinstance(raw, str) or not raw.strip():
        raise GroupASemanticError(f"configuration parameter {key} must be a non-empty comma-separated string")
    try:
        values = tuple(converter(piece.strip()) for piece in raw.split(",") if piece.strip())
    except (ValueError, InvalidOperation) as exc:
        raise GroupASemanticError(f"invalid configuration parameter {key}") from exc
    if not values or len(set(values)) != len(values):
        raise GroupASemanticError(f"configuration parameter {key} must contain unique values")
    return values


def _base(snapshot: InputSnapshot, config: Any, specialist_id: str, findings: list[SpecialistFinding]) -> SpecialistOutput:
    refs = tuple(sorted({r.evidence_id: r for f in findings for r in f.evidence_refs}.values(), key=lambda r: r.evidence_id))
    if len(findings) > int(config.parameter("max_findings")):
        raise GroupASemanticError("Group-A finding bound exceeded")
    if len(refs) > int(config.parameter("max_evidence_refs")):
        raise GroupASemanticError("Group-A evidence reference bound exceeded")
    status, reason = _output_status(findings, refs)
    output = SpecialistOutput(specialist_id, "1.0.0", snapshot.snapshot_id, snapshot.version,
        config.ref(), status, reason, tuple(findings), refs)
    canonical_json(output.as_dict())
    return output


def analyze_s01(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    """S-01 technical interpretation; no indicator mathematics is recomputed."""
    symbols = _config_csv(config, "group_a_symbols", str)
    timeframes = _config_csv(config, "group_a_timeframes", str)
    periods = _config_csv(config, "technical_ema_periods", int)
    primary_period = int(config.parameter("technical_primary_ema_period"))
    if primary_period not in periods:
        raise GroupASemanticError("technical_primary_ema_period must be included in technical_ema_periods")
    rsi_low, rsi_high = _decimal(config.parameter("rsi_oversold")), _decimal(config.parameter("rsi_overbought"))
    adx_threshold = _decimal(config.parameter("adx_trend_threshold"))
    macd_neutral = _decimal(config.parameter("macd_histogram_neutral_threshold"))
    squeeze_threshold = _decimal(config.parameter("bollinger_squeeze_bandwidth_threshold"))
    if rsi_low < 0 or rsi_high > 100 or rsi_low >= rsi_high or adx_threshold < 0 or macd_neutral < 0 or squeeze_threshold < 0:
        raise GroupASemanticError("invalid S-01 threshold ordering")

    findings = []
    for symbol in symbols:
        for timeframe in timeframes:
            price = _price(snapshot, symbol, timeframe)
            emas, missing_periods, refs, ema_metrics = [], [], list(price.refs), []
            for period in periods:
                metric = _metric(snapshot, symbol, timeframe, _ema_names(period, primary_period))
                ema_metrics.append(metric)
                refs.extend(metric.refs)
                if metric.state == "VALID":
                    emas.append((period, metric.value))
                else:
                    missing_periods.append({"period": period, "state": metric.state, "reason": metric.reason})
            if any(metric.state == "POST_BOUNDARY" for metric in ema_metrics):
                alignment_value = {"state": "POST_BOUNDARY", "available_periods": [p for p, _ in emas],
                    "missing_periods": missing_periods}
                alignment_status = SpecialistStatus.PARTIAL
            elif not _same_event_time(*ema_metrics):
                alignment_value = {"state": "CONTRADICTORY_CONTEXT", "available_periods": [p for p, _ in emas],
                    "missing_periods": missing_periods, "reason": "EMA facts refer to different event times"}
                alignment_status = SpecialistStatus.PARTIAL
            elif missing_periods or len(emas) < 2:
                alignment_value = {"state": "INSUFFICIENT_DATA" if len(emas) < 2 else "PARTIAL",
                    "available_periods": [p for p, _ in emas], "missing_periods": missing_periods}
                alignment_status = SpecialistStatus.INSUFFICIENT_DATA if len(emas) < 2 else SpecialistStatus.PARTIAL
            else:
                ordered = [value for _, value in sorted(emas)]
                state = "BULLISH" if all(ordered[i] > ordered[i + 1] for i in range(len(ordered)-1)) else \
                    "BEARISH" if all(ordered[i] < ordered[i + 1] for i in range(len(ordered)-1)) else "MIXED"
                alignment_value = {"state": state, "periods": [p for p, _ in sorted(emas)]}
                alignment_status = SpecialistStatus.SUCCESS
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:MA_ALIGNMENT", alignment_value,
                "EMA ordering from configured authoritative periods; missing periods remain explicit",
                tuple(sorted({r.evidence_id:r for r in refs}.values(), key=lambda r:r.evidence_id)), alignment_status))

            primary_ema = _metric(snapshot, symbol, timeframe, _ema_names(primary_period, primary_period))
            price_refs = tuple(sorted({r.evidence_id:r for r in (*price.refs, *primary_ema.refs)}.values(), key=lambda r:r.evidence_id))
            if price.state != "VALID" or primary_ema.state != "VALID":
                state = "POST_BOUNDARY" if "POST_BOUNDARY" in {price.state, primary_ema.state} else "INSUFFICIENT_DATA"
                value = {"state": state, "price_state": price.state, "ema_state": primary_ema.state}
                fstatus = SpecialistStatus.PARTIAL if state == "POST_BOUNDARY" else SpecialistStatus.INSUFFICIENT_DATA
                reason = "price and configured primary EMA are both required and must be inside the snapshot boundary"
            elif not _same_event_time(price, primary_ema):
                value = {"state": "CONTRADICTORY_CONTEXT", "price_event_time": price.facts[0].metadata.get("event_time"),
                    "ema_event_time": primary_ema.facts[0].metadata.get("event_time")}
                fstatus, reason = SpecialistStatus.PARTIAL, "price and EMA refer to different event times"
            else:
                value = {"state": "ABOVE_MA" if price.value > primary_ema.value else "BELOW_MA" if price.value < primary_ema.value else "AT_MA",
                    "price": price.value, "ema_period": primary_period, "ema": primary_ema.value}
                fstatus, reason = SpecialistStatus.SUCCESS, "closed-candle close compared with configured authoritative EMA"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:PRICE_VS_MA", value, reason, price_refs, fstatus))

            macd, signal, histogram = (_metric(snapshot, symbol, timeframe, (name,)) for name in ("MACD", "MACD_SIGNAL", "MACD_HISTOGRAM"))
            macd_refs = _refs(tuple(f for metric in (macd, signal, histogram) for f in metric.facts))
            if any(metric.state != "VALID" for metric in (macd, signal, histogram)):
                state = "POST_BOUNDARY" if any(metric.state == "POST_BOUNDARY" for metric in (macd, signal, histogram)) else "INSUFFICIENT_DATA"
                value = {"state": state, "macd": macd.state, "signal": signal.state, "histogram": histogram.state}
                fstatus = SpecialistStatus.PARTIAL if state == "POST_BOUNDARY" else SpecialistStatus.INSUFFICIENT_DATA
                reason = "MACD, signal and histogram authoritative facts are all required and must be inside the snapshot boundary"
            elif not _same_event_time(macd, signal, histogram):
                value, fstatus, reason = {"state": "CONTRADICTORY_CONTEXT"}, SpecialistStatus.PARTIAL, "MACD components refer to different event times"
            else:
                state = "BULLISH" if macd.value > signal.value and histogram.value > macd_neutral else \
                    "BEARISH" if macd.value < signal.value and histogram.value < -macd_neutral else "NEUTRAL"
                value = {"state": state, "macd": macd.value, "signal": signal.value, "histogram": histogram.value}
                fstatus, reason = SpecialistStatus.SUCCESS, "MACD state uses persisted MACD, signal and histogram values"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:MACD_STATE", value, reason, macd_refs, fstatus))

            rsi = _metric(snapshot, symbol, timeframe, ("RSI",))
            if rsi.state != "VALID":
                value, fstatus, reason = {"state": rsi.state, "reason": rsi.reason}, _metric_state_status(rsi), "authoritative RSI-14 fact is not valid"
            elif rsi.value < 0 or rsi.value > 100:
                value, fstatus, reason = {"state": "INVALID", "value": rsi.value}, SpecialistStatus.PARTIAL, "RSI value is outside the authoritative [0,100] range"
            else:
                value = {"state": "OVERSOLD" if rsi.value <= rsi_low else "OVERBOUGHT" if rsi.value >= rsi_high else "NEUTRAL",
                    "value": rsi.value, "oversold_boundary_inclusive": True, "overbought_boundary_inclusive": True}
                fstatus, reason = SpecialistStatus.SUCCESS, "RSI zone uses configured inclusive thresholds"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:RSI_ZONE", value, reason, rsi.refs, fstatus))

            adx = _metric(snapshot, symbol, timeframe, ("ADX",))
            if adx.state != "VALID":
                value, fstatus, reason = {"state": adx.state, "reason": adx.reason}, _metric_state_status(adx), "authoritative ADX-14 fact is not valid"
            else:
                value = {"state": "STRONG" if adx.value >= adx_threshold else "WEAK",
                    "value": adx.value, "threshold": adx_threshold, "boundary_inclusive": True}
                fstatus, reason = SpecialistStatus.SUCCESS, "ADX strength uses configured inclusive trend threshold"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:ADX_STRENGTH", value, reason, adx.refs, fstatus))

            upper, lower, middle = (_metric(snapshot, symbol, timeframe, (name,)) for name in
                ("BOLLINGER_UPPER", "BOLLINGER_LOWER", "BOLLINGER_MIDDLE"))
            band_refs = _refs(tuple(f for metric in (price, upper, lower, middle) for f in metric.facts))
            if any(metric.state != "VALID" for metric in (price, upper, lower, middle)):
                post = any(metric.state == "POST_BOUNDARY" for metric in (price, upper, lower, middle))
                value = {"state": "POST_BOUNDARY" if post else "INSUFFICIENT_DATA",
                    "price": price.state, "upper": upper.state, "lower": lower.state, "middle": middle.state}
                fstatus = SpecialistStatus.PARTIAL if post else SpecialistStatus.INSUFFICIENT_DATA
                reason = "price and all three authoritative Bollinger bands are required inside the snapshot boundary"
            elif not _same_event_time(price, upper, lower, middle):
                value, fstatus, reason = {"state": "CONTRADICTORY_CONTEXT"}, SpecialistStatus.PARTIAL, "price and Bollinger bands refer to different event times"
            elif upper.value < lower.value or middle.value < lower.value or middle.value > upper.value:
                value, fstatus, reason = {"state": "INVALID", "reason": "contradictory Bollinger band ordering"}, SpecialistStatus.PARTIAL, "contradictory Bollinger band ordering"
            else:
                state = "ABOVE_UPPER" if price.value > upper.value else "BELOW_LOWER" if price.value < lower.value else \
                    "AT_UPPER" if price.value == upper.value else "AT_LOWER" if price.value == lower.value else \
                    "ABOVE_MIDDLE" if price.value > middle.value else "BELOW_MIDDLE" if price.value < middle.value else "AT_MIDDLE"
                value = {"state": state, "price": price.value, "upper": upper.value, "middle": middle.value, "lower": lower.value}
                fstatus, reason = SpecialistStatus.SUCCESS, "price position compares the closed-candle close with persisted Bollinger bands"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:BOLLINGER_POSITION", value, reason, band_refs, fstatus))

            bandwidth = _metric(snapshot, symbol, timeframe, ("BOLLINGER_BANDWIDTH",))
            if bandwidth.state != "VALID":
                value, fstatus, reason = {"state": bandwidth.state, "reason": bandwidth.reason, "threshold": squeeze_threshold}, \
                    _metric_state_status(bandwidth), "authoritative Bollinger bandwidth is not valid"
            elif bandwidth.value < 0:
                value, fstatus, reason = {"state": "INVALID", "bandwidth": bandwidth.value}, SpecialistStatus.PARTIAL, "bandwidth cannot be negative"
            elif price.state == "VALID" and not _same_event_time(price, bandwidth):
                value, fstatus, reason = {"state": "CONTRADICTORY_CONTEXT"}, SpecialistStatus.PARTIAL, "price and bandwidth refer to different event times"
            else:
                value = {"state": "SQUEEZE" if bandwidth.value <= squeeze_threshold else "NORMAL",
                    "bandwidth": bandwidth.value, "threshold": squeeze_threshold, "boundary_inclusive": True}
                fstatus, reason = SpecialistStatus.SUCCESS, "squeeze uses the configured inclusive bandwidth threshold"
            findings.append(_finding(f"TECHNICAL:{symbol}:{timeframe}:BOLLINGER_SQUEEZE", value, reason, bandwidth.refs, fstatus))
    return _base(snapshot, config, "S-01", findings)


def _direction(snapshot: InputSnapshot, symbol: str, timeframe: str, primary_period: int,
               primary_event_boundary, primary_knowledge_boundary, rsi_midline: Decimal):
    if primary_event_boundary is None or primary_knowledge_boundary is None:
        return "INSUFFICIENT_DATA", (), "primary timeframe has no authoritative closed-candle event/knowledge boundary"
    future = []
    for fact in snapshot.facts:
        metadata = fact.metadata or {}
        if _source_table(fact) not in {"meylux.calculated_indicator_vectors", "meylux.canonical_candles"}:
            continue
        if not metadata.get("symbol") or not metadata.get("timeframe"):
            raise GroupASemanticError("authoritative timeframe fact lacks symbol/timeframe context")
        if _symbol(metadata.get("symbol")) != symbol or _tf(metadata.get("timeframe")) != timeframe:
            continue
        if fact.knowledge_time > primary_knowledge_boundary or metadata.get("event_time", fact.evidence_refs[0].event_time) > primary_event_boundary:
            future.append(fact)
    if future:
        return "POST_BOUNDARY_EVIDENCE", _refs(future), "higher-timeframe event_time or knowledge_time exceeds the corresponding primary boundary"
    ema = _metric(snapshot, symbol, timeframe, _ema_names(primary_period, primary_period), boundary=primary_knowledge_boundary)
    macd = _metric(snapshot, symbol, timeframe, ("MACD",), boundary=primary_knowledge_boundary)
    signal = _metric(snapshot, symbol, timeframe, ("MACD_SIGNAL",), boundary=primary_knowledge_boundary)
    rsi = _metric(snapshot, symbol, timeframe, ("RSI",), boundary=primary_knowledge_boundary)
    refs = _refs(tuple(f for metric in (ema, macd, signal, rsi) for f in metric.facts))
    if any(metric.state != "VALID" for metric in (ema, macd, signal, rsi)):
        return "INSUFFICIENT_DATA", refs, "EMA/MACD/RSI facts are required to interpret this timeframe"
    if not _same_event_time(ema, macd, signal, rsi):
        return "CONTRADICTORY_CONTEXT", refs, "higher-timeframe interpretation combines facts from different event times"
    bullish = macd.value > signal.value and rsi.value >= rsi_midline
    bearish = macd.value < signal.value and rsi.value < rsi_midline
    if bullish:
        return "BULLISH", refs, "persisted EMA/MACD/RSI facts align bullishly"
    if bearish:
        return "BEARISH", refs, "persisted EMA/MACD/RSI facts align bearishly"
    return "NEUTRAL", refs, "authoritative timeframe facts do not establish a directional alignment"

def analyze_s06(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    """S-06 independent per-timeframe interpretation and confluence."""
    symbols = _config_csv(config, "group_a_symbols", str)
    timeframes = _config_csv(config, "group_a_timeframes", str)
    primary_timeframe = _tf(config.parameter("primary_timeframe"))
    primary_period = int(config.parameter("technical_primary_ema_period"))
    rsi_midline = _decimal(config.parameter("rsi_midline"))
    if not Decimal(0) <= rsi_midline <= Decimal(100):
        raise GroupASemanticError("rsi_midline must be within [0,100]")
    if primary_timeframe not in timeframes:
        raise GroupASemanticError("primary_timeframe must be included in group_a_timeframes")
    findings = []
    for symbol in symbols:
        primary_price = _price(snapshot, symbol, primary_timeframe)
        primary_event_boundary = primary_price.facts[0].metadata.get("event_time") if primary_price.state == "VALID" else None
        primary_knowledge_boundary = primary_price.facts[0].knowledge_time if primary_price.state == "VALID" else None
        directions = []
        for timeframe in timeframes:
            state, refs, reason = _direction(snapshot, symbol, timeframe, primary_period,
                primary_event_boundary, primary_knowledge_boundary, rsi_midline)
            directions.append((timeframe, state))
            status = SpecialistStatus.SUCCESS if state in {"BULLISH", "BEARISH", "NEUTRAL"} else \
                SpecialistStatus.PARTIAL if state in {"POST_BOUNDARY_EVIDENCE", "CONTRADICTORY_CONTEXT"} else SpecialistStatus.INSUFFICIENT_DATA
            boundary = max((r.knowledge_time for r in refs if r.knowledge_time is not None), default=None)
            findings.append(_finding(f"MTF:{symbol}:{timeframe}",
                {"timeframe": timeframe, "state": state, "knowledge_boundary": boundary},
                reason, refs, status))
        states = [state for _, state in directions]
        missing = [timeframe for timeframe, state in directions if state == "INSUFFICIENT_DATA"]
        invalid_timeframes = [timeframe for timeframe, state in directions if state in {"POST_BOUNDARY_EVIDENCE", "CONTRADICTORY_CONTEXT"}]
        directional = [state for state in states if state in {"BULLISH", "BEARISH"}]
        if missing or invalid_timeframes:
            outcome = "PARTIAL"
            status = SpecialistStatus.PARTIAL if directional or invalid_timeframes else SpecialistStatus.INSUFFICIENT_DATA
            reason = "one or more required timeframes are missing, insufficient, contradictory or post-boundary"
        elif all(state in {"BULLISH", "BEARISH"} for state in states) and len(set(states)) == 1:
            outcome, status, reason = "CONFLUENCE", SpecialistStatus.SUCCESS, "all required timeframes share the same directional state"
        elif all(state in {"BULLISH", "BEARISH"} for state in states) and len(set(states)) > 1:
            outcome, status, reason = "CONFLICT", SpecialistStatus.PARTIAL, "required timeframes contain opposing directional states"
        else:
            outcome, status, reason = "PARTIAL", SpecialistStatus.PARTIAL, "one or more timeframes are neutral rather than directionally aligned"
        overall_refs = tuple(sorted({r.evidence_id:r for f in findings if f.code.startswith(f"MTF:{symbol}:") for r in f.evidence_refs}.values(), key=lambda r:r.evidence_id))
        if primary_price.refs:
            overall_refs = tuple(sorted({r.evidence_id:r for r in (*overall_refs, *primary_price.refs)}.values(), key=lambda r:r.evidence_id))
        findings.append(_finding(f"MTF:{symbol}:OVERALL", {"outcome": outcome, "timeframes": dict(directions),
            "primary_timeframe": primary_timeframe, "primary_event_boundary": primary_event_boundary,
            "primary_knowledge_boundary": primary_knowledge_boundary,
            "missing_timeframes": missing, "invalid_timeframes": invalid_timeframes}, reason, overall_refs, status))
    return _base(snapshot, config, "S-06", findings)

def analyze_s08(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    """S-08 volatility state from authoritative P4 facts only."""
    symbols = _config_csv(config, "group_a_symbols", str)
    timeframes = _config_csv(config, "group_a_timeframes", str)
    low_pct, high_pct = _decimal(config.parameter("volatility_low_percentile")), _decimal(config.parameter("volatility_high_percentile"))
    low_hv, high_hv = _decimal(config.parameter("historical_volatility_low_threshold")), _decimal(config.parameter("historical_volatility_high_threshold"))
    expanding = _decimal(config.parameter("volatility_expanding_ratio_threshold"))
    contracting = _decimal(config.parameter("volatility_contracting_ratio_threshold"))
    bandwidth_low = _decimal(config.parameter("bollinger_low_bandwidth_threshold"))
    bandwidth_high = _decimal(config.parameter("bollinger_high_bandwidth_threshold"))
    if not (Decimal(0) <= low_pct < high_pct <= Decimal(100) and Decimal(0) <= low_hv < high_hv and
            Decimal(0) < contracting < expanding and Decimal(0) <= bandwidth_low < bandwidth_high):
        raise GroupASemanticError("invalid S-08 threshold configuration")
    findings = []
    for symbol in symbols:
        for timeframe in timeframes:
            atr = _metric(snapshot, symbol, timeframe, ("ATR",))
            hv = _metric(snapshot, symbol, timeframe, ("HISTORICAL_VOLATILITY",))
            percentile = _metric(snapshot, symbol, timeframe, ("ATR_PERCENTILE",))
            ratio = _metric(snapshot, symbol, timeframe, ("VOLATILITY_EXPANSION_RATIO",))
            bandwidth = _metric(snapshot, symbol, timeframe, ("BOLLINGER_BANDWIDTH",))
            refs = _refs(tuple(f for metric in (atr, hv, percentile, ratio, bandwidth) for f in metric.facts))
            required = (("ATR", atr), ("ATR_PERCENTILE", percentile), ("HISTORICAL_VOLATILITY", hv), ("BOLLINGER_BANDWIDTH", bandwidth))
            if any(metric.state != "VALID" for _, metric in required):
                missing = {name: metric.state for name, metric in required if metric.state != "VALID"}
                future = any(metric.state == "POST_BOUNDARY" for _, metric in required)
                class_value = {"state": "POST_BOUNDARY" if future else "INSUFFICIENT_DATA", "missing": missing}
                class_status = SpecialistStatus.PARTIAL if future else SpecialistStatus.INSUFFICIENT_DATA
                class_reason = "volatility facts must be present, valid and inside the snapshot boundary"
            elif not _same_event_time(atr, percentile, hv, bandwidth):
                class_value = {"state": "CONTRADICTORY_CONTEXT", "reason": "volatility facts refer to different event times"}
                class_status, class_reason = SpecialistStatus.PARTIAL, "volatility classification cannot combine mismatched event times"
            elif percentile.value < 0 or percentile.value > 100 or atr.value < 0 or hv.value < 0 or bandwidth.value < 0:
                class_value = {"state": "INVALID", "atr": atr.value, "atr_percentile": percentile.value,
                    "historical_volatility": hv.value, "bandwidth": bandwidth.value}
                class_status, class_reason = SpecialistStatus.PARTIAL, "volatility inputs violate their valid numeric domain"
            else:
                high = percentile.value >= high_pct or hv.value >= high_hv or bandwidth.value >= bandwidth_high
                low = percentile.value <= low_pct and hv.value <= low_hv and bandwidth.value <= bandwidth_low
                state = "HIGH" if high else "LOW" if low else "NORMAL"
                class_value = {"state": state, "atr": atr.value, "atr_percentile": percentile.value,
                    "historical_volatility": hv.value, "bandwidth": bandwidth.value, "low_percentile": low_pct,
                    "high_percentile": high_pct, "historical_volatility_high_threshold": high_hv,
                    "bandwidth_low_threshold": bandwidth_low, "bandwidth_high_threshold": bandwidth_high}
                class_status, class_reason = SpecialistStatus.SUCCESS, "classification combines authoritative ATR, ATR percentile, historical volatility and Bollinger bandwidth"
            findings.append(_finding(f"VOLATILITY:{symbol}:{timeframe}:CLASSIFICATION", class_value, class_reason, refs, class_status))

            if ratio.state != "VALID":
                state_value = {"state": ratio.state, "reason": ratio.reason, "expanding_threshold": expanding, "contracting_threshold": contracting}
                state_status, state_reason = _metric_state_status(ratio), "authoritative volatility expansion ratio is not valid"
            elif all(metric.state == "VALID" for metric in (atr, percentile, hv, bandwidth)) and not _same_event_time(ratio, atr, percentile, hv, bandwidth):
                state_value = {"state": "CONTRADICTORY_CONTEXT", "reason": "expansion ratio and volatility facts refer to different event times"}
                state_status, state_reason = SpecialistStatus.PARTIAL, "expansion ratio is not aligned with the volatility fact event time"
            elif ratio.value >= expanding:
                state_value = {"state": "EXPANDING", "ratio": ratio.value, "threshold": expanding, "boundary_inclusive": True}
                state_status, state_reason = SpecialistStatus.SUCCESS, "ratio at or above configured expansion threshold is expanding"
            elif ratio.value <= contracting:
                state_value = {"state": "CONTRACTING", "ratio": ratio.value, "threshold": contracting, "boundary_inclusive": True}
                state_status, state_reason = SpecialistStatus.SUCCESS, "ratio at or below configured contraction threshold is contracting"
            else:
                state_value = {"state": "STABLE", "ratio": ratio.value, "lower_threshold": contracting, "upper_threshold": expanding}
                state_status, state_reason = SpecialistStatus.SUCCESS, "ratio between configured thresholds is stable"
            findings.append(_finding(f"VOLATILITY:{symbol}:{timeframe}:EXPANSION_STATE", state_value, state_reason, ratio.refs, state_status))

            high_risk = class_value.get("state") == "HIGH" or state_value.get("state") == "EXPANDING"
            risk_value = {"flag": "HIGH_VOLATILITY" if high_risk else None, "atr": atr.value if atr.state == "VALID" else None,
                "volatility_state": class_value.get("state"), "expansion_state": state_value.get("state")}
            if atr.state != "VALID" or class_status is not SpecialistStatus.SUCCESS or state_status is not SpecialistStatus.SUCCESS:
                risk_status, risk_reason = SpecialistStatus.INSUFFICIENT_DATA, "risk context is incomplete because an authoritative volatility fact is missing or invalid"
            else:
                risk_status, risk_reason = SpecialistStatus.SUCCESS, "HIGH_VOLATILITY is emitted for high classification or expanding authoritative ratio"
            findings.append(_finding(f"VOLATILITY:{symbol}:{timeframe}:RISK", risk_value, risk_reason, refs, risk_status))
    return _base(snapshot, config, "S-08", findings)


ANALYSTS = {"S-01": analyze_s01, "S-06": analyze_s06, "S-08": analyze_s08}
