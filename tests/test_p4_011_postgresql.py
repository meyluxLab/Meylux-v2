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
from contracts.canonical.trade import CanonicalTrade
from meylux.orchestration import QuantOrchestrationConfig, QuantitativeOrchestrator
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.queue import QueueEnvelope
from meylux.runtime.quant_worker import QuantWorkerHandler
from meylux.quantitative.regime_venue import RegimeConfig
from meylux.quantitative.volume_orderflow_derivatives import VolumeProfileConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
SYMBOL = "TO-P4-011-CI:BTCUSDT"

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
                self.assertEqual(inserted, 48 + _expected_structural_rows(result))
                replay_inserted = await persistence.persist_orchestration(result)
                self.assertEqual(replay_inserted, 0)

                primary_rows = await persistence.fetch_family("indicator", SYMBOL, "15m", limit=100)
                higher_rows = await persistence.fetch_family("indicator", SYMBOL, "1h", limit=100)
                self.assertEqual(len(primary_rows), 23)
                self.assertEqual(len(higher_rows), 23)
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
                    "VOLATILITY_EXPANSION_RATIO", "VOLUME_SMA", "RVOL", "VOLUME_SPIKE", "VOLUME_CLIMAX",
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
                self.assertEqual([(row["timeframe"], row["n"]) for row in counts], [("15m", 23), ("1h", 23)])
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
                self.assertEqual(
                    await persistence.persist_orchestration(result),
                    48 + _expected_structural_rows(result),
                )
                primary_rows = await persistence.fetch_family("indicator", symbol, "15m", limit=100)
                higher_rows = await persistence.fetch_family("indicator", symbol, "1h", limit=100)
                self.assertEqual(len(primary_rows), 23)
                self.assertEqual(len(higher_rows), 23)
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
                self.assertEqual(len(primary_rows), 23)
                self.assertEqual(len(higher_rows), 23)
                expected_names = {
                    "EMA", "EMA_9", "EMA_20", "EMA_21", "EMA_50", "EMA_200",
                    "RSI", "MACD", "MACD_SIGNAL", "MACD_HISTOGRAM", "ATR", "ADX",
                    "BOLLINGER_MIDDLE", "BOLLINGER_UPPER", "BOLLINGER_LOWER",
                    "BOLLINGER_BANDWIDTH", "HISTORICAL_VOLATILITY", "ATR_PERCENTILE",
                    "VOLATILITY_EXPANSION_RATIO", "VOLUME_SMA", "RVOL", "VOLUME_SPIKE", "VOLUME_CLIMAX",
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
                    [("15m", 23), ("1h", 23)],
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
                    [("15m", 23), ("1h", 23)],
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
                for table in ("market_structure_events", "market_structure_zones"):
                    no_structural_rows = await conn.fetchval(
                        f"SELECT count(*) FROM meylux.{table} WHERE symbol=$1",
                        invalid_symbol,
                    )
                    self.assertEqual(no_structural_rows, 0, f"future HTF input must not persist {table}")
            finally:
                await conn.close()
        asyncio.run(run())


    def test_group_b_structural_events_zones_persist_replay_and_remain_append_only(self):
        async def run():
            conn = await self.asyncpg.connect(
                host=os.environ["MEYLUX_DB_HOST"],
                port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
                database=os.environ["MEYLUX_DB_NAME"],
                user=os.environ["MEYLUX_DB_USER"],
                password=os.environ["MEYLUX_DB_PASSWORD"],
                timeout=10,
                command_timeout=60,
            )
            try:
                config = QuantOrchestrationConfig(
                    RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05"))
                )
                symbol = "TO-P4-013-STRUCTURE:BTCUSDT"

                def with_fvg(candles):
                    values = list(candles)
                    for index, fields in enumerate((
                        {"open": Decimal("100"), "high": Decimal("101"), "low": Decimal("99"), "close": Decimal("100")},
                        {"open": Decimal("102"), "high": Decimal("103"), "low": Decimal("101"), "close": Decimal("102")},
                        {"open": Decimal("105"), "high": Decimal("107"), "low": Decimal("104"), "close": Decimal("106")},
                    )):
                        values[index] = replace(values[index], **fields)
                    return tuple(values)

                primary = with_fvg(_candles("15m", 40, 15, symbol))
                higher_1h = with_fvg(_candles("1h", 10, 60, symbol))
                higher_4h = _candles("4h", 2, 240, symbol)
                envelope = QueueEnvelope(
                    "p4-013-structural-worker-001",
                    "p4-013-structural-worker-001",
                    "CTR-P4-QUANT-CANDLE-CLOSE-1.0",
                    {
                        "candles": [_wire_candle(item) for item in primary],
                        "higher_timeframes": {
                            "1h": [_wire_candle(item) for item in higher_1h],
                            "4h": [_wire_candle(item) for item in higher_4h],
                        },
                    },
                )
                persistence = QuantitativePersistence(conn)
                handler = QuantWorkerHandler(persistence, config)
                await handler(envelope)

                events = await conn.fetch(
                    "SELECT * FROM meylux.market_structure_events "
                    "WHERE symbol=$1 AND event_type <> 'ORCHESTRATION' "
                    "ORDER BY timeframe,event_time,record_id",
                    symbol,
                )
                zones = await conn.fetch(
                    "SELECT * FROM meylux.market_structure_zones "
                    "WHERE symbol=$1 ORDER BY timeframe,event_time,record_id",
                    symbol,
                )
                self.assertTrue(events, "individual StructuralEvent rows must be persisted")
                self.assertTrue(zones, "zone-bearing structural facts must be persisted")
                self.assertEqual({row["timeframe"] for row in events}, {"15m", "1h", "4h"})
                self.assertEqual({row["timeframe"] for row in zones}, {"15m", "1h"})
                self.assertTrue(all(row["knowledge_time"] is not None for row in events))
                self.assertTrue(all(row["knowledge_time"] is not None for row in zones))
                self.assertTrue(all(row["knowledge_time"] <= primary[-1].close_time for row in events + zones))
                self.assertTrue(all(row["event_time"] <= row["knowledge_time"] for row in events + zones))
                self.assertTrue(all(row["venue_context"] is None for row in events + zones),
                                "fixture provenance must not be promoted to an inferred venue")

                def payload(row):
                    value = row["payload_json"]
                    return value if isinstance(value, dict) else json.loads(value)

                event_ids = {row["record_id"] for row in events}
                for row in events:
                    data = payload(row)
                    self.assertEqual(row["record_id"], row["identity_hash"])
                    self.assertEqual(data["event_identity"], row["record_id"])
                    self.assertEqual(data["event_type"], row["event_type"])
                    self.assertEqual(data["event_location"], row["event_time"].isoformat().replace("+00:00", "Z"))
                    self.assertEqual(
                        datetime.fromisoformat(data["confirmation_time"].replace("Z", "+00:00")),
                        row["knowledge_time"],
                    )
                    self.assertTrue(data["source_candle_provenance"])
                    self.assertTrue(data["confirmation_candle_provenance"])
                    self.assertTrue(data["source_window_provenance"])
                    self.assertIsInstance(data["source_member_identities"], list)
                    for member_id in data["source_member_identities"]:
                        self.assertIn(member_id, event_ids)
                    if row["event_type"] in {"HH", "HL", "LH", "LL"}:
                        self.assertEqual(len(data["source_member_identities"]), 2)
                    if data["source_event_identity"]:
                        source_ids = data["source_event_identity"].split(",")
                        for source_id in source_ids:
                            self.assertIn(source_id, event_ids)
                        if row["event_type"] in {"HH", "HL", "LH", "LL"}:
                            self.assertEqual(data["source_member_identities"], [row["record_id"], *source_ids])
                        else:
                            self.assertEqual(data["source_member_identities"], source_ids)
                self.assertTrue(any(row["event_type"] == "FVG" for row in events))
                self.assertTrue(any(row["zone_type"] == "FVG" for row in zones))
                fvg_lifecycle_zones = [
                    row for row in zones if payload(row)["event_type"] == "FVG_LIFECYCLE"
                ]
                self.assertTrue(fvg_lifecycle_zones, "zone lifecycle must be appended under its stable zone type")
                for row in fvg_lifecycle_zones:
                    self.assertEqual(row["zone_type"], "FVG")
                    self.assertLessEqual(
                        datetime.fromisoformat(payload(row)["zone_formation_time"].replace("Z", "+00:00")),
                        row["event_time"],
                    )
                self.assertTrue(any(
                    row["timeframe"] == "4h" and row["event_type"] == "STRUCTURE_STATE"
                    and row["status"] == "insufficient_history"
                    for row in events
                ), "short 4h history must remain explicit, not fabricated")
                self.assertTrue(any(
                    row["timeframe"] == "1h" and row["knowledge_time"] == primary[-1].close_time
                    for row in events
                ), "exact primary boundary knowledge_time must be eligible")

                event_ids_before = {row["record_id"] for row in events}
                zone_ids_before = {row["record_id"] for row in zones}
                await handler(envelope)
                replay_events = await conn.fetch(
                    "SELECT * FROM meylux.market_structure_events "
                    "WHERE symbol=$1 AND event_type <> 'ORCHESTRATION' ORDER BY timeframe,event_time,record_id",
                    symbol,
                )
                replay_zones = await conn.fetch(
                    "SELECT * FROM meylux.market_structure_zones "
                    "WHERE symbol=$1 ORDER BY timeframe,event_time,record_id",
                    symbol,
                )
                self.assertEqual({row["record_id"] for row in replay_events}, event_ids_before)
                self.assertEqual({row["record_id"] for row in replay_zones}, zone_ids_before)
                self.assertEqual(len(replay_events), len(events))
                self.assertEqual(len(replay_zones), len(zones))

                for table in ("market_structure_events", "market_structure_zones"):
                    trigger = await conn.fetchrow(
                        "SELECT t.tgname,t.tgenabled,pg_get_triggerdef(t.oid) AS definition "
                        "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                        "JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "WHERE n.nspname='meylux' AND c.relname=$1 "
                        "AND t.tgname=$2 AND NOT t.tgisinternal",
                        table, f"trg_{table}_append_only",
                    )
                    self.assertIsNotNone(trigger, f"{table} append-only trigger must exist")
                    trigger_enabled = trigger["tgenabled"]
                    if isinstance(trigger_enabled, bytes):
                        trigger_enabled = trigger_enabled.decode("ascii")
                    self.assertEqual(trigger_enabled, "O")
                    self.assertIn("reject_canonical_mutation", trigger["definition"])
                    row = (events if table == "market_structure_events" else zones)[0]
                    before = await conn.fetchval(
                        f"SELECT to_jsonb(s) FROM meylux.{table} AS s WHERE record_id=$1",
                        row["record_id"],
                    )
                    self.assertIsNotNone(before)
                    for operation in ("UPDATE", "DELETE"):
                        try:
                            if operation == "UPDATE":
                                await conn.execute(
                                    f"UPDATE meylux.{table} SET reason=reason || '_forbidden' WHERE record_id=$1",
                                    row["record_id"],
                                )
                            else:
                                await conn.execute(
                                    f"DELETE FROM meylux.{table} WHERE record_id=$1",
                                    row["record_id"],
                                )
                        except self.asyncpg.PostgresError as exc:
                            if exc.sqlstate == "P0001":
                                self.assertEqual(
                                    str(exc),
                                    f"authoritative canonical history is append-only: {operation} is not permitted on {table}",
                                )
                            elif exc.sqlstate == "42501":
                                self.assertIn(f"permission denied for table {table}", str(exc))
                            else:
                                self.fail(f"unexpected SQLSTATE for {operation} on {table}: {exc.sqlstate} {exc}")
                        else:
                            self.fail(f"{operation} unexpectedly mutated {table}")
                        after = await conn.fetchval(
                            f"SELECT to_jsonb(s) FROM meylux.{table} AS s WHERE record_id=$1",
                            row["record_id"],
                        )
                        self.assertEqual(after, before, f"{table} row changed after rejected {operation}")
            finally:
                await conn.close()
        asyncio.run(run())

    def test_explicit_volume_profile_persists_real_canonical_trade_shape_and_replays_idempotently(self):
        async def run():
            conn = await self.asyncpg.connect(
                host=os.environ["MEYLUX_DB_HOST"], port=int(os.environ.get("MEYLUX_DB_PORT", "5432")),
                database=os.environ["MEYLUX_DB_NAME"], user=os.environ["MEYLUX_DB_USER"], password=os.environ["MEYLUX_DB_PASSWORD"],
                timeout=10, command_timeout=30,
            )
            try:
                symbol = "TO-P4-014-CI:BTCUSDT"
                start = datetime(2026, 2, 1, tzinfo=UTC)
                end = start + timedelta(hours=1)
                trades = tuple(
                    CanonicalTrade(
                        f"vp-trade-{i}", symbol, start + timedelta(minutes=10 * i),
                        Decimal("100") + Decimal(i), Decimal("2") + Decimal(i),
                        "BUY" if i == 0 else "SELL", provenance_id=f"vp-ci-provenance-{i}",
                    ) for i in range(2)
                )
                for i, trade in enumerate(trades):
                    event_id = f"vp-ci-raw-{i}"
                    received = trade.timestamp + timedelta(seconds=3 + i)
                    raw_payload = {"venue": "BINANCE"}
                    raw_json = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"))
                    await conn.execute(
                        "INSERT INTO meylux.raw_acquisition_events ("
                        "event_id,provider_id,adapter_id,adapter_version,canonical_instrument_id,provider_instrument_id,event_type,"
                        "event_time,received_at,acquisition_state,source_sequence,provenance_id,acquisition_method,payload_json,canonical_bytes,identity_hash"
                        ") VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb,$15,$16) ON CONFLICT (event_id) DO NOTHING",
                        event_id, "binance", "binance-acquisition", "1.0.0", symbol, "BTCUSDT", "TRADE",
                        trade.timestamp, received, "AVAILABLE", str(i), trade.provenance_id, "CI_FIXTURE", raw_json, raw_json.encode(),
                        hashlib.sha256(event_id.encode()).hexdigest(),
                    )
                    payload = {
                        "trade_id": trade.trade_id, "instrument_id": trade.instrument_id, "timestamp": trade.timestamp.isoformat().replace("+00:00", "Z"),
                        "price": str(trade.price), "quantity": str(trade.quantity), "aggressor_side": trade.aggressor_side,
                        "quote_quantity": None, "provenance_id": trade.provenance_id,
                    }
                    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                    await conn.execute(
                        "INSERT INTO meylux.canonical_trades ("
                        "record_id,event_id,instrument_id,event_time,provenance_id,source_record_id,lineage_parent_id,quality_state,quality_score,payload_json,canonical_bytes,identity_hash"
                        ") VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12) ON CONFLICT (record_id) DO NOTHING",
                        f"vp-ci-record-{i}", f"vp-ci-event-{i}", symbol, trade.timestamp, trade.provenance_id, event_id, event_id,
                        "valid", Decimal("1.00"), canonical_json, canonical_json.encode(), hashlib.sha256(canonical_json.encode()).hexdigest(),
                    )
                persistence = QuantitativePersistence(conn)
                config = VolumeProfileConfig(Decimal("1"), Decimal("0.50"), Decimal("0.10"))
                inserted = await persistence.persist_volume_profile(
                    symbol=symbol, timeframe="1h", trades=trades, interval_start=start, interval_end=end, config=config,
                )
                self.assertEqual(inserted, 1)
                rows = await persistence.fetch_family("volume_profile", symbol, "1h", limit=10)
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual((row["session_start"], row["session_end"]), (start, end))
                self.assertEqual(row["status"], "valid")
                self.assertEqual(row["venue_context"], "BINANCE")
                self.assertEqual(row["knowledge_time"], max(t.timestamp + timedelta(seconds=3 + i) for i, t in enumerate(trades)))
                payload = row["payload_json"] if isinstance(row["payload_json"], dict) else json.loads(row["payload_json"])
                self.assertEqual(payload["profile_interval"]["start"], start.isoformat().replace("+00:00", "Z"))
                self.assertEqual(payload["profile_interval"]["end"], end.isoformat().replace("+00:00", "Z"))
                self.assertEqual(tuple(payload["source_trade_ids"]), tuple(t.trade_id for t in trades))
                self.assertEqual(tuple(payload["source_provenance"]), tuple(t.provenance_id for t in trades))
                self.assertEqual(payload["poc"]["value"], "101")
                replay = await persistence.persist_volume_profile(
                    symbol=symbol, timeframe="1h", trades=trades, interval_start=start, interval_end=end, config=config,
                )
                self.assertEqual(replay, 0)
                self.assertEqual(len(await persistence.fetch_family("volume_profile", symbol, "1h", limit=10)), 1)
            finally:
                await conn.close()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
