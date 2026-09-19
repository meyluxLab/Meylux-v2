import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from contracts.canonical import CanonicalCandle
from contracts.quantitative import CalculationResult, CalculationStatus, MarketStructureResult
from meylux.quantitative.market_structure import MarketStructureEngine, SEMANTIC_VERSION

def candles(n=60, closes=None, highs=None, lows=None, opens=None, gap_index=None):
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    closes=list(closes or [Decimal("102")]*n); highs=list(highs or [Decimal("103")]*n); lows=list(lows or [Decimal("101")]*n); opens=list(opens or closes)
    out=[]
    for i in range(n):
        shift=1 if gap_index is not None and i>=gap_index else 0; ot=start+timedelta(hours=i+shift)
        out.append(CanonicalCandle("TEST","1h",ot,ot+timedelta(hours=1),opens[i],highs[i],lows[i],closes[i],Decimal("1"),provenance_id=f"c-{i}"))
    return tuple(out)

def trend():
    n=60; c=[Decimal("102")]*n; h=[Decimal("103")]*n; l=[Decimal("101")]*n; o=[Decimal("102")]*n
    piv={7:(Decimal("96"),Decimal("97"),Decimal("95")),12:(Decimal("104"),Decimal("105"),Decimal("103")),17:(Decimal("101"),Decimal("102"),Decimal("100")),22:(Decimal("111"),Decimal("112"),Decimal("110")),27:(Decimal("108"),Decimal("109"),Decimal("107")),32:(Decimal("110"),Decimal("118"),Decimal("109"))}
    for i,(op,hi,lo) in piv.items(): o[i]=c[i]=op; h[i]=hi; l[i]=lo
    for i in list(range(23,27))+list(range(28,32)): o[i]=c[i]=Decimal("109"); h[i]=Decimal("110"); l[i]=Decimal("108")
    for i in range(33,37): o[i]=c[i]=Decimal("110"); h[i]=Decimal("110"); l[i]=Decimal("109")
    o[37]=c[37]=Decimal("110"); h[37]=Decimal("110"); l[37]=Decimal("109")
    o[38]=Decimal("118"); c[38]=Decimal("117"); h[38]=Decimal("118"); l[38]=Decimal("116")
    o[39]=c[39]=Decimal("121"); h[39]=Decimal("121"); l[39]=Decimal("120")
    return candles(closes=c,highs=h,lows=l,opens=o)

class ContractTests(unittest.TestCase):
    def test_legacy_constructor_and_extension(self):
        r=CalculationResult(Decimal("1"),CalculationStatus.VALID,"ok"); x=MarketStructureResult("BOS",r)
        self.assertEqual(x.calculation_version,"1.0.0"); self.assertIsNone(x.event_location)
        t=datetime(2026,1,1,tzinfo=timezone.utc); y=MarketStructureResult("BOS",r,SEMANTIC_VERSION,t,t,t,Decimal("1"),direction="bullish",identity="id")
        self.assertEqual(y.knowledge_time,t)
        with self.assertRaises(Exception): y.level=Decimal("2")
        with self.assertRaises(ValueError): MarketStructureResult("BOS",r,SEMANTIC_VERSION,t.replace(tzinfo=timezone(timedelta(hours=1))))

class ScenarioTests(unittest.TestCase):
    def test_pinned_trend_bos_zero_lookahead_and_replay(self):
        c=trend(); e=MarketStructureEngine(); a=e.analyze(c); b=e.analyze(c)
        bos=[x for x in a.events if x.event_type=="BOS"]
        self.assertEqual(len(bos),1); self.assertEqual(bos[0].level,Decimal("118")); self.assertEqual(bos[0].event_location,c[39].open_time); self.assertEqual(bos[0].knowledge_time,c[39].close_time)
        self.assertEqual(a.states[37].state,"TRENDING_UP"); self.assertFalse(any(x.event_type=="BOS" for i in range(33,39) for x in a.states[i].events)); self.assertEqual(a,b)

    def test_choch_unconfirmed_then_mss(self):
        n=60; c=[Decimal("102")]*n; h=[Decimal("103")]*n; l=[Decimal("101")]*n; o=[Decimal("102")]*n
        piv={7:(96,97,95),12:(104,105,103),17:(101,102,100),22:(111,112,110),27:(108,109,107),32:(110,118,109)}
        for i,(op,hi,lo) in piv.items(): o[i]=c[i]=Decimal(op); h[i]=Decimal(hi); l[i]=Decimal(lo)
        for i in list(range(23,27))+list(range(28,32)): o[i]=c[i]=Decimal("109"); h[i]=Decimal("110"); l[i]=Decimal("108")
        for i in range(33,40): o[i]=c[i]=Decimal("110"); h[i]=Decimal("111"); l[i]=Decimal("109")
        o[40]=c[40]=Decimal("106"); h[40]=Decimal("107"); l[40]=Decimal("105")
        o[41]=c[41]=Decimal("108"); h[41]=Decimal("109"); l[41]=Decimal("107")
        o[42]=c[42]=Decimal("104"); h[42]=Decimal("105"); l[42]=Decimal("103")
        for i in (43,44,46): o[i]=c[i]=Decimal("106"); h[i]=Decimal("107"); l[i]=Decimal("105")
        o[45]=c[45]=Decimal("108"); h[45]=Decimal("110"); l[45]=Decimal("107")
        for i in range(47,51): o[i]=c[i]=Decimal("106"); h[i]=Decimal("107"); l[i]=Decimal("105")
        o[51]=c[51]=Decimal("102"); h[51]=Decimal("103"); l[51]=Decimal("101")
        r=MarketStructureEngine().analyze(candles(closes=c,highs=h,lows=l,opens=o))
        self.assertEqual([(x.level,x.direction) for x in r.events if x.event_type=="CHOCH"],[(Decimal("107"),"bearish")])
        self.assertEqual([(x.level,x.direction) for x in r.events if x.event_type=="MSS"],[(Decimal("103"),"bearish")]); self.assertEqual(r.states[40].state,"UNCONFIRMED"); self.assertEqual(r.states[51].state,"TRENDING_DOWN")

    def test_fvg_lifecycle(self):
        c=list(candles(6))
        c[0]=CanonicalCandle("TEST","1h",c[0].open_time,c[0].close_time,Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99"),Decimal("1"),provenance_id="f0")
        c[1]=CanonicalCandle("TEST","1h",c[1].open_time,c[1].close_time,Decimal("101"),Decimal("103"),Decimal("101"),Decimal("102"),Decimal("1"),provenance_id="f1")
        c[2]=CanonicalCandle("TEST","1h",c[2].open_time,c[2].close_time,Decimal("102"),Decimal("104"),Decimal("102"),Decimal("103"),Decimal("1"),provenance_id="f2")
        c[3]=CanonicalCandle("TEST","1h",c[3].open_time,c[3].close_time,Decimal("103"),Decimal("104"),Decimal("101"),Decimal("103"),Decimal("1"),provenance_id="f3")
        c[4]=CanonicalCandle("TEST","1h",c[4].open_time,c[4].close_time,Decimal("103"),Decimal("104"),Decimal("100"),Decimal("102"),Decimal("1"),provenance_id="f4")
        life=[x.lifecycle for x in MarketStructureEngine().analyze(c).events if x.event_type=="FVG_LIFECYCLE"]
        self.assertIn("PARTIALLY_MITIGATED",life); self.assertIn("FULLY_MITIGATED",life)

    def test_order_block_breaker_and_liquidity(self):
        c=list(trend())
        c[38]=CanonicalCandle("TEST","1h",c[38].open_time,c[38].close_time,Decimal("118"),Decimal("118"),Decimal("116"),Decimal("117"),Decimal("1"),provenance_id="ob")
        c[40]=CanonicalCandle("TEST","1h",c[40].open_time,c[40].close_time,Decimal("115"),Decimal("116"),Decimal("114"),Decimal("115"),Decimal("1"),provenance_id="inv")
        c[41]=CanonicalCandle("TEST","1h",c[41].open_time,c[41].close_time,Decimal("119"),Decimal("120"),Decimal("118"),Decimal("119"),Decimal("1"),provenance_id="br")
        r=MarketStructureEngine().analyze(c)
        self.assertEqual(len([x for x in r.events if x.event_type=="ORDER_BLOCK"]),1); self.assertEqual(len([x for x in r.events if x.event_type=="ORDER_BLOCK_INVALIDATION"]),1); self.assertEqual(len([x for x in r.events if x.event_type=="BREAKER"]),1); self.assertEqual(len([x for x in r.events if x.event_type=="BREAKER_INVALIDATION"]),1)
        n=30; cc=[Decimal("100")]*n; hh=[Decimal("101")]*n; ll=[Decimal("99")]*n; oo=[Decimal("100")]*n
        hh[7]=hh[17]=Decimal("110"); cc[7]=cc[17]=Decimal("109"); oo[7]=oo[17]=Decimal("109"); ll[7]=ll[17]=Decimal("108")
        cc[23]=Decimal("111"); oo[23]=Decimal("111"); hh[23]=Decimal("112"); ll[23]=Decimal("110")
        r=MarketStructureEngine().analyze(candles(n=n,closes=cc,highs=hh,lows=ll,opens=oo))
        self.assertEqual(len([x for x in r.events if x.event_type=="LIQUIDITY_POOL"]),1); self.assertEqual(len([x for x in r.events if x.event_type=="LIQUIDITY_POOL_SWEEP"]),1)

    def test_gap_invalid_input_and_prefix_stability(self):
        c=candles(gap_index=30); r=MarketStructureEngine().analyze(c); self.assertEqual(r.states[30].state,"UNCONFIRMED"); self.assertFalse(any(x.event_type in ("BOS","CHOCH","MSS") for x in r.states[30].events)); self.assertEqual(r,MarketStructureEngine().analyze(c))
        with self.assertRaises(TypeError): MarketStructureEngine().analyze([object()])
        bad=list(candles(3)); x=bad[1]; bad[1]=CanonicalCandle("TEST","1h",x.open_time,x.close_time,x.open,x.high,x.low,x.close,x.volume,is_closed=False,provenance_id="open")
        with self.assertRaises(ValueError): MarketStructureEngine().analyze(bad)
        p=MarketStructureEngine().analyze(trend()[:40]); f=MarketStructureEngine().analyze(trend()); self.assertEqual(tuple(x.identity for x in p.events),tuple(x.identity for x in f.events if x.knowledge_time<=trend()[39].close_time))

if __name__=="__main__": unittest.main()
