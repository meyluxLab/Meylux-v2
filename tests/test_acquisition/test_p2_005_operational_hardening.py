from __future__ import annotations

from datetime import datetime, timezone
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderError,
    ProviderIdentity,
    Provenance,
)
from meylux.acquisition.collector import AcquisitionCollector, PersistenceRecoveryOverflow
from meylux.acquisition.persistence import PersistenceResult


UTC = timezone.utc


def make_envelope(
    provider: str,
    sequence: str,
    state: AcquisitionState = AcquisitionState.AVAILABLE,
    *,
    retryable: bool = False,
) -> AcquisitionEnvelope:
    identity = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
    error = None
    if state is not AcquisitionState.AVAILABLE:
        error = ProviderError(
            f"TEST_{state.value}",
            state.value,
            f"synthetic {state.value.lower()} state",
            retryable=retryable,
        )
    return AcquisitionEnvelope(
        provider=identity,
        instrument=InstrumentIdentity("BTCUSDT", "BTCUSDT"),
        provenance=Provenance(f"{provider}-p2-005-test", identity, "TEST"),
        event_type=EventType.TRADE,
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        received_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        state=state,
        provider_error=error,
        payload={"price": "100.00", "qty": "1.0"},
        source_sequence=sequence,
    )


class Sink:
    def __init__(self) -> None:
        self.items: list[AcquisitionEnvelope] = []

    async def persist(self, item: AcquisitionEnvelope) -> PersistenceResult:
        duplicate = any(existing.event_id == item.event_id for existing in self.items)
        if not duplicate:
            self.items.append(item)
        return PersistenceResult(item.event_id, not duplicate)


class Adapter:
    def __init__(self, provider: str, items: tuple[AcquisitionEnvelope, ...], *, fail: bool = False) -> None:
        self.identity = ProviderIdentity(provider, f"{provider}-acquisition", "1.0.0")
        self.items = items
        self.fail = fail
        self.calls: list[dict] = []

    async def stream(self, symbols, **kwargs):
        self.calls.append(dict(kwargs))
        for item in self.items:
            yield item
        if self.fail:
            raise RuntimeError(f"{self.identity.provider_id} synthetic stream failure")


class P2005OperationalHardeningTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_failure_isolation_and_degraded_state_are_bounded(self):
        sink = Sink()
        binance = Adapter(
            "binance",
            (make_envelope("binance", "1", AcquisitionState.DEGRADED, retryable=True),),
            fail=True,
        )
        mexc = Adapter("mexc", (make_envelope("mexc", "1"),))
        collector = AcquisitionCollector({"binance": binance, "mexc": mexc}, sink, max_queue_size=2)

        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1, max_reconnects=2)

        self.assertEqual({item.provider.provider_id for item in sink.items}, {"binance", "mexc"})
        self.assertEqual(stats.degraded, 1)
        self.assertEqual(stats.failures, 1)
        self.assertGreaterEqual(stats.terminal_failures, 2)
        self.assertEqual(binance.calls[0]["max_reconnects"], 2)
        self.assertEqual(mexc.calls[0]["max_reconnects"], 2)

    async def test_rate_limit_and_disconnect_states_are_preserved_and_observable(self):
        sink = Sink()
        collector = AcquisitionCollector(
            {
                "binance": Adapter(
                    "binance",
                    (make_envelope("binance", "10", AcquisitionState.RATE_LIMITED, retryable=True),),
                ),
                "mexc": Adapter(
                    "mexc",
                    (make_envelope("mexc", "20", AcquisitionState.DISCONNECTED),),
                ),
            },
            sink,
            max_queue_size=2,
        )

        stats = await collector.collect_once(["BTCUSDT"], max_messages_per_provider=1, max_reconnects=0)
        states = {item.provider.provider_id: item.state for item in sink.items}
        self.assertEqual(states["binance"], AcquisitionState.RATE_LIMITED)
        self.assertEqual(states["mexc"], AcquisitionState.DISCONNECTED)
        self.assertEqual(stats.rate_limited, 1)
        self.assertEqual(stats.disconnected, 1)
        self.assertEqual(stats.queue_size if hasattr(stats, "queue_size") else collector.queue_size, 0)

    async def test_health_snapshot_exposes_only_bounded_operational_state(self):
        collector = AcquisitionCollector(
            {"binance": Adapter("binance", (make_envelope("binance", "1"),))},
            Sink(),
            max_queue_size=3,
            max_concurrency=2,
            max_recovery_size=2,
        )
        snapshot = collector.health_snapshot()
        self.assertEqual(snapshot["queue_size"], 0)
        self.assertEqual(snapshot["max_queue_size"], 3)
        self.assertEqual(snapshot["recovery_size"], 0)
        self.assertEqual(snapshot["max_recovery_size"], 2)
        self.assertEqual(snapshot["overflow_capacity"], 3 + 2 + 1)
        self.assertFalse(snapshot["stopped"])

        await collector.collect_once(["BTCUSDT"])
        snapshot = collector.health_snapshot()
        self.assertEqual(snapshot["queue_size"], 0)
        self.assertTrue(snapshot["stopped"])
        self.assertLessEqual(snapshot["overflow_unresolved"], snapshot["overflow_capacity"])

    async def test_post_stop_handoff_is_bounded_without_silent_drop(self):
        collector = AcquisitionCollector(
            {"binance": Adapter("binance", (make_envelope("binance", "1"),))},
            Sink(),
            max_queue_size=1,
            max_concurrency=1,
        )
        collector._stop.set()
        self.assertFalse(await collector.publish(make_envelope("binance", "1")))
        self.assertEqual(len(collector.overflow_unresolved_items), 1)
        self.assertLessEqual(len(collector.overflow_unresolved_items), collector.health_snapshot()["overflow_capacity"])
        with self.assertRaises(PersistenceRecoveryOverflow):
            for sequence in ("2", "3", "4"):
                await collector.publish(make_envelope("binance", sequence))

    async def test_duplicate_replay_remains_idempotent_after_operational_hardening(self):
        sink = Sink()
        item = make_envelope("mexc", "42")
        collector = AcquisitionCollector({"mexc": Adapter("mexc", (item,))}, sink)
        first = await collector.collect_once(["BTCUSDT"])
        self.assertEqual(first.persisted, 1)

        collector._stop.clear()
        await collector.publish(item)
        consumer = __import__("asyncio").create_task(collector._consume())
        await collector._queue.join()
        collector._stop.set()
        await collector._queue.put(None)
        await consumer
        self.assertEqual(len(sink.items), 1)
        self.assertEqual(collector.stats.duplicates, 1)


if __name__ == "__main__":
    unittest.main()
