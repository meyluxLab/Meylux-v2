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
from meylux.quantitative.regime_venue import RegimeConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
SYMBOL = "TO-P4-011-CI:BTCUSDT"


def _candles(timeframe: str, count: int, interval_minutes: int) -> tuple[CanonicalCandle, ...]:
    out = []
    for index in range(count):
        opened = T0 + timedelta(minutes=interval_minutes * index)
        closed = opened + timedelta(minutes=interval_minutes) - timedelta(milliseconds=1)
        close = Decimal(100 + index) + Decimal(index % 3) / Decimal(10)
        out.append(CanonicalCandle(
            SYMBOL, timeframe, opened, closed,
            close - Decimal("0.5"), close + Decimal("2"),
            close - Decimal("2"), close, Decimal(10 + index),
            is_closed=True, provenance_id=f"p4-011-ci:{timeframe}:{index}",
        ))
    return tuple(out)


class TestP4011PostgreSQLPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("MEYLUX_RUN_P4011_POSTGRESQL") != "1":
            raise unittest.SkipTest("P4-011 PostgreSQL evidence runs only in the dedicated Docker Foundation step.")
        import asyncpg
        cls.asyncpg = asyncpg

    def test_group_a_facts_are_persisted_read_back_and_replayed_idempotently(self):
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
                primary = _candles("15m", 40, 15)
                higher = _candles("1h", 10, 60)
                result = QuantitativeOrchestrator().process(
                    primary, config, higher_timeframes={"1h": higher}
                )
                persistence = QuantitativePersistence(conn)
                inserted = await persistence.persist_orchestration(result)
                self.assertEqual(inserted, 30)
                replay_inserted = await persistence.persist_orchestration(result)
                self.assertEqual(replay_inserted, 0)

                primary_rows = await persistence.fetch_family("indicator", SYMBOL, "15m", limit=100)
                higher_rows = await persistence.fetch_family("indicator", SYMBOL, "1h", limit=100)
                self.assertEqual(len(primary_rows), 14)
                self.assertEqual(len(higher_rows), 14)
                self.assertEqual({row["timeframe"] for row in primary_rows}, {"15m"})
                self.assertEqual({row["timeframe"] for row in higher_rows}, {"1h"})
                self.assertEqual({row["event_time"] for row in primary_rows}, {primary[-1].close_time})
                self.assertEqual({row["event_time"] for row in higher_rows}, {higher[-1].close_time})
                self.assertEqual({row["knowledge_time"] for row in primary_rows}, {result.knowledge_time})
                self.assertEqual(
                    {row["knowledge_time"] for row in higher_rows},
                    {result.higher_timeframe_facts["1h"].knowledge_time},
                )
                self.assertTrue(all(row["identity_hash"] == row["record_id"] for row in primary_rows + higher_rows))
                self.assertEqual({row["source_ref"] for row in primary_rows}, {primary[-1].provenance_id})
                self.assertEqual({row["source_ref"] for row in higher_rows}, {higher[-1].provenance_id})
                primary_payloads = {
                    row["record_id"]: (
                        row["payload_json"] if isinstance(row["payload_json"], dict)
                        else json.loads(row["payload_json"])
                    )
                    for row in primary_rows
                }
                higher_payloads = {
                    row["record_id"]: (
                        row["payload_json"] if isinstance(row["payload_json"], dict)
                        else json.loads(row["payload_json"])
                    )
                    for row in higher_rows
                }
                expected_names = {
                    "EMA", "RSI", "MACD", "MACD_SIGNAL", "MACD_HISTOGRAM", "ATR", "ADX",
                    "BOLLINGER_MIDDLE", "BOLLINGER_UPPER", "BOLLINGER_LOWER",
                    "BOLLINGER_BANDWIDTH", "HISTORICAL_VOLATILITY", "ATR_PERCENTILE",
                    "VOLATILITY_EXPANSION_RATIO",
                }
                self.assertEqual({p["fact_name"] for p in primary_payloads.values()}, expected_names)
                self.assertEqual({p["fact_name"] for p in higher_payloads.values()}, expected_names)
                self.assertEqual(
                    {row["status"] for row in primary_rows
                     if primary_payloads[row["record_id"]]["fact_name"] == "EMA"},
                    {"valid"},
                )
                for row in primary_rows + higher_rows:
                    payload = row["payload_json"]
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    self.assertEqual(payload["context"]["timeframe"], row["timeframe"])
                    self.assertTrue(payload["fact_name"])
                    self.assertEqual(payload["context"]["timestamp"], row["event_time"].isoformat().replace("+00:00", "Z"))
                    self.assertEqual(payload["context"]["source_ref"], row["source_ref"])

                counts = await conn.fetch(
                    "SELECT timeframe, count(*) AS n FROM meylux.calculated_indicator_vectors "
                    "WHERE symbol=$1 GROUP BY timeframe ORDER BY timeframe",
                    SYMBOL,
                )
                self.assertEqual([(row["timeframe"], row["n"]) for row in counts], [("15m", 14), ("1h", 14)])
            finally:
                await conn.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
