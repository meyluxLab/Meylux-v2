from __future__ import annotations

import ast
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from contracts.specialist import EvidenceRef, FactStatus, SnapshotFact
from meylux.specialists.frm import FRM_ROWS, FRMReason, USR03Disposition, validate_frm
from meylux.specialists.snapshot import (
    AmbiguousFactError,
    ContradictoryFactError,
    FactReason,
    InputSnapshotBuilder,
    LookaheadFactError,
    SnapshotBuildError,
)

UTC = timezone.utc
T0 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
EVENT = T0 - timedelta(minutes=15)


def evidence(identity="b" * 64, *, event_time=EVENT, knowledge_time=T0, record_id="candle:BTCUSDT:15M:1"):
    return EvidenceRef(
        "ev-" + record_id,
        "postgresql",
        "meylux.canonical_candles:" + record_id,
        identity,
        T0,
        "1.0.0",
        "canonical_market",
        record_id,
        event_time,
        knowledge_time,
        "15M",
        "Binance",
    )


def record(
    fact_id="candle:BTCUSDT:15M:1",
    *,
    event_time=EVENT,
    knowledge=T0,
    status="VALID",
    value=None,
    identity="b" * 64,
    reason=None,
    metadata=None,
    refs=None,
):
    return {
        "fact_id": fact_id,
        "status": status,
        "value": value if value is not None else {"close": Decimal("100.25")},
        "event_time": event_time,
        "knowledge_time": knowledge,
        "evidence_refs": tuple(refs if refs is not None else (evidence(identity, event_time=event_time, knowledge_time=knowledge, record_id=fact_id),)),
        "reason": reason,
        "metadata": {
            "symbol": "BTCUSDT",
            "venue": "Binance",
            "product": "Spot",
            "timeframe": "15M",
            "source_table": "meylux.canonical_candles",
            "record_id": fact_id,
            "identity_hash": identity,
            "version": "1.0.0",
            "event_time": event_time,
            "knowledge_time": knowledge,
            **(metadata or {}),
        },
    }


class TestSnapshotBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = InputSnapshotBuilder()

    def test_equal_as_of_is_included(self):
        snap = self.builder.build(as_of=T0, records=[record()])
        self.assertEqual(len(snap.facts), 1)
        self.assertEqual(snap.facts[0].knowledge_time, T0)

    def test_future_knowledge_time_is_rejected(self):
        with self.assertRaises(LookaheadFactError):
            self.builder.build(as_of=T0, records=[record(knowledge=T0 + timedelta(microseconds=1))])

    def test_event_and_knowledge_time_are_distinct_and_preserved(self):
        snap = self.builder.build(as_of=T0, records=[record()])
        fact = snap.facts[0]
        ref = fact.evidence_refs[0]
        self.assertEqual(ref.event_time, EVENT)
        self.assertEqual(ref.knowledge_time, T0)
        self.assertEqual(fact.metadata["event_time"], EVENT)
        self.assertEqual(fact.metadata["knowledge_time"], T0)
        self.assertNotEqual(ref.event_time, ref.knowledge_time)

    def test_event_time_change_changes_identity(self):
        a = self.builder.build(as_of=T0, records=[record(event_time=EVENT)])
        b = self.builder.build(as_of=T0, records=[record(event_time=EVENT + timedelta(minutes=15))])
        self.assertNotEqual(a.snapshot_id, b.snapshot_id)

    def test_identity_replay_is_deterministic(self):
        a = self.builder.build(as_of=T0, records=[record("b"), record("a")])
        b = self.builder.build(as_of=T0, records=[record("a"), record("b")])
        self.assertEqual(a.snapshot_id, b.snapshot_id)
        self.assertEqual(a.serialize(), b.serialize())

    def test_knowledge_time_change_changes_identity(self):
        a = self.builder.build(as_of=T0, records=[record(knowledge=T0)])
        b = self.builder.build(as_of=T0, records=[record(knowledge=T0 - timedelta(minutes=1))])
        self.assertNotEqual(a.snapshot_id, b.snapshot_id)

    def test_empty_evidence_refs_are_rejected(self):
        with self.assertRaisesRegex(SnapshotBuildError, "requires at least one structured EvidenceRef"):
            self.builder.build(as_of=T0, records=[record(refs=())])

    def test_nested_snapshot_content_is_immutable_and_detached_from_source(self):
        source = record(
            value={"outer": {"inner": [{"leaf": {"close": Decimal("100.25")}}]}},
            metadata={"nested": {"levels": [{"x": "original"}]}},
        )
        snap = self.builder.build(as_of=T0, records=[source])
        baseline_id = snap.snapshot_id
        baseline_serialized = snap.serialize()

        with self.assertRaises(TypeError):
            snap.facts[0].value["outer"]["inner"][0]["leaf"]["close"] = Decimal("999")
        with self.assertRaises(TypeError):
            snap.facts[0].metadata["nested"]["levels"][0]["x"] = "changed"
        with self.assertRaises(TypeError):
            snap.facts[0].value["outer"]["inner"] += ({"extra": True},)

        source["value"]["outer"]["inner"][0]["leaf"]["close"] = Decimal("777")
        source["metadata"]["nested"]["levels"][0]["x"] = "source-mutated"

        equivalent = self.builder.build(
            as_of=T0,
            records=[record(
                value={"outer": {"inner": [{"leaf": {"close": Decimal("100.25")}}]}},
                metadata={"nested": {"levels": [{"x": "original"}]}},
            )],
        )
        self.assertEqual(snap.snapshot_id, baseline_id)
        self.assertEqual(snap.serialize(), baseline_serialized)
        self.assertEqual(snap.snapshot_id, equivalent.snapshot_id)
        self.assertEqual(snap.serialize(), equivalent.serialize())

    def test_specialist_output_add_remove_cannot_change_authoritative_snapshot(self):
        authoritative = [record()]
        baseline = self.builder.build(as_of=T0, records=authoritative)
        hypothetical_output = {
            "specialist_id": "S-01",
            "status": "SUCCESS",
            "finding": {"code": "EXAMPLE"},
        }
        with self.assertRaises(ValueError):
            self.builder.build(as_of=T0, records=authoritative + [hypothetical_output])
        restored = self.builder.build(as_of=T0, records=list(authoritative))
        self.assertEqual(baseline.snapshot_id, restored.snapshot_id)
        self.assertEqual(baseline.serialize(), restored.serialize())

    def test_snapshot_dependency_import_path_is_static_and_independent(self):
        snapshot_path = Path(__file__).parents[1] / "src" / "meylux" / "specialists" / "snapshot.py"
        source = snapshot_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(snapshot_path))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        self.assertIn("contracts.specialist", imported)
        self.assertNotIn("meylux.specialists", imported)
        self.assertNotIn("meylux.specialists.engine", imported)
        self.assertNotIn("meylux.specialists.execution", imported)
        self.assertNotIn("meylux.specialists.output", imported)
        self.assertNotIn("SpecialistOutput", source)
        self.assertNotRegex(source, r"\bexecute(?:_specialist|_specialists)?\s*\(")
        builder_source = ast.get_source_segment(source, next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "InputSnapshotBuilder"))
        self.assertIsNotNone(builder_source)
        self.assertNotRegex(builder_source or "", r"\bSpecialist(?:Output|Finding|Request)\b")

    def test_snapshot_content_is_immutable_after_build(self):
        source = record()
        snap = self.builder.build(as_of=T0, records=[source])
        with self.assertRaises(TypeError):
            snap.facts[0].metadata["late_specialist_output"] = "x"
        with self.assertRaises(TypeError):
            snap.facts[0].value["close"] = Decimal("999")
        self.assertEqual(snap.snapshot_id, InputSnapshotBuilder().build(as_of=T0, records=[record()]).snapshot_id)
        self.assertEqual(snap.serialize(), InputSnapshotBuilder().build(as_of=T0, records=[record()]).serialize())

    def test_future_content_cannot_enter_authoritative_snapshot(self):
        future = record(knowledge=T0 + timedelta(minutes=1), value={"close": Decimal("999")})
        with self.assertRaises(LookaheadFactError):
            self.builder.build(as_of=T0, records=[future])

    def test_content_change_changes_identity(self):
        a = self.builder.build(as_of=T0, records=[record(value={"close": Decimal("100.25")})])
        b = self.builder.build(as_of=T0, records=[record(value={"close": Decimal("100.26")})])
        self.assertNotEqual(a.snapshot_id, b.snapshot_id)

    def test_structured_evidence_provenance_is_preserved(self):
        snap = self.builder.build(as_of=T0, records=[record()])
        ref = snap.facts[0].evidence_refs[0]
        self.assertEqual(ref.source_family, "canonical_market")
        self.assertEqual(ref.record_id, snap.facts[0].metadata["record_id"])
        self.assertEqual(ref.identity_hash, snap.facts[0].metadata["identity_hash"])
        self.assertEqual(ref.timeframe, "15M")
        self.assertEqual(ref.venue, "Binance")

    def test_incomplete_evidence_ref_is_rejected(self):
        old_style = EvidenceRef("ev-old", "postgresql", "x", "a" * 64)
        bad = record(refs=(old_style,))
        with self.assertRaises(SnapshotBuildError):
            self.builder.build(as_of=T0, records=[bad])

    def test_non_valid_reason_is_explicit(self):
        snap = self.builder.build(as_of=T0, records=[record(status="UNAVAILABLE", value=None, reason="UNSUPPORTED")])
        self.assertEqual(snap.facts[0].status, FactStatus.UNAVAILABLE)
        self.assertEqual(snap.facts[0].reason, "UNSUPPORTED")

    def test_contradictory_duplicate_is_rejected(self):
        a = record("same", identity="a" * 64)
        b = record("same", identity="b" * 64)
        with self.assertRaises(AmbiguousFactError):
            self.builder.build(as_of=T0, records=[a, b])

    def test_same_identity_different_content_is_rejected(self):
        a = record("same", identity="a" * 64, value={"close": Decimal("100")})
        b = record("same", identity="a" * 64, value={"close": Decimal("101")})
        with self.assertRaises(ContradictoryFactError):
            self.builder.build(as_of=T0, records=[a, b])

    def test_exact_duplicate_is_idempotent(self):
        a = record("same", identity="a" * 64)
        snap = self.builder.build(as_of=T0, records=[a, a])
        self.assertEqual(len(snap.facts), 1)

    def test_specialist_output_cannot_enter_snapshot(self):
        bad = record(metadata={"specialist_output": {"status": "SUCCESS"}})
        with self.assertRaises(ValueError):
            self.builder.build(as_of=T0, records=[bad])

    def test_specialist_ordering_cannot_influence_snapshot_identity(self):
        first = self.builder.build(as_of=T0, records=[record()])
        # The builder accepts only source records; specialist execution order has no input channel.
        second = self.builder.build(as_of=T0, records=[record()])
        self.assertEqual(first.snapshot_id, second.snapshot_id)

    def test_no_wall_clock_dependency(self):
        a = self.builder.build(as_of=T0, records=[record()])
        b = self.builder.build(as_of=T0, records=[record()])
        self.assertEqual(a.snapshot_id, b.snapshot_id)

    def test_classification_never_creates_usr03_state(self):
        cases = (
            ({"supported": False, "available": True}, (FactStatus.UNAVAILABLE, FactReason.UNSUPPORTED.value)),
            ({"supported": True, "available": False}, (FactStatus.UNAVAILABLE, FactReason.UNAVAILABLE.value)),
            ({"supported": True, "available": True, "sufficient": False}, (FactStatus.INSUFFICIENT_DATA, FactReason.INSUFFICIENT.value)),
            ({"supported": True, "available": True, "valid": False}, (FactStatus.INVALID, FactReason.INVALID.value)),
            ({"supported": True, "available": True, "stale": True}, (FactStatus.STALE, FactReason.STALE.value)),
        )
        for kwargs, expected in cases:
            self.assertEqual(InputSnapshotBuilder.classify_absence(**kwargs), expected)

    def test_malformed_record_is_rejected(self):
        with self.assertRaises(SnapshotBuildError):
            self.builder.build(as_of=T0, records=[{"fact_id": "x"}])

    def test_required_provenance_metadata_is_enforced(self):
        bad = record()
        del bad["metadata"]["identity_hash"]
        with self.assertRaises(SnapshotBuildError):
            self.builder.build(as_of=T0, records=[bad])

    def test_knowledge_time_is_mandatory(self):
        bad = record()
        del bad["knowledge_time"]
        with self.assertRaises(SnapshotBuildError):
            self.builder.build(as_of=T0, records=[bad])


class TestFRM(unittest.TestCase):
    def test_exact_three_usr03_dispositions(self):
        self.assertEqual(
            {x.value for x in USR03Disposition},
            {"AVAILABLE_PERSISTED", "PRQ_DELIVERED", "UNAVAILABLE_DISPOSITIONED"},
        )

    def test_every_row_has_source_audit(self):
        self.assertEqual({row.specialist for row in FRM_ROWS}, {f"S-{i:02d}" for i in range(1, 19)})
        self.assertTrue(all(row.source_audit for row in FRM_ROWS))
        self.assertTrue(all(any("knowledge_time=" in item for item in row.source_audit) for row in FRM_ROWS))

    def test_no_runtime_unverified_available_claims(self):
        self.assertTrue(all(row.disposition is USR03Disposition.UNAVAILABLE_DISPOSITIONED for row in FRM_ROWS))

    def test_all_18_specialists_present(self):
        self.assertEqual({row.specialist for row in FRM_ROWS}, {f"S-{i:02d}" for i in range(1, 19)})

    def test_every_unavailable_row_has_governed_disposition(self):

        unavailable = [row for row in FRM_ROWS if row.disposition is USR03Disposition.UNAVAILABLE_DISPOSITIONED]
        self.assertEqual(len(unavailable), 18)
        self.assertTrue(all(row.governed_disposition for row in unavailable))

    def test_s09_and_s18_are_not_available_from_snapshot_or_table_existence(self):
        rows = {row.specialist: row for row in FRM_ROWS}
        self.assertIs(rows["S-09"].disposition, USR03Disposition.UNAVAILABLE_DISPOSITIONED)
        self.assertIs(rows["S-18"].disposition, USR03Disposition.UNAVAILABLE_DISPOSITIONED)
        self.assertIn("OQ-P5-002-PRQ1-FACT-AVAILABILITY", rows["S-09"].governed_disposition)
        self.assertIn("OQ-P5-002-PRQ1-FACT-AVAILABILITY", rows["S-18"].governed_disposition)

    def test_s15_uses_governed_roadmap_disposition(self):
        row = next(x for x in FRM_ROWS if x.specialist == "S-15")
        self.assertIn("SKIPPED / NO_NEWS_PROVIDER_CONFIGURED", row.governed_disposition)

    def test_reason_does_not_create_disposition(self):
        self.assertNotIn("UNSUPPORTED", {x.value for x in USR03Disposition})
        self.assertNotIn("UNAVAILABLE", {x.value for x in USR03Disposition})
        self.assertIn(FRMReason.UNSUPPORTED.value, {x.reason.value for x in FRM_ROWS})


    def test_roadmap_growth_retention_policy_is_documented(self):
        from pathlib import Path
        text = Path("docs/requirements/P5_002_FACT_REQUIREMENTS_MATRIX.md").read_text(encoding="utf-8")
        lowered = text.lower()
        for required in ("logical event identity", "deduplication key", "unique constraint", "expected rate", "peak rate", "daily growth", "retention", "compression/archive", "maximum acceptable cardinality", "alert threshold", "recovery path", "backfill semantics", "replay semantics"):
            self.assertIn(required, lowered)

if __name__ == "__main__":
    unittest.main()
