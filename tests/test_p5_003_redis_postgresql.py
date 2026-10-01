from __future__ import annotations

import asyncio
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot, SnapshotFact
from meylux.queue.model import DuplicateMessage, QueuePolicy
from meylux.queue.redis import AsyncWorker, RedisQueue
from meylux.specialists.config import load_specialists_config
from meylux.specialists.runtime import SpecialistDispatcher, SpecialistWorkerHandler, specialist_policy

RUN_INTEGRATION = os.environ.get("MEYLUX_RUN_P5003_REDIS_INTEGRATION") == "1"


@unittest.skipUnless(
    RUN_INTEGRATION,
    "requires the isolated real Redis/PostgreSQL integration environment",
)
class TestP5003RedisPostgreSQLTransport(unittest.TestCase):
    def test_redis_worker_s10_append_only_persistence_and_readback(self):
        asyncio.run(self._run_real_path())

    async def _run_real_path(self):
        import asyncpg
        import redis.asyncio as redis

        config = load_specialists_config(Path("config/specialists.yaml"))
        pool = await asyncpg.create_pool(
            host=os.environ["MEYLUX_DB_HOST"],
            port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
            database=os.environ["MEYLUX_DB_NAME"],
            user=os.environ["MEYLUX_DB_USER"],
            password=os.environ["MEYLUX_DB_PASSWORD"],
            min_size=1,
            max_size=2,
        )
        client = redis.from_url(
            os.environ.get("MEYLUX_REDIS_URL", "redis://redis:6379/0"),
            decode_responses=False,
        )
        suffix = uuid.uuid4().hex
        queue_name = f"p5-003-transport-{suffix}"
        policy = QueuePolicy(
            **{
                **specialist_policy(config).__dict__,
                "name": queue_name,
                "dlq_name": queue_name,
            }
        )
        queue = RedisQueue(client, policy, f"worker-{suffix}")
        snapshot = None
        try:
            await queue.ensure_group()
            knowledge_time = datetime.now(timezone.utc).replace(microsecond=0)
            event_time = knowledge_time - timedelta(minutes=1)
            ref = EvidenceRef(
                evidence_id=f"transport-{suffix}",
                source_type="p3-quality",
                source_reference=f"quality/transport/{suffix}",
                identity_hash="e" * 64,
                observed_at_utc=event_time,
                content_version="1.0.0",
                source_family="quality",
                record_id=f"transport-{suffix}",
                event_time=event_time,
                knowledge_time=knowledge_time,
                timeframe="15m",
                venue="BINANCE",
            )
            fact = SnapshotFact(
                fact_id=f"transport-fact-{suffix}",
                status=FactStatus.VALID,
                value={
                    "provider_id": "binance",
                    "venue": "BINANCE",
                    "timeframe": "15m",
                    "value": Decimal("100.25"),
                },
                knowledge_time=knowledge_time,
                evidence_refs=(ref,),
                metadata={
                    "event_time": event_time,
                    "knowledge_time": knowledge_time,
                    "venue": "BINANCE",
                    "timeframe": "15m",
                },
            )
            snapshot = InputSnapshot.build(
                as_of=knowledge_time,
                version="1.0.0",
                facts=(fact,),
                provenance_refs=(ref,),
            )
            dispatcher = SpecialistDispatcher(queue, config)
            await dispatcher.publish(snapshot, message_id=snapshot.snapshot_id)

            outcome = await AsyncWorker(
                queue,
                SpecialistWorkerHandler(pool, config),
                consumer=f"worker-{suffix}",
            ).run_once()
            self.assertIsNotNone(outcome)
            self.assertEqual(outcome.status, "ACKED")

            rows = await pool.fetch(
                "SELECT identity_hash,snapshot_id,status,payload_json,evidence_refs_json "
                "FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id='S-10'",
                snapshot.snapshot_id,
            )
            self.assertEqual(len(rows), 1)
            row = rows[0]
            payload = row["payload_json"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            evidence = row["evidence_refs_json"]
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            self.assertEqual(row["snapshot_id"], snapshot.snapshot_id)
            self.assertEqual(payload["snapshot_id"], snapshot.snapshot_id)
            self.assertEqual(payload["specialist_id"], "S-10")
            self.assertEqual(row["status"], "SUCCESS")
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["observed_at_utc"], event_time.isoformat().replace("+00:00", "Z"))
            self.assertEqual(evidence[0]["event_time"], event_time.isoformat().replace("+00:00", "Z"))
            self.assertEqual(evidence[0]["knowledge_time"], knowledge_time.isoformat().replace("+00:00", "Z"))
            self.assertEqual(evidence[0]["timeframe"], "15m")
            self.assertEqual(evidence[0]["venue"], "BINANCE")

            # The queue's real Redis idempotency marker must reject a replay
            # rather than enqueueing the same authoritative Snapshot twice.
            with self.assertRaises(DuplicateMessage):
                await dispatcher.publish(snapshot, message_id=snapshot.snapshot_id)

            # The persisted output remains append-only and replay/read-back
            # semantics are provided by the same persistence implementation.
            async with pool.acquire() as connection:
                from meylux.specialists.persistence import SpecialistPersistence

                persisted = await SpecialistPersistence(connection).fetch_by_identity(row["identity_hash"])
                self.assertIsNotNone(persisted)
                self.assertEqual(persisted["identity_hash"], row["identity_hash"])
                replay_inserted = await SpecialistPersistence(connection).persist(
                    # Reconstruct the same output through the canonical Snapshot
                    # and runtime analyst, using the exact worker configuration.
                    __import__("meylux.specialists.s10", fromlist=["S10DataQualityAnalyst"])
                    .S10DataQualityAnalyst(
                        config.ref(),
                        max_findings=int(config.parameter("max_findings")),
                        max_evidence_refs=int(config.parameter("max_evidence_refs")),
                    )
                    .analyze(snapshot)
                )
                self.assertFalse(replay_inserted)
                reread = await SpecialistPersistence(connection).fetch_by_identity(row["identity_hash"])
                self.assertEqual(reread["identity_hash"], row["identity_hash"])
        finally:
            if snapshot is not None:
                idem_key = queue.idempotency_prefix + f"S-10:{snapshot.snapshot_id}:{config.identity_hash}"
                await client.delete(queue.stream, queue.backlog_key, queue.dlq_stream, idem_key)
            await client.aclose()
            await pool.close()


if __name__ == "__main__":
    unittest.main()
