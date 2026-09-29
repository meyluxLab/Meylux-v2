from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import subprocess
import time
import unittest
from urllib.error import URLError
from decimal import Decimal

from contracts.acquisition import AcquisitionState
from contracts.canonical.foundation import ProvenanceRef, ValidationOutcome, ValidationResult
from contracts.quality import QualityInput, QualitySignals, assess_quality
from contracts.specialist import FactStatus
from meylux.acquisition.binance import BinanceAdapter
from meylux.acquisition.persistence import RawStagingRepository
from meylux.persistence.quality_evidence import QualityEvidencePersistence
from meylux.runtime.p3_008_vertical_slice import process_raw_row
from meylux.specialists.snapshot import InputSnapshotBuilder, LookaheadFactError


ROOT=Path(__file__).resolve().parents[1]
IMAGE="timescale/timescaledb:2.29.2-pg16"
CONTAINER=f"meylux-to-p3-009-pg-{os.getpid()}"
ADMIN="meylux_admin"
APP="meylux_app"
DB="meylux_p3009"
ADMIN_PASSWORD="p3-009-admin"
APP_PASSWORD="p3-009-app"
UTC=timezone.utc
T0=datetime(2026,9,29,12,0,tzinfo=UTC)


class TestP3009PostgreSQLBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("MEYLUX_RUN_P3009_POSTGRESQL") != "1":
            raise unittest.SkipTest("P3-009 PostgreSQL evidence runs only in its dedicated CI Core evidence step.")
        cls.docker=shutil.which("docker")
        if cls.docker is None:
            raise unittest.SkipTest("Docker unavailable; PostgreSQL-backed P3-009 evidence skipped.")
        probe=subprocess.run([cls.docker,"info"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        if probe.returncode != 0:
            raise unittest.SkipTest("Docker daemon unavailable; PostgreSQL-backed P3-009 evidence skipped.")
        cls._run([cls.docker,"run","--rm","--detach","--name",CONTAINER,
                  "--env",f"POSTGRES_DB={DB}","--env",f"POSTGRES_USER={ADMIN}",
                  "--env",f"POSTGRES_PASSWORD={ADMIN_PASSWORD}","--volume",f"{ROOT}:/workspace:ro",
                  IMAGE])
        for _ in range(60):
            ready=cls._run([cls.docker,"exec","--env",f"PGPASSWORD={ADMIN_PASSWORD}",CONTAINER,
                            "psql","-X","-At","-U",ADMIN,"-d",DB,"-c","SELECT 1;"],check=False)
            if ready.returncode==0 and ready.stdout.strip()=="1":
                break
            time.sleep(1)
        else:
            raise RuntimeError("ephemeral PostgreSQL did not become ready")
        for name in (
            "0001_database_foundation.sql","0002_raw_acquisition_staging.sql",
            "0003_canonical_persistence_event_outbox.sql","0004_canonical_quality_state_alignment.sql",
            "0005_quantitative_foundation.sql","0006_application_role_grant_hardening.sql",
            "0007_specialist_foundation.sql","0008_p4_knowledge_time_persistence.sql",
            "0009_quality_evidence_persistence.sql",
        ):
            cls._psql_file(f"migrations/versions/{name}")
        cls._psql(f"ALTER ROLE {APP} LOGIN PASSWORD '{APP_PASSWORD}';")
        cls.db_host=cls._run([cls.docker,"inspect","-f","{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",CONTAINER]).stdout.strip()
        if not cls.db_host:
            raise RuntimeError("unable to resolve ephemeral PostgreSQL container address")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls,"docker",None):
            subprocess.run([cls.docker,"rm","-f",CONTAINER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)

    @classmethod
    def _run(cls,args,check=True):
        return subprocess.run(args,text=True,capture_output=True,check=check)

    @classmethod
    def _psql(cls,sql,user=ADMIN,password=None,check=True):
        return cls._run([cls.docker,"exec","--env",f"PGPASSWORD={password or ADMIN_PASSWORD}",CONTAINER,
                         "psql","-X","-v","ON_ERROR_STOP=1","-At","-U",user,"-d",DB,"-c",sql],check=check)

    @classmethod
    def _psql_file(cls,path):
        cls._run([cls.docker,"exec","--env",f"PGPASSWORD={ADMIN_PASSWORD}",CONTAINER,
                  "psql","-X","-v","ON_ERROR_STOP=1","-U",ADMIN,"-d",DB,"-f",f"/workspace/{path}"])

    @classmethod
    def _connect(cls):
        import asyncpg
        return asyncpg.connect(host=TestP3009PostgreSQLBehavior.db_host,port=5432,database=DB,user=APP,password=APP_PASSWORD)

    @staticmethod
    def _record(*,timeframe="15m",venue="BINANCE",knowledge=T0,sequence="p3009-sequence"):
        from contracts.acquisition import AcquisitionEnvelope,EventType,InstrumentIdentity,ProviderIdentity,Provenance,AcquisitionState
        provider=ProviderIdentity("binance","binance-acquisition","1.0.0")
        instrument=InstrumentIdentity("BINANCE:BTCUSDT","BTCUSDT")
        provenance=Provenance("binance:p3009",provider,"TEST")
        envelope=AcquisitionEnvelope(
            provider,instrument,provenance,EventType.CANDLE,T0-timedelta(minutes=15),knowledge,
            AcquisitionState.AVAILABLE,
            {"timeframe":timeframe,"venue":venue,"close":"100"},
            sequence,
        )
        assessment=assess_quality(QualityInput(
            ValidationOutcome(ValidationResult.VALID),
            QualitySignals(*(Decimal("1.00") for _ in range(6))),
            ProvenanceRef("binance:p3009","binance","TEST"),
            envelope.event_id,envelope.event_id,
        ))
        return envelope,assessment

    def test_actual_unavailable_provider_outcome_reaches_persisted_quality_evidence(self):
        def failing_http(_url,_timeout):
            raise URLError("simulated transport outage")
        adapter=BinanceAdapter(http_get=failing_http,clock=lambda:T0)
        envelope=adapter.fetch_klines("BTCUSDT","15m",limit=1)[0]
        self.assertIs(envelope.state,AcquisitionState.UNAVAILABLE)
        self.assertIsNotNone(envelope.provider_error)
        self.assertEqual(envelope.provider_error.code,"BINANCE_TRANSPORT_FAILURE")

        async def run():
            conn=await self._connect()
            try:
                raw=await RawStagingRepository(conn).persist(envelope)
                self.assertTrue(raw.inserted)
                row=await conn.fetchrow(
                    "SELECT event_id,provider_id,adapter_id,adapter_version,canonical_instrument_id,provider_instrument_id,event_type,event_time,received_at,acquisition_state,source_sequence,provenance_id,acquisition_method,payload_json,canonical_bytes FROM meylux.raw_acquisition_events WHERE event_id=$1",
                    envelope.event_id,
                )
                evidence_result,_=await process_raw_row(conn,row)
                self.assertTrue(evidence_result.inserted)
                persisted=await conn.fetchrow(
                    "SELECT acquisition_state,quality_state,knowledge_time,received_at,source_record_id FROM meylux.quality_evidence WHERE evidence_id=$1",
                    evidence_result.evidence_id,
                )
                self.assertEqual(persisted["acquisition_state"],"UNAVAILABLE")
                self.assertEqual(persisted["quality_state"],"UNAVAILABLE")
                self.assertEqual(persisted["knowledge_time"],persisted["received_at"])
                self.assertEqual(persisted["source_record_id"],envelope.event_id)
            finally:
                await conn.close()
        asyncio.run(run())

    def test_persisted_record_resolves_to_p5_snapshot_and_enforces_temporal_boundary(self):
        async def run():
            conn=await self._connect()
            try:
                envelope,assessment=self._record(venue="BINANCE",sequence="snapshot")
                from contracts.quality_evidence import build_quality_evidence
                evidence=build_quality_evidence(envelope,assessment)
                repo=QualityEvidencePersistence(conn)
                inserted=await repo.persist(evidence)
                self.assertTrue(inserted.inserted)
                ref=await repo.resolve_evidence_ref(evidence.logical_fact_key,require_timeframe=True,require_venue=True)
                self.assertIsNotNone(ref)
                self.assertEqual(set(("source_family","record_id","identity_hash","event_time","knowledge_time","timeframe","venue")),set(ref)-{"evidence_id","source_type","source_reference","observed_at_utc","content_version"})
                self.assertEqual(ref["record_id"],evidence.source_record_id)
                self.assertEqual(ref["identity_hash"],evidence.source_identity_hash)

                metadata={
                    "symbol":"BTCUSDT","venue":"BINANCE","product":"Spot","timeframe":"15m",
                    "source_table":"meylux.quality_evidence","record_id":evidence.source_record_id,
                    "identity_hash":evidence.source_identity_hash,"version":evidence.adapter_version,
                    "event_time":evidence.event_time,"knowledge_time":evidence.knowledge_time,
                }
                record={
                    "fact_id":evidence.source_record_id,"status":"VALID","value":{"quality_state":"VALID"},
                    "event_time":evidence.event_time,"knowledge_time":evidence.knowledge_time,
                    "evidence_refs":(ref,),"reason":None,"metadata":metadata,
                }
                builder=InputSnapshotBuilder()
                snap=builder.build(as_of=evidence.knowledge_time,records=[record])
                self.assertEqual(snap.facts[0].evidence_refs[0].record_id,evidence.source_record_id)
                self.assertEqual(snap.facts[0].evidence_refs[0].identity_hash,evidence.source_identity_hash)
                with self.assertRaises(LookaheadFactError):
                    builder.build(as_of=evidence.knowledge_time-timedelta(microseconds=1),records=[record])

                incomplete_env,incomplete_assessment=self._record(timeframe=None,venue=None)
                incomplete=build_quality_evidence(incomplete_env,incomplete_assessment)
                await repo.persist(incomplete)
                self.assertIsNone(await repo.resolve_evidence_ref(incomplete.logical_fact_key,require_timeframe=True,require_venue=True))
            finally:
                await conn.close()
        asyncio.run(run())

    def test_postgresql_append_only_privileges_and_rerun_behavior(self):
        self._psql_file("migrations/versions/0009_quality_evidence_persistence.sql")
        self.assertEqual(self._psql("SELECT count(*) FROM meylux.schema_migrations WHERE version='0009_quality_evidence_persistence';").stdout.strip(),"1")
        self.assertEqual(self._psql("SELECT has_table_privilege('meylux_app','meylux.quality_evidence','SELECT'),has_table_privilege('meylux_app','meylux.quality_evidence','INSERT'),has_table_privilege('meylux_app','meylux.quality_evidence','UPDATE'),has_table_privilege('meylux_app','meylux.quality_evidence','DELETE'),has_table_privilege('meylux_app','meylux.quality_evidence','TRUNCATE');").stdout.strip(),"t|t|f|f|f")
        denied=self._psql("DELETE FROM meylux.quality_evidence;",user=APP,password=APP_PASSWORD,check=False)
        self.assertNotEqual(denied.returncode,0)
        denied_update=self._psql("UPDATE meylux.quality_evidence SET quality_state='VALID';",user=APP,password=APP_PASSWORD,check=False)
        self.assertNotEqual(denied_update.returncode,0)

    def test_postgresql_transaction_rollback_after_failed_evidence_insert(self):
        sql="""
        BEGIN;
        INSERT INTO meylux.quality_evidence(
            evidence_id,logical_fact_key,source_record_id,source_identity_hash,
            provider_id,adapter_id,adapter_version,canonical_instrument_id,provider_instrument_id,
            event_type,event_time,received_at,knowledge_time,acquisition_state,quality_state,lifecycle_state,
            reason_codes,provenance_id,payload_fingerprint,timeframe,venue
        ) VALUES(
            'p3009-rollback','p3009-rollback-logical','p3009-rollback-source',
            repeat('a',64),'binance','test','1.0.0','BINANCE:BTCUSDT','BTCUSDT','CANDLE',
            '2026-09-29T12:00:00Z','2026-09-29T12:00:01Z','2026-09-29T12:00:01Z',
            'AVAILABLE','VALID','ACCEPTED','[]','binance:p3009',repeat('b',64),'15m','BINANCE'
        );
        INSERT INTO meylux.quality_evidence(
            evidence_id,logical_fact_key,source_record_id,source_identity_hash,
            provider_id,adapter_id,adapter_version,canonical_instrument_id,provider_instrument_id,
            event_type,event_time,received_at,knowledge_time,acquisition_state,quality_state,lifecycle_state,
            reason_codes,provenance_id,payload_fingerprint,timeframe,venue
        ) VALUES(
            'p3009-rollback-bad','p3009-rollback-logical','p3009-rollback-source',
            repeat('c',64),'binance','test','1.0.0','BINANCE:BTCUSDT','BTCUSDT','CANDLE',
            '2026-09-29T12:00:00Z','2026-09-29T12:00:02Z','2026-09-29T12:00:01Z',
            'AVAILABLE','VALID','ACCEPTED','[]','binance:p3009',repeat('d',64),'15m','BINANCE'
        );
        COMMIT;
        """
        failed=self._psql(sql,check=False)
        self.assertNotEqual(failed.returncode,0)
        self.assertEqual(self._psql("SELECT count(*) FROM meylux.quality_evidence WHERE evidence_id='p3009-rollback';").stdout.strip(),"0")

    def test_duplicate_and_contradiction_behavior_on_real_postgresql(self):
        async def run():
            conn=await self._connect()
            try:
                envelope,assessment=self._record(venue="BINANCE",sequence="duplicate")
                from contracts.quality_evidence import build_quality_evidence
                evidence=build_quality_evidence(envelope,assessment)
                repo=QualityEvidencePersistence(conn)
                first=await repo.persist(evidence)
                second=await repo.persist(evidence)
                self.assertTrue(first.inserted)
                self.assertFalse(second.inserted)
                contradictory=envelope
                bad_assessment=assess_quality(QualityInput(
                    ValidationOutcome(ValidationResult.REJECTED),
                    QualitySignals(*(Decimal("1.00") for _ in range(6))),
                    ProvenanceRef("binance:p3009","binance","TEST"),
                    contradictory.event_id,contradictory.event_id,
                ))
                bad=build_quality_evidence(contradictory,bad_assessment)
                self.assertNotEqual(bad.evidence_id,evidence.evidence_id)
                result=await repo.persist(bad)
                self.assertTrue(result.contradictory)
                with self.assertRaises(Exception):
                    await repo.resolve(evidence.logical_fact_key)
            finally:
                await conn.close()
        asyncio.run(run())


if __name__=="__main__":
    unittest.main()
