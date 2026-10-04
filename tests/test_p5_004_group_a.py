from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot, SnapshotFact
from meylux.specialists.config import SpecialistConfig, load_specialists_config
from meylux.specialists.snapshot import InputSnapshotBuilder, SnapshotRecord
from meylux.specialists.group_a import GroupASemanticError, analyze_s01, analyze_s06, analyze_s08

UTC = timezone.utc
AS_OF = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def _fact(symbol, timeframe, name, value, *, source="meylux.calculated_indicator_vectors",
          status=FactStatus.VALID, event=None, knowledge=None, record_suffix=""):
    event = event or AS_OF
    knowledge = knowledge or event
    record_id = f"{symbol}:{timeframe}:{name}:{event.isoformat()}:{record_suffix}"
    identity = __import__("hashlib").sha256(record_id.encode()).hexdigest()
    ref = EvidenceRef(
        evidence_id="ev-" + identity[:24], source_type="postgresql",
        source_reference=f"{source}:{record_id}", identity_hash=identity,
        observed_at_utc=knowledge, content_version="1.0.0",
        source_family="indicator" if "indicator" in source else "canonical_market",
        record_id=record_id, event_time=event, knowledge_time=knowledge,
        timeframe=timeframe, venue="BINANCE",
    )
    if source == "meylux.canonical_candles":
        payload = {"close": value}
    else:
        payload = {"fact_name": name, "value": value, "status": "valid", "reason": "test-authoritative-value",
                   "context": {"timeframe": timeframe, "timestamp": event}}
    metadata = {
        "symbol": symbol, "venue": "BINANCE", "product": "spot", "timeframe": timeframe,
        "source_table": source, "record_id": record_id, "identity_hash": identity,
        "version": "1.0.0", "event_time": event, "knowledge_time": knowledge,
    }
    reason = None if status is FactStatus.VALID else "explicit test state"
    return SnapshotRecord(record_id, status, payload, event, knowledge, (ref,), reason, metadata)


def _snapshot(*, symbols=("BTCUSDT", "SOLUSDT"), timeframes=("15m", "1h", "4h"),
              ema_periods=(9, 20, 21, 50, 200), direction_by_tf=None, missing=(), extra=(), overrides=None):
    facts = list(extra)
    direction_by_tf = direction_by_tf or {}
    overrides = overrides or {}
    for symbol in symbols:
        for timeframe in timeframes:
            base = AS_OF - {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}.get(timeframe, timedelta(minutes=15))
            values = {
                "MACD": Decimal("1"), "MACD_SIGNAL": Decimal("0.5"), "MACD_HISTOGRAM": Decimal("0.5"),
                "RSI": Decimal("70"), "ADX": Decimal("25"), "BOLLINGER_UPPER": Decimal("110"),
                "BOLLINGER_MIDDLE": Decimal("100"), "BOLLINGER_LOWER": Decimal("90"),
                "BOLLINGER_BANDWIDTH": Decimal("0.05"), "ATR": Decimal("2"),
                "HISTORICAL_VOLATILITY": Decimal("0.6"), "ATR_PERCENTILE": Decimal("75"),
                "VOLATILITY_EXPANSION_RATIO": Decimal("1.2"),
            }
            if direction_by_tf.get(timeframe) == "BEARISH":
                values.update({"MACD": Decimal("-1"), "MACD_SIGNAL": Decimal("-0.5"),
                               "MACD_HISTOGRAM": Decimal("-0.5"), "RSI": Decimal("30")})
            for (override_symbol, override_tf, override_name), override_value in overrides.items():
                if (override_symbol, override_tf) == (symbol, timeframe):
                    values[override_name] = override_value
            for period in ema_periods:
                values[f"EMA_{period}"] = Decimal(str(100 - period / 10))
            close_value = Decimal("90") if direction_by_tf.get(timeframe) == "BEARISH" else Decimal("100")
            facts.append(_fact(symbol, timeframe, "CLOSE", close_value, source="meylux.canonical_candles", event=base, knowledge=base))
            for name, value in values.items():
                if (symbol, timeframe, name) in missing:
                    continue
                facts.append(_fact(symbol, timeframe, name, value, event=base, knowledge=base))
    return InputSnapshotBuilder().build(as_of=AS_OF, version="1.2.0", records=tuple(facts))


def _finding(output, code):
    exact = next((item for item in output.findings if item.code == code), None)
    if exact is not None:
        return exact
    parts = code.split(":")
    if len(parts) >= 3:
        venue_code = ":".join((parts[0], parts[1], "BINANCE", *parts[2:]))
        exact = next((item for item in output.findings if item.code == venue_code), None)
        if exact is not None:
            return exact
    raise AssertionError(f"finding not found: {code}")


def _config(**overrides):
    raw = __import__("json").loads(Path("config/specialists.yaml").read_text())
    for key, value in overrides.items():
        raw["parameters"][key]["value"] = value
    return SpecialistConfig.from_mapping(raw)


class TestP5004GroupASemantics(unittest.TestCase):
    def setUp(self):
        self.config = _config(group_a_venues="BINANCE")

    def test_s01_is_deterministic_and_uses_authoritative_fact_families(self):
        snapshot = _snapshot()
        first, second = analyze_s01(snapshot, self.config), analyze_s01(snapshot, self.config)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertEqual(first.identity_hash, second.identity_hash)
        self.assertEqual(_finding(first, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"], "OVERBOUGHT")
        self.assertEqual(_finding(first, "TECHNICAL:BTCUSDT:15m:ADX_STRENGTH").value["state"], "STRONG")
        self.assertEqual(_finding(first, "TECHNICAL:BTCUSDT:15m:BOLLINGER_SQUEEZE").value["state"], "SQUEEZE")
        self.assertEqual(_finding(first, "TECHNICAL:BTCUSDT:15m:PRICE_VS_MA").value["state"], "ABOVE_MA")
        self.assertEqual(first.status.value, "SUCCESS")

    def test_s01_threshold_equality_is_inclusive_and_config_driven(self):
        snapshot = _snapshot()
        config = _config(rsi_overbought=Decimal("70"), adx_trend_threshold=Decimal("25"),
                         bollinger_squeeze_bandwidth_threshold=Decimal("0.05"))
        output = analyze_s01(snapshot, config)
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"], "OVERBOUGHT")
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:ADX_STRENGTH").value["state"], "STRONG")
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:BOLLINGER_SQUEEZE").value["state"], "SQUEEZE")
        changed = analyze_s01(snapshot, _config(rsi_overbought=Decimal("71")))
        self.assertEqual(_finding(changed, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"], "NEUTRAL")

    def test_macd_and_mtf_midline_thresholds_are_versioned_configuration(self):
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",))
        macd_output = analyze_s01(snapshot, _config(macd_histogram_neutral_threshold=Decimal("0.5")))
        self.assertEqual(_finding(macd_output, "TECHNICAL:BTCUSDT:15m:MACD_STATE").value["state"], "NEUTRAL")

        midline_snapshot = _snapshot(overrides={("BTCUSDT", "15m", "RSI"): Decimal("50")})
        inclusive = analyze_s06(midline_snapshot, _config(rsi_midline=Decimal("50")))
        strict = analyze_s06(midline_snapshot, _config(rsi_midline=Decimal("51")))
        self.assertEqual(_finding(inclusive, "MTF:BTCUSDT:15m").value["state"], "BULLISH")
        self.assertEqual(_finding(strict, "MTF:BTCUSDT:15m").value["state"], "NEUTRAL")

    def test_negative_expansion_ratio_and_missing_evidence_ref_are_rejected(self):
        negative = _snapshot(overrides={("BTCUSDT", "15m", "VOLATILITY_EXPANSION_RATIO"): Decimal("-0.1")})
        output = analyze_s08(negative, self.config)
        self.assertEqual(_finding(output, "VOLATILITY:BTCUSDT:15m:EXPANSION_STATE").value["state"], "INVALID")

        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",))
        event = AS_OF - timedelta(minutes=15)
        malformed = SnapshotFact(
            "fact-without-ref", FactStatus.UNAVAILABLE,
            {"fact_name": "RSI", "value": "70", "status": "unavailable"},
            event, (), "source reference absent",
            {"symbol": "BTCUSDT", "timeframe": "15m",
             "source_table": "meylux.calculated_indicator_vectors", "fact_name": "RSI",
             "event_time": event, "knowledge_time": event},
        )
        malformed_snapshot = InputSnapshot.build(
            as_of=AS_OF, version="1.2.0", facts=(*snapshot.facts, malformed),
            provenance_refs=snapshot.provenance_refs,
        )
        with self.assertRaises(GroupASemanticError):
            analyze_s01(malformed_snapshot, self.config)

    def test_s08_low_classification_uses_configured_bandwidth_boundary(self):
        snapshot = _snapshot(overrides={
            ("BTCUSDT", "15m", "ATR_PERCENTILE"): Decimal("25"),
            ("BTCUSDT", "15m", "HISTORICAL_VOLATILITY"): Decimal("0.15"),
            ("BTCUSDT", "15m", "BOLLINGER_BANDWIDTH"): Decimal("0.05"),
        })
        output = analyze_s08(snapshot, self.config)
        self.assertEqual(_finding(output, "VOLATILITY:BTCUSDT:15m:CLASSIFICATION").value["state"], "LOW")

    def test_ema_200_missing_is_explicit_and_never_recomputed(self):
        snapshot = _snapshot(ema_periods=(20,), symbols=("BTCUSDT",), timeframes=("15m",))
        output = analyze_s01(snapshot, self.config)
        alignment = _finding(output, "TECHNICAL:BTCUSDT:15m:MA_ALIGNMENT")
        self.assertEqual(alignment.value["state"], "INSUFFICIENT_DATA")
        self.assertIn(200, {item["period"] for item in alignment.value["missing_periods"]})
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:PRICE_VS_MA").value["state"], "ABOVE_MA")

    def test_s01_missing_and_nonfinite_values_are_explicit(self):
        missing = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",), missing={("BTCUSDT", "15m", "RSI")})
        output = analyze_s01(missing, self.config)
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"], "MISSING")
        invalid = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",),
                            extra=(_fact("BTCUSDT", "15m", "RSI", "NaN", event=AS_OF, knowledge=AS_OF),))
        invalid_output = analyze_s01(invalid, self.config)
        self.assertIn(_finding(invalid_output, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"],
                      {"INVALID", "INSUFFICIENT_DATA"})

    def test_s01_contradictory_same_time_values_are_not_silently_selected(self):
        timestamp = AS_OF - timedelta(minutes=15)
        contradictory = _fact("BTCUSDT", "15m", "RSI", Decimal("40"), event=timestamp, record_suffix="second")
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",),
                             extra=(contradictory,))
        output = analyze_s01(snapshot, self.config)
        self.assertIn(_finding(output, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"],
                      {"CONTRADICTORY", "INVALID", "INSUFFICIENT_DATA"})

    def test_mismatched_event_times_are_explicitly_contradictory(self):
        newer_ema = _fact("BTCUSDT", "15m", "EMA_50", Decimal("95"),
                          event=AS_OF, knowledge=AS_OF, record_suffix="newer-ema")
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",), extra=(newer_ema,))
        technical = analyze_s01(snapshot, self.config)
        self.assertEqual(_finding(technical, "TECHNICAL:BTCUSDT:15m:MA_ALIGNMENT").value["state"],
                         "CONTRADICTORY_CONTEXT")

        newer_percentile = _fact("BTCUSDT", "15m", "ATR_PERCENTILE", Decimal("75"),
                                  event=AS_OF, knowledge=AS_OF, record_suffix="newer-percentile")
        volatility = analyze_s08(_snapshot(symbols=("BTCUSDT",), timeframes=("15m",),
                                            extra=(newer_percentile,)), self.config)
        self.assertEqual(_finding(volatility, "VOLATILITY:BTCUSDT:15m:CLASSIFICATION").value["state"],
                         "CONTRADICTORY_CONTEXT")

    def test_s06_reports_confluence_conflict_and_missing_timeframe(self):
        confluence = analyze_s06(_snapshot(), self.config)
        self.assertEqual(_finding(confluence, "MTF:BTCUSDT:OVERALL").value["outcome"], "CONFLUENCE")
        conflict_snapshot = _snapshot(direction_by_tf={"4h": "BEARISH"})
        conflict = analyze_s06(conflict_snapshot, self.config)
        self.assertEqual(_finding(conflict, "MTF:BTCUSDT:OVERALL").value["outcome"], "CONFLICT")
        missing_snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",))
        partial = analyze_s06(missing_snapshot, self.config)
        self.assertEqual(_finding(partial, "MTF:BTCUSDT:OVERALL").value["outcome"], "PARTIAL")
        self.assertIn("1h", _finding(partial, "MTF:BTCUSDT:OVERALL").value["missing_timeframes"])

    def test_s06_higher_timeframe_event_and_knowledge_must_not_exceed_primary_boundary(self):
        primary_close = AS_OF - timedelta(minutes=15)
        future_htf = _fact("BTCUSDT", "1h", "RSI", Decimal("60"), event=AS_OF, knowledge=AS_OF - timedelta(minutes=15), record_suffix="future-htf")
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",), extra=(future_htf,))
        output = analyze_s06(snapshot, self.config)
        self.assertEqual(_finding(output, "MTF:BTCUSDT:OVERALL").value["outcome"], "PARTIAL")
        self.assertEqual(_finding(output, "MTF:BTCUSDT:1h").value["state"], "POST_BOUNDARY_EVIDENCE")
        self.assertLessEqual(primary_close, AS_OF)

        future_knowledge = _fact("BTCUSDT", "1h", "RSI", Decimal("60"),
            event=AS_OF - timedelta(hours=1), knowledge=AS_OF, record_suffix="future-knowledge")
        knowledge_snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",), extra=(future_knowledge,))
        knowledge_output = analyze_s06(knowledge_snapshot, self.config)
        self.assertEqual(_finding(knowledge_output, "MTF:BTCUSDT:OVERALL").value["outcome"], "PARTIAL")
        self.assertEqual(_finding(knowledge_output, "MTF:BTCUSDT:1h").value["state"], "POST_BOUNDARY_EVIDENCE")

    def test_s08_classification_expansion_and_risk_flag_are_deterministic(self):
        snapshot = _snapshot()
        first, second = analyze_s08(snapshot, self.config), analyze_s08(snapshot, self.config)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertEqual(_finding(first, "VOLATILITY:BTCUSDT:15m:CLASSIFICATION").value["state"], "HIGH")
        self.assertEqual(_finding(first, "VOLATILITY:BTCUSDT:15m:EXPANSION_STATE").value["state"], "EXPANDING")
        self.assertEqual(_finding(first, "VOLATILITY:BTCUSDT:15m:RISK").value["flag"], "HIGH_VOLATILITY")

    def test_s08_threshold_boundary_and_contracting_stable_cases(self):
        snapshot = _snapshot()
        exact = analyze_s08(snapshot, _config(volatility_high_percentile=Decimal("75"),
            historical_volatility_high_threshold=Decimal("0.6"),
            bollinger_high_bandwidth_threshold=Decimal("0.1"),
            volatility_expanding_ratio_threshold=Decimal("1.2")))
        self.assertEqual(_finding(exact, "VOLATILITY:BTCUSDT:15m:CLASSIFICATION").value["state"], "HIGH")
        self.assertEqual(_finding(exact, "VOLATILITY:BTCUSDT:15m:EXPANSION_STATE").value["state"], "EXPANDING")
        low_ratio = _snapshot(overrides={("BTCUSDT", "15m", "VOLATILITY_EXPANSION_RATIO"): Decimal("0.8")})
        contracting = analyze_s08(low_ratio, self.config)
        self.assertEqual(_finding(contracting, "VOLATILITY:BTCUSDT:15m:EXPANSION_STATE").value["state"], "CONTRACTING")

    def test_evidence_provenance_and_identity_are_preserved(self):
        snapshot = _snapshot()
        output = analyze_s01(snapshot, self.config)
        self.assertTrue(output.evidence_refs)
        self.assertTrue(all(ref.record_id and ref.identity_hash and ref.timeframe and ref.venue for ref in output.evidence_refs))
        self.assertEqual(output.identity_hash, analyze_s01(snapshot, self.config).identity_hash)
        self.assertLessEqual(max(ref.knowledge_time for ref in output.evidence_refs), snapshot.as_of)

    def test_config_lists_reject_empty_items_duplicates_and_nonpositive_ema_periods(self):
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",))
        for invalid_symbols in ("BTCUSDT,,SOLUSDT", "BTCUSDT,btcusdt"):
            with self.subTest(value=invalid_symbols):
                with self.assertRaises(GroupASemanticError):
                    analyze_s01(snapshot, _config(group_a_symbols=invalid_symbols))
        for invalid_timeframes in ("15m,,1h", "1h,1H"):
            with self.subTest(value=invalid_timeframes):
                with self.assertRaises(GroupASemanticError):
                    analyze_s01(snapshot, _config(group_a_timeframes=invalid_timeframes))
        with self.assertRaises(GroupASemanticError):
            analyze_s01(snapshot, _config(technical_ema_periods="9,20,0"))

    def test_consumed_evidence_ref_requires_complete_identity_and_utc_context(self):
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",))
        event = AS_OF - timedelta(minutes=15)
        incomplete_ref = EvidenceRef(
            evidence_id="incomplete", source_type="postgresql", source_reference="fixture:incomplete",
            identity_hash="a" * 64, observed_at_utc=event, content_version="1.0.0",
            source_family="indicator", record_id="incomplete", event_time=event,
            knowledge_time=event, timeframe="15m", venue=None,
        )
        malformed = SnapshotFact(
            "incomplete-evidence", FactStatus.VALID,
            {"fact_name": "RSI", "value": "50", "status": "valid"}, event,
            (incomplete_ref,), None,
            {"symbol": "BTCUSDT", "venue": "BINANCE", "timeframe": "15m",
             "source_table": "meylux.calculated_indicator_vectors", "event_time": event,
             "knowledge_time": event},
        )
        candidate = InputSnapshot.build(
            as_of=AS_OF, version="1.2.0", facts=(*snapshot.facts, malformed),
            provenance_refs=snapshot.provenance_refs,
        )
        with self.assertRaises(GroupASemanticError):
            analyze_s01(candidate, self.config)

    def test_qualified_instrument_identity_is_matched_only_against_explicit_venue(self):
        records = []
        for venue, prefix, value in (("BINANCE", "BINANCE", Decimal("70")), ("MEXC", "MEXC", Decimal("30"))):
            record = _fact(f"{prefix}:BTCUSDT", "15m", "RSI", value, event=AS_OF, knowledge=AS_OF, record_suffix=venue)
            # The venue remains an independent authoritative field; it is not inferred from the symbol prefix.
            record = replace(record, metadata={**dict(record.metadata), "venue": venue},
                             evidence_refs=tuple(replace(ref, venue=venue) for ref in record.evidence_refs))
            records.append(record)
        snapshot = InputSnapshotBuilder().build(as_of=AS_OF, version="1.2.0", records=tuple(records))
        cfg = _config(group_a_symbols="BTCUSDT", group_a_timeframes="15m", group_a_venues="BINANCE,MEXC")
        output = analyze_s01(snapshot, cfg)
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:15m:RSI_ZONE").value["state"], "OVERBOUGHT")
        self.assertEqual(_finding(output, "TECHNICAL:BTCUSDT:MEXC:15m:RSI_ZONE").value["state"], "OVERSOLD")

    def test_stage1_independence_is_static_and_runtime_output_is_forbidden(self):
        module = Path(__file__).parents[1] / "src" / "meylux" / "specialists" / "group_a.py"
        tree = ast.parse(module.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertNotIn("meylux.specialists.s10", imports)
        self.assertNotIn("meylux.specialists.runtime", imports)
        with self.assertRaises(ValueError):
            SnapshotFact("forbidden", FactStatus.VALID, {"specialist_output": {"status": "SUCCESS"}},
                        AS_OF, (_fact("BTCUSDT", "15m", "RSI", Decimal("40")).evidence_refs[0],))


if __name__ == "__main__":
    unittest.main()
