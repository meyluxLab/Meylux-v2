from __future__ import annotations

import asyncio
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationStatus
from meylux.orchestration import QuantOrchestrationConfig, QuantitativeOrchestrator
from meylux.persistence.quantitative import QuantitativePersistence, _json
from meylux.quantitative.indicators import (
    adx, atr, atr_percentile, bollinger_bandwidth, bollinger_bands,
    ema_candles, historical_volatility, macd, rsi, volatility_expansion_ratio,
)
from meylux.quantitative.regime_venue import RegimeConfig

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
EXPECTED_FACTS = {
    "EMA", "EMA_9", "EMA_20", "EMA_21", "EMA_50", "EMA_200",
    "RSI", "MACD", "MACD_SIGNAL", "MACD_HISTOGRAM", "ATR", "ADX",
    "BOLLINGER_MIDDLE", "BOLLINGER_UPPER", "BOLLINGER_LOWER",
    "BOLLINGER_BANDWIDTH", "HISTORICAL_VOLATILITY", "ATR_PERCENTILE",
    "VOLATILITY_EXPANSION_RATIO",
}


def candle(i: int, timeframe: str = "15m", *, instrument: str = "BTCUSDT",
           interval_minutes: int = 15, closed: bool = True) -> CanonicalCandle:
    opened = T0 + timedelta(minutes=interval_minutes * i)
    closed_at = opened + timedelta(minutes=interval_minutes)
    close = Decimal(100 + i) + Decimal(i % 3) / Decimal(10)
    return CanonicalCandle(
        instrument, timeframe, opened, closed_at,
        close - Decimal("0.5"), close + Decimal("2"),
        close - Decimal("2"), close, Decimal(10 + i),
        is_closed=closed, provenance_id=f"source:{timeframe}:{i}",
    )


def config() -> QuantOrchestrationConfig:
    return QuantOrchestrationConfig(
        RegimeConfig(2, 2, Decimal("0.10"), Decimal("0.05"), Decimal("0.10"), Decimal("0.05"))
    )


def bars(count: int = 40) -> tuple[CanonicalCandle, ...]:
    return tuple(candle(i) for i in range(count))


def higher_bars(count: int = 10) -> tuple[CanonicalCandle, ...]:
    return tuple(candle(i, "1h", interval_minutes=60) for i in range(count))


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
        self.source_queries = []
        self.provenance_rows = []
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

    async def fetch(self, query, *args):
        if "FROM meylux.raw_acquisition_events" in query:
            self.source_queries.append((query, args))
            refs = set(args[0])
            return [row for row in self.provenance_rows if row["provenance_id"] in refs]
        self.fetches.append((query, args))
        return []

    async def fetchrow(self, query, *args):
        lowered = query.lower()
        table = (
            "meylux.market_structure_events" if "from meylux.market_structure_events" in lowered
            else "meylux.market_structure_zones" if "from meylux.market_structure_zones" in lowered
            else None
        )
        return None if table is None else self.structural_rows.get((table, args[0]))


class TestP4011GroupAFacts(unittest.TestCase):
    def test_complete_group_a_fact_vocabulary_uses_existing_deterministic_engine(self):
        xs = bars()
        cfg = config()
        result = QuantitativeOrchestrator().process(xs, cfg)
        self.assertEqual(set(result.indicators), EXPECTED_FACTS)
        expected_macd = macd(xs, 12, 26, 9)[-1]
        expected_bands = bollinger_bands(xs, 20, "2")[-1]
        expected = {
            "EMA": ema_candles(xs, 20)[-1],
            "EMA_9": ema_candles(xs, 9)[-1],
            "EMA_20": ema_candles(xs, 20)[-1],
            "EMA_21": ema_candles(xs, 21)[-1],
            "EMA_50": ema_candles(xs, 50)[-1],
            "EMA_200": ema_candles(xs, 200)[-1],
            "RSI": rsi(xs, 14)[-1],
            "MACD": expected_macd.macd,
            "MACD_SIGNAL": expected_macd.signal,
            "MACD_HISTOGRAM": expected_macd.histogram,
            "ATR": atr(xs, 14)[-1],
            "ADX": adx(xs, 14)[-1],
            "BOLLINGER_MIDDLE": expected_bands.middle,
            "BOLLINGER_UPPER": expected_bands.upper,
            "BOLLINGER_LOWER": expected_bands.lower,
            "HISTORICAL_VOLATILITY": historical_volatility(xs, 20, "365")[-1],
            "ATR_PERCENTILE": atr_percentile(xs, 14, 100)[-1],
            "VOLATILITY_EXPANSION_RATIO": volatility_expansion_ratio(xs, 14, 20)[-1],
        }
        for name, calculation in expected.items():
            self.assertEqual(result.indicators[name], calculation, name)
        bandwidth = bollinger_bandwidth(xs, 20, "2")[-1]
        self.assertEqual(
            (result.indicators["BOLLINGER_BANDWIDTH"].value,
             result.indicators["BOLLINGER_BANDWIDTH"].status,
             result.indicators["BOLLINGER_BANDWIDTH"].reason),
            (bandwidth.value, bandwidth.status, bandwidth.reason),
        )
        self.assertEqual(result.knowledge_time, result.as_of)
        for name, calculation in result.indicators.items():
            self.assertIsNotNone(calculation.context, name)
            self.assertEqual(calculation.context.timestamp, result.knowledge_time, name)
            self.assertEqual(calculation.context.timeframe, "15m", name)
            self.assertEqual(calculation.context.symbol, "BTCUSDT", name)
            self.assertTrue(calculation.context.source_ref, name)

    def test_insufficient_history_is_explicit_and_never_fabricated(self):
        result = QuantitativeOrchestrator().process(bars(3), config())
        for name, calculation in result.indicators.items():
            self.assertIsNone(calculation.value, name)
            self.assertEqual(calculation.status, CalculationStatus.INSUFFICIENT_HISTORY, name)
            self.assertTrue(calculation.reason, name)
            self.assertEqual(calculation.context.timestamp, result.knowledge_time, name)

    def test_all_configured_ema_periods_produce_values_with_sufficient_history(self):
        xs = bars(240)
        result = QuantitativeOrchestrator().process(xs, config())
        for period in (9, 20, 21, 50, 200):
            with self.subTest(period=period):
                fact = result.indicators[f"EMA_{period}"]
                expected = ema_candles(xs, period)[-1]
                self.assertEqual(fact.status, CalculationStatus.VALID)
                self.assertIsNotNone(fact.value)
                self.assertEqual((fact.value, fact.status, fact.reason),
                                 (expected.value, expected.status, expected.reason))

    def test_real_binance_provenance_requires_and_accepts_explicit_source_venue(self):
        xs = tuple(replace(candle, provenance_id="binance:binance-acquisition") for candle in bars(40))
        result = QuantitativeOrchestrator().process(xs, config())
        db = _DB()
        db.provenance_rows = [
            self._source_row("binance:binance-acquisition", venue="BINANCE")
        ]
        asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        rows = [
            args for query, args in db.sql
            if "INSERT INTO meylux.calculated_indicator_vectors" in query
        ]
        self.assertEqual(len(rows), 19)
        self.assertTrue(all(args[4] == "binance:binance-acquisition" for args in rows))
        self.assertTrue(all(args[5] == "BINANCE" for args in rows))

    def test_ci_provenance_without_authoritative_raw_mapping_remains_unresolved(self):
        xs = tuple(
            replace(candle, provenance_id=f"p4-011-ci:15m:{index}")
            for index, candle in enumerate(bars(4))
        )
        result = QuantitativeOrchestrator().process(xs, config())
        db = _DB()
        asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        rows = [
            args for query, args in db.sql
            if "INSERT INTO meylux.calculated_indicator_vectors" in query
        ]
        self.assertTrue(rows)
        self.assertTrue(all(args[5] is None for args in rows))

    def test_each_configured_ema_period_has_valid_or_explicit_insufficient_history(self):
        result = QuantitativeOrchestrator().process(bars(40), config())
        for period in (9, 20, 21):
            fact = result.indicators[f"EMA_{period}"]
            self.assertEqual(fact.status, CalculationStatus.VALID, f"EMA_{period}")
            self.assertIsNotNone(fact.value, f"EMA_{period}")
        for period in (50, 200):
            fact = result.indicators[f"EMA_{period}"]
            self.assertEqual(fact.status, CalculationStatus.INSUFFICIENT_HISTORY, f"EMA_{period}")
            self.assertIsNone(fact.value, f"EMA_{period}")
            self.assertIn(f"requires_at_least_{period}_observations", fact.reason)

    def test_each_eligible_higher_timeframe_gets_independent_fact_set(self):
        primary = bars(40)
        higher = higher_bars(10)  # final 1h close equals the primary knowledge boundary
        result = QuantitativeOrchestrator().process(primary, config(), higher_timeframes={"1h": higher})
        self.assertIn("1h", result.higher_timeframe_facts)
        facts = result.higher_timeframe_facts["1h"]
        self.assertEqual(set(facts.indicators), EXPECTED_FACTS)
        self.assertEqual(facts.timeframe, "1h")
        self.assertEqual(facts.event_time, higher[-1].close_time)
        self.assertEqual(facts.knowledge_time, higher[-1].close_time)
        self.assertLessEqual(facts.knowledge_time, result.knowledge_time)
        self.assertEqual(facts.indicators["EMA"].context.source_ref, higher[-1].provenance_id)

    def test_post_boundary_incomplete_mixed_instrument_and_mismatched_tf_rejected(self):
        primary = bars(20)
        future = higher_bars(6) + (
            candle(6, "1h", interval_minutes=60),
        )
        with self.assertRaisesRegex(ValueError, "after primary knowledge boundary"):
            QuantitativeOrchestrator().process(primary, config(), higher_timeframes={"1h": future})

        incomplete = list(higher_bars(1))
        incomplete[0] = candle(0, "1h", interval_minutes=60, closed=False)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            QuantitativeOrchestrator().process(primary, config(), higher_timeframes={"1h": incomplete})

        mixed = (candle(0, "1h", instrument="ETHUSDT", interval_minutes=60),)
        with self.assertRaisesRegex(ValueError, "instrument must match"):
            QuantitativeOrchestrator().process(primary, config(), higher_timeframes={"1h": mixed})

        mismatch = (candle(0, "4h", interval_minutes=240),)
        with self.assertRaisesRegex(ValueError, "contains candle with timeframe"):
            QuantitativeOrchestrator().process(primary, config(), higher_timeframes={"1h": mismatch})

    def test_invalid_macd_configuration_and_nonfinite_decimal_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "macd_fast_period must be less"):
            QuantOrchestrationConfig(
                config().regime, macd_fast_period=26, macd_slow_period=26
            )
        with self.assertRaisesRegex(ValueError, "non-finite Decimal"):
            _json(Decimal("NaN"))

    def test_persistence_writes_each_metric_per_timeframe_and_replay_is_idempotent(self):
        result = QuantitativeOrchestrator().process(
            bars(40), config(), higher_timeframes={"1h": higher_bars(10)}
        )
        db = _DB()
        persistence = QuantitativePersistence(db)
        first = asyncio.run(persistence.persist_orchestration(result))
        second = asyncio.run(persistence.persist_orchestration(result))
        self.assertEqual(first, 40)  # 19 primary + 19 HTF + regime + structure summary
        self.assertEqual(second, 0)
        indicator_rows = list({
            args[0]: (query, args)
            for query, args in db.sql if "calculated_indicator_vectors" in query
        }.values())
        self.assertEqual(len(indicator_rows), 38)
        primary_rows = [args for _, args in indicator_rows if args[2] == "15m"]
        higher_rows = [args for _, args in indicator_rows if args[2] == "1h"]
        self.assertEqual(len(primary_rows), 19)
        self.assertEqual(len(higher_rows), 19)
        self.assertTrue(all(args[3] == result.knowledge_time for args in primary_rows))
        self.assertTrue(all(args[3] == result.higher_timeframe_facts["1h"].knowledge_time for args in higher_rows))
        self.assertTrue(all("knowledge_time" not in query.lower() for query, _ in indicator_rows))
        self.assertEqual(len({args[-1] for _, args in indicator_rows}), 38)
        self.assertTrue(all(args[4] == "source:15m:39" for args in primary_rows))
        self.assertTrue(all(args[4] == "source:1h:9" for args in higher_rows))

    @staticmethod
    def _source_row(provenance_id, *, venue="BINANCE", venue_context=None,
                    venue_type="string", venue_context_type=None,
                    provider_id="binance", adapter_id="binance-acquisition",
                    adapter_version="1.0.0"):
        return {
            "provenance_id": provenance_id,
            "provider_id": provider_id,
            "adapter_id": adapter_id,
            "adapter_version": adapter_version,
            "venue": venue,
            "venue_context": venue_context,
            "venue_type": venue_type,
            "venue_context_type": venue_context_type,
        }

    def test_persistence_resolves_venue_from_explicit_raw_provenance_context(self):
        result = QuantitativeOrchestrator().process(bars(40), config())
        db = _DB()
        db.provenance_rows = [
            self._source_row(ref) for ref in result.source_provenance
        ]
        asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        rows = [
            args for query, args in db.sql
            if "INSERT INTO meylux.calculated_indicator_vectors" in query
        ]
        self.assertEqual(len(rows), 19)
        self.assertTrue(all(args[5] == "BINANCE" for args in rows))
        import json
        for args in rows:
            payload = json.loads(args[11])
            self.assertEqual(payload["context"]["venue_context"], "BINANCE")
            self.assertEqual(payload["context"]["source_ref"], args[4])
        self.assertIn("payload_json->>'venue'", db.source_queries[0][0])

    def test_missing_or_contradictory_calculation_source_ref_is_rejected_before_writes(self):
        result = QuantitativeOrchestrator().process(bars(4), config())
        original = result.indicators["EMA"]
        bad_cases = {
            "missing context": replace(original, context=None),
            "missing source_ref": replace(
                original, context=replace(original.context, source_ref=None)
            ),
            "source_ref outside lineage": replace(
                original, context=replace(original.context, source_ref="unrelated-source")
            ),
            "venue conflicts with raw evidence": replace(
                original, context=replace(original.context, venue_context="MEXC")
            ),
        }
        for label, bad_calculation in bad_cases.items():
            with self.subTest(label=label):
                bad_result = replace(
                    result,
                    indicators={**result.indicators, "EMA": bad_calculation},
                )
                db = _DB()
                if label == "venue conflicts with raw evidence":
                    db.provenance_rows = [
                        self._source_row(ref) for ref in result.source_provenance
                    ]
                with self.assertRaisesRegex(ValueError, "source_ref|venue_context"):
                    asyncio.run(QuantitativePersistence(db).persist_orchestration(bad_result))
                self.assertEqual(db.sql, [], "invalid lineage must fail before any persistence")

    def test_provider_identity_alone_never_becomes_venue(self):
        result = QuantitativeOrchestrator().process(bars(4), config())
        db = _DB()
        db.provenance_rows = [
            self._source_row(ref, venue=None, venue_type=None)
            for ref in result.source_provenance
        ]
        asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
        rows = [
            args for query, args in db.sql
            if "INSERT INTO meylux.calculated_indicator_vectors" in query
        ]
        self.assertTrue(rows)
        self.assertTrue(all(args[5] is None for args in rows))
        import json
        self.assertTrue(all(json.loads(args[11])["context"]["venue_context"] is None for args in rows))

    def test_missing_malformed_or_contradictory_provenance_stays_unresolved(self):
        result = QuantitativeOrchestrator().process(bars(4), config())
        refs = tuple(dict.fromkeys(result.source_provenance))
        scenarios = {
            "missing source row": [
                self._source_row(ref) for ref in refs[:-1]
            ],
            "contradictory venue": [
                self._source_row(ref) for ref in refs
            ] + [self._source_row(refs[0], venue="MEXC")],
            "malformed venue type": [
                self._source_row(ref, venue="123", venue_type="number") for ref in refs
            ],
            "conflicting venue fields": [
                self._source_row(ref, venue="BINANCE", venue_context="MEXC",
                                 venue_type="string", venue_context_type="string")
                for ref in refs
            ],
            "conflicting provider identity": [
                self._source_row(ref) for ref in refs
            ] + [self._source_row(refs[0], adapter_id="unrecognized-adapter")],
        }
        for label, source_rows in scenarios.items():
            with self.subTest(label=label):
                db = _DB()
                db.provenance_rows = source_rows
                asyncio.run(QuantitativePersistence(db).persist_orchestration(result))
                rows = [
                    args for query, args in db.sql
                    if "INSERT INTO meylux.calculated_indicator_vectors" in query
                ]
                self.assertTrue(rows)
                self.assertTrue(all(args[5] is None for args in rows), label)

    def test_ema_period_configuration_rejects_empty_duplicate_and_invalid_periods(self):
        for periods in ((), (9, 9), (9, 0), (9, True), [9, 20]):
            with self.subTest(periods=periods):
                with self.assertRaises(ValueError):
                    QuantOrchestrationConfig(config().regime, ema_periods=periods)

    def test_existing_readback_path_filters_independently_by_timeframe(self):
        db = _DB()
        rows = asyncio.run(QuantitativePersistence(db).fetch_family("indicator", "BTCUSDT", "1h", limit=20))
        self.assertEqual(rows, [])
        query, args = db.fetches[0]
        self.assertIn("symbol=$1 AND timeframe=$2", query)
        self.assertEqual(args, ("BTCUSDT", "1h", 20))
        start = T0
        end = T0 + timedelta(days=1)
        asyncio.run(QuantitativePersistence(db).fetch_family(
            "indicator", "BTCUSDT", "1h", start=start, end=end, limit=20
        ))
        bounded_query, bounded_args = db.fetches[1]
        self.assertIn("event_time>$3", bounded_query)
        self.assertIn("event_time<$4", bounded_query)
        self.assertIn("LIMIT $5", bounded_query)
        self.assertEqual(bounded_args, ("BTCUSDT", "1h", start, end, 20))

    def test_persistence_rejects_a_future_timeframe_fact_even_if_constructed_directly(self):
        from dataclasses import replace
        from meylux.orchestration.engine import TimeframeQuantitativeFacts

        result = QuantitativeOrchestrator().process(bars(20), config())
        future_time = result.knowledge_time + timedelta(hours=1)
        future_facts = TimeframeQuantitativeFacts(
            symbol=result.symbol,
            timeframe="1h",
            event_time=future_time,
            knowledge_time=future_time,
            configuration_version=result.configuration_version,
            indicators=result.indicators,
            source_provenance=result.source_provenance,
        )
        malformed = replace(result, higher_timeframe_facts={"1h": future_facts})
        with self.assertRaisesRegex(ValueError, "exceeds primary knowledge boundary"):
            asyncio.run(QuantitativePersistence(_DB()).persist_orchestration(malformed))


if __name__ == "__main__":
    unittest.main()
