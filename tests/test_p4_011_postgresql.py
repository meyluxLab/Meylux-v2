from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import replace
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
SYMBOL = "TO-P4-011-CI:BTCUSDT"


def _candles(
    timeframe: str, count: int, interval_minutes: int, symbol: str = SYMBOL
) -> tuple[CanonicalCandle, ...]:
    out = []
    for index in range(count):
        opened = T0 + timedelta(minutes=interval_minutes * index)
        closed = opened + timedelta(minutes=interval_minutes) - timedelta(milliseconds=1)
        close = Decimal(100 + index) + Decimal(index % 3) / Decimal(10)
        out.append(CanonicalCandle(
            symbol, timeframe, opened, closed,
            close - Decimal("0.5"), close + Decimal("2"),
            close - Decimal("2"), close, Decimal(10 + index),
            is_closed=True, provenance_id=f"p4-011-ci:{timeframe}:{index}",
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
                self.assertEqual(inserted, 40)
                replay_inserted = await persistence.persist_orchestration(result)
                self.assertEqual(replay_inserted, 0)

                primary_rows = await persistence.fetch_family("indicator", SYMBOL, "15m", limit=100)
                higher_rows = await persistence.fetch_family("indicator", SYMBOL, "1h", limit=100)
                self.assertEqual(len(primary_rows), 19)
                self.assertEqual(len(higher_rows), 19)
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
                    "EMA", "EMA_9", "EMA_20", "EMA_21", "EMA_50", "EMA_200",
                    "RSI", "MACD", "MACD_SIGNAL", "MACD_HISTOGRAM", "ATR", "ADX",
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
                primary_status = {
                    primary_payloads[row["record_id"]]["fact_name"]: (row["status"], row["value_numeric"], row["reason"])
                    for row in primary_rows
                }
                for period in (9, 20, 21):
                    self.assertEqual(primary_status[f"EMA_{period}"][0], "valid")
                    self.assertIsNotNone(primary_status[f"EMA_{period}"][1])
                for period in (50, 200):
                    self.assertEqual(primary_status[f"EMA_{period}"][0], "insufficient_history")
                    self.assertIsNone(primary_status[f"EMA_{period}"][1])
                    self.assertIn(f"requires_at_least_{period}_observations", primary_status[f"EMA_{period}"][2])
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
                self.assertEqual([(row["timeframe"], row["n"]) for row in counts], [("15m", 19), ("1h", 19)])
            finally:
                await conn.close()
        asyncio.run(run())


    def test_explicit_raw_venue_context_is_persisted_and_replayed_idempotently(self):
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
                symbol = "TO-P4-012-CI-VENUE:BTCUSDT"
                primary = tuple(
                    replace(item, instrument_id=symbol,
                            provenance_id=f"p4-012-ci:{item.timeframe}:{index}")
                    for index, item in enumerate(_candles("15m", 40, 15, symbol))
                )
                higher = tuple(
                    replace(item, instrument_id=symbol,
                            provenance_id=f"p4-012-ci:{item.timeframe}:{index}")
                    for index, item in enumerate(_candles("1h", 10, 60, symbol))
                )
                # These are explicitly labeled CI fixtures. They exercise the
                # SQL resolver but are not authoritative runtime acceptance evidence.
                for timeframe_candles in (primary, higher):
                    for index, candle in enumerate(timeframe_candles):
                        event_id = f"p4-012-ci-venue:{candle.timeframe}:{index}"
                        payload = {"venue": "BINANCE"}
                        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                        identity_hash = hashlib.sha256(
                            ("p4-012-ci-venue-identity:" + event_id).encode()
                        ).hexdigest()
                        await conn.execute(
                            "INSERT INTO meylux.raw_acquisition_events ("
                            "event_id,provider_id,adapter_id,adapter_version,"
                            "canonical_instrument_id,provider_instrument_id,event_type,"
                            "event_time,received_at,acquisition_state,source_sequence,"
                            "provenance_id,acquisition_method,payload_json,canonical_bytes,identity_hash"
                            ") VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb,$15,$16) "
                            "ON CONFLICT (event_id) DO NOTHING",
                            event_id, "binance", "binance-acquisition", "1.0.0",
                            symbol, "BTCUSDT", "CANDLE", candle.open_time, candle.open_time,
                            "AVAILABLE", str(index), candle.provenance_id, "CI_FIXTURE",
                            payload_json, payload_json.encode("utf-8"), identity_hash,
                        )
                config = QuantOrchestrationConfig(
                    RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05"))
                )
                result = QuantitativeOrchestrator().process(
                    primary, config, higher_timeframes={"1h": higher}
                )
                persistence = QuantitativePersistence(conn)
                self.assertEqual(await persistence.persist_orchestration(result), 40)
                primary_rows = await persistence.fetch_family("indicator", symbol, "15m", limit=100)
                higher_rows = await persistence.fetch_family("indicator", symbol, "1h", limit=100)
                self.assertEqual(len(primary_rows), 19)
                self.assertEqual(len(higher_rows), 19)
                for rows, timeframe in ((primary_rows, "15m"), (higher_rows, "1h")):
                    self.assertEqual({row["venue_context"] for row in rows}, {"BINANCE"})
                    for row in rows:
                        payload = row["payload_json"]
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                        self.assertEqual(payload["context"]["venue_context"], "BINANCE")
                        self.assertEqual(payload["context"]["timeframe"], timeframe)
                self.assertEqual(await persistence.persist_orchestration(result), 0)
                self.assertEqual(
                    {row["record_id"] for row in await persistence.fetch_family("indicator", symbol, "15m", limit=100)},
                    {row["record_id"] for row in primary_rows},
                )
            finally:
                await conn.close()
        asyncio.run(run())

    def test_governed_worker_envelope_persists_mtf_to_postgresql_and_rejects_future_htf(self):
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
                persistence = QuantitativePersistence(conn)
                handler = QuantWorkerHandler(persistence, config)
                worker_symbol = "TO-P4-011-WORKER:BTCUSDT"
                primary = _candles("15m", 40, 15, worker_symbol)
                higher = _candles("1h", 10, 60, worker_symbol)
                envelope = QueueEnvelope(
                    "p4-011-worker-mtf-001",
                    "p4-011-worker-mtf-001",
                    "CTR-P4-QUANT-CANDLE-CLOSE-1.0",
                    {
                        "candles": [_wire_candle(item) for item in primary],
                        "higher_timeframes": {
                            "1h": [_wire_candle(item) for item in higher],
                        },
                    },
                )

                # Exercise QueueEnvelope -> real QuantWorkerHandler -> real orchestrator
                # -> real QuantitativePersistence -> the CI PostgreSQL database.
                await handler(envelope)
                primary_rows = await persistence.fetch_family(
                    "indicator", worker_symbol, "15m", limit=100
                )
                higher_rows = await persistence.fetch_family(
                    "indicator", worker_symbol, "1h", limit=100
                )
                self.assertEqual(len(primary_rows), 19)
                self.assertEqual(len(higher_rows), 19)
                expected_names = {
                    "EMA", "EMA_9", "EMA_20", "EMA_21", "EMA_50", "EMA_200",
                    "RSI", "MACD", "MACD_SIGNAL", "MACD_HISTOGRAM", "ATR", "ADX",
                    "BOLLINGER_MIDDLE", "BOLLINGER_UPPER", "BOLLINGER_LOWER",
                    "BOLLINGER_BANDWIDTH", "HISTORICAL_VOLATILITY", "ATR_PERCENTILE",
                    "VOLATILITY_EXPANSION_RATIO",
                }
                decoded = {}
                for rows, timeframe, candles in (
                    (primary_rows, "15m", primary),
                    (higher_rows, "1h", higher),
                ):
                    self.assertEqual({row["timeframe"] for row in rows}, {timeframe})
                    self.assertEqual({row["event_time"] for row in rows}, {candles[-1].close_time})
                    self.assertEqual({row["knowledge_time"] for row in rows}, {candles[-1].close_time})
                    self.assertLessEqual(
                        max(row["knowledge_time"] for row in rows),
                        primary[-1].close_time,
                    )
                    self.assertEqual({row["source_ref"] for row in rows}, {candles[-1].provenance_id})
                    self.assertTrue(all(row["identity_hash"] == row["record_id"] for row in rows))
                    payloads = {
                        row["record_id"]: (
                            row["payload_json"] if isinstance(row["payload_json"], dict)
                            else json.loads(row["payload_json"])
                        )
                        for row in rows
                    }
                    self.assertEqual(
                        {payload["fact_name"] for payload in payloads.values()},
                        expected_names,
                    )
                    for row in rows:
                        payload = payloads[row["record_id"]]
                        self.assertEqual(payload["context"]["timeframe"], timeframe)
                        self.assertEqual(payload["context"]["source_ref"], row["source_ref"])
                        self.assertEqual(
                            payload["context"]["timestamp"],
                            row["event_time"].isoformat().replace("+00:00", "Z"),
                        )
                    decoded[timeframe] = rows

                before_counts = await conn.fetch(
                    "SELECT timeframe, count(*) AS n FROM meylux.calculated_indicator_vectors "
                    "WHERE symbol=$1 GROUP BY timeframe ORDER BY timeframe",
                    worker_symbol,
                )
                self.assertEqual(
                    [(row["timeframe"], row["n"]) for row in before_counts],
                    [("15m", 19), ("1h", 19)],
                )

                # Same governed envelope through the same worker is replay-safe.
                await handler(envelope)
                replay_primary = await persistence.fetch_family(
                    "indicator", worker_symbol, "15m", limit=100
                )
                replay_higher = await persistence.fetch_family(
                    "indicator", worker_symbol, "1h", limit=100
                )
                self.assertEqual(
                    {row["record_id"] for row in replay_primary},
                    {row["record_id"] for row in primary_rows},
                )
                self.assertEqual(
                    {row["record_id"] for row in replay_higher},
                    {row["record_id"] for row in higher_rows},
                )
                after_counts = await conn.fetch(
                    "SELECT timeframe, count(*) AS n FROM meylux.calculated_indicator_vectors "
                    "WHERE symbol=$1 GROUP BY timeframe ORDER BY timeframe",
                    worker_symbol,
                )
                self.assertEqual(
                    [(row["timeframe"], row["n"]) for row in after_counts],
                    [("15m", 19), ("1h", 19)],
                )

                # A distinct symbol makes the negative-path no-write assertion unambiguous.
                invalid_symbol = "TO-P4-011-FUTURE:BTCUSDT"
                invalid_primary = _candles("15m", 40, 15, invalid_symbol)
                invalid_higher = _candles("1h", 11, 60, invalid_symbol)
                invalid_envelope = QueueEnvelope(
                    "p4-011-worker-future-001",
                    "p4-011-worker-future-001",
                    "CTR-P4-QUANT-CANDLE-CLOSE-1.0",
                    {
                        "candles": [_wire_candle(item) for item in invalid_primary],
                        "higher_timeframes": {
                            "1h": [_wire_candle(item) for item in invalid_higher],
                        },
                    },
                )
                with self.assertRaisesRegex(ValueError, "after primary knowledge boundary"):
                    await handler(invalid_envelope)
                no_rows = await conn.fetch(
                    "SELECT count(*) AS n FROM meylux.calculated_indicator_vectors "
                    "WHERE symbol=$1",
                    invalid_symbol,
                )
                self.assertEqual(no_rows[0]["n"], 0)
            finally:
                await conn.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
