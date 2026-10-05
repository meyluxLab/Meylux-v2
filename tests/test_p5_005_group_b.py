from __future__ import annotations

import ast
import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from dataclasses import replace

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot
from meylux.specialists.config import load_specialists_config
from meylux.specialists.snapshot import InputSnapshotBuilder, SnapshotRecord
from meylux.specialists.group_b import (
    GroupBSemanticError,
    analyze_s02,
    analyze_s11,
    analyze_s12,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
CONFIG = load_specialists_config(Path("config/specialists.yaml"))


def _record(record_id: str, table: str, value, *,
            symbol: str = "BTCUSDT", timeframe: str = "15m",
            venue: str = "BINANCE", event_time: datetime,
            knowledge_time: datetime | None = None,
            status: FactStatus = FactStatus.VALID):
    knowledge_time = knowledge_time or event_time
    identity = hashlib.sha256(
        f"{table}:{record_id}:{symbol}:{timeframe}:{venue}".encode()
    ).hexdigest()
    ref = EvidenceRef(
        evidence_id=f"ev:{record_id}",
        source_type="postgresql",
        source_reference=f"{table}:{record_id}",
        identity_hash=identity,
        observed_at_utc=knowledge_time,
        content_version="1.0.0",
        source_family=table.split(".", 1)[-1],
        record_id=record_id,
        event_time=event_time,
        knowledge_time=knowledge_time,
        timeframe=timeframe,
        venue=venue,
    )
    metadata = {
        "symbol": symbol,
        "venue": venue,
        "product": "spot",
        "timeframe": timeframe,
        "source_table": table,
        "record_id": record_id,
        "identity_hash": identity,
        "version": "1.0.0",
        "event_time": event_time,
        "knowledge_time": knowledge_time,
    }
    reason = None if status is FactStatus.VALID else "controlled insufficient fixture"
    return SnapshotRecord(
        record_id, status, value, event_time, knowledge_time, (ref,), reason, metadata
    )


def _snapshot(*records, as_of=T0 + timedelta(hours=10)):
    return InputSnapshotBuilder().build(
        as_of=as_of, version="1.3.0", records=records
    )


def _finding(output, suffix):
    return next(f for f in output.findings if f.code.endswith(suffix))


class TestP5005GroupB(unittest.TestCase):
    def test_s02_interprets_state_confirmed_protected_price_and_active_zones(self):
        records = [
            _record("state", "meylux.market_structure_events", {
                "event_type": "STRUCTURE_STATE", "structural_state": "UNCONFIRMED",
                "event_location": T0, "knowledge_time": T0,
            }, event_time=T0, knowledge_time=T0),
            _record("confirmed", "meylux.market_structure_events", {
                "event_type": "HH", "level": "120", "direction": "bullish",
                "event_location": T0 + timedelta(minutes=15),
                "knowledge_time": T0 + timedelta(minutes=30),
            }, event_time=T0 + timedelta(minutes=15), knowledge_time=T0 + timedelta(minutes=30)),
            _record("protected", "meylux.market_structure_events", {
                "event_type": "BOS", "level": "100", "direction": "bullish",
                "event_location": T0 + timedelta(minutes=45),
                "knowledge_time": T0 + timedelta(hours=1),
            }, event_time=T0 + timedelta(minutes=45), knowledge_time=T0 + timedelta(hours=1)),
            _record("zone-near", "meylux.market_structure_zones", {
                "event_type": "ORDER_BLOCK", "lifecycle": "ACTIVE",
                "lower_bound": "99", "upper_bound": "101", "direction": "bullish",
                "event_location": T0 + timedelta(minutes=40),
            }, event_time=T0 + timedelta(minutes=40), knowledge_time=T0 + timedelta(hours=1)),
            _record("zone-far", "meylux.market_structure_zones", {
                "event_type": "FVG", "lifecycle": "ACTIVE",
                "lower_bound": "80", "upper_bound": "85", "direction": "bullish",
                "event_location": T0 + timedelta(minutes=30),
            }, event_time=T0 + timedelta(minutes=30), knowledge_time=T0 + timedelta(hours=1)),
            _record("candle", "meylux.canonical_candles", {
                "open": "102", "high": "106", "low": "101", "close": "105",
                "close_time": (T0 + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
            }, event_time=T0 + timedelta(hours=1, minutes=45),
                     knowledge_time=T0 + timedelta(hours=2)),
        ]
        snapshot = _snapshot(*records)
        first = analyze_s02(snapshot, CONFIG)
        second = analyze_s02(snapshot, CONFIG)
        self.assertEqual(first.identity_hash, second.identity_hash)
        self.assertEqual(_finding(first, ":STATE").value["state"], "UNCONFIRMED")
        self.assertEqual(_finding(first, ":LATEST_CONFIRMED").value["event_type"], "HH")
        protected = _finding(first, ":PROTECTED_LEVEL_RELATION")
        self.assertEqual(protected.value["relationship"], "ABOVE")
        self.assertEqual(protected.value["difference"], Decimal("5"))
        zones = _finding(first, ":NEAREST_UNMITIGATED_ZONES")
        self.assertEqual(zones.value["zones"][0]["record_id"], "zone-near")

    def test_s02_excludes_post_as_of_structure_and_preserves_boundary_equality(self):
        equality = T0 + timedelta(hours=2)
        valid = _record("state-eq", "meylux.market_structure_events", {
            "event_type": "STRUCTURE_STATE", "structural_state": "TRENDING_UP",
            "event_location": T0 + timedelta(hours=1), "knowledge_time": equality,
        }, event_time=T0 + timedelta(hours=1), knowledge_time=equality)
        future = _record("state-future", "meylux.market_structure_events", {
            "event_type": "STRUCTURE_STATE", "structural_state": "TRENDING_DOWN",
            "event_location": T0 + timedelta(hours=2), "knowledge_time": equality + timedelta(seconds=1),
        }, event_time=T0 + timedelta(hours=2), knowledge_time=equality + timedelta(seconds=1))
        snapshot = _snapshot(valid, as_of=equality)
        result = analyze_s02(snapshot, CONFIG)
        self.assertEqual(_finding(result, ":STATE").value["state"], "TRENDING_UP")
        with self.assertRaises(ValueError):
            _snapshot(valid, future, as_of=equality)

    def test_s11_detects_closed_candle_patterns_and_uses_authoritative_zone(self):
        previous_open = T0 + timedelta(hours=1)
        current_open = T0 + timedelta(hours=1, minutes=15)
        records = [
            _record("c1", "meylux.canonical_candles", {
                "open": "104.5", "high": "105", "low": "103", "close": "103.5",
                "close_time": (previous_open + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
            }, event_time=previous_open, knowledge_time=previous_open + timedelta(minutes=15)),
            _record("c2", "meylux.canonical_candles", {
                "open": "103", "high": "104.6", "low": "100", "close": "104.5",
                "close_time": (current_open + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
            }, event_time=current_open, knowledge_time=current_open + timedelta(minutes=15)),
            _record("zone", "meylux.market_structure_zones", {
                "event_type": "ORDER_BLOCK", "lifecycle": "ACTIVE",
                "lower_bound": "99", "upper_bound": "100.5", "direction": "bullish",
                "event_location": previous_open,
            }, event_time=previous_open, knowledge_time=previous_open + timedelta(minutes=15)),
        ]
        result = analyze_s11(_snapshot(*records), CONFIG)
        self.assertEqual(_finding(result, ":PIN_BAR").value["state"], "BULLISH")
        self.assertEqual(_finding(result, ":ENGULFING").value["state"], "BULLISH")
        self.assertEqual(_finding(result, ":INSIDE_BAR").value["state"], "NOT_DETECTED")
        rejection = _finding(result, ":ZONE_REJECTION")
        self.assertEqual(rejection.value["state"], "DETECTED")
        self.assertEqual(rejection.value["pattern_time"], current_open + timedelta(minutes=15))

    def test_s11_explicitly_dispositions_missing_candle_surface(self):
        zone = _record("zone", "meylux.market_structure_zones", {
            "event_type": "ORDER_BLOCK", "lifecycle": "ACTIVE",
            "lower_bound": "99", "upper_bound": "100", "direction": "bullish",
            "event_location": T0,
        }, event_time=T0, knowledge_time=T0)
        result = analyze_s11(_snapshot(zone), CONFIG)
        self.assertEqual(result.status.value, "UNAVAILABLE_INPUT")
        self.assertTrue(all(f.status.value == "UNAVAILABLE_INPUT" for f in result.findings))
        self.assertEqual(result.evidence_refs, ())

    def test_s12_orders_liquidity_and_only_counts_post_formation_sweeps(self):
        formation_time = T0
        sweep_time = T0 + timedelta(hours=1)
        records = [
            _record("pool", "meylux.market_structure_zones", {
                "event_type": "LIQUIDITY_POOL", "lifecycle": "ACTIVE",
                "level": "100", "lower_bound": "100", "upper_bound": "100",
                "direction": "bullish", "event_location": formation_time,
            }, event_time=formation_time, knowledge_time=formation_time),
            _record("sweep", "meylux.market_structure_zones", {
                "event_type": "LIQUIDITY_POOL_SWEEP", "lifecycle": "INVALIDATED",
                "level": "100", "lower_bound": "100", "upper_bound": "100",
                "direction": "bullish", "source_event_identity": "pool",
                "event_location": sweep_time,
            }, event_time=sweep_time, knowledge_time=sweep_time),
            _record("candle", "meylux.canonical_candles", {
                "open": "101", "high": "103", "low": "99", "close": "102",
                "close_time": (sweep_time + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
            }, event_time=sweep_time, knowledge_time=sweep_time + timedelta(minutes=15)),
        ]
        result = analyze_s12(_snapshot(*records), CONFIG)
        value = result.findings[0].value
        self.assertEqual(value["zones"][0]["state"], "SWEPT")
        self.assertEqual(value["depth_state"], "PARTIAL")
        self.assertIn("no depth-dependent conclusion", value["depth_interpretation"])

    def test_group_b_rejects_conflicting_venue_context(self):
        record = _record("bad", "meylux.market_structure_events", {
            "event_type": "STRUCTURE_STATE", "structural_state": "TRENDING_UP",
            "event_location": T0,
        }, symbol="BINANCE:BTCUSDT", venue="MEXC", event_time=T0, knowledge_time=T0)
        with self.assertRaises(GroupBSemanticError):
            analyze_s02(_snapshot(record), CONFIG)

    def test_group_b_has_no_specialist_output_dependency(self):
        module = Path(__file__).parents[1] / "src" / "meylux" / "specialists" / "group_b.py"
        tree = ast.parse(module.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertNotIn("meylux.specialists.group_a", imports)
        self.assertNotIn("meylux.specialists.s10", imports)

    def test_non_utc_evidence_is_rejected_before_specialist_execution(self):
        with self.assertRaises(ValueError):
            _record(
                "bad-time", "meylux.market_structure_events",
                {"event_type": "STRUCTURE_STATE", "structural_state": "UNCONFIRMED"},
                event_time=T0.replace(tzinfo=timezone(timedelta(hours=1))),
                knowledge_time=T0.replace(tzinfo=timezone(timedelta(hours=1))),
            )


if __name__ == "__main__":
    unittest.main()
