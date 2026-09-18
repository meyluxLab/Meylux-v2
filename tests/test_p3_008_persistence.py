import unittest
from datetime import datetime, timezone
from decimal import Decimal
from contracts.canonical import CanonicalTrade
from contracts.canonical.foundation import ProvenanceRef, ValidationOutcome, ValidationResult
from contracts.data_quality import DataQualityState
from contracts.event import CanonicalEvent, STREAM
from contracts.quality import QualityInput, QualitySignals, assess_quality
from meylux.persistence.factory import build_canonical_event
from meylux.persistence.canonical import CanonicalRecord, UnsupportedCanonicalState

UTC=timezone.utc
PROV=ProvenanceRef("binance:vertical","binance","WS")
SCORES=QualitySignals(*(Decimal("1.00") for _ in range(6)))

def assessment():
    return assess_quality(QualityInput(ValidationOutcome(ValidationResult.VALID),SCORES,PROV,"raw:1","stage:1"))

class P3008ContractTests(unittest.IsolatedAsyncioTestCase):
    def test_persist_with_assessment_executes_single_quality_log(self):
        from meylux.persistence.canonical import CanonicalPersistence

        class _Tx:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                return False

        class _Connection:
            def __init__(self):
                self.executed=[]
                self.transaction_entries=0

            def transaction(self):
                self.transaction_entries += 1
                return _Tx()

            async def fetchrow(self, query, *args):
                if query.startswith("INSERT INTO meylux.canonical_trades"):
                    return {"record_id": args[0]}
                if query.startswith("INSERT INTO meylux.canonical_event_outbox"):
                    return {"sequence_no": 1}
                raise AssertionError(f"unexpected fetchrow query: {query}")

            async def execute(self, query, *args):
                self.executed.append((query,args))
                return "INSERT 0 1"

            async def fetch(self, query, *args):
                raise AssertionError(f"unexpected fetch query: {query}")

        trade=CanonicalTrade("t-quality","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        record,event=build_canonical_event(trade,assessment(),1)
        connection=_Connection()
        result=await CanonicalPersistence(connection).persist(record,event.to_json(),assessment())

        quality_writes=[query for query,args in connection.executed if query.lstrip().startswith("INSERT INTO meylux.data_quality_logs")]
        self.assertEqual(len(quality_writes),1)
        self.assertTrue(result.inserted)
        self.assertEqual(connection.transaction_entries,1)

    def test_canonical_record_rejects_non_promotable_state(self):
        with self.assertRaises(UnsupportedCanonicalState):
            CanonicalRecord("trade","r","e",datetime(2026,9,18,tzinfo=UTC),"BTCUSDT",{}, "p","s","l", DataQualityState.REJECTED)
    def test_factory_preserves_lineage_and_quality(self):
        trade=CanonicalTrade("t1","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        record,event=build_canonical_event(trade,assessment(),1)
        self.assertEqual(record.quality_state,DataQualityState.VALID)
        self.assertEqual(record.source_record_id,"raw:1"); self.assertEqual(record.lineage_parent_id,"stage:1")
        self.assertEqual(event.provenance_id,"binance:vertical"); self.assertEqual(event.quality_state,DataQualityState.VALID)
        self.assertEqual(event.sequence,1)
    def test_event_serialization_is_deterministic(self):
        trade=CanonicalTrade("t1","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        _,a=build_canonical_event(trade,assessment(),1); _,b=build_canonical_event(trade,assessment(),1)
        self.assertEqual(a.to_json(),b.to_json()); self.assertEqual(a.payload_identity,b.payload_identity)
        self.assertEqual(STREAM,"stream:canonical:market_events")
    def test_factory_blocks_missing_lineage(self):
        a=assess_quality(QualityInput(ValidationOutcome(ValidationResult.VALID),SCORES,PROV,"raw:1",None))
        trade=CanonicalTrade("t1","BTCUSDT",datetime(2026,9,18,tzinfo=UTC),Decimal("100"),Decimal("1"),provenance_id="binance:vertical")
        self.assertFalse(a.canonical_eligible)
        with self.assertRaises(ValueError): build_canonical_event(trade,a,1)
    def test_event_rejects_non_valid_quality(self):
        with self.assertRaises(ValueError):
            CanonicalEvent("e","r","trade",1,datetime(2026,9,18,tzinfo=UTC),DataQualityState.DEGRADED,"p","s","l",{}, "c")
if __name__=="__main__": unittest.main()
