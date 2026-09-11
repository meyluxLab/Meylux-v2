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
    ProviderError,
    Provenance,
)
from meylux.acquisition.collector import AcquisitionCollector
from meylux.acquisition.persistence import PersistenceResult, RawStagingRepository
from meylux.acquisition.transport import AcquisitionQueuePublisher


UTC = timezone.utc


def envelope(provider: str, sequence: str = "1", state: AcquisitionState = AcquisitionState.AVAILABLE) -> AcquisitionEnvelope:
    identity = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
    provider_error = None if state is AcquisitionState.AVAILABLE else ProviderError("TEST_STATE", "test", "synthetic acquisition state")
    return AcquisitionEnvelope(
        provider=identity,
        instrument=InstrumentIdentity("BTCUSDT", "BTCUSDT"),
        provenance=Provenance(f"{provider}-test", identity, "TEST"),
        event_type=EventType.TRADE,
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        received_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        state=state,
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
    def __init__(self, failures_before_success: int = 0, always_fail: bool = False) -> None:
        self.seen: list[str] = []
        self.providers: list[str] = []
        self.sequences: list[str | None] = []
        self.attempts: dict[str, int] = {}
        self.failures_before_success = failures_before_success
        self.always_fail = always_fail

    async def persist(self, item):
        key = item.event_id
        self.providers.append(item.provider.provider_id)
        self.sequences.append(item.source_sequence)
        attempt = self.attempts.get(key, 0) + 1
        self.attempts[key] = attempt
        if self.always_fail or attempt <= self.failures_before_success:
            raise RuntimeError("synthetic persistence failure")
        duplicate = key in self.seen
        if not duplicate:
            self.seen.append(key)
        return PersistenceResult(key, not duplicate)


class FakeAdapter:
    def __init__(self, provider: str, *, sequences: tuple[str, ...] = ("1",), fail_after: bool = False) -> None:
        self.identity = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
        self.sequences = sequences
        self.fail_after = fail_after
        self.calls: list[tuple[tuple[str, ...], dict]] = []

    async def stream(self, symbols, **kwargs):
        self.calls.append((tuple(symbols), dict(kwargs)))
        for sequence in self.sequences:
            yield envelope(self.identity.provider_id, sequence)
        if self.fail_after:
            raise RuntimeError(f"{self.identity.provider_id} stream failure")


class FakeQueue:
    def __init__(self) -> None:
        self.messages = []

    async def publish(self, message):
        self.messages.append(message)
        return "1-0"


class CollectorPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_persistence_is_deterministic_idempotent_and_retrievable(self):
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
        item = envelope("binance")
        collector = AcquisitionCollector({"binance": FakeAdapter("binance", sequences=("1",))}, sink, max_queue_size=2)
        await collector.publish(item)
        consumer = asyncio.create_task(collector._consume())
        await collector._queue.join()
        collector._stop.set()
        await collector._queue.put(None)
        await consumer
        await collector.publish(item)
        collector._stop.clear()
        consumer = asyncio.create_task(collector._consume())
        await collector._queue.join()
        collector._stop.set()
        await collector._queue.put(None)
        await consumer
        self.assertEqual(sink.seen, [item.event_id])
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
        self.assertEqual(collector.stats.overloaded, 1)

    async def test_binance_and_mexc_route_through_provider_neutral_boundary(self):
        sink = FakeSink()
        binance = FakeAdapter("binance", sequences=("10",))
        mexc = FakeAdapter("mexc", sequences=("20",))
        collector = AcquisitionCollector({"binance": binance, "mexc": mexc}, sink)
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1, max_reconnects=3)
        self.assertEqual(set(sink.providers), {"binance", "mexc"})
        self.assertEqual(stats.persisted, 2)
        self.assertEqual(binance.calls[0][1], {"max_messages": 1, "max_reconnects": 3})
        self.assertEqual(mexc.calls[0][1], {"max_messages": 1, "max_reconnects": 3})

    async def test_source_sequence_is_preserved_across_collection(self):
        sink = FakeSink()
        adapter = FakeAdapter("mexc", sequences=("41", "42"))
        collector = AcquisitionCollector({"mexc": adapter}, sink)
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=2, max_reconnects=2)
        self.assertEqual(stats.persisted, 2)
        self.assertEqual(sink.sequences, ["41", "42"])

    async def test_provider_reconnect_failure_is_isolated(self):
        sink = FakeSink()
        failing = FakeAdapter("binance", sequences=("1",), fail_after=True)
        healthy = FakeAdapter("mexc", sequences=("2",))
        collector = AcquisitionCollector({"binance": failing, "mexc": healthy}, sink)
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1, max_reconnects=2)
        self.assertEqual(set(sink.providers), {"binance", "mexc"})
        self.assertEqual(stats.failures, 1)

    async def test_persistence_failure_retries_and_recovers_without_loss(self):
        sink = FakeSink(failures_before_success=2)
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, sink, max_persistence_retries=2)
        stats = await collector.collect_once(["BTCUSDT"])
        self.assertEqual(stats.persisted, 1)
        self.assertEqual(stats.failures, 2)
        self.assertEqual(stats.recovered, 1)
        self.assertEqual(collector.recovery_size, 0)

    async def test_permanent_persistence_failure_is_retained_for_explicit_replay(self):
        sink = FakeSink(always_fail=True)
        item = envelope("binance")
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, sink, max_persistence_retries=2, max_recovery_size=1)
        stats = await collector.collect_once(["BTCUSDT"])
        self.assertEqual(stats.persisted, 0)
        self.assertEqual(stats.failures, 3)
        self.assertEqual(collector.recovery_items, (item,))
        self.assertEqual(collector.recovery_size, 1)
        self.assertEqual(collector.max_recovery_size, 1)

    async def test_retained_failure_can_be_explicitly_replayed(self):
        sink = FakeSink(always_fail=True)
        item = envelope("binance")
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, sink, max_persistence_retries=1, max_recovery_size=1)
        await collector.collect_once(["BTCUSDT"])
        self.assertEqual(collector.recovery_items, (item,))
        sink.always_fail = False
        resolved = await collector.replay_recovery()
        self.assertEqual(resolved, 1)
        self.assertEqual(collector.recovery_size, 0)
        self.assertEqual(sink.seen, [item.event_id])

    async def test_malformed_acquisition_state_is_rejected_by_contract(self):
        with self.assertRaises(TypeError):
            AcquisitionEnvelope(
                provider=ProviderIdentity("binance", "binance-acquisition", "1.0.0"),
                instrument=InstrumentIdentity("BTCUSDT", "BTCUSDT"),
                provenance=Provenance("bad-state", ProviderIdentity("binance", "binance-acquisition", "1.0.0"), "TEST"),
                event_type=EventType.TRADE,
                event_time=datetime(2026, 1, 1, tzinfo=UTC),
                received_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
                state="AVAILABLE",
                payload={"price": "100.00"},
            )

    async def test_invalid_state_with_error_is_persistable_as_acquisition_evidence(self):
        connection = FakeConnection()
        repo = RawStagingRepository(connection)
        item = envelope("mexc", state=AcquisitionState.INVALID)
        result = await repo.persist(item)
        self.assertTrue(result.inserted)
        self.assertEqual(connection.rows[item.event_id]["payload_json"], '{"price":"100.00","qty":"1.0"}')

    async def test_migration_path_includes_ordered_p2_004_schema(self):
        from pathlib import Path
        harness = Path("infrastructure/postgres/migrate.sh").read_text()
        migration = Path("migrations/versions/0002_raw_acquisition_staging.sql").read_text()
        self.assertLess(harness.index("0001_database_foundation.sql"), harness.index("0002_raw_acquisition_staging.sql"))
        self.assertIn("CREATE TABLE IF NOT EXISTS meylux.raw_acquisition_events", migration)
        self.assertIn("ON CONFLICT (event_id) DO NOTHING", migration)
        self.assertIn("Raw/staging is evidence only", migration)
        self.assertIn("identity_hash", migration)

    async def test_collector_is_finite_and_bounded_shutdown(self):
        collector = AcquisitionCollector({"binance": FakeAdapter("binance")}, FakeSink())
        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1)
        self.assertEqual(stats.persisted, 1)
        self.assertEqual(collector.queue_size, 0)
        self.assertTrue(collector._stop.is_set())

    async def test_queue_bridge_preserves_canonical_bytes_identity_and_sequence(self):
        queue = FakeQueue()
        publisher = AcquisitionQueuePublisher(queue)
        item = envelope("mexc", "42")
        entry = await publisher.publish(item)
        self.assertEqual(entry, "1-0")
        queued = queue.messages[0]
        self.assertEqual(queued.message_id, item.event_id)
        self.assertEqual(queued.idempotency_key, item.deduplication_key)
        self.assertEqual(queued.payload["provider_id"], "mexc")
        self.assertEqual(queued.payload["source_sequence"], "42")
        self.assertTrue(queued.payload["canonical_b64"])


if __name__ == "__main__":
    unittest.main()
