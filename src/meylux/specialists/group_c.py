"""Deterministic Phase-5 Group-C specialists: S-03 and S-17.

These specialists consume only authoritative Stage-1 InputSnapshot facts. S-03
interprets existing P4 volume/RVOL facts; S-17 interprets persisted P4
Volume Profile sessions. Neither specialist recreates P4 mathematics or
consumes another specialist's output.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from contracts.specialist import (
    EvidenceRef,
    FactStatus,
    InputSnapshot,
    SpecialistFinding,
    SpecialistOutput,
    SpecialistStatus,
    canonical_json,
)
from meylux.queue import NonRetryableProcessingError


class GroupCSemanticError(NonRetryableProcessingError):
    """Malformed Group-C input or violated authoritative evidence contract."""


INDICATOR_TABLE = "meylux.calculated_indicator_vectors"
PROFILE_TABLE = "meylux.volume_profile_sessions"
CANDLE_TABLE = "meylux.canonical_candles"
VOLUME_FACTS = ("VOLUME_SMA", "RVOL", "VOLUME_SPIKE", "VOLUME_CLIMAX")


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise GroupCSemanticError(f"{field} must be explicit UTC")
    return value


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None or isinstance(value, float):
        raise GroupCSemanticError(f"{field} must be a finite Decimal-compatible value")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise GroupCSemanticError(f"{field} must be a finite Decimal-compatible value") from exc
    if not result.is_finite():
        raise GroupCSemanticError(f"{field} must be finite")
    return result


def _csv(config: Any, key: str, *, upper: bool = False, lower: bool = False) -> tuple[str, ...]:
    raw = config.parameter(key)
    if not isinstance(raw, str) or not raw.strip():
        raise GroupCSemanticError(f"configuration parameter {key} must be non-empty")
    parts = tuple(piece.strip() for piece in raw.split(","))
    if any(not piece for piece in parts) or len(set(parts)) != len(parts):
        raise GroupCSemanticError(f"configuration parameter {key} contains empty or duplicate values")
    if upper:
        return tuple(piece.upper() for piece in parts)
    if lower:
        return tuple(piece.lower() for piece in parts)
    return parts


def _source_table(fact: Any) -> str:
    value = (fact.metadata or {}).get("source_table")
    if not isinstance(value, str) or not value.strip():
        raise GroupCSemanticError("authoritative Group-C fact lacks source_table")
    return value.strip().lower()


def _context(fact: Any, symbol: str, timeframe: str, venue: str) -> bool:
    metadata = fact.metadata or {}
    raw_symbol = metadata.get("symbol")
    raw_timeframe = metadata.get("timeframe")
    raw_venue = metadata.get("venue")
    if not all(isinstance(value, str) and value.strip() for value in (raw_symbol, raw_timeframe, raw_venue)):
        raise GroupCSemanticError("Group-C fact lacks explicit symbol/timeframe/venue context")
    normalized_symbol = raw_symbol.strip().upper()
    normalized_venue = raw_venue.strip().upper()
    if ":" in normalized_symbol:
        qualified_venue, qualified_symbol = normalized_symbol.split(":", 1)
        if qualified_symbol != symbol:
            return False
        if qualified_venue != normalized_venue:
            raise GroupCSemanticError("qualified instrument conflicts with explicit venue")
        if qualified_venue != venue:
            return False
    elif normalized_symbol != symbol:
        return False
    if normalized_venue != venue or raw_timeframe.strip().lower() != timeframe:
        return False

    event_time = metadata.get("event_time")
    knowledge_time = metadata.get("knowledge_time", fact.knowledge_time)
    _utc(event_time, "metadata.event_time")
    _utc(knowledge_time, "metadata.knowledge_time")
    _utc(fact.knowledge_time, "SnapshotFact.knowledge_time")
    if knowledge_time != fact.knowledge_time:
        raise GroupCSemanticError("metadata knowledge_time conflicts with SnapshotFact")
    for ref in fact.evidence_refs:
        required = (
            ref.source_family, ref.record_id, ref.identity_hash,
            ref.event_time, ref.knowledge_time, ref.timeframe, ref.venue,
        )
        if any(value is None or (isinstance(value, str) and not value.strip()) for value in required):
            raise GroupCSemanticError("Group-C EvidenceRef is incomplete")
        if ref.record_id != metadata.get("record_id") or ref.identity_hash != metadata.get("identity_hash"):
            raise GroupCSemanticError("EvidenceRef does not resolve to authoritative record identity")
        if ref.event_time != event_time or ref.knowledge_time != fact.knowledge_time:
            raise GroupCSemanticError("EvidenceRef timing does not match authoritative fact")
        if ref.timeframe.lower() != timeframe or ref.venue.upper() != venue:
            raise GroupCSemanticError("EvidenceRef context conflicts with authoritative fact")
    return True


def _refs(facts: tuple[Any, ...] | list[Any]) -> tuple[EvidenceRef, ...]:
    unique: dict[str, EvidenceRef] = {}
    for fact in facts:
        if not fact.evidence_refs:
            raise GroupCSemanticError("authoritative Group-C fact lacks EvidenceRef")
        for ref in fact.evidence_refs:
            unique[ref.evidence_id] = ref
    return tuple(unique[key] for key in sorted(unique))


def _payload(fact: Any) -> Mapping[str, Any]:
    if not isinstance(fact.value, Mapping):
        raise GroupCSemanticError("authoritative Group-C payload must be a mapping")
    return fact.value


def _value_from_indicator(fact: Any, name: str) -> Decimal | None:
    if fact.status is not FactStatus.VALID:
        return None
    payload = _payload(fact)
    if "value" not in payload:
        raise GroupCSemanticError(f"{name} authoritative payload lacks value")
    return _decimal(payload["value"], f"{name}.value")


def _indicator_facts(snapshot: InputSnapshot, symbol: str, timeframe: str, venue: str) -> dict[str, tuple[Any, ...]]:
    result: dict[str, list[Any]] = {name: [] for name in VOLUME_FACTS}
    for fact in snapshot.facts:
        if _source_table(fact) != INDICATOR_TABLE:
            continue
        if not _context(fact, symbol, timeframe, venue):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupCSemanticError("post-boundary Group-C indicator evidence reached specialist execution")
        metadata = fact.metadata or {}
        value = fact.value if isinstance(fact.value, Mapping) else {}
        name = value.get("fact_name") or metadata.get("fact_name") or value.get("indicator_name") or metadata.get("indicator_name")
        if isinstance(name, str) and name.strip().upper() in result:
            result[name.strip().upper()].append(fact)
    return {name: tuple(items) for name, items in result.items()}


def _single_latest(facts: tuple[Any, ...], name: str) -> Any | None:
    if not facts:
        return None
    latest_time = max(_utc((fact.metadata or {}).get("event_time"), f"{name}.event_time") for fact in facts)
    latest = tuple(fact for fact in facts if _utc((fact.metadata or {}).get("event_time"), f"{name}.event_time") == latest_time)
    if len(latest) > 1:
        raise GroupCSemanticError(f"multiple authoritative {name} records share the latest event time")
    return latest[0]


def _candle_close_time(fact: Any) -> datetime:
    close_time = _payload(fact).get("close_time")
    if isinstance(close_time, str):
        try:
            close_time = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
        except ValueError as exc:
            raise GroupCSemanticError("candle.close_time is not valid ISO-8601") from exc
    return _utc(close_time, "candle.close_time")


def _candle_facts(snapshot: InputSnapshot, symbol: str, timeframe: str, venue: str) -> tuple[Any, ...]:
    rows = []
    for fact in snapshot.facts:
        if _source_table(fact) != CANDLE_TABLE:
            continue
        if not _context(fact, symbol, timeframe, venue):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupCSemanticError("post-boundary Group-C candle evidence reached specialist execution")
        close_time = _candle_close_time(fact)
        if close_time <= snapshot.as_of:
            rows.append((close_time, fact))
    rows.sort(key=lambda item: (item[0], str((item[1].metadata or {}).get("record_id"))))
    return tuple(fact for _, fact in rows)


def _base(snapshot: InputSnapshot, config: Any, specialist_id: str,
          findings: list[SpecialistFinding]) -> SpecialistOutput:
    refs = tuple(sorted({r.evidence_id: r for finding in findings for r in finding.evidence_refs}.values(),
                        key=lambda ref: ref.evidence_id))
    if len(findings) > int(config.parameter("group_c_max_findings")):
        raise GroupCSemanticError("Group-C finding bound exceeded")
    if len(refs) > int(config.parameter("max_evidence_refs")):
        raise GroupCSemanticError("Group-C evidence reference bound exceeded")
    statuses = {finding.status for finding in findings}
    if statuses and statuses <= {SpecialistStatus.SUCCESS}:
        status, reason = SpecialistStatus.SUCCESS, "all configured Group-C interpretations resolved deterministically"
    elif not refs and SpecialistStatus.UNAVAILABLE_INPUT in statuses:
        status, reason = SpecialistStatus.UNAVAILABLE_INPUT, "required Group-C authoritative input surface is unavailable"
    elif statuses <= {SpecialistStatus.INSUFFICIENT_DATA}:
        status, reason = SpecialistStatus.INSUFFICIENT_DATA, "required Group-C facts are insufficient"
    elif statuses <= {SpecialistStatus.UNAVAILABLE_INPUT, SpecialistStatus.INSUFFICIENT_DATA}:
        status, reason = SpecialistStatus.UNAVAILABLE_INPUT, "required Group-C authoritative input is unavailable or insufficient"
    else:
        status, reason = SpecialistStatus.PARTIAL, "some Group-C interpretations are unavailable, invalid, or insufficient"
    output = SpecialistOutput(
        specialist_id, "1.0.0", snapshot.snapshot_id, snapshot.version,
        config.ref(), status, reason, tuple(findings), refs,
    )
    canonical_json(output.as_dict())
    return output


def analyze_s03(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    symbols = _csv(config, "group_c_symbols", upper=True)
    timeframes = _csv(config, "group_c_timeframes", lower=True)
    venues = _csv(config, "group_c_venues", upper=True)
    findings: list[SpecialistFinding] = []

    for symbol in symbols:
        for timeframe in timeframes:
            for venue in venues:
                facts = _indicator_facts(snapshot, symbol, timeframe, venue)
                latest = {name: _single_latest(rows, name) for name, rows in facts.items()}
                missing = tuple(name for name, fact in latest.items() if fact is None)
                refs = _refs(tuple(fact for fact in latest.values() if fact is not None)) if any(latest.values()) else ()

                if missing:
                    findings.append(SpecialistFinding(
                        f"VOLUME:{symbol}:{venue}:{timeframe}:STATE",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA", "missing_facts": missing},
                        "authoritative P4 volume/RVOL facts are incomplete for the governed timeframe",
                        evidence_refs=refs,
                    ))
                    continue

                statuses = {fact.status for fact in latest.values()}
                if statuses != {FactStatus.VALID}:
                    non_valid = tuple(
                        name for name, fact in latest.items() if fact is not None and fact.status is not FactStatus.VALID
                    )
                    state = "UNAVAILABLE_INPUT" if any(f.status is FactStatus.UNAVAILABLE for f in latest.values()) else "INSUFFICIENT_DATA"
                    findings.append(SpecialistFinding(
                        f"VOLUME:{symbol}:{venue}:{timeframe}:STATE",
                        SpecialistStatus.UNAVAILABLE_INPUT if state == "UNAVAILABLE_INPUT" else SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": state, "non_valid_facts": non_valid},
                        "authoritative P4 volume/RVOL facts contain an explicit non-VALID state; no fallback value is inferred",
                        evidence_refs=refs,
                    ))
                    continue

                values = {name: _value_from_indicator(fact, name) for name, fact in latest.items()}
                spike = values["VOLUME_SPIKE"] == Decimal("1")
                climax = values["VOLUME_CLIMAX"] == Decimal("1")
                volume_state = "CLIMAX" if climax else "SPIKE" if spike else "NORMAL"

                findings.append(SpecialistFinding(
                    f"VOLUME:{symbol}:{venue}:{timeframe}:CONDITION",
                    SpecialistStatus.SUCCESS,
                    {
                        "state": volume_state,
                        "volume": values["VOLUME_SMA"],
                        "rvol": values["RVOL"],
                        "spike": values["VOLUME_SPIKE"],
                        "climax": values["VOLUME_CLIMAX"],
                    },
                    "volume condition is deterministically classified from authoritative persisted P4 facts",
                    evidence_refs=refs,
                ))

                candles = _candle_facts(snapshot, symbol, timeframe, venue)
                if len(candles) < 2:
                    findings.append(SpecialistFinding(
                        f"VOLUME:{symbol}:{venue}:{timeframe}:PRICE_CONTEXT",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA"},
                        "at least two authoritative closed candles are required for volume/price movement context",
                        evidence_refs=_refs(candles),
                    ))
                else:
                    previous, current = candles[-2], candles[-1]
                    previous_close = _decimal(_payload(previous)["close"], "previous candle close")
                    current_close = _decimal(_payload(current)["close"], "current candle close")
                    direction = "UP" if current_close > previous_close else "DOWN" if current_close < previous_close else "FLAT"
                    findings.append(SpecialistFinding(
                        f"VOLUME:{symbol}:{venue}:{timeframe}:PRICE_CONTEXT",
                        SpecialistStatus.SUCCESS,
                        {
                            "state": "SUCCESS",
                            "price_change": current_close - previous_close,
                            "direction": direction,
                            "current_close": current_close,
                        },
                        "latest two closed authoritative candles provide deterministic price-movement context; no new indicator is calculated",
                        evidence_refs=_refs((previous, current)),
                    ))
    return _base(snapshot, config, "S-03", findings)


def _profile_metric(payload: Mapping[str, Any], name: str) -> Decimal | None:
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return None
    metric = facts.get(name)
    if not isinstance(metric, Mapping):
        return None
    value = metric.get("value")
    if value is None:
        return None
    return _decimal(value, f"VolumeProfile.{name}")


def _profile_interval(payload: Mapping[str, Any]) -> tuple[datetime, datetime]:
    interval = payload.get("profile_interval")
    if not isinstance(interval, Mapping):
        raise GroupCSemanticError("Volume Profile payload lacks profile_interval")
    start = interval.get("start")
    end = interval.get("end")
    if isinstance(start, str):
        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if isinstance(end, str):
        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    start, end = _utc(start, "profile interval start"), _utc(end, "profile interval end")
    if end <= start:
        raise GroupCSemanticError("Volume Profile interval is not positive")
    return start, end


def _profile_facts(snapshot: InputSnapshot, symbol: str, timeframe: str, venue: str) -> tuple[Any, ...]:
    rows = []
    for fact in snapshot.facts:
        if _source_table(fact) != PROFILE_TABLE:
            continue
        if not _context(fact, symbol, timeframe, venue):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupCSemanticError("post-boundary Volume Profile evidence reached specialist execution")
        rows.append(fact)
    return tuple(rows)


def _current_price(candles: tuple[Any, ...]) -> tuple[Decimal, Any] | None:
    if not candles:
        return None
    current = candles[-1]
    return _decimal(_payload(current)["close"], "current candle close"), current


def _distance(price: Decimal, level: Decimal) -> Decimal:
    return abs(price - level)


def analyze_s17(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    symbols = _csv(config, "group_c_symbols", upper=True)
    timeframes = _csv(config, "group_c_timeframes", lower=True)
    venues = _csv(config, "group_c_venues", upper=True)
    findings: list[SpecialistFinding] = []

    for symbol in symbols:
        for timeframe in timeframes:
            for venue in venues:
                sessions = tuple(
                    fact for fact in _profile_facts(snapshot, symbol, timeframe, venue)
                    if fact.status is FactStatus.VALID
                )
                if not sessions:
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:STATE",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA", "reason": "no authoritative persisted Volume Profile session"},
                        "no authoritative persisted Volume Profile session is available inside the Snapshot boundary",
                        evidence_refs=(),
                    ))
                    continue

                parsed = []
                for fact in sessions:
                    start, end = _profile_interval(_payload(fact))
                    if end <= snapshot.as_of:
                        parsed.append((end, start, fact))
                if not parsed:
                    refs = _refs(sessions)
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:STATE",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA", "reason": "no completed persisted session is at or before as_of"},
                        "Volume Profile session evidence exists but no completed session satisfies the snapshot boundary",
                        evidence_refs=refs,
                    ))
                    continue

                parsed.sort(key=lambda item: (item[0], item[1], str((item[2].metadata or {}).get("record_id"))))
                current_end, current_start, current = parsed[-1]
                current_payload = _payload(current)
                current_poc = _profile_metric(current_payload, "POC")
                current_vah = _profile_metric(current_payload, "VAH")
                current_val = _profile_metric(current_payload, "VAL")
                current_hvn = _profile_metric(current_payload, "HVN")
                current_lvn = _profile_metric(current_payload, "LVN")
                current_candles = tuple(
                    fact for fact in _candle_facts(snapshot, symbol, timeframe, venue)
                    if current_start <= _candle_close_time(fact) < current_end
                )
                price = _current_price(_candle_facts(snapshot, symbol, timeframe, venue))
                session_refs = _refs((current,))
                if price is None:
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:POSITION",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA", "reason": "current authoritative closed price is unavailable"},
                        "current price is required for Value Area position and nearest-level interpretation",
                        evidence_refs=session_refs,
                    ))
                else:
                    current_price, price_fact = price
                    levels = {
                        "POC": current_poc,
                        "VAH": current_vah,
                        "VAL": current_val,
                        "HVN": current_hvn,
                        "LVN": current_lvn,
                    }
                    available = {name: level for name, level in levels.items() if level is not None}
                    if current_val is not None and current_vah is not None:
                        position = "INSIDE" if current_val <= current_price <= current_vah else "ABOVE" if current_price > current_vah else "BELOW"
                    else:
                        position = "INSUFFICIENT_DATA"
                    nearest = None
                    if available:
                        nearest_name, nearest_level = min(available.items(), key=lambda item: (_distance(current_price, item[1]), item[0]))
                        nearest = {"level": nearest_name, "value": nearest_level, "distance": _distance(current_price, nearest_level)}
                    refs = _refs((current, price_fact))
                    status = SpecialistStatus.SUCCESS if position != "INSUFFICIENT_DATA" and nearest is not None else SpecialistStatus.INSUFFICIENT_DATA
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:POSITION",
                        status,
                        {
                            "state": position,
                            "current_price": current_price,
                            "nearest": nearest,
                            "levels": available,
                            "session_start": current_start,
                            "session_end": current_end,
                        },
                        "current price is interpreted against persisted P4 Value Area and profile levels without recomputing Volume Profile mathematics",
                        evidence_refs=refs,
                    ))

                if current_poc is None:
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:POC",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA"},
                        "authoritative current-session POC is unavailable",
                        evidence_refs=session_refs,
                    ))
                else:
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:POC",
                        SpecialistStatus.SUCCESS,
                        {"state": "AVAILABLE", "poc": current_poc},
                        "current-session POC is consumed directly from persisted P4 Volume Profile truth",
                        evidence_refs=session_refs,
                    ))

                if len(parsed) < 2:
                    findings.append(SpecialistFinding(
                        f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:PRIOR_POC_RETURN",
                        SpecialistStatus.INSUFFICIENT_DATA,
                        {"state": "INSUFFICIENT_DATA"},
                        "at least two persisted Volume Profile sessions are required for prior-session POC return semantics",
                        evidence_refs=session_refs,
                    ))
                else:
                    _, prior_start, prior = parsed[-2]
                    prior_payload = _payload(prior)
                    prior_poc = _profile_metric(prior_payload, "POC")
                    if prior_poc is None:
                        findings.append(SpecialistFinding(
                            f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:PRIOR_POC_RETURN",
                            SpecialistStatus.INSUFFICIENT_DATA,
                            {"state": "INSUFFICIENT_DATA"},
                            "prior persisted session exists but its authoritative POC is unavailable",
                            evidence_refs=_refs((prior, current)),
                        ))
                    else:
                        touched = False
                        for candle in current_candles:
                            payload = _payload(candle)
                            high = _decimal(payload["high"], "candle.high")
                            low = _decimal(payload["low"], "candle.low")
                            if low <= prior_poc <= high:
                                touched = True
                                break
                        findings.append(SpecialistFinding(
                            f"VOLUME_PROFILE:{symbol}:{venue}:{timeframe}:PRIOR_POC_RETURN",
                            SpecialistStatus.SUCCESS if current_candles else SpecialistStatus.INSUFFICIENT_DATA,
                            {
                                "state": "RETURNED" if touched else "NOT_RETURNED",
                                "prior_poc": prior_poc,
                                "current_session_start": current_start,
                                "current_session_end": current_end,
                            },
                            "prior-session POC return is evaluated only from persisted prior/current Volume Profile sessions and authoritative current-session closed-candle ranges",
                            evidence_refs=_refs((prior, current, *current_candles)),
                        ))

    return _base(snapshot, config, "S-17", findings)


ANALYSTS = {"S-03": analyze_s03, "S-17": analyze_s17}
