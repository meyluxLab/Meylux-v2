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

    @staticmethod
    def _golden_trace(result):
        base=result.bars[0].open_time
        out=[]
        for st in result.states:
            evs=[]
            for e in st.events:
                loc=int((e.event_location-base).total_seconds()/3600)
                conf=int((e.confirmation_time-base).total_seconds()/3600)
                know=int((e.knowledge_time-base).total_seconds()/3600)
                evs.append(f"{e.event_type}@{loc}/{conf}/{know}|{e.identity}|{e.level}|{e.direction}|{e.lifecycle}|{e.structural_state}|{e.source_event_identity}")
            out.append((st.index,st.state,tuple(evs)))
        return tuple(out)

    def test_complete_bullish_60_candle_golden_trace_and_replay(self):
        bars=trend()
        result=MarketStructureEngine().analyze(bars)
        expected=((0, 'UNCONFIRMED', ('STRUCTURE_STATE@0/1/1|081773847bebb250df3241bdd45cb30266e4141d673aeeeb71fae4cf4f381bd5|None|None|None|UNCONFIRMED|None',)), (1, 'NEUTRAL', ('STRUCTURE_STATE@1/2/2|f92932336b04179a00f54a98894fafa1cadb340c620d761b24008b85015331dd|None|None|None|NEUTRAL|None',)), (2, 'NEUTRAL', ('STRUCTURE_STATE@2/3/3|432a9fdd66d1d50c181e9ec0215584ccdca1dfcf7a537635e9ec01ccde46e795|None|None|None|NEUTRAL|None',)), (3, 'NEUTRAL', ('STRUCTURE_STATE@3/4/4|4783b375cb3ee34c0b97a4f37a95cea1ae11a4423b03ddd46c2c7bf13e3a4755|None|None|None|NEUTRAL|None',)), (4, 'NEUTRAL', ('STRUCTURE_STATE@4/5/5|3ca1dcc1ea333f1333a2749e66fdd5eb4a9e82ac69fb6a4ed078c2568ecd9062|None|None|None|NEUTRAL|None',)), (5, 'NEUTRAL', ('STRUCTURE_STATE@5/6/6|5b1176bfbc11a6df4b4921c8c03617c6d8dbdb8c90fb9829f1d4b1536472533d|None|None|None|NEUTRAL|None',)), (6, 'NEUTRAL', ('STRUCTURE_STATE@6/7/7|3a03b4bc42cc229d19f01876d3238413daa09169360ce5d85e3ee71c7f363f54|None|None|None|NEUTRAL|None',)), (7, 'NEUTRAL', ('FVG@7/8/8|c81aa63d9a71e95fe1b4b0bbaafcf5809562ad8d0d0a5a4f91c6974db3dda5f3|None|bearish|ACTIVE|None|None', 'STRUCTURE_STATE@7/8/8|ed81267a600fb424448bf3f41c365f9bb4c2d537a87ced30bc831c27cd54504d|None|None|None|NEUTRAL|None')), (8, 'NEUTRAL', ('FVG_LIFECYCLE@8/9/9|2208a66f64824bd39d364d5dbdbd555f7b1e9450526bc2171f6217fe7cd482b6|None|bearish|FULLY_MITIGATED|None|c81aa63d9a71e95fe1b4b0bbaafcf5809562ad8d0d0a5a4f91c6974db3dda5f3', 'STRUCTURE_STATE@8/9/9|b641043c9da30545a6cb5850ea6a42a2dafc43076dbf1dcea2ec30de7ba9bccd|None|None|None|NEUTRAL|None')), (9, 'NEUTRAL', ('FVG@9/10/10|bbee9b3100f8bbebf7abef2c81735d95116108c715ae2291cd7791cd962b7b7f|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@9/10/10|07ed9bbd0c86b987a9b05e1c4deddcf85dad07892eda3264091f3f2c4eef6439|None|None|None|NEUTRAL|None')), (10, 'NEUTRAL', ('FVG_LIFECYCLE@10/11/11|8cab237c5e49724177f2263566efe0b3116cd96249a9adb519f1381c3e583e7d|None|bullish|PARTIALLY_MITIGATED|None|bbee9b3100f8bbebf7abef2c81735d95116108c715ae2291cd7791cd962b7b7f', 'STRUCTURE_STATE@10/11/11|d9099e675252cb1ef8c814975c1371600dfc73a574e6f35913f5d55da2929757|None|None|None|NEUTRAL|None')), (11, 'NEUTRAL', ('STRUCTURE_STATE@11/12/12|ebedb3c3926b2bde58e2425e452fe955890790a518f9f706478862f3da4d50a2|None|None|None|NEUTRAL|None',)), (12, 'NEUTRAL', ('SWING_LOW@7/13/13|d4e9d1df9baeadd203e112ab015b784b4d674ea10e3b4142570bea7a0eaeebf5|95|None|None|None|None', 'STRUCTURE_STATE@12/13/13|d01d5e47e4adf86cf86ddeaaae877fa7ca906f20cb1766024dbdae1ea67b5f40|None|None|None|NEUTRAL|None')), (13, 'NEUTRAL', ('STRUCTURE_STATE@13/14/14|201f29e1b750df74456ed35184265baaf8d6fa60e149e7ef90856c73d19a58c6|None|None|None|NEUTRAL|None',)), (14, 'NEUTRAL', ('STRUCTURE_STATE@14/15/15|2c0648fdaee297da5bed2873915989f6db4c67077fcae3a1efd7c5ec20cd05a4|None|None|None|NEUTRAL|None',)), (15, 'NEUTRAL', ('STRUCTURE_STATE@15/16/16|b24ce5003fa0d256d358bf151732157dcf2ecc8a3722b884bdb388c19bea3a10|None|None|None|NEUTRAL|None',)), (16, 'NEUTRAL', ('STRUCTURE_STATE@16/17/17|f76de8ae0e92bbb26f1e401a7d88330aca573df1b88a0dc153db04caf4fb5ee3|None|None|None|NEUTRAL|None',)), (17, 'UNCONFIRMED', ('SWING_HIGH@12/18/18|9031986d25827bd54fbc512422af30dac1447c9a8db7b59eba4443102338ba74|105|None|None|None|None', 'STRUCTURE_STATE@17/18/18|60bd12359c1a09b418e2cccc4161d074c7546356386a89031ab60d3f06bf945b|None|None|None|UNCONFIRMED|None')), (18, 'UNCONFIRMED', ('STRUCTURE_STATE@18/19/19|87ea5e97b298f44d1e37e82efcf8b0745f28bdc6689695aea2547370efb6e6d5|None|None|None|UNCONFIRMED|None',)), (19, 'UNCONFIRMED', ('STRUCTURE_STATE@19/20/20|94b158ffa020e64b8542a4f9a6922526c7733d73fd91b3b64cab1bbab6eca9ac|None|None|None|UNCONFIRMED|None',)), (20, 'UNCONFIRMED', ('STRUCTURE_STATE@20/21/21|679d06d663e73cd08a84bed59b4d014184d8065274daef5782b8dc26c154f946|None|None|None|UNCONFIRMED|None',)), (21, 'UNCONFIRMED', ('STRUCTURE_STATE@21/22/22|23caacc3ad094623f691c9e42c9da49724fad7af57c50f88115f8a3289f13a54|None|None|None|UNCONFIRMED|None',)), (22, 'UNCONFIRMED', ('SWING_LOW@17/23/23|157c589aeaa15c8caff4c8bd25e782e2abc629e9d3230fe724eb9a6ad7ad5602|100|None|None|None|None', 'HL@17/23/23|6c50b56ba8513af7f6840a1d7ac2acb0f54cb46ba69e33f2ad0e49178acac555|100|None|None|None|None', 'FVG@22/23/23|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@22/23/23|b28ffc89d4b1396157a27cc39222b0c5eaf2a9c4cc9169eaa213cda7b86a80e9|None|None|None|UNCONFIRMED|None')), (23, 'UNCONFIRMED', ('FVG@23/24/24|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830|None|bullish|ACTIVE|None|None', 'FVG_LIFECYCLE@23/24/24|c7326eb7c892ceb5d0bdfc68b47b99ea8f95cb27f24f47d900c445df83300072|None|bullish|PARTIALLY_MITIGATED|None|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944', 'STRUCTURE_STATE@23/24/24|5ca31970ca89fb74ef44db81c02c5416031ec9b040f06b29b9a8b4a3a2551fe0|None|None|None|UNCONFIRMED|None')), (24, 'UNCONFIRMED', ('FVG_LIFECYCLE@24/25/25|14a070f97f71320f6ca980e914e56ed0325d2c1a4752a15792bbacdfa97a410e|None|bullish|PARTIALLY_MITIGATED|None|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830', 'STRUCTURE_STATE@24/25/25|b5a168b0e461c3d644dd3009379a29f3d962fb60d72a5901f89b6a7d8d5c95bb|None|None|None|UNCONFIRMED|None')), (25, 'UNCONFIRMED', ('STRUCTURE_STATE@25/26/26|3edb25d0606a95747ebf37f40476631114324f3eda21e581534c2d2e093e4357|None|None|None|UNCONFIRMED|None',)), (26, 'UNCONFIRMED', ('STRUCTURE_STATE@26/27/27|c49091bb3beff7da9bb6319f6006b63b29f3a35b526b56720f5dc2577c758b18|None|None|None|UNCONFIRMED|None',)), (27, 'TRENDING_UP', ('SWING_HIGH@22/28/28|e4ad99560506d1f4c6691ad1de26268db5553f51fb715f279e30d4ce99c6ef1d|112|None|None|None|None', 'HH@22/28/28|d92048e28c90fad7a22af45b2f91da362447a05f73deebddf4abe1313cd6b1a7|112|None|None|None|None', 'STRUCTURE_STATE@27/28/28|ad19cde4de0545cdb06373f3945993450f2cb440bb8c35ffc16ae915befbf276|None|None|None|TRENDING_UP|None')), (28, 'TRENDING_UP', ('STRUCTURE_STATE@28/29/29|4be46f8c1c9279bfa693760ea9c043a6a0db612e5b52b2c4a2c92d066a8b0563|None|None|None|TRENDING_UP|None',)), (29, 'TRENDING_UP', ('STRUCTURE_STATE@29/30/30|896945ddac6ed97e763840ce41c78260f5ba4453bdcfcfb9d2ad2e941e56e3b8|None|None|None|TRENDING_UP|None',)), (30, 'TRENDING_UP', ('STRUCTURE_STATE@30/31/31|c12daddcf0ef688476e6c936c39ab1e9114508061f194a5d6a5f99191eb3a531|None|None|None|TRENDING_UP|None',)), (31, 'TRENDING_UP', ('STRUCTURE_STATE@31/32/32|3822b96d89c7c547e5e9702a3b78823fe7664cf9135cd010e9e969e216dc70ea|None|None|None|TRENDING_UP|None',)), (32, 'TRENDING_UP', ('SWING_LOW@27/33/33|6da251cf79ddf58948f774b9f75b39a4420a0e2c38b01b55462bd8f75d017524|107|None|None|None|None', 'HL@27/33/33|69f6bd1c6b6fcf464b4d0e27895f1fc15c4c56f5a3f75f5697c66b410247913d|107|None|None|None|None', 'STRUCTURE_STATE@32/33/33|decd0d2d19324d1cd3d49f286b87875aaea9da7c0f997fdb3b12fd028452475d|None|None|None|TRENDING_UP|None')), (33, 'TRENDING_UP', ('STRUCTURE_STATE@33/34/34|f5c7ba3719bd35ff1a6e8423d5f94be97b911d397e6c6021891bc366f45fb57e|None|None|None|TRENDING_UP|None',)), (34, 'TRENDING_UP', ('STRUCTURE_STATE@34/35/35|c4ef56fd3798ee761101ac99f5ec79cbc4c082e18dce7d8b18893956f7a32ab0|None|None|None|TRENDING_UP|None',)), (35, 'TRENDING_UP', ('STRUCTURE_STATE@35/36/36|72c0c8316a1d0d13172a58921a79a3d9745ff7c38becc574b08920eaa7f84e75|None|None|None|TRENDING_UP|None',)), (36, 'TRENDING_UP', ('STRUCTURE_STATE@36/37/37|15ba3aba0df8daefe1237424a056741238e17c5acaa4c9d1c49860ccada1bb95|None|None|None|TRENDING_UP|None',)), (37, 'TRENDING_UP', ('SWING_HIGH@32/38/38|464fff0c5fa964cef21776f03e9958e5171de0bfd277802dbf1e0684c9054001|118|None|None|None|None', 'HH@32/38/38|13083fcfd2ea2649558e1d8b01601474a1d47c31fb1c2a126737058a4ef68edf|118|None|None|None|None', 'STRUCTURE_STATE@37/38/38|ab9adea7e7c6236fb972c4df41c3c09e503e71a17b46542408cbe8b3feed5f68|None|None|None|TRENDING_UP|None')), (38, 'TRENDING_UP', ('FVG@38/39/39|b446affb79b58612248ae0d9ff0b59762c8a464904baa6e7408ef85437a6788f|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@38/39/39|2cf578025d089db5cf03e4c56df0bd1c7a2fd49538aa4e76ed46581a9bfc6eac|None|None|None|TRENDING_UP|None')), (39, 'TRENDING_UP', ('BOS@39/40/40|bc6605198fa37179e2e16bd4ec467418773153baa2f4ad7526fac1fad8380554|118|bullish|None|None|None', 'ORDER_BLOCK@38/40/40|e6743c5c225259d5579a78f9a92913c5bf6cd23fe5aaaf86e22b619634e3e0ad|None|bullish|ACTIVE|None|bc6605198fa37179e2e16bd4ec467418773153baa2f4ad7526fac1fad8380554', 'FVG@39/40/40|617bc3a8a01f5624820f1e1dccd142779362e443c0578beb16f53ea2e31f15e1|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@39/40/40|4c193a5f7f581095c690c6e9a1e97570a2683b00b2ea47c588d2fa39658018fc|None|None|None|TRENDING_UP|None')), (40, 'UNCONFIRMED', ('CHOCH@40/41/41|0c3350264ed68b1694e031b9a2aa4a97855278dbac5f889373e214fb941f8dac|107|bearish|None|None|None', 'ORDER_BLOCK_INVALIDATION@40/41/41|f37566e709198a8dff1e3e9f5ea297b8006c009330a9710dc1dfca941aaf677d|None|bearish|INVALIDATED|None|e6743c5c225259d5579a78f9a92913c5bf6cd23fe5aaaf86e22b619634e3e0ad', 'BREAKER@40/41/41|b853d56c972dff33ecbc430ec92893e19f55f9ee62e243d2254b8f6ff1bbe915|None|bearish|ACTIVE|None|e6743c5c225259d5579a78f9a92913c5bf6cd23fe5aaaf86e22b619634e3e0ad', 'FVG@40/41/41|c760d43943908a256e74a352d8e8c85ae80df38964b3057f969ef093216d5aca|None|bearish|ACTIVE|None|None', 'FVG_LIFECYCLE@40/41/41|960d14084fab1c711b822a73672c9086f24f984fe6dde8506b1dca71d49d0418|None|bullish|FULLY_MITIGATED|None|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944', 'FVG_LIFECYCLE@40/41/41|97f944f5c5e4f76da333ea2ba856e031eff86b94a4b5301b0edd6d26eeb04a1a|None|bullish|FULLY_MITIGATED|None|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830', 'FVG_LIFECYCLE@40/41/41|487df88d74b333a4b3dd2ceb1362561fd56e3b12b6b5a061332006d949f04b54|None|bullish|FULLY_MITIGATED|None|b446affb79b58612248ae0d9ff0b59762c8a464904baa6e7408ef85437a6788f', 'FVG_LIFECYCLE@40/41/41|6478942526676a39f7be5958e71e0c0c39fb5462eb86c2321b4d5df6ccae344b|None|bullish|FULLY_MITIGATED|None|617bc3a8a01f5624820f1e1dccd142779362e443c0578beb16f53ea2e31f15e1', 'STRUCTURAL_INVALIDATION@40/41/41|d2937cb0de31188ceda7fc84e2c341d0a0d10f522b39d07bb2168506b3c1c198|118|bearish|INVALIDATED|None|bc6605198fa37179e2e16bd4ec467418773153baa2f4ad7526fac1fad8380554', 'STRUCTURE_STATE@40/41/41|d6d79fabb11cdef8d1c65106cb7870fc054566c8def31a91c24f07b730ef94b9|None|None|None|UNCONFIRMED|None')), (41, 'UNCONFIRMED', ('FVG@41/42/42|3d32cac5de7bd40cd6de49bfba57b38ece35066126b7546e2bce93a7c898b2fa|None|bearish|ACTIVE|None|None', 'FVG_LIFECYCLE@41/42/42|b5d899eb4778726c0112abfdad2cd3632b9f81b9d213ef620f8ea6ca39f452e1|None|bearish|PARTIALLY_MITIGATED|None|c760d43943908a256e74a352d8e8c85ae80df38964b3057f969ef093216d5aca', 'STRUCTURE_STATE@41/42/42|45fbd47ba47afe117dfe4aeeb1e32e6ba7237152d1084775095d7d45c8850420|None|None|None|UNCONFIRMED|None')), (42, 'UNCONFIRMED', ('FVG_LIFECYCLE@42/43/43|b18ce36b9847ed1b02e93c42e64c906456d955181a73a1ea6cef996015e27068|None|bearish|PARTIALLY_MITIGATED|None|3d32cac5de7bd40cd6de49bfba57b38ece35066126b7546e2bce93a7c898b2fa', 'STRUCTURE_STATE@42/43/43|d5c4bddcba41a7d542a6a9382f62b77c366823cf0aea71c2f7574635a8156906|None|None|None|UNCONFIRMED|None')), (43, 'UNCONFIRMED', ('STRUCTURE_STATE@43/44/44|91e08e74984df2d5d936a5c0195c385709cbd95cdbdad0eb391891d66da6f446|None|None|None|UNCONFIRMED|None',)), (44, 'UNCONFIRMED', ('SWING_HIGH@39/45/45|6f1124ea8e097c055ab832deeaf0fa6043da1803c98f509ca97f0e1f51874637|121|None|None|None|None', 'HH@39/45/45|40cec12cd579e5c09363988d1e814420cb11f87341f63d38fed6a11d6c7c16bc|121|None|None|None|None', 'STRUCTURE_STATE@44/45/45|5fa83380859d444e382d019c982a4d31f1d4335c7a9ea692ddb400269e2cf9d0|None|None|None|UNCONFIRMED|None')), (45, 'UNCONFIRMED', ('STRUCTURE_STATE@45/46/46|20e5cd12dc95997be6917107c97f04584fc0ca4cefac5371fac6d05d279d8aef|None|None|None|UNCONFIRMED|None',)), (46, 'UNCONFIRMED', ('STRUCTURE_STATE@46/47/47|bf9b660869d7b0e470c117a9ae7450e591c59f620ae644a69a7cee4e9e17164d|None|None|None|UNCONFIRMED|None',)), (47, 'UNCONFIRMED', ('STRUCTURE_STATE@47/48/48|09355f8dbadc29f24f7aaf509c651e8fc50b10718b1253db82c65cc7696e3a74|None|None|None|UNCONFIRMED|None',)), (48, 'UNCONFIRMED', ('STRUCTURE_STATE@48/49/49|53895598c0a2bbba96197666e22dfeedc189792373e0e00ab557a190b86bcd18|None|None|None|UNCONFIRMED|None',)), (49, 'UNCONFIRMED', ('STRUCTURE_STATE@49/50/50|a38e07e30b94f2171118e1e24a70011b07bfa7e3c1096144dba59bca8256730c|None|None|None|UNCONFIRMED|None',)), (50, 'UNCONFIRMED', ('STRUCTURE_STATE@50/51/51|b8446c4c6780b813a88d02139aaf46167fe29728e5a829cfb5ef2b3258d66ec7|None|None|None|UNCONFIRMED|None',)), (51, 'UNCONFIRMED', ('STRUCTURE_STATE@51/52/52|b4c694f3e196ca3e0d201765b0107efa92450bee13940f56076fbc645f06dd8e|None|None|None|UNCONFIRMED|None',)), (52, 'UNCONFIRMED', ('STRUCTURE_STATE@52/53/53|bbc0932ec4290c06e2acaf09dbb0a1bd4c071a0ebeac7b37de3b06d1016515e5|None|None|None|UNCONFIRMED|None',)), (53, 'UNCONFIRMED', ('STRUCTURE_STATE@53/54/54|aaacb37ac60b194f34bb7da7091e0cf4b53904b313c30655357d6fbca2131849|None|None|None|UNCONFIRMED|None',)), (54, 'UNCONFIRMED', ('STRUCTURE_STATE@54/55/55|4a006f2f806414671687951bd2baada0462b7aaeab6fc9b330b4438c77bf6071|None|None|None|UNCONFIRMED|None',)), (55, 'UNCONFIRMED', ('STRUCTURE_STATE@55/56/56|8011399d2cd1ad8c29e355c30c59521a30481ad130a04bb699fb2dc0ceb9bf6c|None|None|None|UNCONFIRMED|None',)), (56, 'UNCONFIRMED', ('STRUCTURE_STATE@56/57/57|fbf50bc1ae5f62e81bc841bd01fe569eac0c00e4d087a23f3f647df19efa2291|None|None|None|UNCONFIRMED|None',)), (57, 'UNCONFIRMED', ('STRUCTURE_STATE@57/58/58|e6e8b099a825b94c689951b2b9e62c2f0acbeb4a8ef59d9f451a822d4c5edb7f|None|None|None|UNCONFIRMED|None',)), (58, 'UNCONFIRMED', ('STRUCTURE_STATE@58/59/59|ed2dabf99d0650551bcf025b680f6daff0f6ce763589125c6ec0444058b53086|None|None|None|UNCONFIRMED|None',)), (59, 'UNCONFIRMED', ('STRUCTURE_STATE@59/60/60|9bd18d47102d55f28dbc9ef7a13fdc0d82393dcd56fbe00b15bafea0dd5eaf8d|None|None|None|UNCONFIRMED|None',)))
        self.assertEqual(self._golden_trace(result),expected)
        replay=MarketStructureEngine().analyze(bars)
        self.assertEqual(result,replay)
        self.assertEqual(self._golden_trace(replay),expected)

    def test_complete_reversal_60_candle_golden_trace_and_replay(self):
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
        bars=candles(closes=c,highs=h,lows=l,opens=o)
        result=MarketStructureEngine().analyze(bars)
        expected=((0, 'UNCONFIRMED', ('STRUCTURE_STATE@0/1/1|081773847bebb250df3241bdd45cb30266e4141d673aeeeb71fae4cf4f381bd5|None|None|None|UNCONFIRMED|None',)), (1, 'NEUTRAL', ('STRUCTURE_STATE@1/2/2|f92932336b04179a00f54a98894fafa1cadb340c620d761b24008b85015331dd|None|None|None|NEUTRAL|None',)), (2, 'NEUTRAL', ('STRUCTURE_STATE@2/3/3|432a9fdd66d1d50c181e9ec0215584ccdca1dfcf7a537635e9ec01ccde46e795|None|None|None|NEUTRAL|None',)), (3, 'NEUTRAL', ('STRUCTURE_STATE@3/4/4|4783b375cb3ee34c0b97a4f37a95cea1ae11a4423b03ddd46c2c7bf13e3a4755|None|None|None|NEUTRAL|None',)), (4, 'NEUTRAL', ('STRUCTURE_STATE@4/5/5|3ca1dcc1ea333f1333a2749e66fdd5eb4a9e82ac69fb6a4ed078c2568ecd9062|None|None|None|NEUTRAL|None',)), (5, 'NEUTRAL', ('STRUCTURE_STATE@5/6/6|5b1176bfbc11a6df4b4921c8c03617c6d8dbdb8c90fb9829f1d4b1536472533d|None|None|None|NEUTRAL|None',)), (6, 'NEUTRAL', ('STRUCTURE_STATE@6/7/7|3a03b4bc42cc229d19f01876d3238413daa09169360ce5d85e3ee71c7f363f54|None|None|None|NEUTRAL|None',)), (7, 'NEUTRAL', ('FVG@7/8/8|c81aa63d9a71e95fe1b4b0bbaafcf5809562ad8d0d0a5a4f91c6974db3dda5f3|None|bearish|ACTIVE|None|None', 'STRUCTURE_STATE@7/8/8|ed81267a600fb424448bf3f41c365f9bb4c2d537a87ced30bc831c27cd54504d|None|None|None|NEUTRAL|None')), (8, 'NEUTRAL', ('FVG_LIFECYCLE@8/9/9|2208a66f64824bd39d364d5dbdbd555f7b1e9450526bc2171f6217fe7cd482b6|None|bearish|FULLY_MITIGATED|None|c81aa63d9a71e95fe1b4b0bbaafcf5809562ad8d0d0a5a4f91c6974db3dda5f3', 'STRUCTURE_STATE@8/9/9|b641043c9da30545a6cb5850ea6a42a2dafc43076dbf1dcea2ec30de7ba9bccd|None|None|None|NEUTRAL|None')), (9, 'NEUTRAL', ('FVG@9/10/10|bbee9b3100f8bbebf7abef2c81735d95116108c715ae2291cd7791cd962b7b7f|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@9/10/10|07ed9bbd0c86b987a9b05e1c4deddcf85dad07892eda3264091f3f2c4eef6439|None|None|None|NEUTRAL|None')), (10, 'NEUTRAL', ('FVG_LIFECYCLE@10/11/11|8cab237c5e49724177f2263566efe0b3116cd96249a9adb519f1381c3e583e7d|None|bullish|PARTIALLY_MITIGATED|None|bbee9b3100f8bbebf7abef2c81735d95116108c715ae2291cd7791cd962b7b7f', 'STRUCTURE_STATE@10/11/11|d9099e675252cb1ef8c814975c1371600dfc73a574e6f35913f5d55da2929757|None|None|None|NEUTRAL|None')), (11, 'NEUTRAL', ('STRUCTURE_STATE@11/12/12|ebedb3c3926b2bde58e2425e452fe955890790a518f9f706478862f3da4d50a2|None|None|None|NEUTRAL|None',)), (12, 'NEUTRAL', ('SWING_LOW@7/13/13|d4e9d1df9baeadd203e112ab015b784b4d674ea10e3b4142570bea7a0eaeebf5|95|None|None|None|None', 'STRUCTURE_STATE@12/13/13|d01d5e47e4adf86cf86ddeaaae877fa7ca906f20cb1766024dbdae1ea67b5f40|None|None|None|NEUTRAL|None')), (13, 'NEUTRAL', ('STRUCTURE_STATE@13/14/14|201f29e1b750df74456ed35184265baaf8d6fa60e149e7ef90856c73d19a58c6|None|None|None|NEUTRAL|None',)), (14, 'NEUTRAL', ('STRUCTURE_STATE@14/15/15|2c0648fdaee297da5bed2873915989f6db4c67077fcae3a1efd7c5ec20cd05a4|None|None|None|NEUTRAL|None',)), (15, 'NEUTRAL', ('STRUCTURE_STATE@15/16/16|b24ce5003fa0d256d358bf151732157dcf2ecc8a3722b884bdb388c19bea3a10|None|None|None|NEUTRAL|None',)), (16, 'NEUTRAL', ('STRUCTURE_STATE@16/17/17|f76de8ae0e92bbb26f1e401a7d88330aca573df1b88a0dc153db04caf4fb5ee3|None|None|None|NEUTRAL|None',)), (17, 'UNCONFIRMED', ('SWING_HIGH@12/18/18|9031986d25827bd54fbc512422af30dac1447c9a8db7b59eba4443102338ba74|105|None|None|None|None', 'STRUCTURE_STATE@17/18/18|60bd12359c1a09b418e2cccc4161d074c7546356386a89031ab60d3f06bf945b|None|None|None|UNCONFIRMED|None')), (18, 'UNCONFIRMED', ('STRUCTURE_STATE@18/19/19|87ea5e97b298f44d1e37e82efcf8b0745f28bdc6689695aea2547370efb6e6d5|None|None|None|UNCONFIRMED|None',)), (19, 'UNCONFIRMED', ('STRUCTURE_STATE@19/20/20|94b158ffa020e64b8542a4f9a6922526c7733d73fd91b3b64cab1bbab6eca9ac|None|None|None|UNCONFIRMED|None',)), (20, 'UNCONFIRMED', ('STRUCTURE_STATE@20/21/21|679d06d663e73cd08a84bed59b4d014184d8065274daef5782b8dc26c154f946|None|None|None|UNCONFIRMED|None',)), (21, 'UNCONFIRMED', ('STRUCTURE_STATE@21/22/22|23caacc3ad094623f691c9e42c9da49724fad7af57c50f88115f8a3289f13a54|None|None|None|UNCONFIRMED|None',)), (22, 'UNCONFIRMED', ('SWING_LOW@17/23/23|157c589aeaa15c8caff4c8bd25e782e2abc629e9d3230fe724eb9a6ad7ad5602|100|None|None|None|None', 'HL@17/23/23|6c50b56ba8513af7f6840a1d7ac2acb0f54cb46ba69e33f2ad0e49178acac555|100|None|None|None|None', 'FVG@22/23/23|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944|None|bullish|ACTIVE|None|None', 'STRUCTURE_STATE@22/23/23|b28ffc89d4b1396157a27cc39222b0c5eaf2a9c4cc9169eaa213cda7b86a80e9|None|None|None|UNCONFIRMED|None')), (23, 'UNCONFIRMED', ('FVG@23/24/24|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830|None|bullish|ACTIVE|None|None', 'FVG_LIFECYCLE@23/24/24|c7326eb7c892ceb5d0bdfc68b47b99ea8f95cb27f24f47d900c445df83300072|None|bullish|PARTIALLY_MITIGATED|None|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944', 'STRUCTURE_STATE@23/24/24|5ca31970ca89fb74ef44db81c02c5416031ec9b040f06b29b9a8b4a3a2551fe0|None|None|None|UNCONFIRMED|None')), (24, 'UNCONFIRMED', ('FVG_LIFECYCLE@24/25/25|14a070f97f71320f6ca980e914e56ed0325d2c1a4752a15792bbacdfa97a410e|None|bullish|PARTIALLY_MITIGATED|None|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830', 'STRUCTURE_STATE@24/25/25|b5a168b0e461c3d644dd3009379a29f3d962fb60d72a5901f89b6a7d8d5c95bb|None|None|None|UNCONFIRMED|None')), (25, 'UNCONFIRMED', ('STRUCTURE_STATE@25/26/26|3edb25d0606a95747ebf37f40476631114324f3eda21e581534c2d2e093e4357|None|None|None|UNCONFIRMED|None',)), (26, 'UNCONFIRMED', ('STRUCTURE_STATE@26/27/27|c49091bb3beff7da9bb6319f6006b63b29f3a35b526b56720f5dc2577c758b18|None|None|None|UNCONFIRMED|None',)), (27, 'TRENDING_UP', ('SWING_HIGH@22/28/28|e4ad99560506d1f4c6691ad1de26268db5553f51fb715f279e30d4ce99c6ef1d|112|None|None|None|None', 'HH@22/28/28|d92048e28c90fad7a22af45b2f91da362447a05f73deebddf4abe1313cd6b1a7|112|None|None|None|None', 'STRUCTURE_STATE@27/28/28|ad19cde4de0545cdb06373f3945993450f2cb440bb8c35ffc16ae915befbf276|None|None|None|TRENDING_UP|None')), (28, 'TRENDING_UP', ('STRUCTURE_STATE@28/29/29|4be46f8c1c9279bfa693760ea9c043a6a0db612e5b52b2c4a2c92d066a8b0563|None|None|None|TRENDING_UP|None',)), (29, 'TRENDING_UP', ('STRUCTURE_STATE@29/30/30|896945ddac6ed97e763840ce41c78260f5ba4453bdcfcfb9d2ad2e941e56e3b8|None|None|None|TRENDING_UP|None',)), (30, 'TRENDING_UP', ('STRUCTURE_STATE@30/31/31|c12daddcf0ef688476e6c936c39ab1e9114508061f194a5d6a5f99191eb3a531|None|None|None|TRENDING_UP|None',)), (31, 'TRENDING_UP', ('STRUCTURE_STATE@31/32/32|3822b96d89c7c547e5e9702a3b78823fe7664cf9135cd010e9e969e216dc70ea|None|None|None|TRENDING_UP|None',)), (32, 'TRENDING_UP', ('SWING_LOW@27/33/33|6da251cf79ddf58948f774b9f75b39a4420a0e2c38b01b55462bd8f75d017524|107|None|None|None|None', 'HL@27/33/33|69f6bd1c6b6fcf464b4d0e27895f1fc15c4c56f5a3f75f5697c66b410247913d|107|None|None|None|None', 'STRUCTURE_STATE@32/33/33|decd0d2d19324d1cd3d49f286b87875aaea9da7c0f997fdb3b12fd028452475d|None|None|None|TRENDING_UP|None')), (33, 'TRENDING_UP', ('STRUCTURE_STATE@33/34/34|f5c7ba3719bd35ff1a6e8423d5f94be97b911d397e6c6021891bc366f45fb57e|None|None|None|TRENDING_UP|None',)), (34, 'TRENDING_UP', ('STRUCTURE_STATE@34/35/35|c4ef56fd3798ee761101ac99f5ec79cbc4c082e18dce7d8b18893956f7a32ab0|None|None|None|TRENDING_UP|None',)), (35, 'TRENDING_UP', ('STRUCTURE_STATE@35/36/36|72c0c8316a1d0d13172a58921a79a3d9745ff7c38becc574b08920eaa7f84e75|None|None|None|TRENDING_UP|None',)), (36, 'TRENDING_UP', ('STRUCTURE_STATE@36/37/37|15ba3aba0df8daefe1237424a056741238e17c5acaa4c9d1c49860ccada1bb95|None|None|None|TRENDING_UP|None',)), (37, 'TRENDING_UP', ('SWING_HIGH@32/38/38|464fff0c5fa964cef21776f03e9958e5171de0bfd277802dbf1e0684c9054001|118|None|None|None|None', 'HH@32/38/38|13083fcfd2ea2649558e1d8b01601474a1d47c31fb1c2a126737058a4ef68edf|118|None|None|None|None', 'STRUCTURE_STATE@37/38/38|ab9adea7e7c6236fb972c4df41c3c09e503e71a17b46542408cbe8b3feed5f68|None|None|None|TRENDING_UP|None')), (38, 'TRENDING_UP', ('STRUCTURE_STATE@38/39/39|2cf578025d089db5cf03e4c56df0bd1c7a2fd49538aa4e76ed46581a9bfc6eac|None|None|None|TRENDING_UP|None',)), (39, 'TRENDING_UP', ('STRUCTURE_STATE@39/40/40|4c193a5f7f581095c690c6e9a1e97570a2683b00b2ea47c588d2fa39658018fc|None|None|None|TRENDING_UP|None',)), (40, 'UNCONFIRMED', ('CHOCH@40/41/41|0c3350264ed68b1694e031b9a2aa4a97855278dbac5f889373e214fb941f8dac|107|bearish|None|None|None', 'FVG@40/41/41|822a55ec3d284d2227a0984ee91ce07800c060fa5370c2d655982cec6dbc4aa2|None|bearish|ACTIVE|None|None', 'STRUCTURE_STATE@40/41/41|d6d79fabb11cdef8d1c65106cb7870fc054566c8def31a91c24f07b730ef94b9|None|None|None|UNCONFIRMED|None')), (41, 'UNCONFIRMED', ('FVG_LIFECYCLE@41/42/42|b01939fc77450dd9d6a81dcc114479eb0b026dca340c323ba381b68351390bb6|None|bearish|FULLY_MITIGATED|None|822a55ec3d284d2227a0984ee91ce07800c060fa5370c2d655982cec6dbc4aa2', 'STRUCTURE_STATE@41/42/42|45fbd47ba47afe117dfe4aeeb1e32e6ba7237152d1084775095d7d45c8850420|None|None|None|UNCONFIRMED|None')), (42, 'UNCONFIRMED', ('FVG_LIFECYCLE@42/43/43|6650852c0f5f9ad4aa86a95f43989de9c640a501dd4aecc87525a832577de9cb|None|bullish|FULLY_MITIGATED|None|1f572e9fb9c9f864817cb7ff0ad72ec48d543a3396b671c43f395a038fe86944', 'FVG_LIFECYCLE@42/43/43|ead80240775f54c45de5b75f750f1d3a722b5080c20fa1cf565e78aeda47cebd|None|bullish|FULLY_MITIGATED|None|1c54cc4b8bd2717bcf92b06d10873e5f14e8af79e854c99aefcef136d4add830', 'STRUCTURE_STATE@42/43/43|d5c4bddcba41a7d542a6a9382f62b77c366823cf0aea71c2f7574635a8156906|None|None|None|UNCONFIRMED|None')), (43, 'UNCONFIRMED', ('STRUCTURE_STATE@43/44/44|91e08e74984df2d5d936a5c0195c385709cbd95cdbdad0eb391891d66da6f446|None|None|None|UNCONFIRMED|None',)), (44, 'UNCONFIRMED', ('STRUCTURE_STATE@44/45/45|5fa83380859d444e382d019c982a4d31f1d4335c7a9ea692ddb400269e2cf9d0|None|None|None|UNCONFIRMED|None',)), (45, 'UNCONFIRMED', ('STRUCTURE_STATE@45/46/46|20e5cd12dc95997be6917107c97f04584fc0ca4cefac5371fac6d05d279d8aef|None|None|None|UNCONFIRMED|None',)), (46, 'UNCONFIRMED', ('STRUCTURE_STATE@46/47/47|bf9b660869d7b0e470c117a9ae7450e591c59f620ae644a69a7cee4e9e17164d|None|None|None|UNCONFIRMED|None',)), (47, 'UNCONFIRMED', ('SWING_LOW@42/48/48|bf1497618ab243158bb756358d4bb4b0228f257df0941b7d6111a837f0b54c74|103|None|None|None|None', 'LL@42/48/48|b4f3857b20d98f89e36471425296283539c23a5a637337f71e2318921972342d|103|None|None|None|None', 'STRUCTURE_STATE@47/48/48|09355f8dbadc29f24f7aaf509c651e8fc50b10718b1253db82c65cc7696e3a74|None|None|None|UNCONFIRMED|None')), (48, 'UNCONFIRMED', ('STRUCTURE_STATE@48/49/49|53895598c0a2bbba96197666e22dfeedc189792373e0e00ab557a190b86bcd18|None|None|None|UNCONFIRMED|None',)), (49, 'UNCONFIRMED', ('STRUCTURE_STATE@49/50/50|a38e07e30b94f2171118e1e24a70011b07bfa7e3c1096144dba59bca8256730c|None|None|None|UNCONFIRMED|None',)), (50, 'UNCONFIRMED', ('SWING_HIGH@45/51/51|b5b1149d1a2820c1a536280360c7af5d089d3bf2b15fbd36479b27f4b39e1905|110|None|None|None|None', 'LH@45/51/51|27fae03f842ab636d91fcf4b9b0ec56f0372e5881bef3af93a7317d7a3b948ce|110|None|None|None|None', 'STRUCTURE_STATE@50/51/51|b8446c4c6780b813a88d02139aaf46167fe29728e5a829cfb5ef2b3258d66ec7|None|None|None|UNCONFIRMED|None')), (51, 'TRENDING_DOWN', ('MSS@51/52/52|032b6d567a58d0810d4b70ea8689ab7e2707ba209d82173e8416031c83250c18|103|bearish|None|None|None', 'FVG@51/52/52|e5a58ee4f759fbe714a816dbbf417a896b7bb5cc958b89c8e808234f09e9bdcd|None|bearish|ACTIVE|None|None', 'STRUCTURE_STATE@51/52/52|b4c694f3e196ca3e0d201765b0107efa92450bee13940f56076fbc645f06dd8e|None|None|None|TRENDING_DOWN|None')), (52, 'TRENDING_DOWN', ('FVG@52/53/53|e020df230e65bccaf3525582a71e03e88ae0638793937b313d159bae2acf1038|None|bearish|ACTIVE|None|None', 'FVG_LIFECYCLE@52/53/53|2681c06c8b063aaec9baf2a2cae198d1ce355602ea03a38eee2d52b91aaa933d|None|bearish|PARTIALLY_MITIGATED|None|e5a58ee4f759fbe714a816dbbf417a896b7bb5cc958b89c8e808234f09e9bdcd', 'STRUCTURE_STATE@52/53/53|bbc0932ec4290c06e2acaf09dbb0a1bd4c071a0ebeac7b37de3b06d1016515e5|None|None|None|TRENDING_DOWN|None')), (53, 'TRENDING_DOWN', ('FVG_LIFECYCLE@53/54/54|aa7c078359c3f8ba65a08b75b2f2b793232cce073c0a5579a4c307407479e057|None|bearish|PARTIALLY_MITIGATED|None|e020df230e65bccaf3525582a71e03e88ae0638793937b313d159bae2acf1038', 'STRUCTURE_STATE@53/54/54|aaacb37ac60b194f34bb7da7091e0cf4b53904b313c30655357d6fbca2131849|None|None|None|TRENDING_DOWN|None')), (54, 'TRENDING_DOWN', ('STRUCTURE_STATE@54/55/55|4a006f2f806414671687951bd2baada0462b7aaeab6fc9b330b4438c77bf6071|None|None|None|TRENDING_DOWN|None',)), (55, 'TRENDING_DOWN', ('STRUCTURE_STATE@55/56/56|8011399d2cd1ad8c29e355c30c59521a30481ad130a04bb699fb2dc0ceb9bf6c|None|None|None|TRENDING_DOWN|None',)), (56, 'TRENDING_DOWN', ('STRUCTURE_STATE@56/57/57|fbf50bc1ae5f62e81bc841bd01fe569eac0c00e4d087a23f3f647df19efa2291|None|None|None|TRENDING_DOWN|None',)), (57, 'TRENDING_DOWN', ('STRUCTURE_STATE@57/58/58|e6e8b099a825b94c689951b2b9e62c2f0acbeb4a8ef59d9f451a822d4c5edb7f|None|None|None|TRENDING_DOWN|None',)), (58, 'TRENDING_DOWN', ('STRUCTURE_STATE@58/59/59|ed2dabf99d0650551bcf025b680f6daff0f6ce763589125c6ec0444058b53086|None|None|None|TRENDING_DOWN|None',)), (59, 'TRENDING_DOWN', ('STRUCTURE_STATE@59/60/60|9bd18d47102d55f28dbc9ef7a13fdc0d82393dcd56fbe00b15bafea0dd5eaf8d|None|None|None|TRENDING_DOWN|None',)))
        self.assertEqual(self._golden_trace(result),expected)
        replay=MarketStructureEngine().analyze(bars)
        self.assertEqual(result,replay)
        self.assertEqual(self._golden_trace(replay),expected)

if __name__=="__main__": unittest.main()
