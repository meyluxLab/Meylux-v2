"""Stage-1 S-10 queue dispatch and worker boundary."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from meylux.observability import HealthState, Severity, configure_logging, emit
from meylux.queue import AsyncWorker, QueueEnvelope, QueuePolicy, RedisQueue, RetryableProcessingError
from meylux.specialists.config import load_specialists_config
from meylux.specialists.persistence import SpecialistPersistence
from meylux.specialists.s10 import S10DataQualityAnalyst, S10SemanticError, snapshot_from_json

_LOG = configure_logging(logger_name="meylux.specialist")

PAYLOAD_CONTRACT = "CTR-P5-SPECIALIST-SNAPSHOT-1.0"
QUEUE_NAME = "specialist-stage1"
DLQ_NAME = "specialist-stage1"
SPECIALIST_ID = "S-10"


def specialist_policy(config: Any) -> QueuePolicy:
    return QueuePolicy(
        name=QUEUE_NAME,
        owner="ROL-V2-001",
        producer="stage1-snapshot-dispatch",
        consumer="worker-specialist",
        purpose="execute deterministic Stage-1 S-10 against authoritative InputSnapshot",
        payload_contract=PAYLOAD_CONTRACT,
        dlq_name=DLQ_NAME,
        max_backlog=int(config.parameter("max_backlog")),
        max_concurrency=int(config.parameter("max_concurrency")),
        max_attempts=int(config.parameter("max_attempts")),
        timeout_seconds=float(config.parameter("execution_timeout_ms")) / 1000.0,
        backoff_seconds=float(config.parameter("retry_backoff_ms")) / 1000.0,
        retention_seconds=int(config.parameter("retention_seconds")),
        ordering="FIFO_ENQUEUE_AND_DELIVERY",
        idempotency_required=True,
        recovery_method="consumer-group stale-claim",
    )


class SpecialistDispatcher:
    def __init__(self, queue: RedisQueue, config: Any) -> None:
        self.queue = queue
        self.config = config

    async def publish(self, snapshot: Any, *, message_id: str | None = None) -> str:
        if not hasattr(snapshot, "serialize"):
            raise ValueError("dispatcher requires an InputSnapshot")
        envelope = QueueEnvelope(
            message_id=message_id or snapshot.snapshot_id,
            idempotency_key=f"{SPECIALIST_ID}:{snapshot.snapshot_id}:{self.config.identity_hash}",
            payload_contract=PAYLOAD_CONTRACT,
            payload={
                "specialist_id": SPECIALIST_ID,
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_json": snapshot.serialize(),
                "config_name": self.config.name,
                "config_version": self.config.version,
                "config_identity_hash": self.config.identity_hash,
                "config_environment": self.config.environment,
            },
        )
        entry = await self.queue.publish(envelope)
        emit(_LOG, Severity.INFO, "specialist.dispatch", queue=QUEUE_NAME, specialist_id=SPECIALIST_ID, snapshot_id=snapshot.snapshot_id, entry_id=entry, outcome="ENQUEUED")
        return entry


class SpecialistWorkerHandler:
    def __init__(self, pool: Any, config: Any) -> None:
        self.pool = pool
        self.config = config

    async def __call__(self, envelope: QueueEnvelope) -> None:
        if envelope.payload_contract != PAYLOAD_CONTRACT:
            raise S10SemanticError("queue payload contract mismatch")
        payload = envelope.payload
        required = ("specialist_id", "snapshot_id", "snapshot_json", "config_name", "config_version", "config_identity_hash", "config_environment")
        missing = [key for key in required if key not in payload]
        if missing:
            raise S10SemanticError(f"queue payload missing required fields: {missing}")
        if payload["specialist_id"] != SPECIALIST_ID:
            raise S10SemanticError("worker-specialist received an unauthorized specialist")
        if (
            payload["config_name"] != self.config.name
            or payload["config_version"] != self.config.version
            or payload["config_identity_hash"] != self.config.identity_hash
            or payload["config_environment"] != self.config.environment
        ):
            raise S10SemanticError("queue payload configuration identity mismatch")

        snapshot = snapshot_from_json(payload["snapshot_json"])
        if snapshot.snapshot_id != payload["snapshot_id"]:
            raise S10SemanticError("queue payload snapshot identity mismatch")

        analyst = S10DataQualityAnalyst(
            self.config.ref(),
            max_findings=int(self.config.parameter("max_findings")),
            max_evidence_refs=int(self.config.parameter("max_evidence_refs")),
        )
        try:
            output = analyst.analyze(snapshot)
        except S10SemanticError:
            raise
        except Exception as exc:
            raise S10SemanticError("unexpected S-10 semantic/contract failure") from exc

        try:
            async with self.pool.acquire() as connection:
                persistence = SpecialistPersistence(connection)
                inserted = await persistence.persist(output)
                persisted = await persistence.fetch_by_identity(output.identity_hash)
        except Exception as exc:
            module = type(exc).__module__
            if module.startswith("asyncpg") or isinstance(exc, (ConnectionError, TimeoutError)):
                raise RetryableProcessingError("transient specialist persistence failure") from exc
            raise S10SemanticError("unexpected specialist persistence contract failure") from exc
        if persisted is None:
            raise RuntimeError("specialist output was not readable after persistence")
        emit(
            _LOG,
            Severity.INFO,
            "specialist.completed",
            health_state=HealthState.OK.value,
            specialist_id=SPECIALIST_ID,
            snapshot_id=snapshot.snapshot_id,
            output_identity_hash=output.identity_hash,
            inserted=inserted,
            readback=True,
            status=output.status.value,
        )


async def run_specialist_worker() -> None:
    config = load_specialists_config(os.environ.get("MEYLUX_SPECIALISTS_CONFIG", "config/specialists.yaml"))
    pool = await __import__("asyncpg").create_pool(
        host=os.environ["MEYLUX_DB_HOST"],
        port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
        database=os.environ["MEYLUX_DB_NAME"],
        user=os.environ["MEYLUX_DB_USER"],
        password=os.environ["MEYLUX_DB_PASSWORD"],
        min_size=1,
        max_size=max(2, int(config.parameter("max_concurrency"))),
    )
    import redis.asyncio as redis
    client = redis.from_url(os.environ.get("MEYLUX_REDIS_URL", "redis://redis:6379/0"), decode_responses=False)
    policy = specialist_policy(config)
    queue = RedisQueue(client, policy, "specialist-workers")
    worker = AsyncWorker(queue, SpecialistWorkerHandler(pool, config), consumer="worker-specialist")
    try:
        await worker.run()
    finally:
        await client.aclose()
        await pool.close()
