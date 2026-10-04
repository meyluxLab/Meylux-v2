from __future__ import annotations

import asyncio
import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical.candle import CanonicalCandle
from meylux.orchestration import QuantOrchestrationConfig, QuantitativeOrchestrator
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.quantitative.market_structure import StructuralEvent
from meylux.quantitative.regime_venue import RegimeConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _candles(
    timeframe: str = "15m",
    count: int = 40,
    interval_minutes: int = 15,
    symbol: str = "TO-P4-013-UNIT:BTCUSDT",
) -> tuple[CanonicalCandle, ...]:
    out = []
    for index in range(count):
        opened = T0 + timedelta(minutes=interval_minutes * index)
        closed = opened + timedelta(minutes=interval_minutes) - timedelta(milliseconds=1)
        open_value = close_value = Decimal("100")
        high_value, low_value = Decimal("101"), Decimal("99")
        if index in (10, 20):
            high_value = Decimal("110")
        if index == 15:
            low_value = Decimal("90")
        if index == count - 1:
            # An exact-boundary FVG is known at the final closed-candle boundary.
            open_value = close_value = Decimal("105")
            high_value, low_value = Decimal("106"), Decimal("105")
        out.append(CanonicalCandle(
            symbol, timeframe, opened, closed, open_value, high_value, low_value,
            close_value, Decimal("10"), is_closed=True,
            provenance_id=f"to-p4-013:{timeframe}:{index}",
        ))
    return tuple(out)


def _config() -> QuantOrchestrationConfig:
    return QuantOrchestrationConfig(
        RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05"))
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
        self.fetches = []

    def transaction(self):
        return _Tx()

    async def execute(self, query, *args):
        self.sql.append((query, args))
        identity = args[-1]
        if identity in self.seen:
            return "INSERT 0 0"
        self.seen.add(identity)
        return "INSERT 0 1"

    async def fetch(self, query, *args):
        self.fetches.append((query, args))
        return []


class TestP4013StructuralFacts(unittest.TestCase):
    def test_primary_and_higher_timeframe_events_keep_temporal_and_lineage_fields(self):
        primary = _candles(count=60)
        higher = _candles("1h", 12, 60)
        result = QuantitativeOrchestrator().process(
            primary, _config(), higher_timeframes={"1h": higher}
        )
        self.assertTrue(result.structure_events)
        self.assertTrue(result.higher_timeframe_structure_events["1h"])
        self.assertEqual(set(result.structure_event_provenance), {event.identity for event in result.structure_events})
        self.assertEqual(
            set(result.higher_timeframe_structure_event_provenance["1h"]),
            {event.identity for event in result.higher_timeframe_structure_events["1h"]},
        )
        for events, provenance, candles, as_of in (
            (result.structure_events, result.structure_event_provenance, primary, result.as_of),
            (
                result.higher_timeframe_structure_events["1h"],
                result.higher_timeframe_structure_event_provenance["1h"],
                higher, result.as_of,
            ),
        ):
            source_refs = {candle.provenance_id for candle in candles}
            for event in events:
                self.assertLessEqual(event.event_location, event.confirmation_time)
                self.assertEqual(event.confirmation_time, event.knowledge_time)
                self.assertLessEqual(event.knowledge_time, as_of)
                self.assertTrue(provenance[event.identity])
                self.assertTrue(set(provenance[event.identity]).issubset(source_refs))
        # The exact-equality liquidity pool retains both confirmed member identities.
        pool = next(event for event in result.structure_events if event.event_type == "LIQUIDITY_POOL")
        self.assertEqual(len(pool.source_event_identity.split(",")), 2)
        self.assertNotEqual(pool.source_event_identity.split(",")[0], pool.source_event_identity.split(",")[1])

    def test_replay_is_deterministic_and_insufficient_history_does_not_fabricate_structure(self):
        candles = _candles()
        a = QuantitativeOrchestrator().process(candles, _config())
        b = QuantitativeOrchestrator().process(tuple(candles), _config())
        self.assertEqual(a.structure_events, b.structure_events)
        self.assertEqual(a.structure_event_provenance, b.structure_event_provenance)
        short = tuple(
            CanonicalCandle(
                "TO-P4-013-SHORT:BTCUSDT", "15m",
                T0 + timedelta(minutes=15 * index),
                T0 + timedelta(minutes=15 * index + 15) - timedelta(milliseconds=1),
                Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100"),
                Decimal("1"), is_closed=True, provenance_id=f"short:{index}",
            )
            for index in range(10)
        )
        result = QuantitativeOrchestrator().process(short, _config())
        self.assertEqual(result.structure_events, ())
        self.assertEqual(result.structure_event_provenance, {})
        self.assertEqual(result.structure_state, "NEUTRAL")

    def test_canonical_gap_preserves_unconfirmed_state_and_replay(self):
        candles = _candles()
        gapped = tuple(candle for index, candle in enumerate(candles) if index != 30)
        a = QuantitativeOrchestrator().process(gapped, _config())
        b = QuantitativeOrchestrator().process(tuple(gapped), _config())
        self.assertEqual(a.structure_events, b.structure_events)
        self.assertEqual(a.structure_event_provenance, b.structure_event_provenance)
        self.assertEqual(a.structure_state, "UNCONFIRMED")

    def test_persistence_writes_individual_events_and_zones_with_as_of_read_filter(self):
        primary = _candles(count=60)
        higher = _candles("1h", 12, 60)
        result = QuantitativeOrchestrator().process(primary, _config(), higher_timeframes={"1h": higher})
        db = _DB()
        persistence = QuantitativePersistence(db)
        inserted = asyncio.run(persistence.persist_orchestration(result))
        self.assertGreater(inserted, 0)
        self.assertEqual(asyncio.run(persistence.persist_orchestration(result)), 0)
        event_rows = [(sql, args) for sql, args in db.sql if "INSERT INTO meylux.market_structure_events" in sql and "confirmation_time" in sql]
        zone_rows = [(sql, args) for sql, args in db.sql if "INSERT INTO meylux.market_structure_zones" in sql and "confirmation_time" in sql]
        self.assertTrue(event_rows)
        self.assertTrue(zone_rows)
        payloads = [json.loads(args[15]) for _, args in event_rows + zone_rows]
        self.assertTrue(all(payload["structural_identity"] for payload in payloads))
        self.assertTrue(all(payload["event_location"] and payload["confirmation_time"] and payload["knowledge_time"] for payload in payloads))
        self.assertTrue(all(payload["source_candle_provenance"] for payload in payloads))
        self.assertTrue(all(payload["configuration_version"] == result.configuration_version for payload in payloads))
        pool = next(payload for payload in payloads if payload["event_type"] == "LIQUIDITY_POOL")
        self.assertEqual(len(pool["source_member_identities"]), 2)
        exact_boundary = [
            payload for payload in payloads
            if payload["event_type"] == "FVG"
            and payload["knowledge_time"].replace("Z", "+00:00") == result.as_of.isoformat()
        ]
        self.assertTrue(exact_boundary)

        # Readback filtering is inclusive at as_of and excludes later-known facts.
        asyncio.run(persistence.fetch_family("structure_event", result.symbol, result.timeframe, as_of=result.as_of))
        query, args = db.fetches[-1]
        self.assertIn("knowledge_time <= $3", query)
        self.assertEqual(args[-1], result.as_of)
        earlier = result.as_of - timedelta(minutes=15)
        asyncio.run(persistence.fetch_family("structure_zone", result.symbol, result.timeframe, as_of=earlier))
        query, args = db.fetches[-1]
        self.assertIn("knowledge_time <= $3", query)
        self.assertEqual(args[-1], earlier)

    def test_non_utc_as_of_and_malformed_structural_temporal_values_are_rejected(self):
        db = _DB()
        persistence = QuantitativePersistence(db)
        non_utc = T0.astimezone(timezone(timedelta(hours=1)))
        with self.assertRaisesRegex(ValueError, "as_of must be UTC"):
            asyncio.run(persistence.fetch_family("structure_event", "X", "15m", as_of=non_utc))

        result = QuantitativeOrchestrator().process(_candles(), _config())
        original = result.structure_events[0]
        local_time = original.knowledge_time.astimezone(timezone(timedelta(hours=1)))
        malformed = replace(original, confirmation_time=local_time, knowledge_time=local_time)
        broken = replace(
            result,
            structure_events=(malformed,),
            structure_event_provenance={malformed.identity: result.structure_event_provenance[original.identity]},
        )
        with self.assertRaisesRegex(ValueError, "structural confirmation_time must be UTC"):
            asyncio.run(QuantitativePersistence(_DB()).persist_orchestration(broken))

    def test_post_boundary_structural_fact_is_rejected_before_any_write(self):
        result = QuantitativeOrchestrator().process(_candles(), _config())
        original = result.structure_events[0]
        future = result.as_of + timedelta(milliseconds=1)
        malformed = replace(original, confirmation_time=future, knowledge_time=future)
        broken = replace(
            result,
            structure_events=(malformed,),
            structure_event_provenance={malformed.identity: result.structure_event_provenance[original.identity]},
        )
        db = _DB()
        with self.assertRaisesRegex(ValueError, "exceeds snapshot.as_of"):
            asyncio.run(QuantitativePersistence(db).persist_orchestration(broken))
        self.assertFalse(any(query.lstrip().startswith("INSERT") for query, _ in db.sql))


if __name__ == "__main__":
    unittest.main()
