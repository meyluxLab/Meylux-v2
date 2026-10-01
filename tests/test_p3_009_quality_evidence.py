import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
    ProviderError,
)
from contracts.canonical.foundation import ProvenanceRef, ValidationOutcome, ValidationResult
from contracts.quality import QualityInput, QualitySignals, assess_quality
from contracts.data_quality import DataQualityState
from contracts.quality_evidence import build_quality_evidence
from meylux.persistence.quality_evidence import (
    ContradictoryQualityEvidence,
    QualityEvidencePersistence,
)

UTC=timezone.utc
ROOT=Path(__file__).resolve().parents[1]
PROVIDER=ProviderIdentity("binance","binance-adapter","1.0.0")
INSTRUMENT=InstrumentIdentity("BINANCE:BTCUSDT","BTCUSDT")
PROVENANCE=Provenance("binance:test",PROVIDER,"WS")
SCORES=QualitySignals(*(Decimal("1.00") for _ in range(6)))


def envelope(event_time=None, received_at=None, payload=None):
    event_time=event_time or datetime(2026,9,29,12,0,tzinfo=UTC)
    received_at=received_at or datetime(2026,9,29,12,0,2,tzinfo=UTC)
    return AcquisitionEnvelope(
        PROVIDER,INSTRUMENT,PROVENANCE,EventType.CANDLE,event_time,received_at,
        AcquisitionState.AVAILABLE,payload or {"timeframe":"15m","venue":"BINANCE","close":"100"},
        "42"
    )


def assessment(result=ValidationResult.VALID, source="raw:1", parent="stage:1"):
    return assess_quality(QualityInput(
        ValidationOutcome(result),SCORES,ProvenanceRef("binance:test","binance","WS"),source,parent
    ))


class Tx:
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return False


class Conn:
    def __init__(self):
        self.rows={}
        self.calls=[]
    def transaction(self): return Tx()
    async def fetchrow(self,query,*args):
        self.calls.append(("fetchrow",query,args))
        if "WHERE evidence_id=$1" in query:
            return self.rows.get(args[0])
        if "WHERE logical_fact_key = $1" in query:
            values=[v for v in self.rows.values() if v["logical_fact_key"]==args[0]]
            return values[0] if values else None
        return None
    async def fetch(self,query,*args):
        self.calls.append(("fetch",query,args))
        return [v for v in self.rows.values() if v["logical_fact_key"]==args[0]]
    async def execute(self,query,*args):
        self.calls.append(("execute",query,args))
        if "INSERT INTO meylux.quality_evidence" in query:
            keys=(
                "evidence_id","logical_fact_key","source_record_id","source_identity_hash",
                "provider_id","adapter_id","adapter_version","canonical_instrument_id",
                "provider_instrument_id","event_type","event_time","received_at",
                "knowledge_time","acquisition_state","quality_state","lifecycle_state",
                "quality_score","reason_codes","validation_result","provenance_id",
                "lineage_parent_id","payload_fingerprint","timeframe","venue"
            )
            self.rows[args[0]]=dict(zip(keys,args))
        return "INSERT 0 1"


class P3009QualityEvidenceTests(unittest.TestCase):
    def test_semantic_boundary_is_receipt_not_event_or_persistence_time(self):
        e=build_quality_evidence(envelope(),assessment())
        self.assertEqual(e.knowledge_time,e.received_at)
        self.assertNotEqual(e.knowledge_time,e.event_time)
        self.assertTrue(e.event_knowledge_distinct)

    def test_deterministic_identity_replays_identically(self):
        left=build_quality_evidence(envelope(),assessment())
        right=build_quality_evidence(envelope(),assessment())
        self.assertEqual(left.evidence_id,right.evidence_id)
        self.assertEqual(left.logical_fact_key,right.logical_fact_key)

    def test_all_quality_states_are_persistable_as_evidence(self):
        expected={
            ValidationResult.VALID:DataQualityState.VALID,
            ValidationResult.DEGRADED:DataQualityState.DEGRADED,
            ValidationResult.STALE:DataQualityState.STALE,
            ValidationResult.INCOMPLETE:DataQualityState.INCOMPLETE,
            ValidationResult.CONTRADICTORY:DataQualityState.CONTRADICTORY,
            ValidationResult.REJECTED:DataQualityState.REJECTED,
            ValidationResult.UNAVAILABLE:DataQualityState.UNAVAILABLE,
        }
        for validation,state in expected.items():
            with self.subTest(validation=validation):
                e=build_quality_evidence(envelope(),assessment(validation))
                self.assertEqual(e.quality_state,state)

    def test_unavailable_acquisition_evidence_is_persistable_without_fabrication(self):
        unavailable=AcquisitionEnvelope(
            PROVIDER,INSTRUMENT,PROVENANCE,EventType.CANDLE,
            datetime(2026,9,29,12,0,tzinfo=UTC),
            datetime(2026,9,29,12,0,2,tzinfo=UTC),
            AcquisitionState.UNAVAILABLE,{"timeframe":"15m","venue":"BINANCE"},
            "43",ProviderError("UPSTREAM_DOWN","availability","provider unavailable")
        )
        unavailable_assessment=assess_quality(QualityInput(
            None,SCORES,ProvenanceRef("binance:test","binance","WS"),
            unavailable.event_id,unavailable.event_id,record_available=False
        ))
        record=build_quality_evidence(unavailable,unavailable_assessment)
        self.assertEqual(record.quality_state,DataQualityState.UNAVAILABLE)
        self.assertEqual(record.knowledge_time,unavailable.received_at)
        self.assertEqual(record.source_record_id,unavailable.event_id)

    def test_missing_context_is_preserved_not_fabricated(self):
        e=build_quality_evidence(envelope(payload={"close":"100"}),assessment())
        self.assertIsNone(e.timeframe)
        self.assertIsNone(e.venue)

    def test_conflicting_context_is_rejected(self):
        with self.assertRaises(ValueError):
            build_quality_evidence(envelope(payload={"timeframe":"15m","interval":"1h"}),assessment())

    def test_persistence_is_idempotent_and_append_only(self):
        conn=Conn()
        record=build_quality_evidence(envelope(),assessment())
        first=asyncio.run(QualityEvidencePersistence(conn).persist(record))
        second=asyncio.run(QualityEvidencePersistence(conn).persist(record))
        self.assertTrue(first.inserted)
        self.assertFalse(second.inserted)
        self.assertFalse(second.contradictory)

    def test_distinct_quality_identity_for_same_logical_fact_is_contradiction(self):
        conn=Conn()
        record=build_quality_evidence(envelope(),assessment(ValidationResult.VALID))
        conflicting=build_quality_evidence(envelope(),assessment(ValidationResult.REJECTED))
        self.assertEqual(record.logical_fact_key,conflicting.logical_fact_key)
        self.assertNotEqual(record.evidence_id,conflicting.evidence_id)
        asyncio.run(QualityEvidencePersistence(conn).persist(record))
        result=asyncio.run(QualityEvidencePersistence(conn).persist(conflicting))
        self.assertTrue(result.contradictory)
        with self.assertRaises(ContradictoryQualityEvidence):
            asyncio.run(QualityEvidencePersistence(conn).resolve(record.logical_fact_key))

    def test_p5_resolution_requires_context_when_consumer_requires_it(self):
        conn=Conn()
        record=build_quality_evidence(envelope(payload={"close":"100"}),assessment())
        asyncio.run(QualityEvidencePersistence(conn).persist(record))
        ref=asyncio.run(QualityEvidencePersistence(conn).resolve_evidence_ref(record.logical_fact_key,require_timeframe=True,require_venue=True))
        self.assertIsNone(ref)
        partial=build_quality_evidence(envelope(payload={"timeframe":"15m"}),assessment())
        conn2=Conn()
        asyncio.run(QualityEvidencePersistence(conn2).persist(partial))
        self.assertIsNone(asyncio.run(QualityEvidencePersistence(conn2).resolve_evidence_ref(partial.logical_fact_key,require_venue=True)))

    def test_migration_is_additive_idempotent_and_append_only(self):
        sql=(ROOT/"migrations/versions/0009_quality_evidence_persistence.sql").read_text()
        self.assertIn("CREATE TABLE IF NOT EXISTS meylux.quality_evidence",sql)
        self.assertIn("CHECK (knowledge_time = received_at)",sql)
        self.assertIn("BEFORE UPDATE OR DELETE",sql)
        self.assertIn("GRANT SELECT, INSERT",sql)
        self.assertIn("REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER",sql)
        self.assertNotIn("DROP TABLE",sql.upper())
        self.assertIn("ON CONFLICT(version) DO NOTHING",sql)

    def test_migration_harness_and_runtime_use_authoritative_path(self):
        harness=(ROOT/"infrastructure/postgres/migrate.sh").read_text()
        self.assertIn("0008_p4_knowledge_time_persistence.sql",harness)
        self.assertIn("0009_quality_evidence_persistence.sql",harness)
        runtime=(ROOT/"src/meylux/runtime/p3_008_vertical_slice.py").read_text()
        self.assertIn("QualityEvidencePersistence",runtime)
        self.assertIn("build_quality_evidence",runtime)
        self.assertLess(runtime.index("build_quality_evidence"),runtime.index("if not normalized.valid or not assessment.canonical_eligible"))


if __name__=="__main__":
    unittest.main()
