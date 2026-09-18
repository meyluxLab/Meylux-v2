"""PostgreSQL authoritative canonical persistence for P3-008."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import Any, Mapping, Protocol
from contracts.canonical.foundation import canonical_json
from contracts.data_quality import DataQualityState
from contracts.quality import QualityAssessment, fingerprint_payload

TABLES={"instrument":"meylux.canonical_instruments","candle":"meylux.canonical_candles","trade":"meylux.canonical_trades","orderbook":"meylux.canonical_orderbook_depth","derivatives":"meylux.canonical_derivatives"}

class UnsupportedCanonicalState(ValueError): pass

@dataclass(frozen=True, slots=True)
class CanonicalRecord:
    record_type:str; record_id:str; event_id:str; event_time:datetime; instrument_id:str
    payload:Mapping[str,Any]; provenance_id:str; source_record_id:str; lineage_parent_id:str
    quality_state:DataQualityState=DataQualityState.VALID; quality_score:Decimal|None=None
    def __post_init__(self)->None:
        if self.record_type not in TABLES: raise ValueError(f"unsupported canonical record_type: {self.record_type}")
        for v,f in ((self.record_id,"record_id"),(self.event_id,"event_id"),(self.instrument_id,"instrument_id"),(self.provenance_id,"provenance_id"),(self.source_record_id,"source_record_id"),(self.lineage_parent_id,"lineage_parent_id")):
            if not isinstance(v,str) or not v.strip(): raise ValueError(f"{f} must be non-empty")
        if self.quality_state is not DataQualityState.VALID: raise UnsupportedCanonicalState("only VALID quality evidence may enter canonical persistence")
        if not isinstance(self.payload,Mapping): raise TypeError("payload must be a mapping")
        if self.event_time.tzinfo is None or self.event_time.utcoffset()!=timezone.utc.utcoffset(self.event_time): raise ValueError("event_time must be timezone-aware UTC")
        if self.quality_score is not None:
            if not isinstance(self.quality_score,Decimal) or not self.quality_score.is_finite() or not Decimal("0.00")<=self.quality_score<=Decimal("1.00"): raise ValueError("quality_score must be finite and in 0.00..1.00")
    @property
    def canonical_json(self)->str: return canonical_json(self.payload)
    @property
    def identity_hash(self)->str:
        material={"record_type":self.record_type,"record_id":self.record_id,"event_id":self.event_id,"payload":self.payload}
        return hashlib.sha256(canonical_json(material).encode()).hexdigest()

class AsyncConnection(Protocol):
    async def execute(self,query:str,*args:Any)->Any: ...
    async def fetch(self,query:str,*args:Any)->Any: ...
    async def fetchrow(self,query:str,*args:Any)->Any: ...
    def transaction(self)->Any: ...

@dataclass(frozen=True, slots=True)
class PersistenceResult:
    record_id:str; event_id:str; inserted:bool; outbox_sequence:int|None

class CanonicalPersistence:
    def __init__(self,connection:AsyncConnection)->None: self._connection=connection
    async def persist(self,record:CanonicalRecord,event_json:str,assessment:QualityAssessment|None=None)->PersistenceResult:
        table=TABLES[record.record_type]
        if not isinstance(event_json,str) or not event_json: raise ValueError("event_json must be non-empty")
        insert=f"""INSERT INTO {table}(record_id,event_id,instrument_id,event_time,provenance_id,source_record_id,lineage_parent_id,quality_state,quality_score,payload_json,canonical_bytes,identity_hash)
                   VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12) ON CONFLICT(record_id) DO NOTHING RETURNING record_id"""
        quality_log="""INSERT INTO meylux.data_quality_logs(record_id,quality_state,lifecycle_state,quality_score,reason_codes,validation_result,provenance_id,source_record_id,lineage_parent_id,payload_fingerprint)\n                  VALUES($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)"""\n        quality_log="""INSERT INTO meylux.data_quality_logs(record_id,quality_state,lifecycle_state,quality_score,reason_codes,validation_result,provenance_id,source_record_id,lineage_parent_id,payload_fingerprint) VALUES($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)"""
        outbox="""INSERT INTO meylux.canonical_event_outbox(event_id,record_id,event_type,event_time,payload_json)
                  VALUES($1,$2,$3,$4,$5::jsonb) ON CONFLICT(event_id) DO NOTHING RETURNING sequence_no"""
        async with self._connection.transaction():
            row=await self._connection.fetchrow(insert,record.record_id,record.event_id,record.instrument_id,record.event_time,record.provenance_id,record.source_record_id,record.lineage_parent_id,record.quality_state.value,record.quality_score,record.canonical_json,record.canonical_json.encode(),record.identity_hash)
            if row is None:
                existing=await self._connection.fetchrow(f"SELECT record_id,event_id FROM {table} WHERE record_id=$1",record.record_id)
                if existing is None or str(existing["event_id"])!=record.event_id: raise ValueError("canonical record identity conflict")
                outbox_existing=await self._connection.fetchrow("SELECT sequence_no FROM meylux.canonical_event_outbox WHERE event_id=$1",record.event_id)\n                return PersistenceResult(record.record_id,record.event_id,False,None if outbox_existing is None else int(outbox_existing["sequence_no"]))
            if assessment is not None:\n                await self._connection.execute(quality_log,record.record_id,assessment.quality.quality_state.value,assessment.lifecycle.value,assessment.explanation.score,__import__("json").dumps(assessment.quality.reason_codes),assessment.quality.quality_state.value,record.provenance_id,record.source_record_id,record.lineage_parent_id,fingerprint_payload(record.payload))\n            if assessment is not None:
                import json
                await self._connection.execute(quality_log,record.record_id,assessment.quality.quality_state.value,assessment.lifecycle.value,assessment.explanation.score,json.dumps(assessment.quality.reason_codes),assessment.quality.quality_state.value,record.provenance_id,record.source_record_id,record.lineage_parent_id,fingerprint_payload(record.payload))
            out=await self._connection.fetchrow(outbox,record.event_id,record.record_id,record.record_type,record.event_time,event_json)
        return PersistenceResult(record.record_id,record.event_id,True,None if out is None else int(out["sequence_no"]))
    async def fetch(self,record_type:str,record_id:str)->Any:
        return await self._connection.fetchrow(f"SELECT record_id,event_id,instrument_id,event_time,provenance_id,source_record_id,lineage_parent_id,quality_state,quality_score,payload_json,canonical_bytes,identity_hash,persisted_at FROM {TABLES[record_type]} WHERE record_id=$1",record_id)
    async def pending_events(self,limit:int=100)->list[Any]:
        if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=1000: raise ValueError("limit must be 1..1000")
        return await self._connection.fetch("""SELECT sequence_no,event_id,record_id,event_type,event_time,payload_json FROM meylux.canonical_event_outbox WHERE published_at IS NULL ORDER BY sequence_no LIMIT $1""",limit)
    async def mark_event_published(self,event_id:str,stream_id:str)->None:
        await self._connection.execute("""UPDATE meylux.canonical_event_outbox SET published_at=now(),published_stream_id=$2 WHERE event_id=$1 AND published_at IS NULL""",event_id,stream_id)
