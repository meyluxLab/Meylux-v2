from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot, SnapshotFact, SpecialistStatus
from meylux.specialists.config import load_specialists_config
from meylux.specialists.runtime import PAYLOAD_CONTRACT, specialist_policy
from meylux.specialists.s10 import S10DataQualityAnalyst, S10SemanticError, snapshot_from_json

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _ref(name: str, when: datetime = T0) -> EvidenceRef:
    return EvidenceRef(name, "p3-quality", f"quality/{name}", "a" * 64, T0, "1.0.0", "quality", name, when, when, "15m", "BINANCE")


def _snapshot(*facts: SnapshotFact) -> InputSnapshot:
    refs = tuple(ref for fact in facts for ref in fact.evidence_refs)
    return InputSnapshot.build(as_of=T0, version="1.0.0", facts=facts, provenance_refs=refs)


class TestS10(unittest.TestCase):
    def setUp(self):
        self.config = load_specialists_config(Path("config/specialists.yaml")).ref()

    def test_all_valid_is_success_and_deterministic(self):
        ref = _ref("valid")
        snap = _snapshot(SnapshotFact("valid", FactStatus.VALID, Decimal("1"), T0, (ref,)))
        a = S10DataQualityAnalyst(self.config).analyze(snap)
        b = S10DataQualityAnalyst(self.config).analyze(snap)
        self.assertEqual(a.identity_hash, b.identity_hash)
        self.assertEqual(a.status, SpecialistStatus.SUCCESS)
        self.assertEqual(a.findings[0].value["worst_status"], "VALID")

    def test_required_non_valid_states_are_explicit(self):
        cases = (
            (FactStatus.STALE, "STALE_INPUT", SpecialistStatus.PARTIAL),
            (FactStatus.INSUFFICIENT_DATA, "INCOMPLETE_HISTORY", SpecialistStatus.INSUFFICIENT_DATA),
            (FactStatus.CONTRADICTORY, "CONTRADICTORY_INPUT", SpecialistStatus.PARTIAL),
            (FactStatus.UNAVAILABLE, "UNAVAILABLE_INPUT", SpecialistStatus.UNAVAILABLE_INPUT),
        )
        for status, code, output_status in cases:
            with self.subTest(status=status):
                ref = _ref(status.value.lower())
                snap = _snapshot(SnapshotFact("fact", status, None, T0, (ref,), "explicit-test-state"))
                output = S10DataQualityAnalyst(self.config).analyze(snap)
                self.assertEqual(output.status, output_status)
                self.assertIn(code, {finding.code for finding in output.findings})

    def test_zero_lookahead_and_evidence_resolution_are_rechecked_at_worker_boundary(self):
        future = datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)
        ref = _ref("future", future)
        source = InputSnapshot.build(as_of=future, version="1.0.0", facts=(SnapshotFact("future", FactStatus.VALID, Decimal("1"), future, (ref,)),), provenance_refs=(ref,))
        raw = json.loads(source.serialize())
        raw["as_of"] = T0.isoformat().replace("+00:00", "Z")
        with self.assertRaises(S10SemanticError):
            snapshot_from_json(json.dumps(raw))

    def test_canonical_snapshot_round_trip_preserves_identity_and_all_evidence_context(self):
        observed = datetime(2025, 12, 31, 23, 58, tzinfo=UTC)
        event = datetime(2025, 12, 31, 23, 59, tzinfo=UTC)
        knowledge = T0
        ref = EvidenceRef(
            "transport-roundtrip", "p3-quality", "quality/transport-roundtrip",
            "c" * 64, observed, "1.0.0", "quality", "transport-roundtrip",
            event, knowledge, "15m", "BINANCE",
        )
        fact = SnapshotFact(
            "transport-fact", FactStatus.VALID, Decimal("100"), knowledge, (ref,),
            metadata={"event_time": event, "knowledge_time": knowledge,
                      "timeframe": "15m", "venue": "BINANCE"},
        )
        source = _snapshot(fact)
        reconstructed = snapshot_from_json(source.serialize())

        self.assertEqual(reconstructed.snapshot_id, source.snapshot_id)
        self.assertEqual(reconstructed.serialize(), source.serialize())
        restored = reconstructed.facts[0].evidence_refs[0]
        self.assertEqual(restored.evidence_id, ref.evidence_id)
        self.assertEqual(restored.source_type, ref.source_type)
        self.assertEqual(restored.source_reference, ref.source_reference)
        self.assertEqual(restored.identity_hash, ref.identity_hash)
        self.assertEqual(restored.content_version, ref.content_version)
        self.assertEqual(restored.source_family, ref.source_family)
        self.assertEqual(restored.record_id, ref.record_id)
        self.assertEqual(restored.observed_at_utc, observed)
        self.assertEqual(restored.event_time, event)
        self.assertEqual(restored.knowledge_time, knowledge)
        self.assertEqual(restored.timeframe, "15m")
        self.assertEqual(restored.venue, "BINANCE")
        output = S10DataQualityAnalyst(self.config).analyze(reconstructed)
        self.assertEqual(output.snapshot_id, source.snapshot_id)
        self.assertEqual(output.status, SpecialistStatus.SUCCESS)

    def test_canonical_snapshot_round_trip_preserves_explicitly_unavailable_optional_context(self):
        ref = EvidenceRef(
            "transport-unavailable", "p3-quality", "quality/transport-unavailable",
            "d" * 64, None, None, "quality", "transport-unavailable",
            None, T0, None, None,
        )
        source = _snapshot(SnapshotFact(
            "unavailable-context", FactStatus.VALID, Decimal("100"), T0, (ref,)
        ))
        reconstructed = snapshot_from_json(source.serialize())
        self.assertEqual(reconstructed.snapshot_id, source.snapshot_id)
        restored = reconstructed.facts[0].evidence_refs[0]
        self.assertIsNone(restored.observed_at_utc)
        self.assertIsNone(restored.event_time)
        self.assertEqual(restored.knowledge_time, T0)
        self.assertIsNone(restored.timeframe)
        self.assertIsNone(restored.venue)
        self.assertEqual(
            S10DataQualityAnalyst(self.config).analyze(reconstructed).status,
            SpecialistStatus.SUCCESS,
        )

    def test_supplied_evidence_ref_temporal_fields_must_be_valid_explicit_utc(self):
        ref = _ref("malformed-temporal")
        source = _snapshot(SnapshotFact(
            "malformed-temporal", FactStatus.VALID, Decimal("1"), T0, (ref,)
        ))
        for field, value in (
            ("observed_at_utc", "not-a-timestamp"),
            ("event_time", "2026-01-01T00:00:00+01:00"),
            ("knowledge_time", ""),
        ):
            with self.subTest(field=field, value=value):
                raw = json.loads(source.serialize())
                raw["facts"][0]["evidence_refs"][0][field] = value
                with self.assertRaises(S10SemanticError):
                    snapshot_from_json(json.dumps(raw))

    def test_unresolvable_evidence_is_rejected(self):
        ref = _ref("fact")
        snap = _snapshot(SnapshotFact("fact", FactStatus.VALID, Decimal("1"), T0, (ref,)))
        raw = json.loads(snap.serialize())
        raw["provenance_refs"] = []
        with self.assertRaises(S10SemanticError):
            snapshot_from_json(json.dumps(raw, default=lambda x: x.isoformat().replace("+00:00", "Z")))

    def test_malformed_transport_is_non_retryable(self):
        with self.assertRaises(S10SemanticError):
            snapshot_from_json("{not-json}")

    def test_contract_and_policy_are_explicit(self):
        cfg = load_specialists_config(Path("config/specialists.yaml"))
        policy = specialist_policy(cfg)
        self.assertEqual(policy.payload_contract, PAYLOAD_CONTRACT)
        self.assertEqual(policy.ordering, "FIFO_ENQUEUE_AND_DELIVERY")
        self.assertGreaterEqual(policy.max_concurrency, 1)
        self.assertGreaterEqual(policy.max_attempts, 1)

    def test_configuration_is_runtime_driven(self):
        cfg = load_specialists_config(Path("config/specialists.yaml"))
        self.assertEqual(cfg.parameter("execution_timeout_ms"), 5000)
        self.assertEqual(cfg.parameter("max_concurrency"), 2)
        self.assertEqual(cfg.parameter("max_attempts"), 3)

    def test_no_float_leakage(self):
        ref = _ref("decimal")
        snap = _snapshot(SnapshotFact("decimal", FactStatus.VALID, Decimal("1.25"), T0, (ref,)))
        output = S10DataQualityAnalyst(self.config).analyze(snap)
        self.assertNotIn("NaN", output.serialize())
        self.assertNotIn("Infinity", output.serialize())


if __name__ == "__main__":
    unittest.main()
