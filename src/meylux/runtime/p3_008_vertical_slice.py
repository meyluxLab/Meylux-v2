"""Controlled real-data P3-008 vertical-slice runner; no fabricated fallback data."""
from __future__ import annotations
import asyncio
import json
import os
from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType, InstrumentIdentity, ProviderIdentity, Provenance
from contracts.canonical.foundation import ProvenanceRef, ValidationOutcome, ValidationResult, validation_outcome
from contracts.market_semantic import validate_market_semantics
from contracts.normalization import normalize
from contracts.quality import QualityInput, QualitySignals, assess_quality
from contracts.temporal import validate_temporal_evidence
from contracts.validation import validate_acquisition_envelope
from meylux.persistence.canonical import CanonicalPersistence
from meylux.persistence.event_handoff import CanonicalEventRelay
from meylux.persistence.factory import build_canonical_event

def required(name:str)->str:
    value=os.environ.get(name)
    if not value: raise RuntimeError(f"{name} is required")
    return value

def _payload_mapping_from_row(value:Any)->Mapping[str,Any]:
    """Decode the PostgreSQL jsonb runtime representation without weakening the envelope contract."""
    if isinstance(value, Mapping):
        payload=value
    elif isinstance(value, (str, bytes, bytearray)):
        try:
            payload=json.loads(value)
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise ValueError("raw payload_json contains malformed JSON") from exc
    else:
        raise TypeError(f"payload_json must be a JSON object representation, got {type(value).__name__}")
    if not isinstance(payload, Mapping):
        raise TypeError("payload_json must decode to a JSON object")
    return payload

def envelope_from_row(row:Any)->AcquisitionEnvelope:
    provider=ProviderIdentity(str(row["provider_id"]),str(row["adapter_id"]),str(row["adapter_version"]))
    instrument=InstrumentIdentity(str(row["canonical_instrument_id"]),str(row["provider_instrument_id"]))
    provenance=Provenance(str(row["provenance_id"]),provider,str(row["acquisition_method"]))
    payload=_payload_mapping_from_row(row["payload_json"])
    return AcquisitionEnvelope(provider,instrument,provenance,EventType(str(row["event_type"])),row["event_time"],row["received_at"],AcquisitionState(str(row["acquisition_state"])),payload,str(row["source_sequence"]) if row["source_sequence"] is not None else None)

def _quality_validation_outcome(issues: list[Any], normalized_result: ValidationResult) -> ValidationOutcome:
    """Normalize the two existing validation result contracts at the quality boundary.

    Primitive validation findings are mapped through the authoritative
    validation_outcome classifier. When no additional findings exist,
    normalization already supplies a bare ValidationResult and it is
    wrapped without changing its semantic state.
    """
    if not isinstance(normalized_result, ValidationResult):
        raise TypeError("normalized_result must be ValidationResult")
    return validation_outcome(issues) if issues else ValidationOutcome(normalized_result)

def market_values(value:Any)->dict[str,Any]:
    fields={}
    for name in ("price","quantity","open","high","low","close","volume"):
        if hasattr(value,name): fields[name]=getattr(value,name)
    if hasattr(value,"bids") and hasattr(value,"asks") and value.bids and value.asks:
        fields["bid"]=value.bids[0][0]; fields["ask"]=value.asks[0][0]
    return fields

async def main()->int:
    import asyncpg
    import redis.asyncio as redis
    pool=await asyncpg.create_pool(host=required("MEYLUX_DB_HOST"),port=int(os.environ.get("MEYLUX_DB_PORT","5432")),database=required("MEYLUX_DB_NAME"),user=required("MEYLUX_DB_USER"),password=required("MEYLUX_DB_PASSWORD"),min_size=1,max_size=2)
    client=redis.from_url(os.environ.get("MEYLUX_REDIS_URL","redis://redis:6379/0"),decode_responses=False)
    try:
        async with pool.acquire() as conn:
            event_id=os.environ.get("MEYLUX_VERTICAL_SLICE_EVENT_ID")
            row=await conn.fetchrow("SELECT event_id,provider_id,adapter_id,adapter_version,canonical_instrument_id,provider_instrument_id,event_type,event_time,received_at,acquisition_state,source_sequence,provenance_id,acquisition_method,payload_json FROM meylux.raw_acquisition_events WHERE acquisition_state='AVAILABLE' AND ($1::text IS NULL OR event_id=$1) ORDER BY event_time,event_id LIMIT 1",event_id)
            if row is None:
                print("vertical slice: no governed AVAILABLE raw record was found; no fallback data was fabricated",flush=True); return 2
            envelope=envelope_from_row(row)
            structural=validate_acquisition_envelope(envelope)
            temporal=validate_temporal_evidence(envelope)
            normalized=normalize(envelope)
            issues=list(structural.outcome.issues)+list(temporal.outcome.issues)
            if normalized.valid:
                issues.extend(validate_market_semantics(market_values(normalized.value)).issues)
            outcome=_quality_validation_outcome(issues, normalized.result)
            provenance=ProvenanceRef(envelope.provenance.provenance_id,envelope.provider.provider_id,envelope.provenance.acquisition_method)
            signals=QualitySignals(validation_status=Decimal("1.00") if outcome.result.value=="valid" else Decimal("0.00"))
            assessment=assess_quality(QualityInput(outcome,signals,provenance,envelope.event_id,envelope.event_id))
            print(f"vertical slice: raw_event={envelope.event_id} structural={structural.outcome.result.value} temporal={temporal.outcome.result.value} normalized={normalized.result.value} quality={assessment.quality.quality_state.value} canonical_eligible={assessment.canonical_eligible}",flush=True)
            if not normalized.valid or not assessment.canonical_eligible:
                return 3
            record,event=build_canonical_event(normalized.value,assessment,1)
            result=await CanonicalPersistence(conn).persist(record,event.to_json(),assessment)
            print(f"canonical persistence: inserted={result.inserted} record_id={result.record_id} outbox_sequence={result.outbox_sequence}",flush=True)
            count=await CanonicalEventRelay(CanonicalPersistence(conn),client).publish_pending()
            print(f"canonical event handoff: published={count} stream=stream:canonical:market_events",flush=True)
            return 0
    finally:
        await client.aclose()
        await pool.close()

if __name__=="__main__":
    raise SystemExit(asyncio.run(main()))
