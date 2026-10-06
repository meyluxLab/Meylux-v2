"""Append-only adapter to the existing authoritative Phase-4 quantitative tables."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping, Sequence

from contracts.canonical.trade import CanonicalTrade
from contracts.quantitative.base import CalculationResult
from meylux.quantitative.volume_orderflow_derivatives import VolumeProfileConfig, VolumeProfileAnalysis, VolumeProfileEngine
from meylux.orchestration.engine import QuantOrchestrationResult, TimeframeQuantitativeFacts, TimeframeStructuralFacts


def _json(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal")
        return format(value, "f")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("datetime must be UTC")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if is_dataclass(value):
        return _json(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise TypeError(f"unsupported value: {type(value).__name__}")

_STRUCTURE_INTERVALS = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
_STRUCTURE_CLASSIFICATION_EVENTS = {"SWING_HIGH", "SWING_LOW", "HH", "HL", "LH", "LL"}
_ZONE_LIFECYCLE_EVENTS = {
    "FVG", "FVG_LIFECYCLE", "ORDER_BLOCK", "ORDER_BLOCK_INVALIDATION",
    "BREAKER", "BREAKER_INVALIDATION", "LIQUIDITY_POOL", "LIQUIDITY_POOL_SWEEP",
}
_ZONE_TYPE_BY_EVENT = {
    "FVG": "FVG",
    "FVG_LIFECYCLE": "FVG",
    "ORDER_BLOCK": "ORDER_BLOCK",
    "ORDER_BLOCK_INVALIDATION": "ORDER_BLOCK",
    "BREAKER": "BREAKER",
    "BREAKER_INVALIDATION": "BREAKER",
    "LIQUIDITY_POOL": "LIQUIDITY_POOL",
    "LIQUIDITY_POOL_SWEEP": "LIQUIDITY_POOL",
}


def _knowledge_time(result: QuantOrchestrationResult) -> datetime:
    """Authoritative orchestration knowledge boundary: last closed input candle close."""
    value = result.knowledge_time
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("orchestration knowledge_time must be UTC")
    if value != result.as_of:
        raise ValueError("orchestration knowledge_time must equal as_of")
    return value


def _calc(value: CalculationResult) -> dict[str, Any]:
    return {
        "value": None if value.value is None else format(value.value, "f"),
        "status": value.status.value,
        "reason": value.reason,
        "context": _json(value.context),
    }


class QuantitativePersistence:
    TABLES = {
        "indicator": "meylux.calculated_indicator_vectors",
        "structure_event": "meylux.market_structure_events",
        "structure_zone": "meylux.market_structure_zones",
        "volume_profile": "meylux.volume_profile_sessions",
        "regime": "meylux.market_regime_states",
    }

    def __init__(self, connection: Any):
        self._connection = connection

    @staticmethod
    def _id(material: Mapping[str, Any]) -> str:
        canonical = json.dumps(_json(material), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _indicator_row(
        self,
        *,
        symbol: str,
        timeframe: str,
        event_time: datetime,
        configuration_version: str,
        name: str,
        calculation: CalculationResult,
        provenance: tuple[str, ...],
    ) -> tuple[Any, ...]:
        if not isinstance(name, str) or not name:
            raise ValueError("indicator fact name must be non-empty")
        payload = {"fact_name": name, **_calc(calculation)}
        material = {
            "family": "indicator",
            "name": name,
            "symbol": symbol,
            "timeframe": timeframe,
            "event_time": event_time,
            "version": configuration_version,
            "payload": payload,
        }
        record_id = self._id(material)
        context = calculation.context
        if context is None or not context.source_ref:
            raise ValueError("indicator fact requires explicit calculation context and source_ref")
        if context.source_ref not in provenance:
            raise ValueError("indicator source_ref is not present in orchestration provenance")
        source_ref = context.source_ref
        venue = context.venue_context
        return (
            "indicator", record_id, name, calculation.status.value, calculation.reason,
            calculation.value, context, payload, "1.0.0", symbol, timeframe,
            event_time, source_ref, venue, configuration_version,
        )

    async def _resolve_venue_context(self, provenance: tuple[str, ...]) -> str | None:
        """Resolve venue only from explicit source context in authoritative raw evidence.

        Provider identity is deliberately not promoted to venue. Every provenance
        identifier must resolve to one provider/adapter identity and one explicit,
        non-conflicting venue value from AVAILABLE raw candle evidence. Missing,
        malformed, unknown, or contradictory lineage remains unresolved.
        """
        refs = tuple(dict.fromkeys(provenance))
        if not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            return None
        records = await self._connection.fetch(
            "SELECT DISTINCT provenance_id, provider_id, adapter_id, adapter_version, "
            "payload_json->>'venue' AS venue, payload_json->>'venue_context' AS venue_context, "
            "jsonb_typeof(payload_json->'venue') AS venue_type, "
            "jsonb_typeof(payload_json->'venue_context') AS venue_context_type "
            "FROM meylux.raw_acquisition_events "
            "WHERE provenance_id = ANY($1::text[]) AND event_type = 'CANDLE' "
            "AND acquisition_state = 'AVAILABLE'",
            list(refs),
        )
        by_provenance: dict[str, list[Any]] = {ref: [] for ref in refs}
        for record in records:
            provenance_id = record["provenance_id"]
            if provenance_id in by_provenance:
                by_provenance[provenance_id].append(record)

        resolved: set[str] = set()
        for ref in refs:
            candidates = by_provenance[ref]
            if not candidates:
                return None
            identities = {
                (row["provider_id"], row["adapter_id"], row["adapter_version"])
                for row in candidates
            }
            if len(identities) != 1 or any(
                not isinstance(value, str) or not value.strip()
                for identity in identities for value in identity
            ):
                return None
            source_venues: set[str] = set()
            for row in candidates:
                row_venues: set[str] = set()
                for field, type_field in (
                    ("venue", "venue_type"),
                    ("venue_context", "venue_context_type"),
                ):
                    value = row[field]
                    value_type = row[type_field]
                    if value is None and value_type is None:
                        continue
                    if value_type != "string" or not isinstance(value, str) or not value.strip():
                        return None
                    row_venues.add(value.strip())
                if len(row_venues) > 1:
                    return None
                source_venues.update(row_venues)
            if len(source_venues) != 1:
                return None
            resolved.update(source_venues)
        return next(iter(resolved)) if len(resolved) == 1 else None

    @staticmethod
    def _with_venue_context(
        calculation: CalculationResult,
        venue: str | None,
        provenance: tuple[str, ...],
    ) -> CalculationResult:
        context = calculation.context
        if context is None or not context.source_ref:
            raise ValueError("indicator fact requires explicit calculation context and source_ref")
        if context.source_ref not in provenance:
            raise ValueError("indicator source_ref is not present in orchestration provenance")
        if venue is None:
            return calculation
        if context.venue_context is not None:
            if context.venue_context != venue:
                raise ValueError("calculation venue_context conflicts with explicit raw acquisition context")
            return calculation
        return replace(calculation, context=replace(context, venue_context=venue))

    @staticmethod
    def _structural_status(
        facts: TimeframeStructuralFacts, event: Any, location_index: int,
        contiguous_history_counts: tuple[int, ...],
    ) -> str:
        if event.event_type != "STRUCTURE_STATE":
            return "valid"
        if event.structural_state == "UNCONFIRMED":
            return "unconfirmed"
        if facts.timeframe not in _STRUCTURE_INTERVALS:
            return "unavailable"
        if contiguous_history_counts[location_index] < 11:
            return "insufficient_history"
        return "valid"

    @staticmethod
    def _structural_source_window(
        facts: TimeframeStructuralFacts, event: Any,
        by_open: Mapping[datetime, int], by_close: Mapping[datetime, int],
    ) -> tuple[tuple[str, ...], str, str, int]:
        if event.event_location not in by_open:
            raise ValueError("structural event location does not resolve to a source canonical candle")
        if event.confirmation_time not in by_close:
            raise ValueError("structural confirmation_time does not resolve to a closed source candle")
        location_index = by_open[event.event_location]
        confirmation_index = by_close[event.confirmation_time]
        if location_index > confirmation_index:
            raise ValueError("structural event location follows its confirmation candle")
        start_index = location_index
        if event.event_type in _STRUCTURE_CLASSIFICATION_EVENTS:
            start_index = max(0, location_index - 5)
        elif event.event_type == "FVG":
            start_index = max(0, location_index - 2)
        source_window = facts.candles[start_index:confirmation_index + 1]
        refs = tuple(dict.fromkeys(candle.provenance_id for candle in source_window))
        if not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError("structural source window has missing or malformed provenance")
        location_ref = facts.candles[location_index].provenance_id
        confirmation_ref = facts.candles[confirmation_index].provenance_id
        return refs, location_ref, confirmation_ref, location_index

    @staticmethod
    def _structural_source_members(
        facts: TimeframeStructuralFacts, event: Any,
        event_by_identity: Mapping[str, Any], by_open: Mapping[datetime, int],
        interval: timedelta | None,
    ) -> tuple[str, ...]:
        if event.source_event_identity:
            members = tuple(event.source_event_identity.split(","))
            if event.event_type in {"HH", "HL", "LH", "LL"}:
                members = (event.identity, *members)
            if any(not member or member not in event_by_identity for member in members):
                raise ValueError("structural source/member identity does not resolve to an event in the authoritative analysis")
            return members
        if event.event_type not in {"HH", "HL", "LH", "LL"}:
            return ()
        swing_type = "SWING_HIGH" if event.event_type in {"HH", "LH"} else "SWING_LOW"
        location_index = by_open.get(event.event_location)
        if location_index is None or interval is None:
            raise ValueError("classified swing does not resolve to a governed source candle")
        segment_start = location_index
        while (segment_start > 0
               and facts.candles[segment_start].open_time
               == facts.candles[segment_start - 1].open_time + interval):
            segment_start -= 1
        current = [
            candidate for candidate in facts.events
            if candidate.event_type == swing_type
            and candidate.event_location == event.event_location
            and candidate.knowledge_time == event.knowledge_time
            and candidate.level == event.level
        ]
        previous = [
            candidate for candidate in facts.events
            if candidate.event_type == swing_type
            and candidate.event_location < event.event_location
            and by_open.get(candidate.event_location, -1) >= segment_start
            and candidate.knowledge_time <= event.knowledge_time
        ]
        if len(current) != 1 or not previous:
            raise ValueError("classified swing source/member identity cannot be reconstructed unambiguously")
        prior = max(previous, key=lambda candidate: candidate.event_location)
        return current[0].identity, prior.identity

    @staticmethod
    def _canonical_payload(value: Any) -> str:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(_json(value), sort_keys=True, separators=(",", ":"))

    async def _insert_structural_row(
        self,
        *,
        family: str,
        record_id: str,
        symbol: str,
        timeframe: str,
        event_time: datetime,
        event_type: str,
        source_ref: str,
        venue_context: str | None,
        version: str,
        calculation_version: str,
        status: str,
        reason: str,
        value_numeric: Decimal | None,
        payload: Mapping[str, Any],
        knowledge_time: datetime,
    ) -> int:
        if family not in ("structure_event", "structure_zone"):
            raise ValueError("unsupported structural persistence family")
        table = self.TABLES[family]
        type_column = "event_type" if family == "structure_event" else "zone_type"
        payload_json = json.dumps(_json(payload), sort_keys=True, separators=(",", ":"))
        tag = str(await self._connection.execute(
            f"INSERT INTO {table} "
            f"(record_id,symbol,timeframe,event_time,{type_column},source_ref,venue_context,version,"
            "calculation_version,status,reason,value_numeric,payload_json,identity_hash,knowledge_time) "
            "VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14,$15) "
            "ON CONFLICT(identity_hash) DO NOTHING",
            record_id, symbol, timeframe, event_time, event_type, source_ref, venue_context,
            version, calculation_version, status, reason, value_numeric, payload_json, record_id,
            knowledge_time,
        )).strip()
        if tag == "INSERT 0 1":
            return 1
        if tag != "INSERT 0 0":
            raise RuntimeError(f"unexpected structural insert result: {tag}")
        existing = await self._connection.fetchrow(
            f"SELECT record_id,symbol,timeframe,event_time,{type_column},source_ref,venue_context,version,"
            "calculation_version,status,reason,value_numeric,payload_json,identity_hash,knowledge_time "
            f"FROM {table} WHERE identity_hash=$1",
            record_id,
        )
        if existing is None:
            raise ValueError("structural identity conflict has no readable authoritative row")
        expected = (
            record_id, symbol, timeframe, event_time, event_type, source_ref, venue_context, version,
            calculation_version, status, reason, value_numeric, record_id, knowledge_time,
        )
        actual = tuple(existing[name] for name in (
            "record_id", "symbol", "timeframe", "event_time", type_column, "source_ref", "venue_context",
            "version", "calculation_version", "status", "reason", "value_numeric", "identity_hash",
            "knowledge_time",
        ))
        if actual != expected or self._canonical_payload(existing["payload_json"]) != self._canonical_payload(payload):
            raise ValueError("structural identity collision: persisted content differs from deterministic replay")
        return 0

    async def persist_volume_profile(
        self,
        *,
        symbol: str,
        timeframe: str,
        analysis: VolumeProfileAnalysis,
        trades: tuple[CanonicalTrade, ...],
        configuration_version: str,
        source_record_ids: tuple[str, ...],
    ) -> int:
        if not isinstance(analysis, VolumeProfileAnalysis):
            raise TypeError("analysis must be VolumeProfileAnalysis")
        if not isinstance(trades, tuple) or any(not isinstance(t, CanonicalTrade) for t in trades):
            raise TypeError("trades must be a tuple of CanonicalTrade")
        if any(t.instrument_id != symbol for t in trades):
            raise ValueError("profile trades must match symbol")
        if analysis.interval_start.tzinfo is None or analysis.interval_start.utcoffset() != timezone.utc.utcoffset(analysis.interval_start):
            raise ValueError("profile interval_start must be UTC")
        if analysis.interval_end.tzinfo is None or analysis.interval_end.utcoffset() != timezone.utc.utcoffset(analysis.interval_end):
            raise ValueError("profile interval_end must be UTC")
        if analysis.interval_end <= analysis.interval_start:
            raise ValueError("profile interval must be positive")
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe must be non-empty")
        if not isinstance(configuration_version, str) or not configuration_version.strip():
            raise ValueError("configuration_version must be non-empty")
        provenance = tuple(dict.fromkeys(t.provenance_id for t in trades if t.provenance_id))
        if not provenance and trades:
            raise ValueError("profile trades require provenance")
        source_ref = provenance[0] if len(provenance) == 1 else (
            "canonical-provenance:" + "|".join(provenance) if provenance else None
        )
        knowledge_time, venue_context, evidence_complete = await self._profile_evidence_context(trades, source_record_ids) if trades else (None, None, False)

        def metric(result: Any) -> dict[str, Any]:
            return {
                "metric": result.metric,
                "value": None if result.result.value is None else format(result.result.value, "f"),
                "status": result.result.status.value,
                "reason": result.result.reason,
                "calculation_version": result.calculation_version,
                "context": _json(result.result.context),
            }

        payload = {
            "profile_interval": {
                "start": _json(analysis.interval_start),
                "end": _json(analysis.interval_end),
                "boundary": "[start,end)",
            },
            "price_bin_size": format(analysis.price_bin_size, "f"),
            "bins": [[format(price, "f"), format(volume, "f")] for price, volume in analysis.bins],
            "selected_value_area_bins": [format(value, "f") for value in analysis.selected_value_area_bins],
            "hvn_bins": [format(value, "f") for value in analysis.hvn_bins],
            "lvn_bins": [format(value, "f") for value in analysis.lvn_bins],
            "facts": {
                "POC": metric(analysis.poc),
                "VAL": metric(analysis.value_area_low),
                "VAH": metric(analysis.value_area_high),
                "HVN": metric(analysis.hvn),
                "LVN": metric(analysis.lvn),
            },
            "trade_count": len(trades),
            "source_record_ids": list(source_record_ids),
            "provenance": list(provenance),
            "knowledge_time": _json(knowledge_time),
        }
        core_statuses = (
            analysis.poc.result.status,
            analysis.value_area_low.result.status,
            analysis.value_area_high.result.status,
        )
        if not trades:
            status = CalculationStatus.INSUFFICIENT_HISTORY.value
            reason = "missing_or_insufficient_profile_trade_evidence"
        elif not evidence_complete:
            status = CalculationStatus.UNAVAILABLE.value
            reason = "missing_authoritative_quality_evidence"
        else:
            status = (
                CalculationStatus.VALID.value
                if all(value is CalculationStatus.VALID for value in core_statuses)
                else (
                    CalculationStatus.INSUFFICIENT_HISTORY.value
                    if all(value is CalculationStatus.INSUFFICIENT_HISTORY for value in core_statuses)
                    else CalculationStatus.UNAVAILABLE.value
                )
            )
            reason = "volume_profile_analysis" if status == CalculationStatus.VALID.value else "volume_profile_core_fact_unavailable"
        value_numeric = analysis.poc.result.value if status == CalculationStatus.VALID.value else None
        material = {
            "family": "volume_profile",
            "symbol": symbol,
            "timeframe": timeframe,
            "session_start": analysis.interval_start,
            "session_end": analysis.interval_end,
            "version": configuration_version,
            "calculation_version": analysis.poc.calculation_version,
            "source_ref": source_ref,
            "venue_context": venue_context,
            "knowledge_time": knowledge_time,
            "payload": payload,
        }
        record_id = self._id(material)
        sql = (
            "INSERT INTO meylux.volume_profile_sessions "
            "(record_id,symbol,timeframe,session_start,session_end,source_ref,venue_context,"
            "version,calculation_version,status,reason,value_numeric,payload_json,identity_hash,knowledge_time) "
            "VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14,$15) "
            "ON CONFLICT(identity_hash) DO NOTHING"
        )
        payload_json = json.dumps(_json(payload), sort_keys=True, separators=(",", ":"))
        tag = str(await self._connection.execute(
            sql, record_id, symbol, timeframe, analysis.interval_start, analysis.interval_end,
            source_ref, venue_context, configuration_version, analysis.poc.calculation_version,
            status, reason, value_numeric, payload_json, record_id, knowledge_time,
        )).strip()
        if tag == "INSERT 0 1":
            return 1
        if tag != "INSERT 0 0":
            raise RuntimeError(f"unexpected volume-profile insert result: {tag}")
        existing = await self._connection.fetchrow(
            "SELECT record_id,symbol,timeframe,session_start,session_end,source_ref,venue_context,"
            "version,calculation_version,status,reason,value_numeric,payload_json,identity_hash,knowledge_time "
            "FROM meylux.volume_profile_sessions WHERE identity_hash=$1",
            record_id,
        )
        if existing is None:
            raise ValueError("volume-profile identity conflict has no readable authoritative row")
        actual = tuple(existing[name] for name in (
            "record_id","symbol","timeframe","session_start","session_end","source_ref",
            "venue_context","version","calculation_version","status","reason","value_numeric",
            "identity_hash","knowledge_time",
        ))
        expected = (
            record_id,symbol,timeframe,analysis.interval_start,analysis.interval_end,source_ref,
            venue_context,configuration_version,analysis.poc.calculation_version,status,reason,
            value_numeric,record_id,knowledge_time,
        )
        existing_payload = existing["payload_json"]
        if actual != expected or self._canonical_payload(existing_payload) != self._canonical_payload(payload):
            raise ValueError("volume-profile identity collision: persisted content differs from deterministic replay")
        return 0

    async def persist_orchestration(self, result: QuantOrchestrationResult) -> int:
        primary_knowledge_time = _knowledge_time(result)
        rows: list[tuple[Any, ...]] = []
        structural_rows: list[dict[str, Any]] = []
        primary_venue = await self._resolve_venue_context(result.source_provenance)

        # Primary timeframe and each eligible higher timeframe use the same
        # existing P4 indicator engine and the same authoritative append-only table.
        for name, calculation in result.indicators.items():
            calculation = self._with_venue_context(calculation, primary_venue, result.source_provenance)
            rows.append(self._indicator_row(
                symbol=result.symbol,
                timeframe=result.timeframe,
                event_time=result.as_of,
                configuration_version=result.configuration_version,
                name=name,
                calculation=calculation,
                provenance=result.source_provenance,
            ))

        for timeframe, facts in sorted(result.higher_timeframe_facts.items()):
            if not isinstance(facts, TimeframeQuantitativeFacts):
                raise TypeError(f"higher_timeframe_facts[{timeframe}] must be TimeframeQuantitativeFacts")
            if timeframe != facts.timeframe:
                raise ValueError("higher timeframe fact key must match its timeframe")
            if timeframe == result.timeframe:
                raise ValueError("higher timeframe fact timeframe must differ from primary timeframe")
            if facts.symbol != result.symbol:
                raise ValueError("higher timeframe fact instrument must match primary")
            if facts.configuration_version != result.configuration_version:
                raise ValueError("higher timeframe fact configuration must match primary configuration")
            if facts.knowledge_time > primary_knowledge_time:
                raise ValueError("higher timeframe fact knowledge_time exceeds primary knowledge boundary")
            if facts.knowledge_time != facts.event_time:
                raise ValueError("higher timeframe fact knowledge_time must equal event_time")
            higher_venue = await self._resolve_venue_context(facts.source_provenance)
            for name, calculation in facts.indicators.items():
                calculation = self._with_venue_context(calculation, higher_venue, facts.source_provenance)
                rows.append(self._indicator_row(
                    symbol=facts.symbol,
                    timeframe=facts.timeframe,
                    event_time=facts.event_time,
                    configuration_version=facts.configuration_version,
                    name=name,
                    calculation=calculation,
                    provenance=facts.source_provenance,
                ))

        regime_payload = {
            "state": result.regime.state,
            "transition": result.regime_transition,
            "result": _calc(result.regime.result),
            "source_provenance": result.source_provenance,
            "htf": _json(result.htf),
        }
        regime_material = {
            "family": "regime",
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "event_time": result.as_of,
            "version": result.configuration_version,
            "payload": regime_payload,
        }
        rows.append((
            "regime", self._id(regime_material), result.regime.state,
            result.regime.result.status.value, result.regime.result.reason,
            result.regime.result.value, result.regime.result.context, regime_payload,
            result.regime.calculation_version, result.symbol, result.timeframe,
            result.as_of, result.configuration_version,
        ))

        # The ORCHESTRATION structure row is a snapshot summary, not a
        # DOC-P4-002 structural fact. Its event_time is preserved as the
        # orchestration reference boundary, but no knowledge_time is claimed.
        structure_payload = {
            "event_count": result.structure_event_count,
            "state": result.structure_state,
            "source_provenance": result.source_provenance,
        }
        structure_material = {
            "family": "structure_event",
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "event_time": result.as_of,
            "version": result.configuration_version,
            "payload": structure_payload,
        }
        rows.append((
            "structure_event", self._id(structure_material), "ORCHESTRATION",
            "valid", "orchestration_snapshot", None, None, structure_payload,
            "1.0.0", result.symbol, result.timeframe, result.as_of,
            f"canonical-provenance:{'|'.join(result.source_provenance)}", None,
            result.configuration_version,
        ))

        # Persist the existing ratified P4 engine's individual facts. The
        # summary row above remains compatibility-only and carries no claimed
        # structural knowledge_time.
        for timeframe, facts in sorted(result.structural_facts.items()):
            if not isinstance(facts, TimeframeStructuralFacts):
                raise TypeError(f"structural_facts[{timeframe}] must be TimeframeStructuralFacts")
            if timeframe != facts.timeframe:
                raise ValueError("structural fact key must match its timeframe")
            if facts.symbol != result.symbol:
                raise ValueError("structural fact symbol must match the primary instrument")
            if facts.as_of > primary_knowledge_time:
                raise ValueError("structural timeframe knowledge boundary exceeds primary snapshot")
            provenance = tuple(dict.fromkeys(c.provenance_id for c in facts.candles))
            venue = await self._resolve_venue_context(provenance)
            by_open = {candle.open_time: index for index, candle in enumerate(facts.candles)}
            by_close = {candle.close_time: index for index, candle in enumerate(facts.candles)}
            interval = _STRUCTURE_INTERVALS.get(facts.timeframe)
            history_counts: list[int] = []
            for index, candle in enumerate(facts.candles):
                if (index == 0 or interval is None
                        or candle.open_time != facts.candles[index - 1].open_time + interval):
                    history_counts.append(1)
                else:
                    history_counts.append(history_counts[-1] + 1)
            contiguous_history_counts = tuple(history_counts)
            event_by_identity = {event.identity: event for event in facts.events}
            seen_identities: set[str] = set()
            for event in facts.events:
                if event.identity in seen_identities:
                    raise ValueError("duplicate structural identity emitted within one analysis")
                seen_identities.add(event.identity)
                for field_name in ("event_location", "confirmation_time", "knowledge_time"):
                    value = getattr(event, field_name)
                    if (not isinstance(value, datetime) or value.tzinfo is None
                            or value.utcoffset() != timezone.utc.utcoffset(value)):
                        raise ValueError(f"structural {field_name} must be UTC")
                if event.event_location > event.confirmation_time:
                    raise ValueError("structural event location must not follow confirmation_time")
                if event.confirmation_time != event.knowledge_time:
                    raise ValueError("confirmed structural event confirmation_time must equal knowledge_time")
                if event.knowledge_time > primary_knowledge_time:
                    raise ValueError("structural event knowledge_time exceeds primary snapshot boundary")
                refs, location_ref, confirmation_ref, location_index = self._structural_source_window(
                    facts, event, by_open, by_close
                )
                source_ref = "canonical-provenance:" + "|".join(refs)
                status = self._structural_status(facts, event, location_index, contiguous_history_counts)
                reason = event.reason or event.event_type
                if status == "insufficient_history":
                    reason = f"{reason};requires_11_contiguous_closed_candles"
                zone_formation_time = event.event_location
                if event.event_type in {
                    "FVG_LIFECYCLE", "ORDER_BLOCK_INVALIDATION",
                    "BREAKER_INVALIDATION", "LIQUIDITY_POOL_SWEEP",
                }:
                    source_identity = event.source_event_identity
                    if not source_identity or "," in source_identity or source_identity not in event_by_identity:
                        raise ValueError("structural lifecycle transition must resolve one authoritative source event identity")
                    zone_formation_time = event_by_identity[source_identity].event_location
                    if zone_formation_time > event.event_location:
                        raise ValueError("structural lifecycle transition precedes its source zone formation")
                payload = {
                    "event_identity": event.identity,
                    "event_type": event.event_type,
                    "event_location": _json(event.event_location),
                    "zone_formation_time": _json(zone_formation_time),
                    "confirmation_time": _json(event.confirmation_time),
                    "knowledge_time": _json(event.knowledge_time),
                    "direction": event.direction,
                    "level": _json(event.level),
                    "lower_bound": _json(event.lower_bound),
                    "upper_bound": _json(event.upper_bound),
                    "lifecycle": event.lifecycle,
                    "structural_state": event.structural_state,
                    "source_event_identity": event.source_event_identity,
                    "source_member_identities": list(self._structural_source_members(
                        facts, event, event_by_identity, by_open, interval
                    )),
                    "prior_structural_state": event.prior_structural_state,
                    "semantic_version": facts.calculation_version,
                    "source_candle_provenance": location_ref,
                    "confirmation_candle_provenance": confirmation_ref,
                    "source_window_provenance": list(refs),
                }
                common = {
                    "record_id": event.identity,
                    "symbol": facts.symbol,
                    "timeframe": facts.timeframe,
                    "event_time": event.event_location,
                    "event_type": event.event_type,
                    "source_ref": source_ref,
                    "venue_context": venue,
                    "version": result.configuration_version,
                    "calculation_version": facts.calculation_version,
                    "status": status,
                    "reason": reason,
                    "value_numeric": event.level,
                    "payload": payload,
                    "knowledge_time": event.knowledge_time,
                }
                structural_rows.append({"family": "structure_event", **common})
                if (event.event_type in _ZONE_LIFECYCLE_EVENTS
                        and (event.lower_bound is not None or event.upper_bound is not None
                             or event.event_type in {"LIQUIDITY_POOL", "LIQUIDITY_POOL_SWEEP"})):
                    zone_row = dict(common)
                    zone_row["event_type"] = _ZONE_TYPE_BY_EVENT[event.event_type]
                    structural_rows.append({"family": "structure_zone", **zone_row})

        async with self._connection.transaction():
            inserted = 0
            for row in rows:
                family = row[0]
                if family == "indicator":
                    (_, record_id, name, status, reason, value, context, payload, calculation_version,
                     symbol, timeframe, event_time, source_ref, venue, version) = row
                    sql = (
                        f"INSERT INTO {self.TABLES[family]} "
                        "(record_id,symbol,timeframe,event_time,source_ref,venue_context,version,calculation_version,"
                        "status,reason,value_numeric,payload_json,identity_hash) "
                        "VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,$13) "
                        "ON CONFLICT(identity_hash) DO NOTHING"
                    )
                    args = (
                        record_id, symbol, timeframe, event_time, source_ref, venue, version,
                        calculation_version, status, reason, value,
                        json.dumps(_json(payload), sort_keys=True, separators=(",", ":")), record_id,
                    )
                elif family == "regime":
                    (_, record_id, state, status, reason, value, context, payload, calculation_version,
                     symbol, timeframe, event_time, version) = row
                    source_ref = context.source_ref if context and context.source_ref else f"canonical-provenance:{'|'.join(result.source_provenance)}"
                    venue = context.venue_context if context else None
                    sql = (
                        f"INSERT INTO {self.TABLES[family]} "
                        "(record_id,symbol,timeframe,event_time,regime_state,source_ref,venue_context,version,"
                        "calculation_version,status,reason,value_numeric,payload_json,identity_hash) "
                        "VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14) "
                        "ON CONFLICT(identity_hash) DO NOTHING"
                    )
                    args = (
                        record_id, symbol, timeframe, event_time, state, source_ref, venue, version,
                        calculation_version, status, reason, value,
                        json.dumps(_json(payload), sort_keys=True, separators=(",", ":")), record_id,
                    )
                else:
                    (_, record_id, event_type, status, reason, value, context, payload, calculation_version,
                     symbol, timeframe, event_time, source_ref, venue, version) = row
                    sql = (
                        f"INSERT INTO {self.TABLES[family]} "
                        "(record_id,symbol,timeframe,event_time,event_type,source_ref,venue_context,version,"
                        "calculation_version,status,reason,value_numeric,payload_json,identity_hash) "
                        "VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14) "
                        "ON CONFLICT(identity_hash) DO NOTHING"
                    )
                    args = (
                        record_id, symbol, timeframe, event_time, event_type, source_ref, venue, version,
                        calculation_version, status, reason, value,
                        json.dumps(_json(payload), sort_keys=True, separators=(",", ":")), record_id,
                    )
                if str(await self._connection.execute(sql, *args)).strip() == "INSERT 0 1":
                    inserted += 1
            for structural_row in structural_rows:
                inserted += await self._insert_structural_row(**structural_row)
        return inserted

    async def fetch_family(
        self,
        family: str,
        symbol: str,
        timeframe: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
    ) -> list[Any]:
        if family not in self.TABLES:
            raise ValueError("unsupported quantitative family")
        if not symbol or not timeframe:
            raise ValueError("symbol and timeframe are required")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be 1..1000")
        sql = f"SELECT * FROM {self.TABLES[family]} WHERE symbol=$1 AND timeframe=$2"
        args: list[Any] = [symbol, timeframe]
        time_column = "session_start" if family == "volume_profile" else "event_time"
        if start is not None:
            if start.tzinfo is None or start.utcoffset() != timezone.utc.utcoffset(start): raise ValueError("start must be UTC")
            sql += f" AND {time_column}>{chr(36)}{len(args) + 1}"
            args.append(start)
        if end is not None:
            if end.tzinfo is None or end.utcoffset() != timezone.utc.utcoffset(end): raise ValueError("end must be UTC")
            if start is not None and end < start: raise ValueError("end must not precede start")
            sql += f" AND {time_column}<{chr(36)}{len(args) + 1}"
            args.append(end)
        sql += f" ORDER BY {time_column},record_id LIMIT {chr(36)}{len(args) + 1}"
        args.append(limit)
        return list(await self._connection.fetch(sql, *args))
