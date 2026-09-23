from __future__ import annotations
import asyncio,json,unittest
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from contracts.specialist import EvidenceRef,FactStatus,InputSnapshot,SnapshotFact,SpecialistConfigRef,SpecialistFinding,SpecialistOutput,SpecialistStatus
from meylux.specialists.config import SpecialistConfig,SpecialistConfigError,load_specialists_config
from meylux.specialists.persistence import SpecialistPersistence
UTC=timezone.utc; T0=datetime(2026,1,1,tzinfo=UTC)
REF=EvidenceRef("ev-1","data","canonical/candle/1","a"*64,T0,"1.0.0"); CFG=SpecialistConfigRef("p5-foundation","1.0.0","b"*64,"development")
def snapshot():
 return InputSnapshot.build(as_of=T0,version="1.0.0",facts=(SnapshotFact("price",FactStatus.VALID,Decimal("100.25"),T0,(REF,)),),provenance_refs=(REF,))
def output(status=SpecialistStatus.SUCCESS):
 return SpecialistOutput("S-TEST","1.0.0",snapshot().snapshot_id,snapshot().version,CFG,status,"ok" if status is SpecialistStatus.SUCCESS else "explicit-test-state",(SpecialistFinding("F-1",status,Decimal("1"),"test",Decimal("0.75"),(REF,)),) if status in {SpecialistStatus.SUCCESS,SpecialistStatus.PARTIAL} else (), (REF,))
class TestContracts(unittest.TestCase):
 def test_identity_order_independent(self):
  a=snapshot(); b=InputSnapshot.build(as_of=T0,version="1.0.0",facts=tuple(reversed(a.facts)),provenance_refs=tuple(reversed(a.provenance_refs))); self.assertEqual(a.snapshot_id,b.snapshot_id)
 def test_lookahead_rejected(self):
  with self.assertRaises(ValueError): InputSnapshot.build(as_of=T0,version="1.0.0",facts=(SnapshotFact("future",FactStatus.VALID,Decimal("1"),datetime(2026,1,1,0,0,1,tzinfo=UTC),(REF,)),))
 def test_specialist_dependency_rejected(self):
  with self.assertRaises(ValueError): SnapshotFact("bad",FactStatus.VALID,{"specialist_output":{"status":"SUCCESS"}},T0,(REF,))
 def test_nonfinite_float_rejected(self):
  with self.assertRaises((ValueError,TypeError)): SnapshotFact("nan",FactStatus.VALID,Decimal("NaN"),T0,(REF,))
  with self.assertRaises(TypeError): SnapshotFact("float",FactStatus.VALID,1.5,T0,(REF,))
 def test_success_requires_evidence(self):
  with self.assertRaises(ValueError): SpecialistOutput("S","1.0.0",snapshot().snapshot_id,"1.0.0",CFG,SpecialistStatus.SUCCESS,"missing")
 def test_confidence_bounded(self):
  with self.assertRaises(ValueError): SpecialistFinding("F",SpecialistStatus.SUCCESS,Decimal("1"),"bad",Decimal("1.1"),(REF,))
 def test_status_taxonomy(self):
  self.assertEqual({x.value for x in SpecialistStatus},{"SUCCESS","PARTIAL","INSUFFICIENT_DATA","UNAVAILABLE_INPUT","SKIPPED","DISABLED","FAILED","TIMEOUT"})
 def test_serialization_stable(self):
  a=output().serialize(); b=output().serialize(); self.assertEqual(a,b); self.assertNotIn("NaN",a); self.assertNotIn("Infinity",a)
class TestConfig(unittest.TestCase):
 def test_scaffold(self):
  cfg=load_specialists_config(Path("config/specialists.yaml")); self.assertEqual(cfg.version,"1.0.0"); self.assertEqual(cfg.parameter("execution_timeout_ms"),5000); self.assertEqual(len(cfg.identity_hash),64)
 def test_bounds(self):
  raw=json.loads(Path("config/specialists.yaml").read_text()); raw["parameters"]["execution_timeout_ms"]["value"]=0
  with self.assertRaises(SpecialistConfigError): SpecialistConfig.from_mapping(raw)
 def test_safety(self):
  raw=json.loads(Path("config/specialists.yaml").read_text()); raw["safety"]["allow_trading"]=True
  with self.assertRaises(SpecialistConfigError): SpecialistConfig.from_mapping(raw)
class _Tx:
 async def __aenter__(self): return self
 async def __aexit__(self,*args): return False
class _DB:
 def __init__(self): self.sql=[]; self.seen=set()
 def transaction(self): return _Tx()
 async def execute(self,q,*args):
  self.sql.append((q,args)); identity=args[-1]
  if identity in self.seen: return "INSERT 0 0"
  self.seen.add(identity); return "INSERT 0 1"
 async def fetchrow(self,q,*args): return None
class TestPersistence(unittest.TestCase):
 def test_duplicate_replay_idempotent(self):
  db=_DB(); p=SpecialistPersistence(db); self.assertTrue(asyncio.run(p.persist(output()))); self.assertFalse(asyncio.run(p.persist(output()))); self.assertIn("ON CONFLICT (identity_hash) DO NOTHING",db.sql[0][0])
 def test_failure_has_no_fake_finding(self):
  failed=output(SpecialistStatus.FAILED); self.assertEqual(failed.findings,()); self.assertTrue(asyncio.run(SpecialistPersistence(_DB()).persist(failed)))
class TestMigration(unittest.TestCase):
 def test_append_only_and_privileges(self):
  sql=Path("migrations/versions/0007_specialist_foundation.sql").read_text()
  self.assertIn("BEFORE UPDATE OR DELETE",sql); self.assertIn("reject_canonical_mutation()",sql); self.assertIn("GRANT SELECT,INSERT",sql); self.assertIn("REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER",sql)
if __name__=="__main__": unittest.main()
