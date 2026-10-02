from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot, SnapshotFact
from meylux.specialists.config import SpecialistConfig, load_specialists_config
from meylux.specialists.group_a import analyze_s01, analyze_s06, analyze_s08

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
    return SnapshotFact(record_id, status, payload, knowledge, (ref,), reason, metadata)


def _snapshot(*, symbols=("BTCUSDT", "SOLUSDT"), timeframes=("15m", "1h", "4h"),
              ema_periods=(20, 50, 200), direction_by_tf=None, missing=(), extra=()):
    facts = list(extra)
    direction_by_tf = direction_by_tf or {}
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
            for period in ema_periods:
                values[f"EMA_{period}"] = Decimal(str(100 - period / 10))
            facts.append(_fact(symbol, timeframe, "CLOSE", Decimal("100"), source="meylux.canonical_candles", event=base, knowledge=base))
            for name, value in values.items():
                if (symbol, timeframe, name) in missing:
                    continue
                facts.append(_fact(symbol, timeframe, name, value, event=base, knowledge=base))
    return InputSnapshot.build(as_of=AS_OF, version="1.2.0", facts=tuple(facts),
                               provenance_refs=tuple(ref for fact in facts for ref in fact.evidence_refs))


def _finding(output, code):
    return next(item for item in output.findings if item.code == code)


def _config(**overrides):
    raw = __import__("json").loads(Path("config/specialists.yaml").read_text())
    for key, value in overrides.items():
        raw["parameters"][key]["value"] = value
    return SpecialistConfig.from_mapping(raw)


class TestP5004GroupASemantics(unittest.TestCase):
    def setUp(self):
        self.config = load_specialists_config(Path("config/specialists.yaml"))

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

    def test_s06_higher_timeframe_knowledge_must_not_exceed_primary_boundary(self):
        primary_close = AS_OF - timedelta(minutes=15)
        future_htf = _fact("BTCUSDT", "1h", "RSI", Decimal("60"), event=AS_OF, knowledge=AS_OF, record_suffix="future-htf")
        snapshot = _snapshot(symbols=("BTCUSDT",), timeframes=("15m",), extra=(future_htf,))
        output = analyze_s06(snapshot, self.config)
        self.assertEqual(_finding(output, "MTF:BTCUSDT:OVERALL").value["outcome"], "PARTIAL")
        self.assertEqual(_finding(output, "MTF:BTCUSDT:1h").value["state"], "POST_BOUNDARY_EVIDENCE")
        self.assertLessEqual(primary_close, AS_OF)

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
        low_ratio = _snapshot(extra=(_fact("BTCUSDT", "15m", "VOLATILITY_EXPANSION_RATIO", Decimal("0.8"),
                                           event=AS_OF, knowledge=AS_OF, record_suffix="ratio-low"),))
        contracting = analyze_s08(low_ratio, self.config)
        self.assertEqual(_finding(contracting, "VOLATILITY:BTCUSDT:15m:EXPANSION_STATE").value["state"], "CONTRACTING")

    def test_evidence_provenance_and_identity_are_preserved(self):
        snapshot = _snapshot()
        output = analyze_s01(snapshot, self.config)
        self.assertTrue(output.evidence_refs)
        self.assertTrue(all(ref.record_id and ref.identity_hash and ref.timeframe and ref.venue for ref in output.evidence_refs))
        self.assertEqual(output.identity_hash, analyze_s01(snapshot, self.config).identity_hash)
        self.assertLessEqual(max(ref.knowledge_time for ref in output.evidence_refs), snapshot.as_of)

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
