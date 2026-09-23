"""Deterministic Phase-5 configuration validation."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any,Mapping
from contracts.specialist import canonical_json
class SpecialistConfigError(ValueError): pass
@dataclass(frozen=True,slots=True)
class SpecialistConfig:
    name:str; schema_version:str; version:str; environment:str; provenance:str; parameters:Mapping[str,Mapping[str,Any]]; identity_hash:str
    @classmethod
    def from_mapping(cls,raw):
        if not isinstance(raw,Mapping): raise SpecialistConfigError("configuration root must be a mapping")
        req=("name","schema_version","configuration_version","environment","provenance","parameters","safety")
        missing=[x for x in req if x not in raw]
        if missing: raise SpecialistConfigError("missing configuration fields: "+",".join(missing))
        safety=raw["safety"]
        expected={"read_only":True,"allow_private_provider_access":False,"allow_trading":False,"allow_capital_movement":False,"allow_custody":False}
        if safety!=expected: raise SpecialistConfigError("configuration cannot weaken frozen read-only/security invariants")
        for k in ("name","schema_version","configuration_version","environment","provenance"):
            if not isinstance(raw[k],str) or not raw[k]: raise SpecialistConfigError(f"{k} must be a non-empty string")
        if not isinstance(raw["parameters"],Mapping): raise SpecialistConfigError("parameters must be a mapping")
        params={}
        for name,spec in raw["parameters"].items():
            if not isinstance(name,str) or not name: raise SpecialistConfigError("parameter names must be non-empty strings")
            if not isinstance(spec,Mapping): raise SpecialistConfigError(f"parameter {name} must be a mapping")
            for field in ("type","unit","value"):
                if field not in spec: raise SpecialistConfigError(f"parameter {name} missing {field}")
            ptype,unit,value=spec["type"],spec["unit"],spec["value"]
            if ptype not in {"integer","decimal","string","boolean"}: raise SpecialistConfigError(f"parameter {name} has unsupported type")
            if not isinstance(unit,str) or not unit: raise SpecialistConfigError(f"parameter {name} unit is required")
            value=_convert(ptype,value,name)
            if "minimum" in spec and value<_convert(ptype,spec["minimum"],name+".minimum"): raise SpecialistConfigError(f"parameter {name} violates minimum")
            if "maximum" in spec and value>_convert(ptype,spec["maximum"],name+".maximum"): raise SpecialistConfigError(f"parameter {name} violates maximum")
            if "allowed" in spec:
                allowed=spec["allowed"]
                if not isinstance(allowed,list) or value not in [_convert(ptype,x,name+".allowed") for x in allowed]: raise SpecialistConfigError(f"parameter {name} is outside allowed values")
            params[name]={**dict(spec),"value":value}
        material={"name":raw["name"],"schema_version":raw["schema_version"],"configuration_version":raw["configuration_version"],"environment":raw["environment"],"provenance":raw["provenance"],"parameters":params,"safety":safety}
        digest=hashlib.sha256(canonical_json(material).encode()).hexdigest()
        return cls(raw["name"],raw["schema_version"],raw["configuration_version"],raw["environment"],raw["provenance"],params,digest)
    def ref(self):
        from contracts.specialist import SpecialistConfigRef
        return SpecialistConfigRef(self.name,self.version,self.identity_hash,self.environment)
    def parameter(self,name): 
        if name not in self.parameters: raise SpecialistConfigError(f"unknown parameter: {name}")
        return self.parameters[name]["value"]
def _convert(ptype,value,field):
    if ptype=="integer":
        if isinstance(value,bool) or not isinstance(value,int): raise SpecialistConfigError(f"{field} must be integer")
        return value
    if ptype=="decimal":
        if isinstance(value,float): raise SpecialistConfigError(f"{field} must not be float")
        try: value=Decimal(str(value))
        except Exception as exc: raise SpecialistConfigError(f"{field} must be Decimal-compatible") from exc
        if not value.is_finite(): raise SpecialistConfigError(f"{field} must be finite")
        return value
    if ptype=="string":
        if not isinstance(value,str): raise SpecialistConfigError(f"{field} must be string")
        return value
    if not isinstance(value,bool): raise SpecialistConfigError(f"{field} must be boolean")
    return value
def load_specialists_config(path):
    try: raw=json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: raise SpecialistConfigError("specialists.yaml must use the repository JSON-compatible YAML subset") from exc
    return SpecialistConfig.from_mapping(raw)
