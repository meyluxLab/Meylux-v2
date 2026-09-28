from __future__ import annotations
import asyncio
import unittest
from datetime import datetime, timezone

from decimal import Decimal
from datetime import timedelta
from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationStatus
from meylux.orchestration import QuantitativeOrchestrator, QuantOrchestrationConfig
from meylux.persistence.quantitative import QuantitativePersistence, _knowledge_time
from meylux.quantitative.regime_venue import RegimeConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)

def candle(i: int) -> CanonicalCandle:
    t = T0 + timedelta(minutes=15 * i)
    value = Decimal(100 + i)
    return CanonicalCandle("BTCUSDT", "15m", t, t + timedelta(minutes=15), value, value, value, value, Decimal("10"), is_closed=True, provenance_id=f"p-{i}")

def bars() -> tuple[CanonicalCandle, ...]:
    return tuple(candle(i) for i in range(30))

def config() -> QuantOrchestrationConfig:
    return QuantOrchestrationConfig(RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05")))

class _Tx:
    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False

class _DB:
    def __init__(self): self.sql = []; self.seen = set()
    def transaction(self): return _Tx()
    async def execute(self, query, *args):
        self.sql.append((query, args))
        identity = args[-1]
        if identity in self.seen: return "INSERT 0 0"
        self.seen.add(identity)
        return "INSERT 0 1"
    async def fetch(self, *args): return []
    async def fetchrow(self, *args): return None


class TestP4010KnowledgeTime(unittest.TestCase):
    def test_orchestration_knowledge_time_is_last_closed_input_close(self):
        result = QuantitativeOrchestrator().process(bars(), config())
        self.assertEqual(_knowledge_time(result), bars()[-1].close_time)
        self.assertEqual(result.as_of, bars()[-1].close_time)
        self.assertTrue(result.as_of.tzinfo is not None)
        self.assertEqual(result.as_of.utcoffset(), timezone.utc.utcoffset(result.as_of))

    def test_persistence_writes_explicit_knowledge_time_for_every_written_family(self):
        db = _DB()
        result = QuantitativeOrchestrator().process(bars(), config())
        inserted = asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        self.assertEqual(inserted, 5)
        self.assertEqual(len(db.sql), 5)
        for query, args in db.sql:
            self.assertIn("knowledge_time", query)
            self.assertIsInstance(args[4], datetime)
            self.assertEqual(args[4], result.as_of)

    def test_replay_preserves_knowledge_time_and_identity(self):
        first_db = _DB()
        second_db = _DB()
        first = QuantitativeOrchestrator().process(bars(), config())
        second = QuantitativeOrchestrator().process(tuple(bars()), config())
        self.assertEqual(_knowledge_time(first), _knowledge_time(second))
        self.assertEqual(first, second)
        asyncio.run(QuantitativePersistence(first_db).persist_orchestration(first))
        asyncio.run(QuantitativePersistence(second_db).persist_orchestration(second))
        self.assertEqual(
            [args[-1] for _, args in first_db.sql],
            [args[-1] for _, args in second_db.sql],
        )
        self.assertEqual(
            [args[4] for _, args in first_db.sql],
            [args[4] for _, args in second_db.sql],
        )

    def test_persistence_does_not_use_persisted_at_as_knowledge_time(self):
        db = _DB()
        result = QuantitativeOrchestrator().process(bars(), config())
        asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        for query, args in db.sql:
            self.assertNotIn("persisted_at", query.lower())
            self.assertEqual(args[4], result.as_of)


class TestP4010Migration(unittest.TestCase):
    def test_migration_adds_knowledge_time_to_all_authoritative_p4_families(self):
        from pathlib import Path
        text = Path("migrations/versions/0008_p4_knowledge_time_persistence.sql").read_text(encoding="utf-8")
        for table in (
            "calculated_indicator_vectors",
            "market_structure_events",
            "market_structure_zones",
            "volume_profile_sessions",
            "market_regime_states",
        ):
            self.assertIn(f"ALTER TABLE meylux.{table} ADD COLUMN IF NOT EXISTS knowledge_time timestamptz", text)
            self.assertIn(f"ALTER TABLE meylux.{table} ALTER COLUMN knowledge_time SET NOT NULL", text)
        self.assertIn("SET knowledge_time=event_time", text)
        self.assertIn("SET knowledge_time=session_end", text)
        self.assertIn("ON CONFLICT(version) DO NOTHING", text)
        self.assertIn("'0008_p4_knowledge_time_persistence'", text)

    def test_migration_is_non_destructive_and_has_explicit_backfill_failure_gate(self):
        from pathlib import Path
        text = Path("migrations/versions/0008_p4_knowledge_time_persistence.sql").read_text(encoding="utf-8")
        self.assertNotIn("DROP TABLE", text.upper())
        self.assertNotIn("DELETE FROM", text.upper())
        self.assertIn("knowledge_time IS NULL", text)
        self.assertIn("RAISE EXCEPTION", text)


if __name__ == "__main__":
    unittest.main()
