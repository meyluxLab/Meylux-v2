from __future__ import annotations

import asyncio
from dataclasses import replace
import json
import os
import resource
import statistics
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus
from meylux.specialists.snapshot import InputSnapshotBuilder, SnapshotRecord
from meylux.queue import QueueEnvelope
from meylux.queue.redis import AsyncWorker, RedisQueue
from meylux.specialists.config import load_specialists_config
from meylux.specialists.runtime import (
    PAYLOAD_CONTRACT, SpecialistDispatcher, SpecialistWorkerHandler, S10SemanticError, specialist_policy,
)

RUN_INTEGRATION = os.environ.get("MEYLUX_RUN_P5004_REDIS_INTEGRATION") == "1"
UTC = timezone.utc


def _integration_snapshot(suffix: str) -> InputSnapshot:
    as_of = datetime.now(UTC).replace(microsecond=0)
    event = as_of - timedelta(minutes=1)
    facts = []
    values = {
        "EMA": Decimal("100"), "RSI": Decimal("70"), "MACD": Decimal("1"),
        "MACD_SIGNAL": Decimal("0.5"), "MACD_HISTOGRAM": Decimal("0.5"),
        "ADX": Decimal("25"), "BOLLINGER_UPPER": Decimal("110"),
        "BOLLINGER_MIDDLE": Decimal("100"), "BOLLINGER_LOWER": Decimal("90"),
        "BOLLINGER_BANDWIDTH": Decimal("0.05"), "ATR": Decimal("2"),
        "HISTORICAL_VOLATILITY": Decimal("0.6"), "ATR_PERCENTILE": Decimal("75"),
        "VOLATILITY_EXPANSION_RATIO": Decimal("1.2"),
    }
    records = [("CLOSE", {"close": Decimal("101")}, "meylux.canonical_candles")]
    records.extend((name, {"fact_name": name, "value": value, "status": "valid", "reason": "controlled integration fixture"},
                    "meylux.calculated_indicator_vectors") for name, value in values.items())
    for name, value, table in records:
        record_id = f"p5-004:{suffix}:BTCUSDT:15m:{name}"
        identity = __import__("hashlib").sha256(record_id.encode()).hexdigest()
        ref = EvidenceRef(
            evidence_id=f"ev-{suffix}-{name}", source_type="postgresql",
            source_reference=f"{table}:{record_id}", identity_hash=identity,
            observed_at_utc=event, content_version="1.0.0",
            source_family="canonical_market" if table.endswith("canonical_candles") else "indicator",
            record_id=record_id, event_time=event, knowledge_time=event,
            timeframe="15m", venue="BINANCE",
        )
        metadata = {
            "symbol": "BTCUSDT", "venue": "BINANCE", "product": "spot", "timeframe": "15m",
            "source_table": table, "record_id": record_id, "identity_hash": identity,
            "version": "1.0.0", "event_time": event, "knowledge_time": event,
        }
        facts.append(SnapshotRecord(record_id, FactStatus.VALID, value, event, event, (ref,), None, metadata))
    return InputSnapshotBuilder().build(as_of=as_of, version="1.2.0", records=tuple(facts))


def _percentile(values, percentile):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))]


@unittest.skipUnless(RUN_INTEGRATION, "requires isolated real Redis/PostgreSQL acceptance environment")
class TestP5004RedisPostgreSQL(unittest.TestCase):
    def test_group_a_queue_worker_postgres_readback_replay_and_baseline(self):
        asyncio.run(self._run())

    async def _run(self):
        import asyncpg
        import redis.asyncio as redis

        config = load_specialists_config(Path("config/specialists.yaml"))
        pool = await asyncpg.create_pool(
            host=os.environ["MEYLUX_DB_HOST"], port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
            database=os.environ["MEYLUX_DB_NAME"], user=os.environ["MEYLUX_DB_USER"],
            password=os.environ["MEYLUX_DB_PASSWORD"], min_size=1, max_size=4,
        )
        client = redis.from_url(os.environ.get("MEYLUX_REDIS_URL", "redis://redis:6379/0"), decode_responses=False)
        suffix = uuid.uuid4().hex
        queue_name = f"p5-004-group-a-{suffix}"
        queue = RedisQueue(client, replace(specialist_policy(config), name=queue_name, dlq_name=queue_name), f"worker-{suffix}")
        snapshot = _integration_snapshot(suffix)
        handler = SpecialistWorkerHandler(pool, config)
        dispatcher = SpecialistDispatcher(queue, config)
        cold_ms, warm_samples = {}, []
        cpu_start = resource.getrusage(resource.RUSAGE_SELF)
        try:
            await queue.ensure_group()
            for specialist_id in ("S-01", "S-06", "S-08"):
                message_id = f"{specialist_id}:{suffix}"
                started = time.perf_counter_ns()
                await dispatcher.publish(snapshot, message_id=message_id, specialist_id=specialist_id)
                outcome = await AsyncWorker(queue, handler, consumer=f"worker-{suffix}").run_once()
                self.assertIsNotNone(outcome)
                self.assertEqual(outcome.status, "ACKED")
                cold_ms[specialist_id] = (time.perf_counter_ns() - started) / 1_000_000

                rows = await pool.fetch(
                    "SELECT record_id,identity_hash,snapshot_id,specialist_id,status,payload_json,evidence_refs_json "
                    "FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id=$2",
                    snapshot.snapshot_id, specialist_id,
                )
                self.assertEqual(len(rows), 1)
                row = rows[0]
                payload = row["payload_json"]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                evidence = row["evidence_refs_json"]
                if isinstance(evidence, str):
                    evidence = json.loads(evidence)
                self.assertEqual(row["record_id"], row["identity_hash"])
                self.assertEqual(payload["specialist_id"], specialist_id)
                self.assertEqual(payload["snapshot_id"], snapshot.snapshot_id)
                self.assertTrue(evidence)
                self.assertTrue(all(item["record_id"] and item["identity_hash"] and item["knowledge_time"] for item in evidence))

                envelope = QueueEnvelope(
                    message_id=message_id,
                    idempotency_key=f"{specialist_id}:{snapshot.snapshot_id}:{config.identity_hash}",
                    payload_contract=PAYLOAD_CONTRACT,
                    payload={
                        "specialist_id": specialist_id, "snapshot_id": snapshot.snapshot_id,
                        "snapshot_json": snapshot.serialize(), "config_name": config.name,
                        "config_version": config.version, "config_identity_hash": config.identity_hash,
                        "config_environment": config.environment,
                    },
                )
                # The queue path above has already persisted the output. Concurrent handler
                # replay must converge on the same append-only identity and one read-back row.
                await asyncio.gather(handler(envelope), handler(envelope))
                count = await pool.fetchval(
                    "SELECT count(*) FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id=$2",
                    snapshot.snapshot_id, specialist_id,
                )
                self.assertEqual(count, 1)
                if specialist_id == "S-01":
                    with self.assertRaises(asyncpg.InsufficientPrivilegeError):
                        await pool.execute(
                            "UPDATE meylux.specialist_outputs SET reason='forbidden' WHERE identity_hash=$1",
                            row["identity_hash"],
                        )
                    with self.assertRaises(asyncpg.InsufficientPrivilegeError):
                        await pool.execute(
                            "DELETE FROM meylux.specialist_outputs WHERE identity_hash=$1",
                            row["identity_hash"],
                        )
                    unchanged = await pool.fetchval(
                        "SELECT count(*) FROM meylux.specialist_outputs WHERE identity_hash=$1",
                        row["identity_hash"],
                    )
                    self.assertEqual(unchanged, 1)
                for _ in range(10):
                    warm_start = time.perf_counter_ns()
                    await handler(envelope)
                    warm_samples.append((time.perf_counter_ns() - warm_start) / 1_000_000)

            # Exercise first-write concurrency on a new deterministic output identity.
            race_snapshot = _integration_snapshot(f"race-{suffix}")
            race_payload = {
                "specialist_id": "S-08", "snapshot_id": race_snapshot.snapshot_id,
                "snapshot_json": race_snapshot.serialize(), "config_name": config.name,
                "config_version": config.version, "config_identity_hash": config.identity_hash,
                "config_environment": config.environment,
            }
            race_envelope = QueueEnvelope(
                message_id=f"S-08:race:{suffix}",
                idempotency_key=f"S-08:{race_snapshot.snapshot_id}:{config.identity_hash}",
                payload_contract=PAYLOAD_CONTRACT, payload=race_payload,
            )
            await asyncio.gather(handler(race_envelope), handler(race_envelope))
            race_count = await pool.fetchval(
                "SELECT count(*) FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id='S-08'",
                race_snapshot.snapshot_id,
            )
            self.assertEqual(race_count, 1)

            invalid_envelope = QueueEnvelope(
                message_id=f"invalid:{suffix}", idempotency_key=f"invalid:{suffix}",
                payload_contract=PAYLOAD_CONTRACT,
                payload={"specialist_id": "S-02", "snapshot_id": snapshot.snapshot_id,
                    "snapshot_json": snapshot.serialize(), "config_name": config.name,
                    "config_version": config.version, "config_identity_hash": config.identity_hash,
                    "config_environment": config.environment},
            )
            with self.assertRaises(S10SemanticError):
                await handler(invalid_envelope)

            cpu_end = resource.getrusage(resource.RUSAGE_SELF)
            print("P5-004_PERF_BASELINE " + json.dumps({
                "revision": os.environ.get("GITHUB_SHA", "CI checkout revision"),
                "environment": "Docker Foundation CI; real Redis 7.4.6 + TimescaleDB/PostgreSQL; controlled synthetic Snapshot fixture",
                "workload": "one InputSnapshot, sequential first queue/worker execution for S-01/S-06/S-08, then concurrent duplicate handler replay and 30 warm persistence/read-back replays",
                "sample_size": {"cold_first_path_per_specialist": 3, "warm_replay": len(warm_samples)},
                "condition": "first path after DB/Redis setup; warm replay after persisted identity exists",
                "concurrency": {"initial_queue_workers": 1, "duplicate_replay": 2},
                "cold_first_path_ms": cold_ms,
                "warm_replay_ms": {"p50": statistics.median(warm_samples), "p95": _percentile(warm_samples, 0.95)},
                "process_resource_delta": {"user_cpu_seconds": cpu_end.ru_utime - cpu_start.ru_utime,
                    "system_cpu_seconds": cpu_end.ru_stime - cpu_start.ru_stime,
                    "max_rss_platform_units": cpu_end.ru_maxrss},
                "interpretation": "CI baseline only; CONTROL must separately measure deployed runtime CPU/RAM/disk/queue and latency.",
            }, sort_keys=True))
        finally:
            await client.aclose()
            await pool.close()


if __name__ == "__main__":
    unittest.main()
