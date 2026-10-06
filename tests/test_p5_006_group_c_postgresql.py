from __future__ import annotations

import asyncio
import hashlib
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus
from meylux.queue import AsyncWorker, QueueEnvelope
from meylux.specialists.config import load_specialists_config
from meylux.specialists.runtime import (
    PAYLOAD_CONTRACT,
    SpecialistDispatcher,
    SpecialistWorkerHandler,
    specialist_policy,
)
from meylux.specialists.snapshot import InputSnapshotBuilder, SnapshotRecord
from meylux.specialists.group_c import analyze_s03, analyze_s17


RUN_INTEGRATION = os.environ.get("MEYLUX_RUN_P5006_POSTGRESQL") == "1"
UTC = timezone.utc


def _record(source_table, record_id, value, event_time, *, timeframe="15m"):
    identity = hashlib.sha256(record_id.encode()).hexdigest()
    ref = EvidenceRef(
        evidence_id=f"ev-{record_id}",
        source_type="postgresql",
        source_reference=f"{source_table}:{record_id}",
        identity_hash=identity,
        observed_at_utc=event_time,
        content_version="1.0.0",
        source_family="P4:GROUP-C",
        record_id=record_id,
        event_time=event_time,
        knowledge_time=event_time,
        timeframe=timeframe,
        venue="BINANCE",
    )
    metadata = {
        "symbol": "BTCUSDT",
        "venue": "BINANCE",
        "product": "spot",
        "timeframe": timeframe,
        "source_table": source_table,
        "record_id": record_id,
        "identity_hash": identity,
        "version": "1.0.0",
        "event_time": event_time,
        "knowledge_time": event_time,
    }
    return SnapshotRecord(
        record_id, FactStatus.VALID, value, event_time, event_time, (ref,), None, metadata
    )


def _snapshot(suffix: str):
    as_of = datetime.now(UTC).replace(microsecond=0)
    current_start = as_of - timedelta(hours=1)
    prior_start = as_of - timedelta(hours=2)
    current_end = as_of
    records = []
    for name, value in (
        ("VOLUME_SMA", "100"),
        ("RVOL", "2.5"),
        ("VOLUME_SPIKE", "1"),
        ("VOLUME_CLIMAX", "0"),
    ):
        records.append(_record(
            "meylux.calculated_indicator_vectors",
            f"p5-006:{suffix}:{name}",
            {"fact_name": name, "value": value, "status": "VALID"},
            current_end - timedelta(minutes=1),
        ))
    records.extend([
        _record(
            "meylux.volume_profile_sessions",
            f"p5-006:{suffix}:profile:prior",
            {
                "profile_interval": {"start": prior_start, "end": current_start, "boundary": "[start,end)"},
                "facts": {name: {"value": value, "status": "VALID", "reason": "volume_profile_analysis"}
                          for name, value in (("POC", "100"), ("VAH", "105"), ("VAL", "95"), ("HVN", "103"), ("LVN", "97"))},
                "trade_count": 20,
            },
            current_start,
        ),
        _record(
            "meylux.volume_profile_sessions",
            f"p5-006:{suffix}:profile:current",
            {
                "profile_interval": {"start": current_start, "end": current_end, "boundary": "[start,end)"},
                "facts": {name: {"value": value, "status": "VALID", "reason": "volume_profile_analysis"}
                          for name, value in (("POC", "101"), ("VAH", "106"), ("VAL", "96"), ("HVN", "104"), ("LVN", "98"))},
                "trade_count": 20,
            },
            current_end,
        ),
    ])
    for i, close in enumerate(("99", "100", "102")):
        opened = current_start + timedelta(minutes=15 * (i + 1))
        records.append(_record(
            "meylux.canonical_candles",
            f"p5-006:{suffix}:candle:{i}",
            {
                "open": Decimal(close) - 1,
                "high": Decimal(close) + 1,
                "low": Decimal(close) - 1,
                "close": Decimal(close),
                "close_time": opened + timedelta(minutes=15),
            },
            opened,
        ))
    return InputSnapshotBuilder().build(as_of=as_of, version="1.2.0", records=records)


@unittest.skipUnless(RUN_INTEGRATION, "requires isolated real PostgreSQL/Redis acceptance environment")
class TestP5006GroupCPostgreSQL(unittest.TestCase):
    def test_group_c_queue_postgres_readback_and_replay(self):
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
        queue_name = f"p5-006-group-c-{suffix}"
        from dataclasses import replace
        from meylux.queue.redis import RedisQueue

        queue = RedisQueue(
            client,
            replace(specialist_policy(config), name=queue_name, dlq_name=queue_name),
            f"worker-{suffix}",
        )
        snapshot = _snapshot(suffix)
        # Validate the exact integration snapshot through the semantic boundary before queue dispatch;
        # this keeps any semantic defect observable with its precise diagnostic rather than only as a DLQ state.
        for specialist_id, analyzer in (("S-03", analyze_s03), ("S-17", analyze_s17)):
            try:
                analyzer(snapshot, config)
            except Exception as exc:
                self.fail(f"{specialist_id} semantic preflight failed: {type(exc).__name__}: {exc}")
        handler = SpecialistWorkerHandler(pool, config)
        dispatcher = SpecialistDispatcher(queue, config)
        try:
            await queue.ensure_group()
            for specialist_id, required_code in (("S-03", ":CONDITION"), ("S-17", ":POSITION")):
                message_id = f"{specialist_id}:{suffix}"
                await dispatcher.publish(snapshot, message_id=message_id, specialist_id=specialist_id)
                outcome = await AsyncWorker(queue, handler, consumer=f"worker-{suffix}").run_once()
                self.assertIsNotNone(outcome)
                self.assertEqual(outcome.status, "ACKED")

                row = await pool.fetchrow(
                    "SELECT record_id, identity_hash, specialist_id, snapshot_id, status, payload_json, evidence_refs_json "
                    "FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id=$2",
                    snapshot.snapshot_id, specialist_id,
                )
                self.assertIsNotNone(row)
                self.assertEqual(row["record_id"], row["identity_hash"])
                payload = row["payload_json"]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                evidence = row["evidence_refs_json"]
                if isinstance(evidence, str):
                    evidence = json.loads(evidence)
                self.assertEqual(payload["specialist_id"], specialist_id)
                self.assertTrue(evidence)
                self.assertTrue(any(required_code in finding["code"] for finding in payload["findings"]))

                envelope = QueueEnvelope(
                    message_id=message_id,
                    idempotency_key=f"{specialist_id}:{snapshot.snapshot_id}:{config.identity_hash}",
                    payload_contract=PAYLOAD_CONTRACT,
                    payload={
                        "specialist_id": specialist_id,
                        "snapshot_id": snapshot.snapshot_id,
                        "snapshot_json": snapshot.serialize(),
                        "config_name": config.name,
                        "config_version": config.version,
                        "config_identity_hash": config.identity_hash,
                        "config_environment": config.environment,
                    },
                )
                await asyncio.gather(handler(envelope), handler(envelope))
                count = await pool.fetchval(
                    "SELECT count(*) FROM meylux.specialist_outputs WHERE snapshot_id=$1 AND specialist_id=$2",
                    snapshot.snapshot_id, specialist_id,
                )
                self.assertEqual(count, 1)
        finally:
            await client.aclose()
            await pool.close()


if __name__ == "__main__":
    unittest.main()
