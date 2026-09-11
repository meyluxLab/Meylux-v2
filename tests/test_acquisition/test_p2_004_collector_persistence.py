from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
)
from meylux.acquisition.collector import AcquisitionCollector
from meylux.acquisition.persistence import RawStagingRepository


UTC = timezone.utc


def envelope(provider: str, sequence: str = "1") -> AcquisitionEnvelope:
    identity = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
    return AcquisitionEnvelope(
        provider=identity,
        instrument=InstrumentIdentity("BTCUSDT", "BTCUSDT"),
        provenance=Provenance(f"{provider}-test", identity, "TEST"),
        event_type=EventType.TRADE,
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        received_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        state=AcquisitionState.AVAILABLE,
        payload={"price": "100.00", "qty": "1.0"},
        source_sequence=sequence,
    )


class FakeConnection:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.calls: list[tuple[str, tuple]] = []

    async def execute(self, query: str, *args):
        self.calls.append((query, args))
        event_id = args[0]
        if event_id in self.rows:
            return "INSERT 0 0"
        self.rows[event_id] = {
            "event_id": event_id,
            "canonical_bytes": args[14],
            "identity_hash": args[15],
            "payload_json": args[13],
        }
        return "INSERT 0 1"

    async def fetchrow(self, query: str, *args):
        return self.rows.get(args[0])


class FakeSink:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def persist(self, item):
        key = item.event_id
        duplicate = key in self.seen
        if not duplicate:
            self.seen.append(key)
        from meylux.acquisition.persistence import PersistenceResult
        return PersistenceResult(key, not duplicate)


class FakeAdapter:
    def __init__(self, provider: str, fail: bool = False) -> None:
        self.provider = provider
        self.fail = fail

    @property
    def identity(self):
        return self.provider

    async def stream(self, symbols, **kwargs):
        yield envelope(self.provider)
        if self.fail:
            raise RuntimeError(f"{self.provider} stream failure")


class CollectorPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_persistence_is_deterministic_and_idempotent(self):
        connection = FakeConnection()
        repo = RawStagingRepository(connection)
        first = await repo.persist(envelope("binance"))
        second = await repo.persist(envelope("binance"))
        self.assertTrue(first.inserted)
        self.assertFalse(second.inserted)
        self.assertEqual(first.event_id, second.event_id)
        self.assertEqual(connection.rows[first.event_id]["canonical_bytes"], envelope("binance").canonical_bytes())
        self.assertEqual(await repo.fetch(first.event_id), connection.rows[first.event_id])

    async def test_replay_same_evidence_does_not_create_duplicate(self):
        sink = FakeSink()
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, sink, max_queue_size=2)
        await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1)
        first_count = len(sink.seen)
        await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1)
        self.assertEqual(first_count, 1)
        self.assertEqual(collector.stats.duplicates, 1)

    async def test_bounded_queue_applies_backpressure_without_drop(self):
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, FakeSink(), max_queue_size=1)
        item = envelope("binance")
        await collector.publish(item)
        self.assertEqual(collector.queue_size, 1)
        blocked = asyncio.create_task(collector.publish(item))
        await asyncio.sleep(0)
        self.assertFalse(blocked.done())
        queued = collector._queue.get_nowait()
        collector._queue.task_done()
        await blocked
        self.assertIs(queued, item)
        self.assertEqual(collector.queue_size, 1)

    async def test_provider_failure_isolated_from_other_provider(self):
        sink = FakeSink()
        collector = AcquisitionCollector(
            {"binance": FakeAdapter("binance", fail=True), "mexc": FakeAdapter("mexc")},
            sink,
            max_queue_size=4,
        )
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1)
        self.assertEqual(len(sink.seen), 2)
        self.assertEqual(stats.failures, 1)

    async def test_collector_is_finite_and_leaves_no_active_consumer(self):
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, FakeSink())
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1)
        self.assertEqual(stats.persisted, 1)
        self.assertEqual(collector.queue_size, 0)

    async def test_migration_is_append_only_and_explicitly_staging(self):
        from pathlib import Path
        migration = Path("migrations/versions/0002_raw_acquisition_staging.sql").read_text()
        self.assertIn("CREATE TABLE IF NOT EXISTS meylux.raw_acquisition_events", migration)
        self.assertIn("ON CONFLICT (event_id) DO NOTHING", migration)
        self.assertIn("Raw/staging is evidence only", migration)


if __name__ == "__main__":
    unittest.main()
