"""Bridge verified P3-005/P3-007 outputs into P3-008 persistence/event contracts."""
from __future__ import annotations
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import Any, Mapping
from contracts.canonical import CanonicalCandle, CanonicalDerivatives, CanonicalInstrument, CanonicalOrderBook, CanonicalTrade
from contracts.canonical.foundation import deterministic_identity
from contracts.event import CanonicalEvent
from contracts.quality import QualityAssessment
from contracts.data_quality import DataQualityState
from .canonical import CanonicalRecord

TYPE_MAP={CanonicalInstrument:"instrument",CanonicalCandle:"candle",CanonicalTrade:"trade",CanonicalOrderBook:"orderbook",CanonicalDerivatives:"derivatives"}

def _json_value(value:Any)->Any:
    if isinstance(value,datetime):
        if value.tzinfo is None or value.utcoffset()!=timezone.utc.utcoffset(value): raise ValueError("datetime must be UTC")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
    if isinstance(value,Decimal):
        if not value.is_finite(): raise ValueError("non-finite Decimal")
        return format(value,"f")
    if is_dataclass(value): return {f.name:_json_value(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,Mapping): return {str(k):_json_value(v) for k,v in sorted(value.items(),key=lambda x:str(x[0]))}
    if isinstance(value,(tuple,list)): return [_json_value(v) for v in value]
    if isinstance(value,(str,int,bool)) or value is None: return value
    raise TypeError(f"unsupported canonical payload value: {type(value).__name__}")

def _time(value:Any)->datetime:
    for name in ("as_of","open_time","timestamp"):
        if hasattr(value,name): return getattr(value,name)
    raise ValueError("canonical value has no authoritative event time")

def build_canonical_event(value:Any,assessment:QualityAssessment,sequence:int)->tuple[CanonicalRecord,CanonicalEvent]:
    if type(value) not in TYPE_MAP: raise TypeError(f"unsupported canonical value: {type(value).__name__}")
    if not assessment.canonical_eligible or assessment.quality.quality_state is not DataQualityState.VALID:
        raise ValueError("only canonical-eligible VALID assessment can cross persistence boundary")
    if assessment.provenance_id is None or assessment.source_record_id is None or assessment.lineage_parent_id is None:
        raise ValueError("complete provenance/source/lineage is required for canonical persistence")
    payload=_json_value(value)
    record_type=TYPE_MAP[type(value)]
    instrument_id=getattr(value,"instrument_id",getattr(value,"canonical_instrument_id",""))
    semantic_identity={"type":record_type,"value":payload}
    record_id=deterministic_identity(semantic_identity)
    event_id=hashlib.sha256(("canonical:"+record_id).encode()).hexdigest()
    event=CanonicalEvent(event_id,record_id,record_type,sequence,_time(value),DataQualityState.VALID,assessment.provenance_id,assessment.source_record_id,assessment.lineage_parent_id,payload)
    record=CanonicalRecord(record_type,record_id,event_id,_time(value),instrument_id,payload,assessment.provenance_id,assessment.source_record_id,assessment.lineage_parent_id,DataQualityState.VALID,assessment.explanation.score)
    return record,event
