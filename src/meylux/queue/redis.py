"""Redis Streams transport boundary for the V2 async foundation."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
import uuid

from meylux.observability import HealthState, Severity, configure_logging, emit, new_correlation_id, set_context
from .model import DuplicateMessage, ProcessingOutcome, QueueEnvelope, QueueOverloaded, QueuePolicy

_LOG = configure_logging(logger_name="meylux.queue")

_ENQUEUE_LUA = """
local current = tonumber(redis.call('GET', KEYS[2]) or '0')
if current >= tonumber(ARGV[1]) then return 0 end
local idem = KEYS[3]
if ARGV[5] == '1' and redis.call('EXISTS', idem) == 1 then return -1 end
redis.call('INCR', KEYS[2])
local id = redis.call('XADD', KEYS[1], '*', 'body', ARGV[2])
if ARGV[5] == '1' then redis.call('SET', idem, ARGV[3], 'EX', ARGV[4]) end
return id
"""
_RETRY_TRANSITION_LUA = """
local existing = redis.call('GET', KEYS[3])
if existing then
  redis.call('XACK', KEYS[1], ARGV[1], ARGV[2]); return {2, existing}
end
local current = tonumber(redis.call('GET', KEYS[2]) or '0')
if current > tonumber(ARGV[4]) then return {0, ''} end
local retry_id = redis.call('XADD', KEYS[4], '*', 'body', ARGV[3])
redis.call('SET', KEYS[3], retry_id)
redis.call('XACK', KEYS[1], ARGV[1], ARGV[2]); return {1, retry_id}
"""
_DLQ_LUA = """
local current = tonumber(redis.call('GET', KEYS[2]) or '0')
redis.call('XADD', KEYS[3], '*', 'body', ARGV[3], 'reason', ARGV[4])
redis.call('XTRIM', KEYS[3], 'MINID', ARGV[5])
local acked = redis.call('XACK', KEYS[1], ARGV[1], ARGV[2])
if acked == 1 and current > 0 then redis.call('DECR', KEYS[2]) end
return acked
"""
_ACK_LUA = """
local acked = redis.call('XACK', KEYS[1], ARGV[1], ARGV[2])
if acked == 1 then
  local current = tonumber(redis.call('GET', KEYS[2]) or '0')
  if current > 0 then redis.call('DECR', KEYS[2]) end
  if ARGV[3] ~= '' then redis.call('DEL', ARGV[3]) end
end
return acked
"""

def _decode(value: Any) -> Any:
    return value.decode() if isinstance(value, bytes) else value

def _id_ms(stream_id: str) -> int:
    return int(stream_id.split('-', 1)[0])

class RedisQueue:
    """Bounded Redis Streams queue using consumer-group delivery."""
    def __init__(self, client: Any, policy: QueuePolicy, group: str) -> None:
        self._client = client; self.policy = policy; self.group = group
        self.stream = f"meylux:v2:queue:{policy.name}"
        self.dlq_stream = f"meylux:v2:dlq:{policy.dlq_name}"
        self.backlog_key = f"meylux:v2:backlog:{policy.name}"
        self.idempotency_prefix = f"meylux:v2:idem:{policy.name}:"
        self.retry_prefix = f"meylux:v2:retry:{policy.name}:"

    def _ctx(self, envelope: QueueEnvelope | None = None, *, operation: str = "") -> dict[str, str]:
        return {"correlation_id": new_correlation_id(), "queue": self.policy.name, "queue_operation": operation, **({"message_id": envelope.message_id} if envelope else {})}

    async def ensure_group(self) -> None:
        from redis.exceptions import ResponseError
        try:
            await self._client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
            emit(_LOG, Severity.INFO, "queue.group.ready", queue=self.policy.name, group=self.group)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc): raise

    async def publish(self, envelope: QueueEnvelope) -> str:
        with _Context(self._ctx(envelope, operation="publish")):
            if envelope.payload_contract != self.policy.payload_contract: raise ValueError("payload contract does not match queue policy")
            idem_key = self.idempotency_prefix + envelope.idempotency_key
            result = await self._client.eval(_ENQUEUE_LUA, 3, self.stream, self.backlog_key, idem_key, self.policy.max_backlog, envelope.to_json(), envelope.message_id, self.policy.retention_seconds, '1' if self.policy.idempotency_required else '0')
            if result in (0, b"0", "0"):
                emit(_LOG, Severity.WARNING, "queue.overload", health_state=HealthState.OVERLOAD.value, max_backlog=self.policy.max_backlog); raise QueueOverloaded(self.policy.name)
            if result in (-1, b"-1", "-1"):
                emit(_LOG, Severity.INFO, "queue.duplicate", outcome="DUPLICATE"); raise DuplicateMessage(envelope.idempotency_key)
            entry_id = _decode(result); emit(_LOG, Severity.INFO, "queue.published", outcome="ENQUEUED", entry_id=entry_id); return entry_id

    async def read(self, consumer: str, block_ms: int = 1000) -> tuple[str, QueueEnvelope] | None:
        with _Context({"correlation_id": new_correlation_id(), "queue": self.policy.name, "queue_operation": "read", "consumer": consumer}):
            rows = await self._client.xreadgroup(self.group, consumer, streams={self.stream: ">"}, count=1, block=block_ms)
            if not rows: return None
            _, entries = rows[0]; entry_id, fields = entries[0]; body = fields.get(b"body", fields.get("body")); envelope = QueueEnvelope.from_json(_decode(body))
            set_context(message_id=envelope.message_id)
            emit(_LOG, Severity.DEBUG, "queue.delivered", outcome="DELIVERED", entry_id=_decode(entry_id), attempt=envelope.attempt)
            return _decode(entry_id), envelope

    async def ack(self, entry_id: str, envelope: QueueEnvelope | None = None) -> None:
        with _Context(self._ctx(envelope, operation="ack")):
            retry_key = self.retry_prefix + envelope.idempotency_key if envelope is not None and envelope.attempt > 1 else ""
            await self._client.eval(_ACK_LUA, 2, self.stream, self.backlog_key, self.group, entry_id, retry_key)
            emit(_LOG, Severity.INFO, "queue.acked", outcome="ACKED", entry_id=entry_id)

    async def retry_or_dlq(self, entry_id: str, envelope: QueueEnvelope, reason: str) -> ProcessingOutcome:
        with _Context(self._ctx(envelope, operation="retry_or_dlq")):
            if envelope.attempt < self.policy.max_attempts:
                retry = QueueEnvelope(message_id=envelope.message_id, idempotency_key=f"{envelope.idempotency_key}:attempt:{envelope.attempt + 1}", payload_contract=envelope.payload_contract, payload=envelope.payload, attempt=envelope.attempt + 1)
                delay = self.policy.backoff_seconds * (2 ** (envelope.attempt - 1))
                if delay: await asyncio.sleep(delay)
                retry_key = self.retry_prefix + retry.idempotency_key
                result = await self._client.eval(_RETRY_TRANSITION_LUA, 4, self.stream, self.backlog_key, retry_key, self.stream, self.group, entry_id, retry.to_json(), self.policy.max_backlog)
                state = int(result[0]) if isinstance(result, (list, tuple)) else int(result)
                outcome = "BACKPRESSURE" if state == 0 else "RETRY"
                emit(_LOG, Severity.WARNING if state == 0 else Severity.INFO, "queue.retry", outcome=outcome, reason=reason, attempt=envelope.attempt)
                return ProcessingOutcome("RETRY", envelope.attempt, outcome if state == 0 else reason)
            now = await self._client.time(); now_ms = int(now[0]) * 1000 + int(now[1]) // 1000; cutoff = max(0, now_ms - self.policy.retention_seconds * 1000)
            await self._client.eval(_DLQ_LUA, 3, self.stream, self.backlog_key, self.dlq_stream, self.group, entry_id, envelope.to_json(), reason, f"{cutoff}-0")
            emit(_LOG, Severity.ERROR, "queue.dlq", outcome="DLQ", reason=reason, attempt=envelope.attempt)
            return ProcessingOutcome("DLQ", envelope.attempt, reason)

    async def recover_stale(self, consumer: str, min_idle_ms: int) -> list[tuple[str, QueueEnvelope]]:
        pending = await self._client.xpending_range(self.stream, self.group, min="-", max="+", count=self.policy.max_concurrency, idle=min_idle_ms); recovered = []
        for item in pending:
            entry_id = _decode(item["message_id"]); claimed = await self._client.xclaim(self.stream, self.group, consumer, min_idle_time=min_idle_ms, message_ids=[entry_id])
            if not claimed: continue
            fields = claimed[0][1]; body = fields.get(b"body", fields.get("body")); recovered.append((entry_id, QueueEnvelope.from_json(_decode(body))))
        if recovered: emit(_LOG, Severity.WARNING, "queue.recovered_stale", outcome="RECOVERED", count=len(recovered), consumer=consumer)
        return recovered

    async def recover_retry(self, entry_id: str, envelope: QueueEnvelope) -> ProcessingOutcome:
        with _Context(self._ctx(envelope, operation="recover_retry")):
            if envelope.attempt >= self.policy.max_attempts: return ProcessingOutcome("DLQ", envelope.attempt, "RECOVERY_BOUNDARY")
            retry = QueueEnvelope(message_id=envelope.message_id, idempotency_key=f"{envelope.idempotency_key}:attempt:{envelope.attempt + 1}", payload_contract=envelope.payload_contract, payload=envelope.payload, attempt=envelope.attempt + 1); retry_key = self.retry_prefix + retry.idempotency_key
            result = await self._client.eval(_RETRY_TRANSITION_LUA, 4, self.stream, self.backlog_key, retry_key, self.stream, self.group, entry_id, retry.to_json(), self.policy.max_backlog); state = int(result[0]) if isinstance(result, (list, tuple)) else int(result)
            emit(_LOG, Severity.WARNING, "queue.retry.recovered", outcome="RECOVERED_RETRY" if state in {1,2} else "BACKPRESSURE", attempt=envelope.attempt)
            return ProcessingOutcome("RETRY", envelope.attempt, "RECOVERED_RETRY" if state in {1,2} else "BACKPRESSURE")

    async def retention_sweep(self) -> int:
        now = await self._client.time(); now_ms = int(now[0]) * 1000 + int(now[1]) // 1000; cutoff = max(0, now_ms - self.policy.retention_seconds * 1000); groups = await self._client.xinfo_groups(self.stream); oldest_pending = None
        for group in groups:
            group_name = _decode(group.get("name", group.get(b"name"))); pending_count = int(group.get("pending", group.get(b"pending", 0)) or 0)
            if pending_count:
                summary = await self._client.xpending(self.stream, group_name); oldest = summary.get("min") if isinstance(summary, dict) else summary[1]
                if oldest:
                    oldest_ms = _id_ms(_decode(oldest)); oldest_pending = oldest_ms if oldest_pending is None else min(oldest_pending, oldest_ms)
        safe_cutoff = cutoff if oldest_pending is None else min(cutoff, oldest_pending); main_deleted = int(await self._client.xtrim(self.stream, minid=f"{safe_cutoff}-0", approximate=False)); dlq_deleted = int(await self._client.xtrim(self.dlq_stream, minid=f"{cutoff}-0", approximate=False)); return main_deleted + dlq_deleted

Handler = Callable[[QueueEnvelope], Awaitable[None]]

class _Context:
    def __init__(self, values: dict[str, str]): self.values = values; self.token = None
    def __enter__(self): self.token = set_context(**self.values); return self
    def __exit__(self, exc_type, exc, tb): self_token = self.token; clear = __import__('meylux.observability', fromlist=['clear_context']).clear_context; clear(self_token); return False

class AsyncWorker:
    """Bounded worker execution loop around one queue and one handler."""
    def __init__(self, queue: RedisQueue, handler: Handler, *, consumer: str | None = None) -> None:
        self.queue = queue; self.handler = handler; self.consumer = consumer or f"worker-{uuid.uuid4().hex}"; self._stop = asyncio.Event()
    def stop(self) -> None: self._stop.set()
    async def run_once(self) -> ProcessingOutcome | None:
        item = await self.queue.read(self.consumer)
        if item is None: return None
        entry_id, envelope = item
        try:
            await asyncio.wait_for(self.handler(envelope), timeout=self.queue.policy.timeout_seconds)
        except asyncio.TimeoutError:
            emit(_LOG, Severity.ERROR, "worker.timeout", health_state=HealthState.DEGRADED.value, entry_id=entry_id, attempt=envelope.attempt)
            return await self.queue.retry_or_dlq(entry_id, envelope, "TIMEOUT")
        except Exception as exc:
            emit(_LOG, Severity.ERROR, "worker.failure", health_state=HealthState.DEGRADED.value, entry_id=entry_id, error_type=type(exc).__name__)
            return await self.queue.retry_or_dlq(entry_id, envelope, f"FAILURE:{type(exc).__name__}")
        await self.queue.ack(entry_id, envelope); emit(_LOG, Severity.INFO, "worker.completed", outcome="ACKED", entry_id=entry_id, attempt=envelope.attempt); return ProcessingOutcome("ACKED", envelope.attempt)
    async def run(self) -> None:
        await self.queue.ensure_group(); tasks: set[asyncio.Task[ProcessingOutcome | None]] = set()
        while not self._stop.is_set():
            while len(tasks) < self.queue.policy.max_concurrency and not self._stop.is_set():
                task = asyncio.create_task(self.run_once()); tasks.add(task); task.add_done_callback(tasks.discard); await asyncio.sleep(0)
            if tasks: await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            else: await asyncio.sleep(0)
