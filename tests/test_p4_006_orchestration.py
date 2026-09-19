from __future__ import annotations
import asyncio
import json
import unittest
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from contracts.canonical.candle import CanonicalCandle
from contracts.quantitative.base import CalculationStatus
from meylux.api.quantitative import QuantitativeAPI
from meylux.orchestration import QuantOrchestrationConfig,QuantitativeOrchestrator,align_higher_timeframe
from meylux.persistence.quantitative import QuantitativePersistence
from meylux.quantitative.regime_venue import RegimeConfig,BULLISH,RANGE
from meylux.replay import QuantitativeReplay
from meylux.runtime.quant_worker import QuantWorkerHandler
from meylux.queue import QueueEnvelope

UTC=timezone.utc
T0=datetime(2026,1,1,tzinfo=UTC)

def candle(i:int,close:str,tf="15m",instrument="BTCUSDT",closed=True)->CanonicalCandle:
    t=T0+timedelta(minutes=15*i)
    c=Decimal(close)
    return CanonicalCandle(instrument,tf,t,t+timedelta(minutes=15),c,c,c,c,Decimal("10"),is_closed=closed,provenance_id=f"p-{tf}-{i}")

def config()->QuantOrchestrationConfig:
    return QuantOrchestrationConfig(RegimeConfig(2,2,Decimal("0.10"),Decimal("0.05"),Decimal("0.10"),Decimal("0.05")))

def bars()->tuple[CanonicalCandle,...]:
    return tuple(candle(i,str(100+i*3)) for i in range(30))

class TestMTF(unittest.TestCase):
    def test_exact_close_boundary_is_visible(self):
        p=candle(3,"109")
        h=candle(0,"100","1h")
        h2=CanonicalCandle("BTCUSDT","1h",T0+timedelta(minutes=60),T0+timedelta(minutes=120),Decimal("101"),Decimal("101"),Decimal("101"),Decimal("101"),Decimal("1"),provenance_id="h2")
        self.assertEqual(align_higher_timeframe(p,(h,h2)).candle,h)
        p2=CanonicalCandle("BTCUSDT","15m",T0+timedelta(minutes=8*15),T0+timedelta(minutes=9*15),Decimal("110"),Decimal("110"),Decimal("110"),Decimal("110"),Decimal("1"),provenance_id="p8")
        a=align_higher_timeframe(p2,(h,h2))
        self.assertEqual(a.candle,h2)
        self.assertEqual(a.available_at,h2.close_time)
        self.assertLessEqual(a.candle.close_time,a.primary_close)

    def test_future_htf_never_selected(self):
        p=candle(5,"115")
        future=CanonicalCandle("BTCUSDT","1h",T0+timedelta(minutes=60),T0+timedelta(minutes=120),Decimal("1"),Decimal("1"),Decimal("1"),Decimal("1"),Decimal("1"),provenance_id="future")
        self.assertIsNone(align_higher_timeframe(p,(future,)).candle)

    def test_incomplete_and_wrong_order_rejected(self):
        with self.assertRaises(ValueError): align_higher_timeframe(candle(1,"101"),(candle(0,"100","1h",closed=False),))
        h0=candle(0,"100","1h"); h1=candle(0,"101","1h")
        with self.assertRaises(ValueError): align_higher_timeframe(candle(3,"109"),(h0,h1))

class TestOrchestrator(unittest.TestCase):
    def test_deterministic_composition_and_replay(self):
        xs=bars()
        htf=(CanonicalCandle("BTCUSDT","1h",T0,T0+timedelta(hours=1),Decimal("100"),Decimal("100"),Decimal("100"),Decimal("100"),Decimal("1"),provenance_id="h0"),
             CanonicalCandle("BTCUSDT","1h",T0+timedelta(hours=1),T0+timedelta(hours=2),Decimal("101"),Decimal("101"),Decimal("101"),Decimal("101"),Decimal("1"),provenance_id="h1"))
        a=QuantitativeOrchestrator().process(xs,config(),higher_timeframes={"1h":htf})
        b=QuantitativeOrchestrator().process(xs,config(),higher_timeframes={"1h":htf})
        self.assertEqual(a,b)
        self.assertEqual(a.regime.state,b.regime.state)
        self.assertEqual(a.indicators["EMA"].status,CalculationStatus.VALID)
        self.assertIn("1h",a.htf)
        self.assertIsNotNone(a.htf["1h"].candle)
        self.assertEqual(a.as_of,xs[-1].close_time)

    def test_incomplete_and_nonincreasing_inputs_are_rejected(self):
        xs=list(bars()); xs[-1]=candle(29,"187",closed=False)
        with self.assertRaises(ValueError): QuantitativeOrchestrator().process(xs,config())
        xs=list(bars()); xs[-1]=candle(28,"187")
        with self.assertRaises(ValueError): QuantitativeOrchestrator().process(xs,config())

    def test_empty_and_config_boundaries(self):
        with self.assertRaises(ValueError): QuantitativeOrchestrator().process((),config())
        with self.assertRaises(ValueError): QuantOrchestrationConfig(config().regime,ema_period=0)

class TestReplay(unittest.TestCase):
    def test_repeated_and_equivalent_replay_have_identical_fingerprint(self):
        xs=bars(); replay=QuantitativeReplay()
        a=replay.run(xs,config()); b=replay.run(tuple(xs),config())
        self.assertEqual(replay.fingerprint(a),replay.fingerprint(b))
        self.assertEqual(a,b)

class _FakePersistence:
    def __init__(self): self.results=[]
    async def persist_orchestration(self,result): self.results.append(result); return 3
    async def fetch_family(self,*args,**kwargs): return [{"record_id":"r1","value_numeric":Decimal("1.25")}]

class TestWorkerAPI(unittest.TestCase):
    def test_worker_rejects_incomplete_and_accepts_closed(self):
        p=_FakePersistence(); handler=QuantWorkerHandler(p,config())
        payload={"candles":[
            {"instrument_id":"BTCUSDT","timeframe":"15m","open_time":candle(0,"100").open_time.isoformat().replace("+00:00","Z"),"close_time":candle(0,"100").close_time.isoformat().replace("+00:00","Z"),"open":"100","high":"100","low":"100","close":"100","volume":"10","is_closed":True,"provenance_id":"p0"},
            {"instrument_id":"BTCUSDT","timeframe":"15m","open_time":candle(1,"103").open_time.isoformat().replace("+00:00","Z"),"close_time":candle(1,"103").close_time.isoformat().replace("+00:00","Z"),"open":"103","high":"103","low":"103","close":"103","volume":"10","is_closed":True,"provenance_id":"p1"},
            {"instrument_id":"BTCUSDT","timeframe":"15m","open_time":candle(2,"106").open_time.isoformat().replace("+00:00","Z"),"close_time":candle(2,"106").close_time.isoformat().replace("+00:00","Z"),"open":"106","high":"106","low":"106","close":"106","volume":"10","is_closed":True,"provenance_id":"p2"},
        ]}
        asyncio.run(handler(QueueEnvelope("m1","i1","CTR-P4-QUANT-CANDLE-CLOSE-1.0",payload)))
        self.assertEqual(len(p.results),1)
        payload["candles"][-1]["is_closed"]=False
        with self.assertRaises(ValueError): asyncio.run(handler(QueueEnvelope("m2","i2","CTR-P4-QUANT-CANDLE-CLOSE-1.0",payload)))

    def test_api_rejects_negative_limit(self):
        response=asyncio.run(QuantitativeAPI(_FakePersistence()).handle("GET","/v1/quantitative/regime/BTCUSDT/15m",{"limit":"-1"}))
        self.assertEqual(response.status,400)

    def test_api_rejects_unknown_family(self):
        response=asyncio.run(QuantitativeAPI(_FakePersistence()).handle("GET","/v1/quantitative/unknown/BTCUSDT/15m",{}))
        self.assertEqual(response.status,404)

    def test_api_is_read_only_and_deterministic(self):
        api=QuantitativeAPI(_FakePersistence())
        post=asyncio.run(api.handle("POST","/v1/quantitative/regime/BTCUSDT/15m",{}))
        self.assertEqual(post.status,405)
        get=asyncio.run(api.handle("GET","/v1/quantitative/regime/BTCUSDT/15m",{"limit":"1"}))
        self.assertEqual(get.status,200)
        self.assertEqual(get.body,'[{"record_id":"r1","value_numeric":"1.25"}]')
        bad=asyncio.run(api.handle("GET","/v1/quantitative/regime/BTCUSDT/15m",{"limit":"x"}))
        self.assertEqual(bad.status,400)

class _Tx:
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return False
class _DB:
    def __init__(self): self.sql=[]; self.seen=set()
    def transaction(self): return _Tx()
    async def execute(self,query,*args):
        self.sql.append((query,args))
        identity=args[-1]
        if identity in self.seen: return "INSERT 0 0"
        self.seen.add(identity)
        return "INSERT 0 1"
    async def fetch(self,*args): return []
    async def fetchrow(self,*args): return None

class TestPersistence(unittest.TestCase):
    def test_idempotent_identity_is_stable(self):
        db=_DB(); result=asyncio.run(QuantitativePersistence(db).persist_orchestration(QuantitativeOrchestrator().process(bars(),config())))
        again=asyncio.run(QuantitativePersistence(db).persist_orchestration(QuantitativeOrchestrator().process(bars(),config())))
        self.assertEqual(result,5); self.assertEqual(again,0)
        self.assertEqual(len(db.sql),6)
        identities=[args[-1] for _,args in db.sql]
        self.assertEqual(identities, [args[-1] for _,args in db.sql])
        self.assertTrue(all(isinstance(x,str) and len(x)==64 for x in identities))

if __name__=="__main__": unittest.main()
