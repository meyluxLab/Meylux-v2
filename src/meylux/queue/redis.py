"""Redis Streams transport boundary for the V2 async foundation."""
from __future__ import annotations
import asyncio, uuid
from collections.abc import Awaitable, Callable
from typing import Any
from meylux.observability import HealthState, Severity, clear_context, configure_logging, emit, new_correlation_id, set_context
from .model import DuplicateMessage, NonRetryableProcessingError, ProcessingOutcome, QueueEnvelope, QueueOverloaded, QueuePolicy
_LOG=configure_logging(logger_name="meylux.queue")
_ENQUEUE_LUA="""local current=tonumber(redis.call('GET',KEYS[2]) or '0')
if current>=tonumber(ARGV[1]) then return 0 end
local idem=KEYS[3]
if ARGV[5]=='1' and redis.call('EXISTS',idem)==1 then return -1 end
redis.call('INCR',KEYS[2]); local id=redis.call('XADD',KEYS[1],'*','body',ARGV[2])
if ARGV[5]=='1' then redis.call('SET',idem,ARGV[3],'EX',ARGV[4]) end
return id"""
_RETRY_TRANSITION_LUA="""local existing=redis.call('GET',KEYS[3])
if existing then redis.call('XACK',KEYS[1],ARGV[1],ARGV[2]); return {2,existing} end
local current=tonumber(redis.call('GET',KEYS[2]) or '0')
if current>tonumber(ARGV[4]) then return {0,''} end
local retry_id=redis.call('XADD',KEYS[4],'*','body',ARGV[3]); redis.call('SET',KEYS[3],retry_id)
redis.call('XACK',KEYS[1],ARGV[1],ARGV[2]); return {1,retry_id}"""
_DLQ_LUA="""local current=tonumber(redis.call('GET',KEYS[2]) or '0')
redis.call('XADD',KEYS[3],'*','body',ARGV[3],'reason',ARGV[4]); redis.call('XTRIM',KEYS[3],'MINID',ARGV[5])
local acked=redis.call('XACK',KEYS[1],ARGV[1],ARGV[2]); if acked==1 and current>0 then redis.call('DECR',KEYS[2]) end; return acked"""
_ACK_LUA="""local acked=redis.call('XACK',KEYS[1],ARGV[1],ARGV[2])
if acked==1 then local current=tonumber(redis.call('GET',KEYS[2]) or '0'); if current>0 then redis.call('DECR',KEYS[2]) end; if ARGV[3]~='' then redis.call('DEL',ARGV[3]) end end
return acked"""
def _decode(v): return v.decode() if isinstance(v,bytes) else v
def _id_ms(v): return int(v.split('-',1)[0])
class RedisQueue:
    def __init__(self,client,policy,group):
        self._client=client; self.policy=policy; self.group=group
        self.stream=f"meylux:v2:queue:{policy.name}"; self.dlq_stream=f"meylux:v2:dlq:{policy.dlq_name}"
        self.backlog_key=f"meylux:v2:backlog:{policy.name}"; self.idempotency_prefix=f"meylux:v2:idem:{policy.name}:"
        self.retry_prefix=f"meylux:v2:retry:{policy.name}:"
    async def ensure_group(self):
        from redis.exceptions import ResponseError
        try: await self._client.xgroup_create(self.stream,self.group,id="0",mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc): raise
    async def publish(self,envelope):
        if envelope.payload_contract!=self.policy.payload_contract: raise ValueError("payload contract does not match queue policy")
        result=await self._client.eval(_ENQUEUE_LUA,3,self.stream,self.backlog_key,self.idempotency_prefix+envelope.idempotency_key,self.policy.max_backlog,envelope.to_json(),envelope.message_id,self.policy.retention_seconds,'1' if self.policy.idempotency_required else '0')
        if result in (0,b"0","0"): raise QueueOverloaded(self.policy.name)
        if result in (-1,b"-1","-1"): raise DuplicateMessage(envelope.idempotency_key)
        return _decode(result)
    async def read(self,consumer,block_ms=1000):
        rows=await self._client.xreadgroup(self.group,consumer,streams={self.stream:">"},count=1,block=block_ms)
        if not rows:return None
        _,entries=rows[0]; eid,fields=entries[0]; return _decode(eid),QueueEnvelope.from_json(_decode(fields.get(b"body",fields.get("body"))))
    async def ack(self,eid,envelope=None):
        retry_key=self.retry_prefix+envelope.idempotency_key if envelope is not None and envelope.attempt>1 else ""
        await self._client.eval(_ACK_LUA,2,self.stream,self.backlog_key,self.group,eid,retry_key)
    async def dead_letter(self,eid,envelope,reason):
        now=await self._client.time(); cutoff=max(0,int(now[0])*1000+int(now[1])//1000-self.policy.retention_seconds*1000)
        await self._client.eval(_DLQ_LUA,3,self.stream,self.backlog_key,self.dlq_stream,self.group,eid,envelope.to_json(),reason,f"{cutoff}-0")
        return ProcessingOutcome("DLQ",envelope.attempt,reason)
    async def retry_or_dlq(self,eid,envelope,reason):
        if envelope.attempt<self.policy.max_attempts:
            retry=QueueEnvelope(envelope.message_id,f"{envelope.idempotency_key}:attempt:{envelope.attempt+1}",envelope.payload_contract,envelope.payload,envelope.attempt+1)
            delay=self.policy.backoff_seconds*(2**(envelope.attempt-1))
            if delay: await asyncio.sleep(delay)
            result=await self._client.eval(_RETRY_TRANSITION_LUA,4,self.stream,self.backlog_key,self.retry_prefix+retry.idempotency_key,self.stream,self.group,eid,retry.to_json(),self.policy.max_backlog)
            state=int(result[0]) if isinstance(result,(list,tuple)) else int(result)
            return ProcessingOutcome("RETRY",envelope.attempt,"BACKPRESSURE" if state==0 else reason)
        return await self.dead_letter(eid,envelope,reason)
    async def recover_stale(self,consumer,min_idle_ms):
        pending=await self._client.xpending_range(self.stream,self.group,min="-",max="+",count=self.policy.max_concurrency,idle=min_idle_ms); out=[]
        for item in pending:
            eid=_decode(item["message_id"]); claimed=await self._client.xclaim(self.stream,self.group,consumer,min_idle_time=min_idle_ms,message_ids=[eid])
            if claimed: out.append((eid,QueueEnvelope.from_json(_decode(claimed[0][1].get(b"body",claimed[0][1].get("body"))))))
        return out
    async def recover_retry(self,eid,envelope):
        if envelope.attempt>=self.policy.max_attempts:return ProcessingOutcome("DLQ",envelope.attempt,"RECOVERY_BOUNDARY")
        retry=QueueEnvelope(envelope.message_id,f"{envelope.idempotency_key}:attempt:{envelope.attempt+1}",envelope.payload_contract,envelope.payload,envelope.attempt+1)
        result=await self._client.eval(_RETRY_TRANSITION_LUA,4,self.stream,self.backlog_key,self.retry_prefix+retry.idempotency_key,self.stream,self.group,eid,retry.to_json(),self.policy.max_backlog)
        return ProcessingOutcome("RETRY",envelope.attempt,"RECOVERED_RETRY" if int(result[0]) in {1,2} else "BACKPRESSURE")
    async def retention_sweep(self):
        now=await self._client.time(); cutoff=max(0,int(now[0])*1000+int(now[1])//1000-self.policy.retention_seconds*1000)
        return int(await self._client.xtrim(self.stream,minid=f"{cutoff}-0",approximate=False))+int(await self._client.xtrim(self.dlq_stream,minid=f"{cutoff}-0",approximate=False))
Handler=Callable[[Any],Awaitable[None]]
class _Context:
    def __init__(self,v): self.v=v; self.t=None
    def __enter__(self): self.t=set_context(**self.v); return self
    def __exit__(self,*args): clear_context(self.t); return False
class AsyncWorker:
    def __init__(self,queue,handler,*,consumer=None):
        self.queue=queue; self.handler=handler; self.consumer=consumer or f"worker-{uuid.uuid4().hex}"; self._stop=asyncio.Event()
    def stop(self): self._stop.set()
    async def run_once(self):
        item=await self.queue.read(self.consumer)
        if item is None:return None
        eid,envelope=item
        with _Context({"correlation_id":new_correlation_id(),"queue":self.queue.policy.name,"queue_operation":"worker","consumer":self.consumer,"message_id":envelope.message_id,"correlation_key":envelope.message_id}):
            try:
                await asyncio.wait_for(self.handler(envelope),timeout=self.queue.policy.timeout_seconds)
            except asyncio.TimeoutError: return await self.queue.retry_or_dlq(eid,envelope,"TIMEOUT")
            except NonRetryableProcessingError as exc: return await self.queue.dead_letter(eid,envelope,f"SEMANTIC:{type(exc).__name__}")
            except Exception as exc: return await self.queue.retry_or_dlq(eid,envelope,f"FAILURE:{type(exc).__name__}")
            await self.queue.ack(eid,envelope); return ProcessingOutcome("ACKED",envelope.attempt)
    async def run(self):
        await self.queue.ensure_group(); tasks=set()
        while not self._stop.is_set():
            while len(tasks)<self.queue.policy.max_concurrency and not self._stop.is_set():
                task=asyncio.create_task(self.run_once()); tasks.add(task); task.add_done_callback(tasks.discard); await asyncio.sleep(0)
            if tasks: await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            else: await asyncio.sleep(0)
