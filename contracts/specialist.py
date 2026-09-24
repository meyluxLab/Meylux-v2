"""Phase-5 specialist contracts: deterministic, provider-neutral, Stage-1 independent."""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

class SpecialistStatus(str, Enum):
    SUCCESS="SUCCESS"; PARTIAL="PARTIAL"; INSUFFICIENT_DATA="INSUFFICIENT_DATA"; UNAVAILABLE_INPUT="UNAVAILABLE_INPUT"
    SKIPPED="SKIPPED"; DISABLED="DISABLED"; FAILED="FAILED"; TIMEOUT="TIMEOUT"

class FactStatus(str, Enum):
    VALID="VALID"; PARTIAL="PARTIAL"; INSUFFICIENT_DATA="INSUFFICIENT_DATA"; UNAVAILABLE="UNAVAILABLE"
    INVALID="INVALID"; STALE="STALE"; CONTRADICTORY="CONTRADICTORY"

def _utc(v: datetime, field: str) -> datetime:
    if not isinstance(v, datetime): raise TypeError(f"{field} must be datetime")
    if v.tzinfo is None or v.utcoffset() is None or v.utcoffset()!=timezone.utc.utcoffset(v): raise ValueError(f"{field} must be timezone-aware UTC")
    return v

def _token(v: object, field: str) -> str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{field} must be a non-empty string")
    return v

def _normalise(v: Any) -> Any:
    if isinstance(v,Decimal):
        if not v.is_finite(): raise ValueError("non-finite Decimal is forbidden")
        return {"__decimal__":format(v,"f")}
    if isinstance(v,datetime): return _utc(v,"datetime").isoformat().replace("+00:00","Z")
    if isinstance(v,float): raise TypeError("float values are forbidden in authoritative specialist contracts")
    if isinstance(v,Mapping):
        if any(not isinstance(k,str) for k in v):
            raise TypeError("mapping keys must be strings in authoritative specialist contracts")
        return {k:_normalise(v[k]) for k in sorted(v)}
    if isinstance(v,(tuple,list)): return [_normalise(x) for x in v]
    if isinstance(v,(str,int,bool)) or v is None: return v
    if isinstance(v,Enum): return v.value
    raise TypeError(f"unsupported contract value: {type(v).__name__}")

def canonical_json(v: Any) -> str:
    return json.dumps(_normalise(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)

def identity_hash(v: Any) -> str:
    return hashlib.sha256(canonical_json(v).encode()).hexdigest()

_FORBIDDEN=frozenset({"specialist_output","specialist_output_ref","specialist_id","finding","findings"})
def _no_specialist_dependency(v: Any) -> None:
    if isinstance(v,Mapping):
        for k,x in v.items():
            if str(k).lower() in _FORBIDDEN: raise ValueError("Stage-1 InputSnapshot cannot contain specialist output/dependency fields")
            _no_specialist_dependency(x)
    elif isinstance(v,(tuple,list)):
        for x in v: _no_specialist_dependency(x)

def _freeze(value: Any) -> Any:
    """Recursively copy supported Snapshot content into intrinsically read-only containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return value

@dataclass(frozen=True,slots=True)
class EvidenceRef:
    evidence_id:str; source_type:str; source_reference:str; identity_hash:str
    observed_at_utc:datetime|None=None; content_version:str|None=None
    source_family:str|None=None; record_id:str|None=None; event_time:datetime|None=None
    knowledge_time:datetime|None=None; timeframe:str|None=None; venue:str|None=None
    def __post_init__(self):
        for v,f in ((self.evidence_id,"evidence_id"),(self.source_type,"source_type"),(self.source_reference,"source_reference"),(self.identity_hash,"identity_hash")): _token(v,f)
        if len(self.identity_hash)!=64 or any(c not in "0123456789abcdef" for c in self.identity_hash.lower()): raise ValueError("identity_hash must be a 64-character hexadecimal SHA-256 value")
        if self.observed_at_utc is not None: _utc(self.observed_at_utc,"observed_at_utc")
        if self.content_version is not None: _token(self.content_version,"content_version")
        for v,f in ((self.source_family,"source_family"),(self.record_id,"record_id"),(self.timeframe,"timeframe"),(self.venue,"venue")):
            if v is not None: _token(v,f)
        if self.event_time is not None: _utc(self.event_time,"event_time")
        if self.knowledge_time is not None: _utc(self.knowledge_time,"knowledge_time")
    def as_dict(self): return {"evidence_id":self.evidence_id,"source_type":self.source_type,"source_reference":self.source_reference,"identity_hash":self.identity_hash,"observed_at_utc":self.observed_at_utc,"content_version":self.content_version,"source_family":self.source_family,"record_id":self.record_id,"event_time":self.event_time,"knowledge_time":self.knowledge_time,"timeframe":self.timeframe,"venue":self.venue}

@dataclass(frozen=True,slots=True)
class SnapshotFact:
    fact_id:str; status:FactStatus; value:Any=None; knowledge_time:datetime|None=None
    evidence_refs:tuple[EvidenceRef,...]=(); reason:str|None=None; metadata:Mapping[str,Any]|None=None
    def __post_init__(self):
        _token(self.fact_id,"fact_id")
        if not isinstance(self.status,FactStatus): raise TypeError("status must be FactStatus")
        if self.knowledge_time is None: raise ValueError("knowledge_time is mandatory for SnapshotFact")
        _utc(self.knowledge_time,"knowledge_time")
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("SnapshotFact evidence_refs must be a tuple")
        if self.status is FactStatus.VALID and not self.evidence_refs:
            raise ValueError("authoritative SnapshotFact requires at least one EvidenceRef")
        if any(not isinstance(ref, EvidenceRef) for ref in self.evidence_refs):
            raise TypeError("SnapshotFact evidence_refs must contain EvidenceRef values")
        if self.status is not FactStatus.VALID and (not isinstance(self.reason,str) or not self.reason.strip()):
            raise ValueError("non-VALID SnapshotFact requires an explicit reason")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise TypeError("SnapshotFact metadata must be a mapping")
        if isinstance(self.metadata, Mapping):
            if "event_time" in self.metadata:
                _utc(self.metadata["event_time"],"metadata.event_time")
            if "knowledge_time" in self.metadata:
                _utc(self.metadata["knowledge_time"],"metadata.knowledge_time")
                if self.metadata["knowledge_time"] != self.knowledge_time:
                    raise ValueError("metadata.knowledge_time must match SnapshotFact.knowledge_time")
            if "event_time" in self.metadata and "knowledge_time" in self.metadata:
                # Equality is permitted only when explicitly supplied by the authoritative source.
                pass
        _no_specialist_dependency(self.value); _normalise(self.value)
        _no_specialist_dependency(self.metadata); _normalise(self.metadata or {})
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "metadata", _freeze(self.metadata or {}))
        if self.status is FactStatus.VALID and self.value is None: raise ValueError("VALID fact requires a value")
        if len({r.evidence_id for r in self.evidence_refs})!=len(self.evidence_refs): raise ValueError("duplicate evidence_id in fact")
    def as_dict(self): return {"fact_id":self.fact_id,"status":self.status.value,"value":self.value,"knowledge_time":self.knowledge_time,"evidence_refs":[r.as_dict() for r in self.evidence_refs],"reason":self.reason,"metadata":self.metadata}

@dataclass(frozen=True,slots=True)
class InputSnapshot:
    snapshot_id:str; as_of:datetime; version:str; facts:tuple[SnapshotFact,...]; provenance_refs:tuple[EvidenceRef,...]=()
    def __post_init__(self):
        _token(self.snapshot_id,"snapshot_id"); _token(self.version,"version"); _utc(self.as_of,"as_of")
        if len({f.fact_id for f in self.facts})!=len(self.facts): raise ValueError("InputSnapshot fact_id values must be unique")
        for f in self.facts:
            if f.knowledge_time is not None and f.knowledge_time>self.as_of: raise ValueError("InputSnapshot cannot include lookahead facts")
        expected=identity_hash({"version":self.version,"as_of":self.as_of,"facts":sorted((f.as_dict() for f in self.facts),key=lambda x:x["fact_id"]),"provenance_refs":sorted((r.as_dict() for r in self.provenance_refs),key=lambda x:x["evidence_id"])})
        if self.snapshot_id!=expected: raise ValueError("snapshot_id does not match deterministic snapshot identity")
    @classmethod
    def build(cls,*,as_of,version,facts,provenance_refs=()):
        material={"version":version,"as_of":as_of,"facts":sorted((f.as_dict() for f in facts),key=lambda x:x["fact_id"]),"provenance_refs":sorted((r.as_dict() for r in provenance_refs),key=lambda x:x["evidence_id"])}
        return cls(identity_hash(material),as_of,version,facts,provenance_refs)
    def as_dict(self): return {"snapshot_id":self.snapshot_id,"as_of":self.as_of,"version":self.version,"facts":sorted((f.as_dict() for f in self.facts),key=lambda x:x["fact_id"]),"provenance_refs":sorted((r.as_dict() for r in self.provenance_refs),key=lambda x:x["evidence_id"])}
    def serialize(self): return canonical_json(self.as_dict())

@dataclass(frozen=True,slots=True)
class SpecialistConfigRef:
    name:str; version:str; identity_hash:str; environment:str
    def __post_init__(self):
        for v,f in ((self.name,"name"),(self.version,"version"),(self.identity_hash,"identity_hash"),(self.environment,"environment")): _token(v,f)
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.identity_hash): raise ValueError("config identity_hash must be a 64-character hexadecimal SHA-256 value")

@dataclass(frozen=True,slots=True)
class SpecialistRequest:
    specialist_id:str; snapshot:InputSnapshot; config:SpecialistConfigRef
    def __post_init__(self): _token(self.specialist_id,"specialist_id")

@dataclass(frozen=True,slots=True)
class SpecialistFinding:
    code:str; status:SpecialistStatus; value:Any=None; reason:str=""; confidence:Decimal|None=None; evidence_refs:tuple[EvidenceRef,...]=()
    def __post_init__(self):
        _token(self.code,"code")
        if not isinstance(self.status,SpecialistStatus): raise TypeError("status must be SpecialistStatus")
        if not self.reason: raise ValueError("reason is required")
        _no_specialist_dependency(self.value); _normalise(self.value)
        if self.confidence is not None:
            if not isinstance(self.confidence,Decimal) or not self.confidence.is_finite() or not Decimal("0")<=self.confidence<=Decimal("1"): raise ValueError("confidence must be a finite Decimal in [0,1]")
        if len({r.evidence_id for r in self.evidence_refs})!=len(self.evidence_refs): raise ValueError("duplicate evidence_id in finding")
    def as_dict(self): return {"code":self.code,"status":self.status.value,"value":self.value,"reason":self.reason,"confidence":self.confidence,"evidence_refs":[r.as_dict() for r in self.evidence_refs]}

@dataclass(frozen=True,slots=True)
class SpecialistOutput:
    specialist_id:str; output_version:str; snapshot_id:str; snapshot_version:str; config:SpecialistConfigRef
    status:SpecialistStatus; reason:str; findings:tuple[SpecialistFinding,...]=(); evidence_refs:tuple[EvidenceRef,...]=()
    def __post_init__(self):
        for v,f in ((self.specialist_id,"specialist_id"),(self.output_version,"output_version"),(self.snapshot_id,"snapshot_id"),(self.snapshot_version,"snapshot_version"),(self.reason,"reason")): _token(v,f)
        if not isinstance(self.status,SpecialistStatus): raise TypeError("status must be SpecialistStatus")
        if len({f.code for f in self.findings})!=len(self.findings): raise ValueError("finding codes must be unique")
        evidence={r.evidence_id for r in self.evidence_refs}
        for f in self.findings: evidence.update(r.evidence_id for r in f.evidence_refs)
        if self.status in {SpecialistStatus.SUCCESS,SpecialistStatus.PARTIAL} and not evidence: raise ValueError("SUCCESS/PARTIAL output requires evidence")
    def as_dict(self):
        return {"specialist_id":self.specialist_id,"output_version":self.output_version,"snapshot_id":self.snapshot_id,"snapshot_version":self.snapshot_version,"config":{"name":self.config.name,"version":self.config.version,"identity_hash":self.config.identity_hash,"environment":self.config.environment},"status":self.status.value,"reason":self.reason,"findings":[f.as_dict() for f in self.findings],"evidence_refs":[r.as_dict() for r in self.evidence_refs]}
    @property
    def identity_hash(self): return identity_hash(self.as_dict())
    def serialize(self): return canonical_json(self.as_dict())
