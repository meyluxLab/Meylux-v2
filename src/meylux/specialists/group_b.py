"""Deterministic Phase-5 Group-B specialists: S-02, S-11 and S-12.

The specialists consume only authoritative Stage-1 InputSnapshot facts. They
interpret persisted P4 structure/candle/depth facts and never recreate P4
mathematical truth or consume another specialist's output.
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


class GroupBSemanticError(NonRetryableProcessingError):
    """Malformed Group-B input or violated authoritative evidence contract."""


STRUCTURE_EVENTS = {
    "SWING_HIGH", "SWING_LOW", "HH", "HL", "LH", "LL",
    "BOS", "CHOCH", "MSS", "STRUCTURE_STATE",
}
CONFIRMED_EVENTS = STRUCTURE_EVENTS - {"STRUCTURE_STATE"}
PROTECTED_EVENTS = {"BOS", "CHOCH", "MSS"}
ZONE_TABLE = "meylux.market_structure_zones"
EVENT_TABLE = "meylux.market_structure_events"
CANDLE_TABLE = "meylux.canonical_candles"
DEPTH_TABLE = "meylux.canonical_orderbook_depth"
ZONE_TYPES = {"FVG", "ORDER_BLOCK", "BREAKER", "LIQUIDITY_POOL"}
ACTIVE_LIFECYCLES = {"ACTIVE"}


def _decimal(value: Any, field: str = "value") -> Decimal:
    if isinstance(value, bool) or isinstance(value, float) or value is None:
        raise GroupBSemanticError(f"{field} must be a finite Decimal-compatible value")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise GroupBSemanticError(f"{field} must be a finite Decimal-compatible value") from exc
    if not result.is_finite():
        raise GroupBSemanticError(f"{field} must be finite")
    return result


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise GroupBSemanticError(f"{field} must be explicit UTC")
    return value


def _csv(config: Any, key: str, *, upper: bool = False, lower: bool = False) -> tuple[str, ...]:
    raw = config.parameter(key)
    if not isinstance(raw, str) or not raw.strip():
        raise GroupBSemanticError(f"configuration parameter {key} must be non-empty")
    parts = tuple(piece.strip() for piece in raw.split(","))
    if any(not piece for piece in parts) or len(set(parts)) != len(parts):
        raise GroupBSemanticError(f"configuration parameter {key} contains empty or duplicate values")
    if upper:
        return tuple(piece.upper() for piece in parts)
    if lower:
        return tuple(piece.lower() for piece in parts)
    return parts


def _source_table(fact: Any) -> str:
    value = (fact.metadata or {}).get("source_table")
    if not isinstance(value, str) or not value.strip():
        raise GroupBSemanticError("authoritative Group-B fact lacks source_table")
    return value.strip().lower()


def _context(fact: Any, symbol: str, timeframe: str, venue: str) -> bool:
    metadata = fact.metadata or {}
    raw_symbol = metadata.get("symbol")
    raw_timeframe = metadata.get("timeframe")
    raw_venue = metadata.get("venue")
    if not all(isinstance(value, str) and value.strip() for value in (raw_symbol, raw_timeframe, raw_venue)):
        raise GroupBSemanticError("Group-B fact lacks explicit symbol/timeframe/venue context")
    normalized_symbol = raw_symbol.strip().upper()
    normalized_venue = raw_venue.strip().upper()
    if ":" in normalized_symbol:
        qualified_venue, qualified_symbol = normalized_symbol.split(":", 1)
        if qualified_symbol != symbol:
            return False
        # A qualified instrument is authoritative venue context. A fact whose
        # explicit venue disagrees with that qualification is intrinsically
        # contradictory and must remain rejected. A well-formed fact belonging
        # to another configured venue is simply outside this venue's candidate
        # set and must not poison the current venue evaluation.
        if qualified_venue != normalized_venue:
            raise GroupBSemanticError("qualified instrument conflicts with explicit venue")
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
        raise GroupBSemanticError("metadata knowledge_time conflicts with SnapshotFact")
    for ref in fact.evidence_refs:
        required = (ref.source_family, ref.record_id, ref.identity_hash, ref.event_time,
                    ref.knowledge_time, ref.timeframe, ref.venue)
        if any(value is None or (isinstance(value, str) and not value.strip()) for value in required):
            raise GroupBSemanticError("Group-B EvidenceRef is incomplete")
        if ref.record_id != metadata.get("record_id") or ref.identity_hash != metadata.get("identity_hash"):
            raise GroupBSemanticError("EvidenceRef does not resolve to the authoritative record identity")
        if ref.event_time != event_time or ref.knowledge_time != fact.knowledge_time:
            raise GroupBSemanticError("EvidenceRef timing does not match authoritative fact")
        if ref.timeframe.lower() != timeframe or ref.venue.upper() != venue:
            raise GroupBSemanticError("EvidenceRef context conflicts with authoritative fact")
    return True


def _refs(facts: tuple[Any, ...] | list[Any]) -> tuple[EvidenceRef, ...]:
    unique: dict[str, EvidenceRef] = {}
    for fact in facts:
        if not fact.evidence_refs:
            raise GroupBSemanticError("authoritative Group-B fact lacks EvidenceRef")
        for ref in fact.evidence_refs:
            unique[ref.evidence_id] = ref
    return tuple(unique[key] for key in sorted(unique))


def _payload(fact: Any) -> Mapping[str, Any]:
    if not isinstance(fact.value, Mapping):
        raise GroupBSemanticError("authoritative Group-B payload must be a mapping")
    return fact.value


def _valid(fact: Any) -> bool:
    return fact.status is FactStatus.VALID


def _facts(snapshot: InputSnapshot, table: str, symbol: str, timeframe: str, venue: str) -> tuple[Any, ...]:
    result = []
    for fact in snapshot.facts:
        if _source_table(fact) != table:
            continue
        if not _context(fact, symbol, timeframe, venue):
            continue
        if fact.knowledge_time > snapshot.as_of:
            raise GroupBSemanticError("post-boundary Group-B evidence reached specialist execution")
        result.append(fact)
    return tuple(result)


def _event_time(fact: Any) -> datetime:
    return _utc((fact.metadata or {}).get("event_time"), "event_time")


def _close_time(fact: Any) -> datetime:
    payload = _payload(fact)
    raw = payload.get("close_time")
    if isinstance(raw, str):
        try:
            raw = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise GroupBSemanticError("candle close_time is not valid ISO-8601") from exc
    return _utc(raw, "candle.close_time")


def _close(fact: Any) -> Decimal:
    payload = _payload(fact)
    if "close" not in payload:
        raise GroupBSemanticError("candle payload missing close")
    return _decimal(payload["close"], "candle.close")


def _ohlc(fact: Any) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    payload = _payload(fact)
    try:
        return tuple(_decimal(payload[name], f"candle.{name}") for name in ("open", "high", "low", "close"))  # type: ignore[return-value]
    except KeyError as exc:
        raise GroupBSemanticError(f"candle payload missing {exc.args[0]}") from exc


def _finding(code: str, value: Any, reason: str, refs: tuple[EvidenceRef, ...],
             status: SpecialistStatus) -> SpecialistFinding:
    return SpecialistFinding(code, status, value, reason, evidence_refs=refs)


def _base(snapshot: InputSnapshot, config: Any, specialist_id: str,
          findings: list[SpecialistFinding]) -> SpecialistOutput:
    refs = tuple(sorted({r.evidence_id: r for finding in findings for r in finding.evidence_refs}.values(),
                        key=lambda ref: ref.evidence_id))
    limit = int(config.parameter("group_b_max_findings"))
    if len(findings) > limit:
        raise GroupBSemanticError("Group-B finding bound exceeded")
    if len(refs) > int(config.parameter("max_evidence_refs")):
        raise GroupBSemanticError("Group-B evidence reference bound exceeded")
    statuses = {finding.status for finding in findings}
    if statuses and statuses <= {SpecialistStatus.SUCCESS}:
        status, reason = SpecialistStatus.SUCCESS, "all configured Group-B interpretations resolved deterministically"
    elif not refs and SpecialistStatus.UNAVAILABLE_INPUT in statuses:
        status, reason = SpecialistStatus.UNAVAILABLE_INPUT, "required Group-B authoritative input surface is unavailable"
    elif statuses <= {SpecialistStatus.INSUFFICIENT_DATA}:
        status, reason = SpecialistStatus.INSUFFICIENT_DATA, "required Group-B facts are insufficient"
    elif statuses <= {SpecialistStatus.UNAVAILABLE_INPUT, SpecialistStatus.INSUFFICIENT_DATA}:
        status, reason = SpecialistStatus.UNAVAILABLE_INPUT, "required Group-B authoritative input is unavailable or insufficient"
    else:
        status, reason = SpecialistStatus.PARTIAL, "some Group-B interpretations are unavailable, invalid, or insufficient"
    output = SpecialistOutput(
        specialist_id, "1.0.0", snapshot.snapshot_id, snapshot.version,
        config.ref(), status, reason, tuple(findings), refs,
    )
    canonical_json(output.as_dict())
    return output


def _nearest_zones(zone_facts: tuple[Any, ...], price: Decimal, *,
                   zone_type: str | None = None) -> tuple[dict[str, Any], ...]:
    candidates = []
    for fact in zone_facts:
        if not _valid(fact):
            continue
        payload = _payload(fact)
        if zone_type is not None and str(payload.get("event_type", "")).upper() != zone_type:
            continue
        lifecycle = str(payload.get("lifecycle") or "").upper()
        if lifecycle not in ACTIVE_LIFECYCLES:
            continue
        lower_raw, upper_raw = payload.get("lower_bound"), payload.get("upper_bound")
        if lower_raw is None and upper_raw is None:
            continue
        lower = _decimal(lower_raw, "zone.lower_bound") if lower_raw is not None else None
        upper = _decimal(upper_raw, "zone.upper_bound") if upper_raw is not None else None
        if lower is not None and upper is not None and lower > upper:
            raise GroupBSemanticError("zone lower_bound exceeds upper_bound")
        distance = Decimal("0")
        if lower is not None and price < lower:
            distance = lower - price
        elif upper is not None and price > upper:
            distance = price - upper
        candidates.append((
            distance,
            _event_time(fact),
            str((fact.metadata or {}).get("record_id")),
            {
                "record_id": (fact.metadata or {}).get("record_id"),
                "zone_type": (fact.metadata or {}).get("source_table"),
                "original_event_type": payload.get("event_type"),
                "lower_bound": lower,
                "upper_bound": upper,
                "distance": distance,
                "lifecycle": lifecycle,
                "formation_time": payload.get("zone_formation_time") or payload.get("event_location"),
                "direction": payload.get("direction"),
            },
            fact,
        ))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return tuple(item[3] for item in candidates)


def analyze_s02(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    symbols = _csv(config, "group_a_symbols", upper=True)
    timeframes = _csv(config, "group_a_timeframes", lower=True)
    venues = _csv(config, "group_a_venues", upper=True)
    findings: list[SpecialistFinding] = []
    for symbol in symbols:
        for venue in venues:
            for timeframe in timeframes:
                events = _facts(snapshot, EVENT_TABLE, symbol, timeframe, venue)
                zones = _facts(snapshot, ZONE_TABLE, symbol, timeframe, venue)
                candles = _facts(snapshot, CANDLE_TABLE, symbol, timeframe, venue)
                refs = _refs(events + zones + candles) if events or zones or candles else ()
                state_events = tuple(
                    fact for fact in events
                    if str(_payload(fact).get("event_type", "")).upper() == "STRUCTURE_STATE"
                    and _valid(fact)
                )
                if state_events:
                    latest_state = max(state_events, key=lambda fact: (_utc(fact.knowledge_time, "knowledge_time"), _event_time(fact),
                                                                       str((fact.metadata or {}).get("record_id"))))
                    state_payload = _payload(latest_state)
                    dominant = str(state_payload.get("structural_state") or "UNCONFIRMED").upper()
                    state_ref = _refs((latest_state,))
                    state_status = SpecialistStatus.SUCCESS
                    state_reason = "latest persisted STRUCTURE_STATE is authoritative and inside snapshot boundary"
                else:
                    dominant, state_ref = "INSUFFICIENT_DATA", ()
                    state_status = SpecialistStatus.INSUFFICIENT_DATA
                    state_reason = "no authoritative persisted STRUCTURE_STATE is available"
                findings.append(_finding(
                    f"STRUCTURE:{symbol}:{venue}:{timeframe}:STATE",
                    {"state": dominant, "knowledge_time": latest_state.knowledge_time if state_events else None},
                    state_reason, state_ref, state_status,
                ))

                confirmed = tuple(
                    fact for fact in events
                    if str(_payload(fact).get("event_type", "")).upper() in CONFIRMED_EVENTS
                    and _valid(fact)
                )
                if confirmed:
                    latest_confirmed = max(
                        confirmed,
                        key=lambda fact: (_utc(fact.knowledge_time, "knowledge_time"), _event_time(fact),
                                           str((fact.metadata or {}).get("record_id"))),
                    )
                    cp = _payload(latest_confirmed)
                    confirmed_value = {
                        "event_type": cp.get("event_type"),
                        "record_id": (latest_confirmed.metadata or {}).get("record_id"),
                        "event_time": _event_time(latest_confirmed),
                        "knowledge_time": latest_confirmed.knowledge_time,
                        "level": _decimal(cp["level"], "event.level") if cp.get("level") is not None else None,
                        "direction": cp.get("direction"),
                    }
                    confirmed_refs = _refs((latest_confirmed,))
                    confirmed_status = SpecialistStatus.SUCCESS
                    confirmed_reason = "latest confirmed persisted structural event satisfies knowledge_time <= snapshot.as_of"
                else:
                    confirmed_value, confirmed_refs = {"state": "INSUFFICIENT_DATA"}, ()
                    confirmed_status = SpecialistStatus.INSUFFICIENT_DATA
                    confirmed_reason = "no confirmed persisted structural event is available"
                findings.append(_finding(
                    f"STRUCTURE:{symbol}:{venue}:{timeframe}:LATEST_CONFIRMED",
                    confirmed_value, confirmed_reason, confirmed_refs, confirmed_status,
                ))

                protected = tuple(
                    fact for fact in events
                    if str(_payload(fact).get("event_type", "")).upper() in PROTECTED_EVENTS
                    and _payload(fact).get("level") is not None and _valid(fact)
                )
                if protected and candles:
                    latest_protected = max(
                        protected,
                        key=lambda fact: (_utc(fact.knowledge_time, "knowledge_time"), _event_time(fact),
                                           str((fact.metadata or {}).get("record_id"))),
                    )
                    candle_times = []
                    for candle in candles:
                        close = _close_time(candle)
                        if close <= snapshot.as_of:
                            candle_times.append((close, candle))
                    if candle_times:
                        current_close_time, current = max(candle_times, key=lambda item: (item[0], str((item[1].metadata or {}).get("record_id"))))
                        current_price = _close(current)
                        protected_level = _decimal(_payload(latest_protected)["level"], "protected.level")
                        relation = "ABOVE" if current_price > protected_level else "BELOW" if current_price < protected_level else "AT"
                        difference = current_price - protected_level
                        pstatus = SpecialistStatus.SUCCESS
                        preason = "current closed-candle price compared with latest protected P4 structural level using Decimal arithmetic"
                        pref = _refs((latest_protected, current))
                    else:
                        relation, difference = "INSUFFICIENT_DATA", None
                        pstatus, preason, pref = SpecialistStatus.INSUFFICIENT_DATA, "no closed candle is eligible at snapshot.as_of", _refs((latest_protected,))
                else:
                    relation, difference = "INSUFFICIENT_DATA", None
                    pstatus, preason = SpecialistStatus.INSUFFICIENT_DATA, "protected structural level and current closed price are both required"
                    pref = _refs((latest_protected,)) if protected else ()
                findings.append(_finding(
                    f"STRUCTURE:{symbol}:{venue}:{timeframe}:PROTECTED_LEVEL_RELATION",
                    {"relationship": relation, "difference": difference,
                     "protected_level": _decimal(_payload(latest_protected)["level"], "protected.level") if protected else None},
                    preason, pref, pstatus,
                ))

                if candles:
                    current_times = [(_close_time(candle), candle) for candle in candles if _close_time(candle) <= snapshot.as_of]
                    current_price = _close(max(current_times, key=lambda item: item[0])[1]) if current_times else None
                else:
                    current_price = None
                if current_price is None:
                    zone_value, zone_status, zone_reason, zone_refs = {"state": "INSUFFICIENT_DATA", "zones": ()}, SpecialistStatus.INSUFFICIENT_DATA, \
                        "current closed-candle price is required to rank applicable unmitigated zones", ()
                else:
                    nearest = _nearest_zones(zones, current_price)
                    zone_refs = _refs(zones) if nearest else ()
                    zone_value, zone_status, zone_reason = {"state": "SUCCESS", "zones": nearest}, SpecialistStatus.SUCCESS, \
                        "nearest active persisted P4 zones ranked by Decimal distance to current closed price"
                findings.append(_finding(
                    f"STRUCTURE:{symbol}:{venue}:{timeframe}:NEAREST_UNMITIGATED_ZONES",
                    zone_value, zone_reason, zone_refs, zone_status,
                ))
    return _base(snapshot, config, "S-02", findings)


def _candle_records(snapshot: InputSnapshot, symbol: str, timeframe: str, venue: str) -> tuple[Any, ...]:
    facts = _facts(snapshot, CANDLE_TABLE, symbol, timeframe, venue)
    ordered = []
    seen_close: dict[datetime, Any] = {}
    for fact in facts:
        if not _valid(fact):
            continue
        close = _close_time(fact)
        if close > snapshot.as_of or fact.knowledge_time > snapshot.as_of:
            continue
        if close in seen_close:
            raise GroupBSemanticError("multiple authoritative candles share the same closed boundary")
        seen_close[close] = fact
    ordered = sorted(seen_close.values(), key=lambda fact: (_close_time(fact), str((fact.metadata or {}).get("record_id"))))
    return tuple(ordered)


def _pattern_pin_bar(current: tuple[Decimal, Decimal, Decimal, Decimal], wick_ratio: Decimal,
                     body_ratio: Decimal, opposite_ratio: Decimal) -> str | None:
    opened, high, low, close = current
    body = abs(close - opened)
    full = high - low
    if full <= 0 or body <= 0 or body / full > body_ratio:
        return None
    upper = high - max(opened, close)
    lower = min(opened, close) - low
    if lower >= wick_ratio * body and upper <= opposite_ratio * body:
        return "BULLISH"
    if upper >= wick_ratio * body and lower <= opposite_ratio * body:
        return "BEARISH"
    return None


def _pattern_engulfing(previous: tuple[Decimal, Decimal, Decimal, Decimal],
                       current: tuple[Decimal, Decimal, Decimal, Decimal],
                       min_ratio: Decimal) -> str | None:
    po, _, _, pc = previous
    co, _, _, cc = current
    previous_body = abs(pc - po)
    current_body = abs(cc - co)
    if previous_body <= 0 or current_body < previous_body * min_ratio:
        return None
    if pc < po and cc > co and co <= pc and cc >= po:
        return "BULLISH"
    if pc > po and cc < co and co >= pc and cc <= po:
        return "BEARISH"
    return None


def _pattern_inside_bar(previous: tuple[Decimal, Decimal, Decimal, Decimal],
                         current: tuple[Decimal, Decimal, Decimal, Decimal]) -> bool:
    _, previous_high, previous_low, _ = previous
    _, current_high, current_low, _ = current
    return current_high <= previous_high and current_low >= previous_low


def _zone_rejection(candle: tuple[Decimal, Decimal, Decimal, Decimal],
                    zone: Any, close_ratio: Decimal) -> bool:
    opened, high, low, close = candle
    payload = _payload(zone)
    if payload.get("direction") not in {"bullish", "bearish", "BULLISH", "BEARISH"}:
        return False
    lower_raw, upper_raw = payload.get("lower_bound"), payload.get("upper_bound")
    if lower_raw is None or upper_raw is None:
        return False
    lower, upper = _decimal(lower_raw, "zone.lower_bound"), _decimal(upper_raw, "zone.upper_bound")
    if lower > upper or high < lower or low > upper:
        return False
    span = high - low
    if span <= 0:
        return False
    position = (close - low) / span
    direction = str(payload["direction"]).lower()
    if direction == "bullish":
        return close > upper and position >= close_ratio
    return close < lower and position <= (Decimal("1") - close_ratio)


def analyze_s11(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    symbols = _csv(config, "group_a_symbols", upper=True)
    timeframes = _csv(config, "group_a_timeframes", lower=True)
    venues = _csv(config, "group_a_venues", upper=True)
    wick_ratio = _decimal(config.parameter("price_action_pin_wick_to_body_ratio"))
    body_ratio = _decimal(config.parameter("price_action_pin_max_body_range_ratio"))
    opposite_ratio = _decimal(config.parameter("price_action_pin_max_opposite_wick_ratio"))
    engulf_ratio = _decimal(config.parameter("price_action_engulfing_min_body_ratio"))
    rejection_ratio = _decimal(config.parameter("price_action_zone_rejection_close_position"))
    if wick_ratio <= 0 or body_ratio <= 0 or body_ratio > 1 or opposite_ratio < 0 or engulf_ratio <= 0 or not Decimal("0") <= rejection_ratio <= Decimal("1"):
        raise GroupBSemanticError("invalid S-11 price-action configuration")
    findings: list[SpecialistFinding] = []
    for symbol in symbols:
        for venue in venues:
            for timeframe in timeframes:
                candles = _candle_records(snapshot, symbol, timeframe, venue)
                zones = _facts(snapshot, ZONE_TABLE, symbol, timeframe, venue)
                if not candles:
                    for pattern in ("PIN_BAR", "ENGULFING", "INSIDE_BAR", "ZONE_REJECTION"):
                        findings.append(_finding(
                            f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:{pattern}",
                            {"state": "UNAVAILABLE_INPUT", "pattern_time": None},
                            "authoritative closed-candle facts are unavailable in the Stage-1 InputSnapshot",
                            (), SpecialistStatus.UNAVAILABLE_INPUT,
                        ))
                    continue
                if len(candles) < 2:
                    refs = _refs(candles)
                    for pattern in ("PIN_BAR", "ENGULFING", "INSIDE_BAR"):
                        findings.append(_finding(
                            f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:{pattern}",
                            {"state": "INSUFFICIENT_DATA", "pattern_time": _close_time(candles[-1])},
                            "at least two authoritative closed candles are required",
                            refs, SpecialistStatus.INSUFFICIENT_DATA,
                        ))
                else:
                    previous, current = candles[-2], candles[-1]
                    previous_ohlc, current_ohlc = _ohlc(previous), _ohlc(current)
                    refs = _refs((previous, current))
                    pin = _pattern_pin_bar(current_ohlc, wick_ratio, body_ratio, opposite_ratio)
                    findings.append(_finding(
                        f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:PIN_BAR",
                        {"state": pin or "NOT_DETECTED", "pattern_time": _close_time(current),
                         "wick_to_body_ratio": wick_ratio, "max_body_range_ratio": body_ratio},
                        "PIN_BAR uses only the latest two closed authoritative candles and configured Decimal thresholds",
                        refs, SpecialistStatus.SUCCESS,
                    ))
                    engulf = _pattern_engulfing(previous_ohlc, current_ohlc, engulf_ratio)
                    findings.append(_finding(
                        f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:ENGULFING",
                        {"state": engulf or "NOT_DETECTED", "pattern_time": _close_time(current),
                         "min_body_ratio": engulf_ratio},
                        "ENGULFING compares adjacent closed candle bodies using configured inclusive size semantics",
                        refs, SpecialistStatus.SUCCESS,
                    ))
                    inside = _pattern_inside_bar(previous_ohlc, current_ohlc)
                    findings.append(_finding(
                        f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:INSIDE_BAR",
                        {"state": "DETECTED" if inside else "NOT_DETECTED", "pattern_time": _close_time(current)},
                        "INSIDE_BAR requires current high/low to remain within the immediately preceding closed candle",
                        refs, SpecialistStatus.SUCCESS,
                    ))
                zone_refs = _refs(zones) if zones else ()
                active_zones = tuple(
                    zone for zone in zones if _valid(zone) and str(_payload(zone).get("lifecycle") or "").upper() == "ACTIVE"
                    and _payload(zone).get("lower_bound") is not None and _payload(zone).get("upper_bound") is not None
                )
                if not active_zones:
                    findings.append(_finding(
                        f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:ZONE_REJECTION",
                        {"state": "INSUFFICIENT_DATA", "pattern_time": _close_time(candles[-1])},
                        "authoritative persisted directional zones with complete bounds are required for ZONE_REJECTION",
                        zone_refs, SpecialistStatus.INSUFFICIENT_DATA,
                    ))
                else:
                    matches = [
                        zone for zone in active_zones
                        if _zone_rejection(_ohlc(candles[-1]), zone, rejection_ratio)
                    ]
                    refs = _refs((candles[-1], *matches))
                    findings.append(_finding(
                        f"PRICE_ACTION:{symbol}:{venue}:{timeframe}:ZONE_REJECTION",
                        {"state": "DETECTED" if matches else "NOT_DETECTED",
                         "pattern_time": _close_time(candles[-1]),
                         "zone_record_ids": [z.metadata.get("record_id") for z in matches]},
                        "ZONE_REJECTION uses authoritative persisted P4 zones; no P5 zone model is created",
                        refs, SpecialistStatus.SUCCESS,
                    ))
    return _base(snapshot, config, "S-11", findings)


def _liquidity_state(zone_facts: tuple[Any, ...], as_of: datetime) -> tuple[tuple[dict[str, Any], ...], tuple[Any, ...]]:
    formations = [
        fact for fact in zone_facts
        if _valid(fact) and str(_payload(fact).get("event_type", "")).upper() == "LIQUIDITY_POOL"
        and str(_payload(fact).get("lifecycle") or "").upper() == "ACTIVE"
    ]
    sweeps = [
        fact for fact in zone_facts
        if _valid(fact) and str(_payload(fact).get("event_type", "")).upper() == "LIQUIDITY_POOL_SWEEP"
    ]
    result = []
    used = []
    for formation in formations:
        formation_id = str((formation.metadata or {}).get("record_id"))
        formation_time = _event_time(formation)
        eligible_sweeps = [
            sweep for sweep in sweeps
            if sweep.knowledge_time <= as_of
            and _event_time(sweep) > formation_time
            and sweep.knowledge_time >= formation.knowledge_time
            and str(_payload(sweep).get("source_event_identity") or "") == formation_id
        ]
        sweep = max(eligible_sweeps, key=lambda fact: (_utc(fact.knowledge_time, "knowledge_time"), _event_time(fact),
                                                        str((fact.metadata or {}).get("record_id"))), default=None)
        payload = _payload(formation)
        lower = _decimal(payload["lower_bound"], "liquidity.lower_bound") if payload.get("lower_bound") is not None else None
        upper = _decimal(payload["upper_bound"], "liquidity.upper_bound") if payload.get("upper_bound") is not None else None
        if lower is None and upper is None:
            level = _decimal(payload["level"], "liquidity.level") if payload.get("level") is not None else None
            lower = upper = level
        if lower is None and upper is None:
            continue
        result.append({
            "record_id": formation_id,
            "lower_bound": lower,
            "upper_bound": upper,
            "direction": payload.get("direction"),
            "state": "SWEPT" if sweep else "UNSWEPT",
            "formation_time": formation_time,
            "sweep_record_id": (sweep.metadata or {}).get("record_id") if sweep else None,
        })
        used.extend((formation, sweep) if sweep else (formation,))
    result.sort(key=lambda item: (
        item["formation_time"], item["record_id"]
    ))
    return tuple(result), tuple(used)


def analyze_s12(snapshot: InputSnapshot, config: Any) -> SpecialistOutput:
    symbols = _csv(config, "group_a_symbols", upper=True)
    timeframes = _csv(config, "group_a_timeframes", lower=True)
    venues = _csv(config, "group_a_venues", upper=True)
    max_zones = int(config.parameter("liquidity_max_zones"))
    if max_zones <= 0:
        raise GroupBSemanticError("liquidity_max_zones must be positive")
    findings: list[SpecialistFinding] = []
    for symbol in symbols:
        for venue in venues:
            for timeframe in timeframes:
                zones = _facts(snapshot, ZONE_TABLE, symbol, timeframe, venue)
                depth = _facts(snapshot, DEPTH_TABLE, symbol, timeframe, venue)
                liquidity, used = _liquidity_state(zones, snapshot.as_of)
                refs = _refs(used) if used else ()
                nearest = []
                current_price = None
                candles = _candle_records(snapshot, symbol, timeframe, venue)
                if candles:
                    current_price = _ohlc(candles[-1])[3]
                    def distance(item):
                        lower, upper = item["lower_bound"], item["upper_bound"]
                        if lower is not None and current_price < lower:
                            return lower - current_price
                        if upper is not None and current_price > upper:
                            return current_price - upper
                        return Decimal("0")
                    nearest = sorted(liquidity, key=lambda item: (distance(item), item["formation_time"], item["record_id"]))[:max_zones]
                if not liquidity:
                    status = SpecialistStatus.INSUFFICIENT_DATA
                    reason = "no persisted liquidity-pool formation is available inside the snapshot boundary"
                    value = {"state": "INSUFFICIENT_DATA", "zones": (), "depth_state": "AVAILABLE" if depth else "PARTIAL"}
                else:
                    status = SpecialistStatus.SUCCESS if depth else SpecialistStatus.PARTIAL
                    reason = "liquidity-pool state uses persisted formation/sweep facts and post-formation knowledge-time ordering"
                    value = {
                        "state": "SUCCESS" if depth else "PARTIAL",
                        "zones": tuple(nearest),
                        "depth_state": "AVAILABLE" if depth else "PARTIAL",
                        "depth_interpretation": "authoritative depth is present" if depth else "depth evidence is unavailable; no depth-dependent conclusion is inferred",
                    }
                    if not candles:
                        status = SpecialistStatus.PARTIAL
                        reason = "liquidity zones are available but current candle evidence is unavailable for nearest-price ranking"
                        value = {**value, "state": "PARTIAL", "nearest_state": "INSUFFICIENT_DATA"}
                findings.append(_finding(
                    f"LIQUIDITY:{symbol}:{venue}:{timeframe}",
                    value, reason, refs, status,
                ))
    return _base(snapshot, config, "S-12", findings)


ANALYSTS = {"S-02": analyze_s02, "S-11": analyze_s11, "S-12": analyze_s12}
