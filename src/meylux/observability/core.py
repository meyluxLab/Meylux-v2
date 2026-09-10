"""Deterministic and bounded structured observability primitives."""
from __future__ import annotations
import contextvars, json, logging, re, sys, time, uuid
from enum import Enum
from typing import Any, Mapping, TextIO
_CONTEXT=contextvars.ContextVar("meylux_observability_context",default={})
_SECRET_KEY=re.compile(r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|access[_-]?key|connection[_-]?string|authorization|credential)",re.I)
_SECRET_VALUE=re.compile(r"(?i)\\b(?:bearer|basic)\\s+[A-Za-z0-9._~+/=-]+|-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",re.S)
class Severity(str,Enum): DEBUG="DEBUG"; INFO="INFO"; WARNING="WARNING"; ERROR="ERROR"; CRITICAL="CRITICAL"
class HealthState(str,Enum): NORMAL="NORMAL"; DEGRADED="DEGRADED"; OVERLOAD="OVERLOAD"; DEPENDENCY_FAILURE="DEPENDENCY_FAILURE"; UNAVAILABLE="UNAVAILABLE"
class ObservabilityLimits:
    def __init__(self,max_event_bytes=16384,max_fields=32,max_string_length=2048,max_events_per_second=100):
        if min(max_event_bytes,max_fields,max_string_length,max_events_per_second)<=0: raise ValueError("observability limits must be positive")
        self.max_event_bytes=max_event_bytes; self.max_fields=max_fields; self.max_string_length=max_string_length; self.max_events_per_second=max_events_per_second
class _RateFilter(logging.Filter):
    def __init__(self,limit):
        self.limit=limit; self.second=-1; self.count=0; self.error_count=0; self.critical_count=0
    def filter(self,record):
        second=int(time.time())
        if second!=self.second: self.second,self.count,self.error_count,self.critical_count=second,0,0,0
        # Reserve one bounded slot per second for ERROR and one for CRITICAL.
        # This preserves critical diagnostics under normal-budget saturation
        # without allowing either severity to bypass the total emission bound.
        if record.levelno >= logging.CRITICAL:
            if self.critical_count >= 1: return False
            self.critical_count += 1
            return True
        if record.levelno >= logging.ERROR:
            if self.error_count >= 1: return False
            self.error_count += 1
            return True
        if self.count>=self.limit: return False
        self.count+=1; return True
def set_context(**values):
    current=dict(_CONTEXT.get())
    for key,value in values.items():
        if value is not None: current[key]=str(value)
    return _CONTEXT.set(current)
def clear_context(token): _CONTEXT.reset(token)
def get_context(): return dict(_CONTEXT.get())
def new_correlation_id(): return uuid.uuid4().hex
def scrub(value,*,limits=None,_depth=0):
    limits=limits or ObservabilityLimits()
    if _depth>6: return "[TRUNCATED]"
    if isinstance(value,Mapping):
        out={}
        for i,(key,item) in enumerate(value.items()):
            if i>=limits.max_fields: break
            key_s=str(key); out[key_s]="[REDACTED]" if _SECRET_KEY.search(key_s) else scrub(item,limits=limits,_depth=_depth+1)
        return out
    if isinstance(value,(list,tuple)): return [scrub(x,limits=limits,_depth=_depth+1) for x in list(value)[:limits.max_fields]]
    if isinstance(value,str): return _SECRET_VALUE.sub("[REDACTED]",value)[:limits.max_string_length]
    if isinstance(value,(int,float,bool)) or value is None: return value
    return str(value)[:limits.max_string_length]
def _bounded(event,limits):
    cleaned=scrub(event,limits=limits); raw=json.dumps(cleaned,ensure_ascii=False,separators=(",",":"),sort_keys=True)
    if len(raw.encode())<=limits.max_event_bytes: return cleaned
    required={k:cleaned[k] for k in ("timestamp","severity","event","correlation_id") if k in cleaned}; required["observability_truncated"]=True
    if len(json.dumps(required,ensure_ascii=False,separators=(",",":")).encode())>limits.max_event_bytes: return {"event":"OBSERVABILITY_TRUNCATED","observability_truncated":True}
    return required
class JsonEventFormatter(logging.Formatter):
    def __init__(self,limits=None): super().__init__(); self.limits=limits or ObservabilityLimits()
    def format(self,record):
        fields=getattr(record,"event_data",{}); event={"timestamp":record.created,"severity":record.levelname,"event":getattr(record,"event_name",record.name),**get_context(),**(dict(fields) if isinstance(fields,Mapping) else {})}
        return json.dumps(_bounded(event,self.limits),ensure_ascii=False,separators=(",",":"),sort_keys=True)
def configure_logging(*,stream=None,logger_name="meylux",limits=None):
    limits=limits or ObservabilityLimits(); logger=logging.getLogger(logger_name); logger.setLevel(logging.DEBUG); logger.propagate=False
    for h in list(logger.handlers): logger.removeHandler(h)
    handler=logging.StreamHandler(stream or sys.stderr); handler.setFormatter(JsonEventFormatter(limits)); handler.addFilter(_RateFilter(limits.max_events_per_second)); logger.addHandler(handler); return logger
def emit(logger,severity,event,**fields):
    level=logging._nameToLevel.get(severity.value if isinstance(severity, Severity) else str(severity),logging.INFO); logger.log(level,event,extra={"event_name":event,"event_data":fields})