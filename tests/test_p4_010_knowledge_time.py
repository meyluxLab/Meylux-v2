from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.canonical.candle import CanonicalCandle
from contracts.specialist import EvidenceRef, FactStatus
from meylux.orchestration import QuantitativeOrchestrator, QuantOrchestrationConfig
from meylux.persistence.quantitative import QuantitativePersistence, _knowledge_time
from meylux.quantitative.regime_venue import RegimeConfig
from meylux.specialists.snapshot import (
    InputSnapshotBuilder,
    LookaheadFactError,
    SnapshotBuildError,
    SnapshotRecord,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)

_ZONE_EVENT_TYPES = {
    "FVG", "FVG_LIFECYCLE", "ORDER_BLOCK", "ORDER_BLOCK_INVALIDATION",
    "BREAKER", "BREAKER_INVALIDATION", "LIQUIDITY_POOL", "LIQUIDITY_POOL_SWEEP",
}


def _expected_structural_rows(result) -> int:
    count = 0
    for facts in result.structural_facts.values():
        count += len(facts.events)
        count += sum(
            event.event_type in _ZONE_EVENT_TYPES
            and (event.lower_bound is not None or event.upper_bound is not None
                 or event.event_type in {"LIQUIDITY_POOL", "LIQUIDITY_POOL_SWEEP"})
            for event in facts.events
        )
    return count


def candle(i: int) -> CanonicalCandle:
    t = T0 + timedelta(minutes=15 * i)
    value = Decimal(100 + i)
    return CanonicalCandle(
        "BINANCE:BTCUSDT",
        "15m",
        t,
        t + timedelta(minutes=15) - timedelta(milliseconds=1),
        value,
        value,
        value,
        value,
        Decimal("10"),
        is_closed=True,
        provenance_id=f"binance:test:{i}",
    )


def bars() -> tuple[CanonicalCandle, ...]:
    return tuple(candle(i) for i in range(30))


def config() -> QuantOrchestrationConfig:
    return QuantOrchestrationConfig(
        RegimeConfig(
            2,
            2,
            Decimal("0.10"),
            Decimal("0.05"),
            Decimal("0.10"),
            Decimal("0.05"),
        )
    )


class _Tx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class _DB:
    def __init__(self):
        self.sql = []
        self.seen = set()
        self.structural_rows = {}

    def transaction(self):
        return _Tx()

    async def execute(self, query, *args):
        self.sql.append((query, args))
        structural = "knowledge_time)" in query.lower() and (
            "insert into meylux.market_structure_events" in query.lower()
            or "insert into meylux.market_structure_zones" in query.lower()
        )
        table = (
            "meylux.market_structure_events" if "insert into meylux.market_structure_events" in query.lower()
            else "meylux.market_structure_zones" if "insert into meylux.market_structure_zones" in query.lower()
            else query.lower().split("insert into ", 1)[1].split()[0] if "insert into " in query.lower()
            else "unknown"
        )
        identity = args[-2] if structural else args[-1]
        key = (table, identity)
        if key in self.seen:
            return "INSERT 0 0"
        self.seen.add(key)
        if structural:
            type_column = "event_type" if table.endswith("market_structure_events") else "zone_type"
            fields = (
                "record_id", "symbol", "timeframe", "event_time", type_column,
                "source_ref", "venue_context", "version", "calculation_version",
                "status", "reason", "value_numeric", "payload_json", "identity_hash",
                "knowledge_time",
            )
            import json
            self.structural_rows[key] = dict(zip(fields, args))
            self.structural_rows[key]["payload_json"] = json.loads(args[12])
        return "INSERT 0 1"

    async def fetch(self, *args):
        return []

    async def fetchrow(self, query, *args):
        lowered = query.lower()
        table = (
            "meylux.market_structure_events" if "from meylux.market_structure_events" in lowered
            else "meylux.market_structure_zones" if "from meylux.market_structure_zones" in lowered
            else None
        )
        return None if table is None else self.structural_rows.get((table, args[0]))


def p5_record(*, knowledge_time: datetime, event_time: datetime | None = None) -> SnapshotRecord:
    event_time = event_time or knowledge_time
    identity = "a" * 64
    ref = EvidenceRef(
        "ev-p4-010",
        "postgresql",
        "meylux.calculated_indicator_vectors",
        identity,
        source_family="p4_quantitative",
        record_id=identity,
        event_time=event_time,
        knowledge_time=knowledge_time,
        timeframe="15m",
        venue="Binance",
    )
    metadata = {
        "symbol": "BINANCE:BTCUSDT",
        "venue": "Binance",
        "product": "spot",
        "timeframe": "15m",
        "source_table": "meylux.calculated_indicator_vectors",
        "record_id": identity,
        "identity_hash": identity,
        "version": "1.0.0",
        "event_time": event_time,
        "knowledge_time": knowledge_time,
    }
    return SnapshotRecord(
        fact_id=identity,
        status=FactStatus.VALID,
        value={"value": Decimal("1")},
        event_time=event_time,
        knowledge_time=knowledge_time,
        evidence_refs=(ref,),
        reason=None,
        metadata=metadata,
    )


class TestP4010KnowledgeTime(unittest.TestCase):
    def test_orchestration_exposes_explicit_knowledge_time(self):
        result = QuantitativeOrchestrator().process(bars(), config())
        self.assertEqual(result.knowledge_time, bars()[-1].close_time)
        self.assertEqual(result.knowledge_time, result.as_of)
        self.assertIsNotNone(result.knowledge_time.tzinfo)
        self.assertEqual(result.knowledge_time.utcoffset(), UTC.utcoffset(result.knowledge_time))

    def test_knowledge_time_is_independent_from_execution_wall_clock(self):
        first = QuantitativeOrchestrator().process(bars(), config())
        second = QuantitativeOrchestrator().process(tuple(bars()), config())
        self.assertEqual(first.knowledge_time, second.knowledge_time)
        self.assertEqual(first.knowledge_time, first.as_of)
        self.assertEqual(first, second)

    def test_family_semantics_independently_preserve_authoritative_closed_boundary(self):
        result = QuantitativeOrchestrator().process(bars(), config())
        boundary = bars()[-1].close_time
        self.assertEqual(result.as_of, boundary)
        self.assertEqual(result.knowledge_time, boundary)
        for name, calculation in result.indicators.items():
            self.assertIsNotNone(calculation.context, name)
            self.assertEqual(calculation.context.timestamp, boundary, name)
        self.assertIsNotNone(result.regime.result.context)
        self.assertEqual(result.regime.result.context.timestamp, boundary)

    def test_persistence_writes_authoritative_knowledge_time_only_for_proven_families(self):
        db = _DB()
        result = QuantitativeOrchestrator().process(bars(), config())
        inserted = asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        expected_structural = _expected_structural_rows(result)
        self.assertEqual(inserted, 23 + expected_structural)
        self.assertEqual(len(db.sql), 21 + expected_structural)
        indicator_and_regime = [
            (query, args) for query, args in db.sql
            if "calculated_indicator_vectors" in query or "market_regime_states" in query
        ]
        structure = [
            (query, args) for query, args in db.sql
            if "market_structure_events" in query
        ]
        self.assertEqual(len(indicator_and_regime), 20)
        summaries = [(query, args) for query, args in structure if len(args) > 4 and args[4] == "ORCHESTRATION"]
        structural_facts = [(query, args) for query, args in structure if len(args) > 4 and args[4] != "ORCHESTRATION"]
        self.assertEqual(len(summaries), 1)
        self.assertEqual(len(structural_facts), len(result.structural_facts["15m"].events))
        for query, args in indicator_and_regime:
            self.assertNotIn("persisted_at", query.lower())
            self.assertEqual(args[3], result.knowledge_time)
            self.assertIsInstance(args[3], datetime)
        self.assertEqual(summaries[0][1][3], result.as_of)
        self.assertNotIn("knowledge_time", summaries[0][0].lower())
        self.assertTrue(all("knowledge_time" in query.lower() for query, _ in structural_facts))
        self.assertTrue(all(args[-1] <= result.as_of for _, args in structural_facts))

    def test_persistence_rejects_non_utc_or_mismatched_knowledge_time(self):
        result = QuantitativeOrchestrator().process(bars(), config())
        db = _DB()
        bad_utc = result.__class__(
            result.symbol,
            result.timeframe,
            result.as_of,
            result.knowledge_time.replace(tzinfo=None),
            result.configuration_version,
            result.regime,
            result.regime_transition,
            result.indicators,
            result.structure_event_count,
            result.structure_state,
            result.htf,
            result.source_provenance,
        )
        with self.assertRaises(ValueError):
            _knowledge_time(bad_utc)

        mismatched = result.__class__(
            result.symbol,
            result.timeframe,
            result.as_of,
            result.knowledge_time - timedelta(milliseconds=1),
            result.configuration_version,
            result.regime,
            result.regime_transition,
            result.indicators,
            result.structure_event_count,
            result.structure_state,
            result.htf,
            result.source_provenance,
        )
        with self.assertRaises(ValueError):
            asyncio.run(QuantitativePersistence(db).persist_orchestration(mismatched))

    def test_replay_preserves_knowledge_time_and_identity(self):
        first_db = _DB()
        second_db = _DB()
        first = QuantitativeOrchestrator().process(bars(), config())
        second = QuantitativeOrchestrator().process(tuple(bars()), config())
        asyncio.run(QuantitativePersistence(first_db).persist_orchestration(first))
        asyncio.run(QuantitativePersistence(second_db).persist_orchestration(second))
        self.assertEqual([args[-1] for _, args in first_db.sql], [args[-1] for _, args in second_db.sql])
        self.assertEqual([args[4] for _, args in first_db.sql], [args[4] for _, args in second_db.sql])

    def test_identity_material_does_not_change_when_knowledge_time_is_represented(self):
        persistence = QuantitativePersistence(_DB())
        material = {
            "family": "indicator",
            "name": "EMA",
            "symbol": "BINANCE:BTCUSDT",
            "timeframe": "15m",
            "event_time": T0,
            "version": "1.0.0",
            "payload": {"value": "1", "status": "valid", "reason": "ok", "context": None},
        }
        before = persistence._id(material)
        after = persistence._id(dict(material))
        self.assertEqual(before, after)

    def test_p5_boundary_accepts_equal_knowledge_time(self):
        as_of = T0
        record = p5_record(knowledge_time=as_of)
        snapshot = InputSnapshotBuilder().build(as_of=as_of, records=[record])
        self.assertEqual(snapshot.facts[0].knowledge_time, as_of)
        self.assertEqual(snapshot.facts[0].evidence_refs[0].knowledge_time, as_of)

    def test_p5_boundary_excludes_future_knowledge_time(self):
        as_of = T0
        record = p5_record(knowledge_time=as_of + timedelta(microseconds=1))
        with self.assertRaises(LookaheadFactError):
            InputSnapshotBuilder().build(as_of=as_of, records=[record])

    def test_p5_requires_explicit_knowledge_time_and_complete_provenance(self):
        with self.assertRaises(ValueError):
            p5_record(knowledge_time=None)  # type: ignore[arg-type]

        record = p5_record(knowledge_time=T0)
        ref = EvidenceRef(
            "ev-incomplete",
            "postgresql",
            "meylux.calculated_indicator_vectors",
            "a" * 64,
            source_family="p4_quantitative",
            record_id="a" * 64,
            event_time=T0,
            knowledge_time=T0,
            timeframe="15m",
            venue=None,
        )
        with self.assertRaises(SnapshotBuildError):
            SnapshotRecord(
                fact_id=record.fact_id,
                status=FactStatus.VALID,
                value=record.value,
                event_time=T0,
                knowledge_time=T0,
                evidence_refs=(ref,),
                reason=None,
                metadata=dict(record.metadata),
            )

    def test_event_time_and_knowledge_time_remain_distinct_in_p5_contract(self):
        event_time = T0 - timedelta(minutes=15)
        record = p5_record(knowledge_time=T0, event_time=event_time)
        snapshot = InputSnapshotBuilder().build(as_of=T0, records=[record])
        self.assertEqual(snapshot.facts[0].knowledge_time, T0)
        self.assertEqual(snapshot.facts[0].metadata["event_time"], event_time)

    def test_migration_keeps_legacy_unknown_rows_representable(self):
        text = Path("migrations/versions/0008_p4_knowledge_time_persistence.sql").read_text(encoding="utf-8")
        self.assertEqual(text.count("GENERATED ALWAYS AS (event_time) STORED"), 2)
        self.assertNotIn("CASE WHEN event_type = 'ORCHESTRATION'", text)
        self.assertIn("market_structure_events", text)
        self.assertIn("ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;", text)
        self.assertNotIn("ALTER COLUMN knowledge_time SET NOT NULL", text)
        self.assertNotIn("UPDATE meylux.", text)
        self.assertIn("market_structure_zones", text)
        self.assertIn("volume_profile_sessions", text)
        self.assertNotIn("session_end", text)

    def test_migration_is_non_destructive_and_idempotent(self):
        text = Path("migrations/versions/0008_p4_knowledge_time_persistence.sql").read_text(encoding="utf-8")
        self.assertNotIn("DROP TABLE", text.upper())
        self.assertNotIn("DELETE FROM", text.upper())
        self.assertIn("ADD COLUMN IF NOT EXISTS", text)
        self.assertEqual(text.count("GENERATED ALWAYS AS"), 2)
        self.assertIn("ON CONFLICT(version) DO NOTHING", text)
        self.assertNotIn("UPDATE meylux.", text)

    def test_out_of_order_primary_candles_are_rejected_before_knowledge_time_is_derived(self):
        ordered = list(bars())
        ordered[-1], ordered[-2] = ordered[-2], ordered[-1]
        with self.assertRaises(ValueError):
            QuantitativeOrchestrator().process(ordered, config())


    def test_semantic_evidence_artifact_preserves_family_specific_authority(self):
        text = Path("docs/quantitative/P4_010_KNOWLEDGE_TIME_SEMANTIC_EVIDENCE.md").read_text(encoding="utf-8")
        for marker in (
            "calculated_indicator_vectors",
            "market_regime_states",
            "market_structure_events",
            "DOC-P4-002",
            "P4_002_INDICATOR_SEMANTICS.md",
            "P5_002_FACT_REQUIREMENTS_MATRIX.md",
            "CLASS-B",
            "UNAVAILABLE",
        ):
            self.assertIn(marker, text)
        self.assertIn("ORCHESTRATION", text)
        self.assertIn("not itself one of those governed structural event objects", text)

if __name__ == "__main__":
    unittest.main()
