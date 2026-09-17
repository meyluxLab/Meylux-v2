from datetime import datetime, timezone
from decimal import Decimal
import unittest
from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType, InstrumentIdentity, ProviderError, ProviderIdentity, Provenance
from contracts.canonical import CanonicalCandle, CanonicalOrderBook, CanonicalTrade
from contracts.normalization import SID, VERSION, normalize
UTC=timezone.utc; NOW=datetime(2026,9,17,12,0,tzinfo=UTC)
def env(provider,event,payload,state=AcquisitionState.AVAILABLE,**kw):
 p=ProviderIdentity(provider,f"{provider}-acquisition","1.0.0"); return AcquisitionEnvelope(p,InstrumentIdentity(kw.get("instrument",f"{provider.upper()}:BTCUSDT"),"BTCUSDT"),Provenance(f"{provider}:test",p,"TEST"),event,NOW,NOW,state,payload,"42",ProviderError("INVALID","TEST","invalid") if state is not AcquisitionState.AVAILABLE else None)
class P3005NormalizationTests(unittest.TestCase):
 def test_identity(self): self.assertEqual((SID,VERSION),("STEP-P3-005","1.0.0"))
 def test_binance_trade(self):
  r=normalize(env("binance",EventType.TRADE,{"e":"trade","s":"BTCUSDT","t":7,"T":1757592000000,"p":"100.25","q":"2","m":False,"Y":"200.50","wire":"x"})); self.assertTrue(r.valid); self.assertIsInstance(r.value,CanonicalTrade); self.assertEqual((r.value.trade_id,r.value.price,r.value.quantity,r.value.aggressor_side),("7",Decimal("100.25"),Decimal("2"),"BUY")); self.assertFalse(hasattr(r.value,"wire"))
 def test_mexc_trade_does_not_guess_trade_type(self):
  r=normalize(env("mexc",EventType.TRADE,{"price":"100","qty":"2","time":1757592000000,"tradeId":"7","tradeType":1})); self.assertTrue(r.valid); self.assertIsNone(r.value.aggressor_side)
 def test_binance_candle(self):
  r=normalize(env("binance",EventType.CANDLE,{"k":{"i":"1m","t":1757592000000,"T":1757592059999,"o":"100","h":"110","l":"90","c":"105","v":"12","q":"1250","n":10,"x":True,"wire":"x"}})); self.assertTrue(r.valid); self.assertIsInstance(r.value,CanonicalCandle); self.assertEqual((r.value.timeframe,r.value.close),("1m",Decimal("105")))
 def test_mexc_candle(self):
  r=normalize(env("mexc",EventType.CANDLE,{"data":{"interval":"Min1","windowStart":1757592000,"windowEnd":1757592059,"openingPrice":"100","closingPrice":"105","highestPrice":"110","lowestPrice":"90","volume":"12","amount":"1250"}})); self.assertTrue(r.valid); self.assertEqual(r.value.timeframe,"Min1")
 def test_order_books(self):
  for provider in ("binance","mexc"):
   with self.subTest(provider=provider):
    r=normalize(env(provider,EventType.ORDER_BOOK,{"bids":[["100","2"]],"asks":[["101","1"]]})); self.assertTrue(r.valid); self.assertIsInstance(r.value,CanonicalOrderBook)
 def test_instrument_identity_and_spot_semantics(self):
  r=normalize(env("binance",EventType.INSTRUMENT,{"symbols":[{"symbol":"BTCUSDT","baseAsset":"BTC","quoteAsset":"USDT","status":"TRADING","pricePrecision":2,"quantityPrecision":6}]},instrument="BINANCE:BTCUSDT")); self.assertTrue(r.valid); self.assertEqual((r.value.instrument_id,r.value.market_type,r.value.contract_type,r.value.unit,r.value.provenance_id),("BINANCE:BTCUSDT","SPOT","SPOT","BTC","binance:test"))
 def test_supported_alias_translation(self):
  r=normalize(env("binance",EventType.TRADE,{"price":"100","qty":"2","id":9,"time":1757592000000,"isBuyerMaker":True})); self.assertTrue(r.valid); self.assertEqual(r.value.aggressor_side,"SELL")
 def test_unsupported_event_rejected(self):
  r=normalize(env("binance",EventType.UPDATE,{"foo":"bar"})); self.assertFalse(r.valid); self.assertIsNone(r.value)
 def test_invalid_state_not_promoted(self):
  r=normalize(env("binance",EventType.TRADE,{},AcquisitionState.INVALID)); self.assertFalse(r.valid); self.assertIsNone(r.value)
 def test_malformed_trade_rejected(self):
  r=normalize(env("binance",EventType.TRADE,{"p":"bad","q":"2","t":1,"T":1757592000000})); self.assertFalse(r.valid); self.assertIsNone(r.value)
 def test_float_rejected_at_acquisition_boundary(self):
  with self.assertRaises(TypeError): env("binance",EventType.TRADE,{"p":100.25,"q":"2","t":1,"T":1757592000000})
 def test_zero_book_quantity_rejected(self):
  r=normalize(env("mexc",EventType.ORDER_BOOK,{"bids":[["100","0"]],"asks":[["101","1"]]})); self.assertFalse(r.valid); self.assertIsNone(r.value)
 def test_missing_timeframe_rejected(self):
  r=normalize(env("binance",EventType.CANDLE,{"o":"100","h":"110","l":"90","c":"105","v":"1"})); self.assertFalse(r.valid)
 def test_deterministic_and_provenance(self):
  e=env("binance",EventType.TRADE,{"p":"100","q":"2","t":1,"T":1757592000000}); a,b=normalize(e),normalize(e); self.assertTrue(a.valid); self.assertEqual(a.value,b.value); self.assertEqual(a.value.provenance_id,"binance:test")
 def test_derivatives_without_explicit_mapping_rejected(self):
  r=normalize(env("mexc",EventType.DERIVATIVES,{"fundingRate":"0.001"})); self.assertFalse(r.valid)
if __name__=="__main__": unittest.main()
