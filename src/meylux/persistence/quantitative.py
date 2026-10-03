"""Append-only adapter to the existing authoritative Phase-4 quantitative tables."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from contracts.quantitative.base import CalculationResult
from meylux.orchestration.engine import QuantOrchestrationResult, TimeframeQuantitativeFacts


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
        source_ref = context.source_ref if context and context.source_ref else f"canonical-provenance:{'|'.join(provenance)}"
        venue = context.venue_context if context else None
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
    def _with_venue_context(calculation: CalculationResult, venue: str | None) -> CalculationResult:
        context = calculation.context
        if context is None or context.venue_context is not None or venue is None:
            return calculation
        return replace(calculation, context=replace(context, venue_context=venue))

    async def persist_orchestration(self, result: QuantOrchestrationResult) -> int:
        primary_knowledge_time = _knowledge_time(result)
        rows: list[tuple[Any, ...]] = []
        primary_venue = await self._resolve_venue_context(result.source_provenance)

        # Primary timeframe and each eligible higher timeframe use the same
        # existing P4 indicator engine and the same authoritative append-only table.
        for name, calculation in result.indicators.items():
            calculation = self._with_venue_context(calculation, primary_venue)
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
                calculation = self._with_venue_context(calculation, higher_venue)
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
        if start is not None:
            if start.tzinfo is None or start.utcoffset() != timezone.utc.utcoffset(start):
                raise ValueError("start must be UTC")
            sql += f" AND event_time>{chr(36)}{len(args) + 1}"
            args.append(start)
        if end is not None:
            if end.tzinfo is None or end.utcoffset() != timezone.utc.utcoffset(end):
                raise ValueError("end must be UTC")
            if start is not None and end < start:
                raise ValueError("end must not precede start")
            sql += f" AND event_time<{chr(36)}{len(args) + 1}"
            args.append(end)
        sql += f" ORDER BY event_time,record_id LIMIT {chr(36)}{len(args) + 1}"
        args.append(limit)
        return list(await self._connection.fetch(sql, *args))
