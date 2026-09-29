"""Append-only authoritative persistence for P3 quality/acquisition evidence."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol

from contracts.quality_evidence import QualityEvidenceRecord


class AsyncConnection(Protocol):
    async def execute(self, query: str, *args: Any) -> Any: ...
    async def fetchrow(self, query: str, *args: Any) -> Any: ...
    async def fetch(self, query: str, *args: Any) -> Any: ...
    def transaction(self) -> Any: ...


@dataclass(frozen=True, slots=True)
class QualityEvidencePersistenceResult:
    evidence_id: str
    inserted: bool
    contradictory: bool


class ContradictoryQualityEvidence(ValueError):
    """Raised when a logical fact has multiple distinct authoritative identities."""


class QualityEvidencePersistence:
    """Transactional, deterministic, append-only quality-evidence repository."""

    INSERT_SQL = """
        INSERT INTO meylux.quality_evidence (
            evidence_id, logical_fact_key, source_record_id, source_identity_hash,
            provider_id, adapter_id, adapter_version, canonical_instrument_id,
            provider_instrument_id, event_type, event_time, received_at,
            knowledge_time, acquisition_state, quality_state, lifecycle_state,
            quality_score, reason_codes, validation_result, provenance_id,
            lineage_parent_id, payload_fingerprint, timeframe, venue
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,
            $18::jsonb,$19,$20,$21,$22,$23,$24
        )
        ON CONFLICT (evidence_id) DO NOTHING
    """

    FETCH_BY_ID_SQL = """
        SELECT evidence_id, logical_fact_key, source_record_id, source_identity_hash,
               provider_id, adapter_id, adapter_version, canonical_instrument_id,
               provider_instrument_id, event_type, event_time, received_at,
               knowledge_time, acquisition_state, quality_state, lifecycle_state,
               quality_score, reason_codes, validation_result, provenance_id,
               lineage_parent_id, payload_fingerprint, timeframe, venue
          FROM meylux.quality_evidence
         WHERE evidence_id = $1
    """

    FETCH_LOGICAL_SQL = """
        SELECT evidence_id, logical_fact_key, source_record_id, source_identity_hash,
               provider_id, adapter_id, adapter_version, canonical_instrument_id,
               provider_instrument_id, event_type, event_time, received_at,
               knowledge_time, acquisition_state, quality_state, lifecycle_state,
               quality_score, reason_codes, validation_result, provenance_id,
               lineage_parent_id, payload_fingerprint, timeframe, venue
          FROM meylux.quality_evidence
         WHERE logical_fact_key = $1
         ORDER BY evidence_id
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def persist(self, record: QualityEvidenceRecord) -> QualityEvidencePersistenceResult:
        if not isinstance(record, QualityEvidenceRecord):
            raise TypeError("record must be QualityEvidenceRecord")
        async with self._connection.transaction():
            existing = await self._connection.fetchrow(
                "SELECT evidence_id FROM meylux.quality_evidence WHERE evidence_id=$1",
                record.evidence_id,
            )
            if existing is not None:
                rows = await self._connection.fetch(self.FETCH_LOGICAL_SQL, record.logical_fact_key)
                contradictory = len({str(row["evidence_id"]) for row in rows}) > 1
                return QualityEvidencePersistenceResult(record.evidence_id, False, contradictory)
            await self._connection.execute(
                self.INSERT_SQL,
                record.evidence_id, record.logical_fact_key, record.source_record_id,
                record.source_identity_hash, record.provider_id, record.adapter_id,
                record.adapter_version, record.canonical_instrument_id,
                record.provider_instrument_id, record.event_type, record.event_time,
                record.received_at, record.knowledge_time, record.acquisition_state,
                record.quality_state.value, record.lifecycle_state.value,
                record.quality_score, json.dumps(record.reason_codes),
                record.validation_result, record.provenance_id, record.lineage_parent_id,
                record.payload_fingerprint, record.timeframe, record.venue,
            )
            rows = await self._connection.fetch(self.FETCH_LOGICAL_SQL, record.logical_fact_key)
            contradictory = len({str(row["evidence_id"]) for row in rows}) > 1
        return QualityEvidencePersistenceResult(record.evidence_id, True, contradictory)

    async def fetch(self, evidence_id: str) -> Any:
        return await self._connection.fetchrow(self.FETCH_BY_ID_SQL, evidence_id)

    async def resolve(self, logical_fact_key: str) -> Any:
        rows = await self._connection.fetch(self.FETCH_LOGICAL_SQL, logical_fact_key)
        if len(rows) > 1:
            raise ContradictoryQualityEvidence(
                "multiple distinct evidence identities exist for one logical quality fact"
            )
        return rows[0] if rows else None

    async def resolve_evidence_ref(self, logical_fact_key: str) -> dict[str, Any] | None:
        row = await self.resolve(logical_fact_key)
        if row is None or row["knowledge_time"] is None:
            return None
        return {
            "evidence_id": str(row["evidence_id"]),
            "source_type": "meylux.data_quality_evidence",
            "source_reference": f"meylux.quality_evidence:{row['evidence_id']}",
            "identity_hash": str(row["source_identity_hash"]),
            "observed_at_utc": row["received_at"],
            "content_version": str(row["adapter_version"]),
            "source_family": "P3:QUALITY_EVIDENCE",
            "record_id": str(row["source_record_id"]),
            "event_time": row["event_time"],
            "knowledge_time": row["knowledge_time"],
            "timeframe": row["timeframe"],
            "venue": row["venue"],
        }
