from __future__ import annotations

import asyncio
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical.candle import CanonicalCandle
from meylux.orchestration import QuantOrchestrationConfig, QuantitativeOrchestrator
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.queue import QueueEnvelope
from meylux.runtime.quant_worker import QuantWorkerHandler
from meylux.quantitative.regime_venue import RegimeConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
SYMBOL = "TO-P4-013-CI:BTCUSDT"


def _candles(timeframe: str, count: int, interval_minutes: int, symbol: str = SYMBOL):
    out = []
    for index in range(count):
        opened = T0 + timedelta(minutes=interval_minutes * index)
        closed = opened + timedelta(minutes=interval_minutes) - timedelta(milliseconds=1)
        open_value = close_value = Decimal("100")
        high_value, low_value = Decimal("101"), Decimal("99")
        # Two exact-equal confirmed swing highs yield a liquidity pool with member IDs.
        if index in (10, 20):
            high_value = Decimal("110")
        if index == 30:
            high_value = Decimal("112")
        if index == 15:
            low_value = Decimal("90")
        if index == count - 1:
            # A real engine-produced FVG becomes knowable exactly at this candle close.
            open_value = close_value = Decimal("105")
            high_value, low_value = Decimal("106"), Decimal("105")
        out.append(CanonicalCandle(
            symbol, timeframe, opened, closed, open_value, high_value, low_value,
            close_value, Decimal("10"), is_closed=True,
            provenance_id=f"to-p4-013-ci:{timeframe}:{index}",
        ))
    return tuple(out)


def _wire_candle(candle: CanonicalCandle) -> dict[str, object]:
    def iso(value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {
        "instrument_id": candle.instrument_id,
        "timeframe": candle.timeframe,
        "open_time": iso(candle.open_time),
        "close_time": iso(candle.close_time),
        "open": str(candle.open),
        "high": str(candle.high),
        "low": str(candle.low),
        "close": str(candle.close),
        "volume": str(candle.volume),
        "quote_volume": None if candle.quote_volume is None else str(candle.quote_volume),
        "trade_count": candle.trade_count,
        "is_closed": candle.is_closed,
        "provenance_id": candle.provenance_id,
    }


def _payload(row):
    value = row["payload_json"]
    return value if isinstance(value, dict) else json.loads(value)


class TestP4013StructuralPostgreSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("MEYLUX_RUN_P4013_POSTGRESQL") != "1":
            raise unittest.SkipTest(
                "TO-P4-013 PostgreSQL evidence runs only in the dedicated Docker Foundation step."
            )
        import asyncpg
        cls.asyncpg = asyncpg

    def test_closed_candle_worker_persists_and_reads_back_authoritative_events_and_zones(self):
        async def run():
            conn = await self.asyncpg.connect(
                host=os.environ["MEYLUX_DB_HOST"],
                port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
                database=os.environ["MEYLUX_DB_NAME"],
                user=os.environ["MEYLUX_DB_USER"],
                password=os.environ["MEYLUX_DB_PASSWORD"],
                timeout=10,
                command_timeout=30,
            )
            try:
                config = QuantOrchestrationConfig(
                    RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05"))
                )
                primary = _candles("15m", 60, 15)
                higher = _candles("1h", 12, 60)
                orchestrator = QuantitativeOrchestrator()
                expected = orchestrator.process(primary, config, higher_timeframes={"1h": higher})
                replay = orchestrator.process(tuple(primary), config, higher_timeframes={"1h": tuple(higher)})
                self.assertEqual(expected.structure_events, replay.structure_events)
                self.assertEqual(expected.structure_event_provenance, replay.structure_event_provenance)

                persistence = QuantitativePersistence(conn)
                handler = QuantWorkerHandler(persistence, config)
                envelope = QueueEnvelope(
                    "to-p4-013-closed-candle-001",
                    "to-p4-013-closed-candle-001",
                    "CTR-P4-QUANT-CANDLE-CLOSE-1.0",
                    {
                        "candles": [_wire_candle(item) for item in primary],
                        "higher_timeframes": {"1h": [_wire_candle(item) for item in higher]},
                    },
                )

                # Exercise the real worker -> orchestrator -> persistence -> PostgreSQL path.
                await handler(envelope)
                events_15m = await persistence.fetch_family(
                    "structure_event", SYMBOL, "15m", limit=1000, as_of=primary[-1].close_time
                )
                zones_15m = await persistence.fetch_family(
                    "structure_zone", SYMBOL, "15m", limit=1000, as_of=primary[-1].close_time
                )
                events_1h = await persistence.fetch_family(
                    "structure_event", SYMBOL, "1h", limit=1000, as_of=primary[-1].close_time
                )
                zones_1h = await persistence.fetch_family(
                    "structure_zone", SYMBOL, "1h", limit=1000, as_of=primary[-1].close_time
                )
                self.assertTrue(events_15m)
                self.assertTrue(zones_15m)
                self.assertTrue(events_1h)
                self.assertTrue(zones_1h)
                for rows, timeframe in (
                    (events_15m, "15m"), (zones_15m, "15m"),
                    (events_1h, "1h"), (zones_1h, "1h"),
                ):
                    self.assertEqual({row["timeframe"] for row in rows}, {timeframe})
                    self.assertTrue(all(row["knowledge_time"] is not None for row in rows))
                    self.assertTrue(all(row["knowledge_time"] <= primary[-1].close_time for row in rows))
                    self.assertTrue(all(row["confirmation_time"] is not None for row in rows))
                    self.assertTrue(all(row["identity_hash"] == row["record_id"] for row in rows))
                    self.assertTrue(all(row["source_ref"].startswith("canonical-provenance:") for row in rows))
                    for row in rows:
                        payload = _payload(row)
                        self.assertEqual(row["event_time"], datetime.fromisoformat(payload["event_location"].replace("Z", "+00:00")))
                        self.assertEqual(row["confirmation_time"], datetime.fromisoformat(payload["confirmation_time"].replace("Z", "+00:00")))
                        self.assertEqual(row["knowledge_time"], datetime.fromisoformat(payload["knowledge_time"].replace("Z", "+00:00")))
                        self.assertTrue(payload["structural_identity"])
                        self.assertTrue(payload["source_candle_provenance"])
                        # No raw acquisition lineage was seeded for this CI symbol; venue stays unresolved.
                        self.assertIsNone(row["venue_context"])
                        self.assertIsNone(payload["venue_context"])

                swing = next(
                    row for row in events_15m
                    if row["event_type"] == "SWING_HIGH" and row["event_time"] == primary[10].open_time
                )
                swing_payload = _payload(swing)
                self.assertLess(swing["event_time"], swing["confirmation_time"])
                self.assertEqual(len(swing_payload["source_candle_provenance"]), 11)

                pool = next(row for row in events_15m if row["event_type"] == "LIQUIDITY_POOL")
                pool_payload = _payload(pool)
                self.assertEqual(len(pool_payload["source_member_identities"]), 2)
                self.assertIsNone(pool["source_event_identity"])

                # Database CHECK constraints reject direct inserts that bypass the Python writer.
                invalid_time = primary[-2].close_time
                future_knowledge = invalid_time + timedelta(milliseconds=1)
                invalid_payload = json.dumps({"test": "invalid-temporal-boundary"}, sort_keys=True)
                for table, family_column, family_value, constraint in (
                    ("market_structure_events", "event_type", "TO-P4-013-INVALID-TIME", "ck_structure_events_fact_temporal"),
                    ("market_structure_zones", "zone_type", "TO-P4-013-INVALID-TIME", "ck_structure_zones_fact_temporal"),
                ):
                    record_id = ("e" if table == "market_structure_events" else "z") * 64
                    try:
                        if table == "market_structure_events":
                            await conn.execute(
                                "INSERT INTO meylux.market_structure_events ("
                                "record_id,symbol,timeframe,event_time,confirmation_time,knowledge_time,event_type,"
                                "source_event_identity,source_ref,venue_context,version,calculation_version,status,reason,"
                                "value_numeric,payload_json,identity_hash"
                                ") VALUES ($1,$2,$3,$4,$5,$6,$7,NULL,$8,NULL,$9,$10,$11,$12,NULL,$13::jsonb,$14)",
                                record_id, SYMBOL, "15m", primary[-2].open_time, invalid_time, future_knowledge,
                                family_value, "test-invalid-temporal", "1.0.0", "1.0.0", "valid",
                                "invalid temporal boundary", invalid_payload, record_id,
                            )
                        else:
                            await conn.execute(
                                "INSERT INTO meylux.market_structure_zones ("
                                "record_id,symbol,timeframe,event_time,confirmation_time,knowledge_time,zone_type,"
                                "source_event_identity,source_ref,venue_context,version,calculation_version,status,reason,"
                                "value_numeric,payload_json,identity_hash"
                                ") VALUES ($1,$2,$3,$4,$5,$6,$7,NULL,$8,NULL,$9,$10,$11,$12,NULL,$13::jsonb,$14)",
                                record_id, SYMBOL, "15m", primary[-2].open_time, invalid_time, future_knowledge,
                                family_value, "test-invalid-temporal", "1.0.0", "1.0.0", "valid",
                                "invalid temporal boundary", invalid_payload, record_id,
                            )
                    except self.asyncpg.CheckViolationError as exc:
                        self.assertEqual(exc.sqlstate, "23514")
                        self.assertIn(constraint, str(exc))
                    else:
                        self.fail(f"database accepted an invalid temporal fact in {table}")
                    self.assertEqual(
                        await conn.fetchval(f"SELECT count(*) FROM meylux.{table} WHERE record_id=$1", record_id),
                        0,
                    )

                # The final-candle FVG is eligible at exact knowledge_time == snapshot.as_of.
                exact = next(
                    row for row in events_15m
                    if row["event_type"] == "FVG"
                    and row["event_time"] == primary[-1].open_time
                    and row["knowledge_time"] == primary[-1].close_time
                )
                exact_zone = next(
                    row for row in zones_15m
                    if row["zone_type"] == "FVG"
                    and row["event_time"] == primary[-1].open_time
                    and row["knowledge_time"] == primary[-1].close_time
                )
                self.assertIsNotNone(exact)
                self.assertIsNotNone(exact_zone)

                # Earlier as_of reads exclude later-known facts rather than looking ahead.
                earlier = primary[30].close_time
                earlier_rows = await persistence.fetch_family(
                    "structure_event", SYMBOL, "15m", limit=1000, as_of=earlier
                )
                self.assertTrue(all(row["knowledge_time"] <= earlier for row in earlier_rows))
                self.assertNotIn(exact["record_id"], {row["record_id"] for row in earlier_rows})

                # Replaying the same real worker envelope preserves the complete fact set.
                before_ids = {
                    family: {row["record_id"] for row in rows}
                    for family, rows in (
                        ("event15", events_15m), ("zone15", zones_15m),
                        ("event1h", events_1h), ("zone1h", zones_1h),
                    )
                }
                await handler(envelope)
                after_ids = {
                    "event15": {row["record_id"] for row in await persistence.fetch_family(
                        "structure_event", SYMBOL, "15m", limit=1000, as_of=primary[-1].close_time
                    )},
                    "zone15": {row["record_id"] for row in await persistence.fetch_family(
                        "structure_zone", SYMBOL, "15m", limit=1000, as_of=primary[-1].close_time
                    )},
                    "event1h": {row["record_id"] for row in await persistence.fetch_family(
                        "structure_event", SYMBOL, "1h", limit=1000, as_of=primary[-1].close_time
                    )},
                    "zone1h": {row["record_id"] for row in await persistence.fetch_family(
                        "structure_zone", SYMBOL, "1h", limit=1000, as_of=primary[-1].close_time
                    )},
                }
                self.assertEqual(before_ids, after_ids)

                # Check governed append-only trigger and privilege boundaries on both families.
                for table, trigger, row in (
                    ("market_structure_events", "trg_market_structure_events_append_only", swing),
                    ("market_structure_zones", "trg_market_structure_zones_append_only", exact_zone),
                ):
                    enabled = await conn.fetchval(
                        "SELECT tgenabled FROM pg_trigger WHERE tgname=$1 AND NOT tgisinternal",
                        trigger,
                    )
                    if isinstance(enabled, bytes):
                        enabled = enabled.decode("ascii")
                    self.assertIn(enabled, ("O", "A", "R"))
                    can_update = await conn.fetchval(
                        "SELECT has_table_privilege(current_user, $1, 'UPDATE')", f"meylux.{table}"
                    )
                    can_delete = await conn.fetchval(
                        "SELECT has_table_privilege(current_user, $1, 'DELETE')", f"meylux.{table}"
                    )
                    self.assertFalse(can_update)
                    self.assertFalse(can_delete)
                    before = await conn.fetchval(
                        f"SELECT to_jsonb(t) FROM meylux.{table} AS t WHERE record_id=$1", row["record_id"]
                    )
                    self.assertIsNotNone(before)
                    for operation, sql in (
                        ("UPDATE", f"UPDATE meylux.{table} SET reason=reason WHERE record_id=$1"),
                        ("DELETE", f"DELETE FROM meylux.{table} WHERE record_id=$1"),
                    ):
                        try:
                            await conn.execute(sql, row["record_id"])
                        except self.asyncpg.PostgresError as exc:
                            if exc.sqlstate == "P0001":
                                self.assertIn("append-only", str(exc))
                                self.assertIn(table, str(exc))
                            elif exc.sqlstate == "42501":
                                self.assertIn(f"permission denied for table {table}", str(exc))
                            else:
                                self.fail(f"unexpected {operation} rejection SQLSTATE {exc.sqlstate}: {exc}")
                        else:
                            self.fail(f"{operation} unexpectedly succeeded on {table}")
                        after = await conn.fetchval(
                            f"SELECT to_jsonb(t) FROM meylux.{table} AS t WHERE record_id=$1", row["record_id"]
                        )
                        self.assertEqual(before, after, f"{table} row changed after {operation} attempt")
            finally:
                await conn.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
