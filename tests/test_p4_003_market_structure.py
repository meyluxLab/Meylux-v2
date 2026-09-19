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


    def test_gap_unconfirmed_persists_until_fresh_post_gap_structure(self):
        c=list(candles(gap_index=30))
        for i,(hi,lo) in {37:(Decimal("103"),Decimal("95")),42:(Decimal("105"),Decimal("100")),47:(Decimal("103"),Decimal("99")),52:(Decimal("112"),Decimal("100"))}.items():
            c[i]=CanonicalCandle("TEST","1h",c[i].open_time,c[i].close_time,Decimal("102"),hi,lo,Decimal("102"),Decimal("1"),provenance_id=f"gap-{i}")
        r=MarketStructureEngine().analyze(c)
        self.assertEqual(r.states[30].state,"UNCONFIRMED")
        self.assertEqual(r.states[31].state,"UNCONFIRMED")
        self.assertEqual(r.states[40].state,"UNCONFIRMED")
        self.assertEqual(r.states[45].state,"UNCONFIRMED")
        self.assertEqual(r.states[51].state,"UNCONFIRMED")
        self.assertEqual(r.states[57].state,"TRENDING_UP")

    def test_equal_high_and_low_remain_unconfirmed(self):
        n=27
        c=list(candles(n))
        for i,hi,lo in ((7,Decimal("110"),Decimal("101")),(12,Decimal("103"),Decimal("95")),(17,Decimal("110"),Decimal("101")),(22,Decimal("103"),Decimal("95"))):
            c[i]=CanonicalCandle("TEST","1h",c[i].open_time,c[i].close_time,Decimal("102"),hi,lo,Decimal("102"),Decimal("1"),provenance_id=f"eq-{i}")
        r=MarketStructureEngine().analyze(c)
        self.assertFalse(any(e.event_type in ("HH","LH","HL","LL") and e.level in (Decimal("110"),Decimal("95")) for e in r.events))
        self.assertEqual(r.states[26].state,"UNCONFIRMED")

    def test_fvg_lifecycle_is_monotonic_and_terminal(self):
        c=list(candles(7))
        vals=[
            (Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99")),
            (Decimal("101"),Decimal("102"),Decimal("101"),Decimal("102")),
            (Decimal("103"),Decimal("104"),Decimal("103"),Decimal("103")),
            (Decimal("103"),Decimal("104"),Decimal("102"),Decimal("103")),
            (Decimal("103"),Decimal("104"),Decimal("99"),Decimal("100")),
            (Decimal("100"),Decimal("101"),Decimal("98"),Decimal("100")),
            (Decimal("100"),Decimal("101"),Decimal("98"),Decimal("100")),
        ]
        for i,(op,hi,lo,cl) in enumerate(vals):
            c[i]=CanonicalCandle("TEST","1h",c[i].open_time,c[i].close_time,op,hi,lo,cl,Decimal("1"),provenance_id=f"life-{i}")
        r=MarketStructureEngine().analyze(c)
        fvg=next(e for e in r.events if e.event_type=="FVG" and e.event_location==c[2].open_time)
        life=[e.lifecycle for e in r.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==fvg.identity]
        self.assertEqual(life,["PARTIALLY_MITIGATED","FULLY_MITIGATED"])
        self.assertEqual(len([e for e in r.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==fvg.identity and e.lifecycle=="PARTIALLY_MITIGATED"]),1)
        self.assertEqual(len([e for e in r.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==fvg.identity and e.lifecycle=="FULLY_MITIGATED"]),1)

    def test_liquidity_identity_contains_ordered_member_identities(self):
        n=30; cc=[Decimal("100")]*n; hh=[Decimal("101")]*n; ll=[Decimal("99")]*n; oo=[Decimal("100")]*n
        for i in (7,17):
            oo[i]=cc[i]=Decimal("109"); hh[i]=Decimal("110"); ll[i]=Decimal("108")
        r=MarketStructureEngine().analyze(candles(n=n,closes=cc,highs=hh,lows=ll,opens=oo))
        swings=[e for e in r.events if e.event_type=="SWING_HIGH" and e.level==Decimal("110")]
        pool=[e for e in r.events if e.event_type=="LIQUIDITY_POOL" and e.level==Decimal("110")]
        self.assertEqual(len(swings),2); self.assertEqual(len(pool),1)
        self.assertEqual(pool[0].source_event_identity,swings[0].identity+","+swings[1].identity)
        replay=MarketStructureEngine().analyze(candles(n=n,closes=cc,highs=hh,lows=ll,opens=oo))
        self.assertEqual(pool[0].identity,[e for e in replay.events if e.event_type=="LIQUIDITY_POOL"][0].identity)

    def test_structural_invalidation_is_append_only(self):
        r=MarketStructureEngine().analyze(trend())
        bos=[e for e in r.events if e.event_type=="BOS"]
        inv=[e for e in r.events if e.event_type=="STRUCTURAL_INVALIDATION" and e.source_event_identity in {x.identity for x in bos}]
        self.assertEqual(len(bos),1)
        self.assertTrue(inv)
        self.assertIn(bos[0].identity,{e.source_event_identity for e in inv})
        self.assertIn(bos[0],r.events)

    def test_per_bar_processing_order_is_explicit_and_deterministic(self):
        r=MarketStructureEngine().analyze(trend())
        expected=("continuity","swing","classification","state","structural_breaks","ob_breaker","fvg","liquidity","official_post_bar_state")
        self.assertTrue(all(st.processing_order==expected for st in r.states))
        self.assertEqual(r.states[39].processing_order,expected)
        self.assertEqual(r.states[39].state,"TRENDING_UP")



    def test_exact_5_5_confirmation_boundary_and_insufficient_history(self):
        n=16; c=list(candles(n))
        c[5]=CanonicalCandle("TEST","1h",c[5].open_time,c[5].close_time,Decimal("102"),Decimal("110"),Decimal("101"),Decimal("102"),Decimal("1"),provenance_id="boundary-high")
        r=MarketStructureEngine().analyze(c)
        self.assertFalse(any(e.event_type=="SWING_HIGH" and e.event_location==c[5].open_time for e in r.states[0].events))
        self.assertFalse(any(e.event_type=="SWING_HIGH" and e.event_location==c[5].open_time for st in r.states[:10] for e in st.events))
        self.assertTrue(any(e.event_type=="SWING_HIGH" and e.event_location==c[5].open_time for e in r.states[10].events))
        self.assertEqual(next(e for e in r.states[10].events if e.event_type=="SWING_HIGH").knowledge_time,c[10].close_time)

    def test_bearish_bos_and_close_only_equality_and_wick_rejection(self):
        n=60; c=[Decimal("102")]*n; h=[Decimal("103")]*n; l=[Decimal("101")]*n; o=[Decimal("102")]*n
        piv={7:(104,105,103),12:(96,97,95),17:(99,100,98),22:(89,90,88),27:(92,93,91),32:(83,84,82)}
        for i,(op,hi,lo) in piv.items(): o[i]=c[i]=Decimal(op); h[i]=Decimal(hi); l[i]=Decimal(lo)
        for i in list(range(23,27))+list(range(28,32)): o[i]=c[i]=Decimal("91"); h[i]=Decimal("92"); l[i]=Decimal("90")
        for i in range(33,38): o[i]=c[i]=Decimal("90"); h[i]=Decimal("91"); l[i]=Decimal("89")
        o[38]=Decimal("83"); c[38]=Decimal("82"); h[38]=Decimal("84"); l[38]=Decimal("81")
        o[39]=c[39]=Decimal("80"); h[39]=Decimal("83"); l[39]=Decimal("79")
        bars=candles(n=n,closes=c,highs=h,lows=l,opens=o)
        r=MarketStructureEngine().analyze(bars)
        bos=[e for e in r.events if e.event_type=="BOS" and e.direction=="bearish"]
        self.assertEqual(len(bos),1); self.assertEqual(bos[0].level,Decimal("82")); self.assertEqual(bos[0].knowledge_time,bars[39].close_time)
        self.assertFalse(any(e.event_type=="BOS" and e.direction=="bearish" for e in r.states[38].events))
        self.assertFalse(any(e.event_type=="BOS" and e.level==Decimal("82") for e in MarketStructureEngine().analyze(candles(n=40,closes=c[:40],highs=h[:40],lows=l[:40],opens=o[:40])).events if e.event_location==bars[38].open_time))
        equality=list(bars); x=equality[39]
        equality[39]=CanonicalCandle("TEST","1h",x.open_time,x.close_time,Decimal("82"),Decimal("83"),Decimal("79"),Decimal("82"),Decimal("1"),provenance_id="bear-eq")
        eq=MarketStructureEngine().analyze(tuple(equality))
        self.assertFalse(any(e.event_type=="BOS" and e.level==Decimal("82") for e in eq.events))

    def test_bullish_choch_unconfirmed_then_mss_mirror(self):
        n=60; c=[Decimal("102")]*n; h=[Decimal("103")]*n; l=[Decimal("101")]*n; o=[Decimal("102")]*n
        piv={7:(104,105,103),12:(96,97,95),17:(99,100,98),22:(89,90,88),27:(92,93,91),32:(83,84,82)}
        for i,(op,hi,lo) in piv.items(): o[i]=c[i]=Decimal(op); h[i]=Decimal(hi); l[i]=Decimal(lo)
        for i in list(range(23,27))+list(range(28,32)): o[i]=c[i]=Decimal("91"); h[i]=Decimal("92"); l[i]=Decimal("90")
        for i in range(33,40): o[i]=c[i]=Decimal("90"); h[i]=Decimal("91"); l[i]=Decimal("89")
        o[40]=c[40]=Decimal("94"); h[40]=Decimal("96"); l[40]=Decimal("93")
        o[41]=c[41]=Decimal("95"); h[41]=Decimal("97"); l[41]=Decimal("94")
        o[42]=c[42]=Decimal("96"); h[42]=Decimal("98"); l[42]=Decimal("95")
        o[43]=c[43]=Decimal("94"); h[43]=Decimal("95"); l[43]=Decimal("92")
        o[44]=c[44]=Decimal("93"); h[44]=Decimal("94"); l[44]=Decimal("91")
        o[45]=c[45]=Decimal("90"); h[45]=Decimal("92"); l[45]=Decimal("89")
        for i in (46,47,48,49): o[i]=c[i]=Decimal("91"); h[i]=Decimal("92"); l[i]=Decimal("90")
        o[50]=c[50]=Decimal("91"); h[50]=Decimal("93"); l[50]=Decimal("90")
        o[51]=c[51]=Decimal("100"); h[51]=Decimal("101"); l[51]=Decimal("99")
        bars=candles(closes=c,highs=h,lows=l,opens=o)
        r=MarketStructureEngine().analyze(bars)
        choch=[e for e in r.events if e.event_type=="CHOCH" and e.direction=="bullish"]
        mss=[e for e in r.events if e.event_type=="MSS" and e.direction=="bullish"]
        self.assertEqual([(e.level,e.event_location) for e in choch],[(Decimal("93"),bars[40].open_time)])
        self.assertEqual([(e.level,e.event_location) for e in mss],[(Decimal("98"),bars[51].open_time)])
        self.assertEqual(r.states[40].state,"UNCONFIRMED"); self.assertEqual(r.states[50].state,"UNCONFIRMED"); self.assertEqual(r.states[51].state,"TRENDING_UP")

    def test_wick_only_bos_rejected_in_both_directions(self):
        up=list(trend())
        up[39]=CanonicalCandle("TEST","1h",up[39].open_time,up[39].close_time,Decimal("117"),Decimal("121"),Decimal("116"),Decimal("117"),Decimal("1"),provenance_id="bull-wick")
        ur=MarketStructureEngine().analyze(tuple(up))
        self.assertFalse(any(e.event_type=="BOS" and e.direction=="bullish" for e in ur.events))
        down=list(self._bearish_trend_bars())
        down[39]=CanonicalCandle("TEST","1h",down[39].open_time,down[39].close_time,Decimal("83"),Decimal("84"),Decimal("79"),Decimal("83"),Decimal("1"),provenance_id="bear-wick")
        dr=MarketStructureEngine().analyze(tuple(down))
        self.assertFalse(any(e.event_type=="BOS" and e.direction=="bearish" for e in dr.events))

    @staticmethod
    def _bearish_trend_bars():
        n=60; c=[Decimal("102")]*n; h=[Decimal("103")]*n; l=[Decimal("101")]*n; o=[Decimal("102")]*n
        piv={7:(104,105,103),12:(96,97,95),17:(99,100,98),22:(89,90,88),27:(92,93,91),32:(83,84,82)}
        for i,(op,hi,lo) in piv.items(): o[i]=c[i]=Decimal(op); h[i]=Decimal(hi); l[i]=Decimal(lo)
        for i in list(range(23,27))+list(range(28,32)): o[i]=c[i]=Decimal("91"); h[i]=Decimal("92"); l[i]=Decimal("90")
        for i in range(33,38): o[i]=c[i]=Decimal("90"); h[i]=Decimal("91"); l[i]=Decimal("89")
        o[38]=Decimal("83"); c[38]=Decimal("83"); h[38]=Decimal("84"); l[38]=Decimal("82")
        o[39]=c[39]=Decimal("80"); h[39]=Decimal("83"); l[39]=Decimal("79")
        return candles(n=n,closes=c,highs=h,lows=l,opens=o)

    def test_ob_and_breaker_wick_only_invalidation_both_directions(self):
        def exercise(bars, ob_direction):
            r=MarketStructureEngine().analyze(bars)
            obs=[e for e in r.events if e.event_type=="ORDER_BLOCK" and e.direction==ob_direction]
            self.assertTrue(obs)
            ob=obs[-1]
            self.assertFalse(any(e.event_type=="ORDER_BLOCK_INVALIDATION" and e.source_event_identity==ob.identity for e in r.events if e.event_location==bars[40].open_time))
        up=list(trend())
        up[38]=CanonicalCandle("TEST","1h",up[38].open_time,up[38].close_time,Decimal("118"),Decimal("118"),Decimal("116"),Decimal("117"),Decimal("1"),provenance_id="bull-ob")
        up[40]=CanonicalCandle("TEST","1h",up[40].open_time,up[40].close_time,Decimal("117"),Decimal("119"),Decimal("115"),Decimal("117"),Decimal("1"),provenance_id="bull-ob-wick")
        ur=MarketStructureEngine().analyze(tuple(up))
        uobs=[e for e in ur.events if e.event_type=="ORDER_BLOCK" and e.direction=="bullish"]
        self.assertTrue(uobs); uob=uobs[-1]
        self.assertFalse(any(e.event_type=="ORDER_BLOCK_INVALIDATION" and e.source_event_identity==uob.identity and e.event_location==up[40].open_time for e in ur.events))
        down=list(self._bearish_trend_bars())
        down[38]=CanonicalCandle("TEST","1h",down[38].open_time,down[38].close_time,Decimal("82"),Decimal("84"),Decimal("81"),Decimal("83"),Decimal("1"),provenance_id="bear-ob")
        down[40]=CanonicalCandle("TEST","1h",down[40].open_time,down[40].close_time,Decimal("83"),Decimal("85"),Decimal("81"),Decimal("83"),Decimal("1"),provenance_id="bear-ob-wick")
        dr=MarketStructureEngine().analyze(tuple(down))
        dobs=[e for e in dr.events if e.event_type=="ORDER_BLOCK" and e.direction=="bearish"]
        self.assertTrue(dobs); dob=dobs[-1]
        self.assertFalse(any(e.event_type=="ORDER_BLOCK_INVALIDATION" and e.source_event_identity==dob.identity and e.event_location==down[40].open_time for e in dr.events))


    def test_breaker_wick_only_invalidation_does_not_transition(self):
        up=list(trend())
        up[38]=CanonicalCandle("TEST","1h",up[38].open_time,up[38].close_time,Decimal("118"),Decimal("118"),Decimal("116"),Decimal("117"),Decimal("1"),provenance_id="br-up-ob")
        up[40]=CanonicalCandle("TEST","1h",up[40].open_time,up[40].close_time,Decimal("115"),Decimal("117"),Decimal("114"),Decimal("115"),Decimal("1"),provenance_id="br-up-inv")
        up[41]=CanonicalCandle("TEST","1h",up[41].open_time,up[41].close_time,Decimal("117"),Decimal("120"),Decimal("116"),Decimal("117"),Decimal("1"),provenance_id="br-up-wick")
        up[42]=CanonicalCandle("TEST","1h",up[42].open_time,up[42].close_time,Decimal("119"),Decimal("120"),Decimal("118"),Decimal("119"),Decimal("1"),provenance_id="br-up-close")
        ur=MarketStructureEngine().analyze(tuple(up))
        uob=next(e for e in ur.events if e.event_type=="ORDER_BLOCK" and e.direction=="bullish")
        ubr=next(e for e in ur.events if e.event_type=="BREAKER" and e.source_event_identity==uob.identity)
        self.assertFalse(any(e.event_type=="BREAKER_INVALIDATION" and e.source_event_identity==ubr.identity and e.event_location==up[41].open_time for e in ur.events))
        self.assertTrue(any(e.event_type=="BREAKER_INVALIDATION" and e.source_event_identity==ubr.identity and e.event_location==up[42].open_time for e in ur.events))

        down=list(self._bearish_trend_bars())
        down[38]=CanonicalCandle("TEST","1h",down[38].open_time,down[38].close_time,Decimal("82"),Decimal("84"),Decimal("81"),Decimal("83"),Decimal("1"),provenance_id="br-down-ob")
        down[40]=CanonicalCandle("TEST","1h",down[40].open_time,down[40].close_time,Decimal("85"),Decimal("86"),Decimal("83"),Decimal("85"),Decimal("1"),provenance_id="br-down-inv")
        down[41]=CanonicalCandle("TEST","1h",down[41].open_time,down[41].close_time,Decimal("82"),Decimal("83"),Decimal("79"),Decimal("82"),Decimal("1"),provenance_id="br-down-wick")
        down[42]=CanonicalCandle("TEST","1h",down[42].open_time,down[42].close_time,Decimal("80"),Decimal("81"),Decimal("78"),Decimal("80"),Decimal("1"),provenance_id="br-down-close")
        dr=MarketStructureEngine().analyze(tuple(down))
        dob=next(e for e in dr.events if e.event_type=="ORDER_BLOCK" and e.direction=="bearish")
        dbr=next(e for e in dr.events if e.event_type=="BREAKER" and e.source_event_identity==dob.identity)
        self.assertFalse(any(e.event_type=="BREAKER_INVALIDATION" and e.source_event_identity==dbr.identity and e.event_location==down[41].open_time for e in dr.events))
        self.assertTrue(any(e.event_type=="BREAKER_INVALIDATION" and e.source_event_identity==dbr.identity and e.event_location==down[42].open_time for e in dr.events))

    def test_fvg_bullish_bearish_equality_and_direct_full_traversal(self):
        def make(vals):
            base=candles(len(vals))
            return tuple(CanonicalCandle("TEST","1h",base[i].open_time,base[i].close_time,*vals[i],Decimal("1"),provenance_id=f"fvg-{i}") for i in range(len(vals)))
        bullish=make([
            (Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99")),
            (Decimal("101"),Decimal("102"),Decimal("101"),Decimal("102")),
            (Decimal("103"),Decimal("104"),Decimal("103"),Decimal("103")),
            (Decimal("103"),Decimal("104"),Decimal("102"),Decimal("103")),
            (Decimal("103"),Decimal("104"),Decimal("99"),Decimal("100")),
        ])
        br=MarketStructureEngine().analyze(bullish)
        f=next(e for e in br.events if e.event_type=="FVG" and e.event_location==bullish[2].open_time)
        life=[e.lifecycle for e in br.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==f.identity]
        self.assertEqual(life,["PARTIALLY_MITIGATED","FULLY_MITIGATED"])
        direct=list(bullish); direct[3]=CanonicalCandle("TEST","1h",direct[3].open_time,direct[3].close_time,Decimal("103"),Decimal("104"),Decimal("99"),Decimal("100"),Decimal("1"),provenance_id="direct-full")
        dr=MarketStructureEngine().analyze(tuple(direct))
        df=next(e for e in dr.events if e.event_type=="FVG" and e.event_location==direct[2].open_time)
        dlife=[e.lifecycle for e in dr.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==df.identity]
        self.assertEqual(dlife,["FULLY_MITIGATED"])
        self.assertEqual(len([e for e in dr.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==df.identity]),1)
        bearish=make([
            (Decimal("103"),Decimal("105"),Decimal("103"),Decimal("104")),
            (Decimal("101"),Decimal("102"),Decimal("101"),Decimal("101")),
            (Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99")),
            (Decimal("102"),Decimal("104"),Decimal("100"),Decimal("102")),
        ])
        rr=MarketStructureEngine().analyze(bearish)
        bf=next(e for e in rr.events if e.event_type=="FVG" and e.event_location==bearish[2].open_time)
        self.assertEqual([e.lifecycle for e in rr.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==bf.identity],["FULLY_MITIGATED"])
        equal=make([
            (Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99")),
            (Decimal("101"),Decimal("102"),Decimal("101"),Decimal("102")),
            (Decimal("103"),Decimal("103"),Decimal("100"),Decimal("102")),
        ])
        self.assertFalse(any(e.event_type=="FVG" for e in MarketStructureEngine().analyze(equal).events))

    def test_fvg_terminal_no_revival_is_identity_specific(self):
        c=list(candles(7))
        vals=[
            (Decimal("99"),Decimal("100"),Decimal("98"),Decimal("99")),
            (Decimal("101"),Decimal("102"),Decimal("101"),Decimal("102")),
            (Decimal("103"),Decimal("104"),Decimal("103"),Decimal("103")),
            (Decimal("103"),Decimal("104"),Decimal("99"),Decimal("100")),
            (Decimal("100"),Decimal("101"),Decimal("98"),Decimal("100")),
            (Decimal("100"),Decimal("101"),Decimal("98"),Decimal("100")),
            (Decimal("100"),Decimal("101"),Decimal("98"),Decimal("100")),
        ]
        for i,v in enumerate(vals):
            c[i]=CanonicalCandle("TEST","1h",c[i].open_time,c[i].close_time,*v,Decimal("1"),provenance_id=f"term-{i}")
        r=MarketStructureEngine().analyze(c)
        f=next(e for e in r.events if e.event_type=="FVG" and e.event_location==c[2].open_time)
        self.assertEqual([e.lifecycle for e in r.events if e.event_type=="FVG_LIFECYCLE" and e.source_event_identity==f.identity],["FULLY_MITIGATED"])
        self.assertFalse(any(e.source_event_identity==f.identity and e.lifecycle=="PARTIALLY_MITIGATED" for e in r.events if e.event_type=="FVG_LIFECYCLE"))

    def test_liquidity_pool_sweep_both_directions_and_exact_equality(self):
        n=30; cc=[Decimal("100")]*n; hh=[Decimal("101")]*n; ll=[Decimal("99")]*n; oo=[Decimal("100")]*n
        for i in (7,17):
            oo[i]=cc[i]=Decimal("109"); hh[i]=Decimal("110"); ll[i]=Decimal("108")
        cc[23]=Decimal("111"); oo[23]=Decimal("111"); hh[23]=Decimal("112"); ll[23]=Decimal("110")
        r=MarketStructureEngine().analyze(candles(n=n,closes=cc,highs=hh,lows=ll,opens=oo))
        pool=next(e for e in r.events if e.event_type=="LIQUIDITY_POOL")
        sweep=next(e for e in r.events if e.event_type=="LIQUIDITY_POOL_SWEEP")
        self.assertEqual(sweep.source_event_identity,pool.identity); self.assertEqual(sweep.level,Decimal("110"))
        cc2=[Decimal("100")]*n; hh2=[Decimal("101")]*n; ll2=[Decimal("99")]*n; oo2=[Decimal("100")]*n
        for i in (7,17):
            oo2[i]=cc2[i]=Decimal("91"); hh2[i]=Decimal("92"); ll2[i]=Decimal("90")
        cc2[23]=Decimal("89"); oo2[23]=Decimal("89"); hh2[23]=Decimal("90"); ll2[23]=Decimal("88")
        r2=MarketStructureEngine().analyze(candles(n=n,closes=cc2,highs=hh2,lows=ll2,opens=oo2))
        pool2=next(e for e in r2.events if e.event_type=="LIQUIDITY_POOL")
        sweep2=next(e for e in r2.events if e.event_type=="LIQUIDITY_POOL_SWEEP")
        self.assertEqual(sweep2.source_event_identity,pool2.identity); self.assertEqual(sweep2.level,Decimal("90"))
        ll2[17]=Decimal("89.999999999999999999999999999999999999")
        self.assertFalse(any(e.event_type=="LIQUIDITY_POOL" for e in MarketStructureEngine().analyze(candles(n=n,closes=cc2,highs=hh2,lows=ll2,opens=oo2)).events))

    def test_large_small_decimal_and_malformed_contradictory_inputs(self):
        huge=Decimal("9.0E+60"); tiny=Decimal("1E-60")
        c=list(candles(16))
        for i in range(len(c)):
            c[i]=CanonicalCandle("TEST","1h",c[i].open_time,c[i].close_time,huge,Decimal("9.1E+60"),Decimal("8.9E+60"),huge,Decimal("0"),provenance_id=f"num-{i}")
        c[5]=CanonicalCandle("TEST","1h",c[5].open_time,c[5].close_time,huge,Decimal("9.9E+60"),Decimal("8.9E+60"),huge,Decimal("0"),provenance_id="num-swing")
        r=MarketStructureEngine().analyze(tuple(c))
        self.assertTrue(any(e.event_type=="SWING_HIGH" and e.level==Decimal("9.9E+60") for e in r.events))
        small=list(candles(16))
        for i in range(len(small)):
            small[i]=CanonicalCandle("TEST","1h",small[i].open_time,small[i].close_time,tiny,Decimal("1.1E-60"),Decimal("0.9E-60"),tiny,Decimal("0"),provenance_id=f"small-{i}")
        small[5]=CanonicalCandle("TEST","1h",small[5].open_time,small[5].close_time,tiny,Decimal("1.9E-60"),Decimal("0.9E-60"),tiny,Decimal("0"),provenance_id="small-swing")
        sr=MarketStructureEngine().analyze(tuple(small))
        self.assertTrue(any(e.event_type=="SWING_HIGH" for e in sr.events))
        with self.assertRaises(ValueError): CanonicalCandle("TEST","1h",c[0].open_time,c[0].close_time,Decimal("10"),Decimal("9"),Decimal("8"),Decimal("9"),Decimal("1"),provenance_id="bad-high")
        with self.assertRaises(ValueError): CanonicalCandle("TEST","1h",c[0].open_time,c[0].close_time,Decimal("10"),Decimal("12"),Decimal("11"),Decimal("10"),Decimal("1"),provenance_id="bad-low")
        with self.assertRaises(ValueError): MarketStructureEngine().analyze((c[0], CanonicalCandle("OTHER","1h",c[1].open_time,c[1].close_time,huge,huge,huge,huge,Decimal("0"),provenance_id="contradictory-instrument")))

    def test_DIAGNOSTIC_dump_golden_traces(self):
        def trace(result, bars):
            base=bars[0].open_time
            out=[]
            for st in result.states:
                evs=[]
                for e in st.events:
                    loc=int((e.event_location-base).total_seconds()/3600)
                    evs.append(f"{e.event_type}@{loc}:{e.level}:{e.direction}:{e.lifecycle}:{e.structural_state}:{e.source_event_identity}")
                out.append((st.index,st.state,tuple(evs)))
            return tuple(out)

        trend_bars=trend()
        trend_result=MarketStructureEngine().analyze(trend_bars)

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
        reversal_bars=candles(closes=c,highs=h,lows=l,opens=o)
        reversal_result=MarketStructureEngine().analyze(reversal_bars)
        raise AssertionError("TREND_TRACE="+repr(trace(trend_result,trend_bars))+"\\nREVERSAL_TRACE="+repr(trace(reversal_result,reversal_bars)))

if __name__=="__main__": unittest.main()
