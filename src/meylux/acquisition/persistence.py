"""Raw/staging persistence boundary for Phase 2 acquisition evidence.

This module persists the already-governed AcquisitionEnvelope without validating,
normalizing, or promoting provider data to analytical truth.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Protocol

from contracts.acquisition import AcquisitionEnvelope
from meylux.acquisition.models import RawAcquisitionRecord

SID = "STEP-P2-004"


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    event_id: str
    inserted: bool


class AsyncConnection(Protocol):
    async def execute(self, query: str, *args: Any) -> Any: ...
    async def fetchrow(self, query: str, *args: Any) -> Any: ...


class RawStagingRepository:
    """PostgreSQL repository for append-only acquisition evidence."""

    INSERT_SQL = """
        INSERT INTO meylux.raw_acquisition_events (
            event_id, provider_id, adapter_id, adapter_version,
            canonical_instrument_id, provider_instrument_id, event_type,
            event_time, received_at, acquisition_state, source_sequence,
            provenance_id, acquisition_method, payload_json, canonical_bytes,
            identity_hash
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7,
            $8, $9, $10, $11, $12, $13, $14::jsonb, $15, $16
        )
        ON CONFLICT (event_id) DO NOTHING
    """

    FETCH_SQL = """
        SELECT event_id, provider_id, adapter_id, adapter_version,
               canonical_instrument_id, provider_instrument_id, event_type,
               event_time, received_at, acquisition_state, source_sequence,
               provenance_id, acquisition_method, payload_json,
               canonical_bytes, identity_hash, persisted_at
          FROM meylux.raw_acquisition_events
         WHERE event_id = $1
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def persist(self, envelope: AcquisitionEnvelope) -> PersistenceResult:
        canonical = envelope.canonical_bytes()
        identity = envelope.identity_bytes()
        payload_json = json.dumps(
            json.loads(canonical.decode("utf-8"))["payload"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        result = await self._connection.execute(
            self.INSERT_SQL,
            envelope.event_id,
            envelope.provider.provider_id,
            envelope.provider.adapter_id,
            envelope.provider.adapter_version,
            envelope.instrument.canonical_instrument_id,
            envelope.instrument.provider_instrument_id,
            envelope.event_type.value,
            envelope.event_time,
            envelope.received_at,
            envelope.state.value,
            envelope.source_sequence,
            envelope.provenance.provenance_id,
            envelope.provenance.acquisition_method,
            payload_json,
            canonical,
            hashlib.sha256(identity).hexdigest(),
        )
        inserted = str(result).upper().endswith("1")
        return PersistenceResult(envelope.event_id, inserted)

    async def fetch(self, event_id: str) -> Any:
        return await self._connection.fetchrow(self.FETCH_SQL, event_id)

    async def fetch_record(self, event_id: str) -> RawAcquisitionRecord | None:
        row = await self.fetch(event_id)
        if row is None:
            return None
        values = dict(row) if hasattr(row, "keys") else None
        if values is not None:
            return RawAcquisitionRecord(**values)
        return RawAcquisitionRecord(
            event_id=row[0], provider_id=row[1], adapter_id=row[2], adapter_version=row[3],
            canonical_instrument_id=row[4], provider_instrument_id=row[5], event_type=row[6],
            event_time=row[7], received_at=row[8], acquisition_state=row[9], source_sequence=row[10],
            provenance_id=row[11], acquisition_method=row[12], payload_json=row[13],
            canonical_bytes=row[14], identity_hash=row[15], persisted_at=row[16],
        )
