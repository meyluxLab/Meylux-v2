import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from contracts.canonical import CanonicalTrade
from contracts.canonical.foundation import ProvenanceRef, ValidationOutcome, ValidationResult
from contracts.data_quality import DataQualityState
from contracts.quality import QualityInput, QualitySignals, assess_quality
from meylux.persistence.canonical import CanonicalPersistence
from meylux.persistence.event_handoff import CanonicalEventRelay, EventHandoffError
from meylux.persistence.factory import build_canonical_event

ROOT=Path(__file__).resolve().parents[1]
UTC=timezone.utc
PROV=ProvenanceRef("binance:vertical","binance","WS")
SCORES=QualitySignals(*(Decimal("1.00") for _ in range(6)))

def assessment():
    return assess_quality(QualityInput(ValidationOutcome(ValidationResult.VALID),SCORES,PROV,"raw:1","stage:1"))

class Tx:
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return False

class FakeConnection:
    def __init__(self,duplicate=False,expected_event_id=None):
        self.duplicate=duplicate; self.expected_event_id=expected_event_id; self.calls=[]; self.outbox_sequence=7
    def transaction(self): return Tx()
    async def fetchrow(self,query,*args):
        self.calls.append(("fetchrow",query,args))
        if "ON CONFLICT(record_id)" in query:
            if self.duplicate: return None
            return {"record_id":args[0]}
        if "SELECT record_id,event_id" in query:
            return {"record_id":args[0],"event_id":self.expected_event_id or "event"}
        if "canonical_event_outbox" in query:
            return {"sequence_no":self.outbox_sequence}
        return None
    async def execute(self,query,*args):
        self.calls.append(("execute",query,args)); return "OK"
    async def fetch(self,query,*args): return []

class FakeRedis:
    def __init__(self,fail=False): self.fail=fail; self.calls=[]
    async def eval(self,*args):
        self.calls.append(args)
        if self.fail: raise ConnectionError("redis unavailable")
        return b"1740000000000-0"

class P3008PersistenceIntegrationTests(unittest.TestCase):
    def test_migration_contains_authoritative_objects_and_append_only_controls(self):
        sql=(ROOT/"migrations/versions/0003_canonical_persistence_event_outbox.sql").read_text()
        for table in ("canonical_instruments","canonical_candles","canonical_trades","canonical_orderbook_depth","canonical_derivatives","data_quality_logs"):
            self.assertIn(f"me ylux.{table}".replace(" ",""),sql)
        self.assertIn("CREATE TRIGGER trg_%I_append_only",sql)
        self.assertIn("FOREACH t IN ARRAY ARRAY[",sql)
        self.assertIn("canonical_event_outbox",sql)
        self.assertIn("REVOKE UPDATE, DELETE, TRUNCATE",sql)
        self.assertIn("VALUES ('0003_canonical_persistence_event_outbox')",sql)
    def test_migration_harness_is_ordered_and_compose_wires_runtime(self):
        harness=(ROOT/"infrastructure/postgres/migrate.sh").read_text()
        self.assertLess(harness.index("0002_raw_acquisition_staging.sql"),harness.index("0003_canonical_persistence_event_outbox.sql"))
        compose=(ROOT/"infrastructure/compose/docker-compose.yml").read_text()
        self.assertIn("MEYLUX_DB_USER: meylux_app",compose)
        self.assertIn("MEYLUX_DB_PASSWORD: ${MEYLUX_APP_PASSWORD",compose)
        self.assertIn("MEYLUX_REDIS_URL: redis://redis:6379/0",compose)
    def test_persistence_is_atomic_and_records_quality_and_outbox(self):
        trade=CanonicalTrade("t1","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        record,event=build_canonical_event(trade,assessment(),1)
        conn=FakeConnection()
        result=asyncio.run(CanonicalPersistence(conn).persist(record,event.to_json(),assessment()))
        self.assertTrue(result.inserted); self.assertEqual(result.outbox_sequence,7)
        self.assertTrue(any(c[0]=="execute" and "data_quality_logs" in c[1] for c in conn.calls))
        self.assertTrue(any(c[0]=="fetchrow" and "canonical_event_outbox" in c[1] for c in conn.calls))
    def test_duplicate_replay_is_not_inserted_again(self):
        trade=CanonicalTrade("t1","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        record,event=build_canonical_event(trade,assessment(),1)
        conn=FakeConnection(duplicate=True,expected_event_id=event.event_id)
        result=asyncio.run(CanonicalPersistence(conn).persist(record,event.to_json(),assessment()))
        self.assertFalse(result.inserted)
    def test_event_relay_publishes_in_order_and_marks_outbox(self):
        class P:
            async def pending_events(self,limit): return [
                {"sequence_no":1,"event_id":"e1","record_id":"r1","event_type":"trade","event_time":datetime(2026,9,18,tzinfo=UTC),"payload_json":"{\"x\":1}"},
                {"sequence_no":2,"event_id":"e2","record_id":"r2","event_type":"trade","event_time":datetime(2026,9,18,tzinfo=UTC),"payload_json":"{\"x\":2}"}
            ]
            async def mark_event_published(self,event_id,stream_id): self.marked.append((event_id,stream_id))
        p=P(); p.marked=[]; redis=FakeRedis()
        count=asyncio.run(CanonicalEventRelay(p,redis).publish_pending())
        self.assertEqual(count,2); self.assertEqual([x[0] for x in p.marked],["e1","e2"]); self.assertEqual(redis.calls[0][2],"stream:canonical:market_events")
    def test_event_relay_isolates_transport_failure(self):
        class P:
            async def pending_events(self,limit): return [{"sequence_no":1,"event_id":"e1","record_id":"r1","event_type":"trade","event_time":datetime(2026,9,18,tzinfo=UTC),"payload_json":"{}"}]
            async def mark_event_published(self,*args): raise AssertionError("must not mark failed publication")
        with self.assertRaises(EventHandoffError):
            asyncio.run(CanonicalEventRelay(P(),FakeRedis(fail=True)).publish_pending())

if __name__=="__main__": unittest.main()
