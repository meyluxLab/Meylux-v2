"""Transactional-outbox relay to the governed normalized Redis stream."""
from __future__ import annotations
import json
from typing import Any
from contracts.event import STREAM
from meylux.persistence.canonical import CanonicalPersistence
_PUBLISH_LUA="""local idem=KEYS[2]
if redis.call('EXISTS',idem)==1 then return redis.call('GET',idem) end
local stream_id=redis.call('XADD',KEYS[1],'MAXLEN','~',ARGV[6],'*','event_id',ARGV[1],'record_id',ARGV[2],'event_type',ARGV[3],'event_time',ARGV[4],'body',ARGV[5])
redis.call('SET',idem,stream_id,'EX',ARGV[7])
return stream_id"""
class EventHandoffError(RuntimeError): pass
class CanonicalEventRelay:
    def __init__(self,persistence:CanonicalPersistence,redis_client:Any,*,max_batch:int=100,max_stream_length:int=100000,idempotency_ttl_seconds:int=86400)->None:
        if isinstance(max_batch,bool) or not isinstance(max_batch,int) or not 1<=max_batch<=1000: raise ValueError("max_batch must be 1..1000")
        if isinstance(max_stream_length,bool) or not isinstance(max_stream_length,int) or not 1000<=max_stream_length<=10000000: raise ValueError("max_stream_length must be 1000..10000000")
        if isinstance(idempotency_ttl_seconds,bool) or not isinstance(idempotency_ttl_seconds,int) or not 60<=idempotency_ttl_seconds<=604800: raise ValueError("idempotency_ttl_seconds must be 60..604800")
        self.persistence=persistence; self.redis=redis_client; self.max_batch=max_batch; self.max_stream_length=max_stream_length; self.idempotency_ttl_seconds=idempotency_ttl_seconds; self.stream=STREAM; self.idempotency_prefix="meylux:v2:canonical-event:"
    async def publish_pending(self)->int:
        rows=await self.persistence.pending_events(self.max_batch); published=0
        for row in rows:
            payload=row["payload_json"]
            if not isinstance(payload,str): payload=json.dumps(payload,sort_keys=True,separators=(",",":"))
            try:
                sid=await self.redis.eval(_PUBLISH_LUA,2,self.stream,self.idempotency_prefix+str(row["event_id"]),str(row["event_id"]),str(row["record_id"]),str(row["event_type"]),row["event_time"].isoformat(),payload,str(self.max_stream_length),str(self.idempotency_ttl_seconds))
            except Exception as exc: raise EventHandoffError(f"event publication failed for {row['event_id']}: {type(exc).__name__}") from exc
            sid=sid.decode() if isinstance(sid,bytes) else str(sid)
            await self.persistence.mark_event_published(str(row["event_id"]),sid); published+=1
        return published
