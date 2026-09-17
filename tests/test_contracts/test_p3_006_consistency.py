from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest
from contracts.canonical import CanonicalCandle, CanonicalDerivatives, CanonicalInstrument, CanonicalOrderBook, CanonicalTrade
from contracts.consistency import SID, VERSION, CanonicalVenueEvidence, ComparisonCode, ComparisonPolicy, ComparisonStatus, compare
UTC=timezone.utc
T=datetime(2026,9,18,0,0,tzinfo=UTC)

def instrument(venue, instrument_id=None, **kw):
    return CanonicalVenueEvidence(venue, CanonicalInstrument(instrument_id or f'{venue}:BTCUSDT', kw.get('base','BTC'), kw.get('quote','USDT'), kw.get('market','SPOT'), kw.get('contract','SPOT'), kw.get('unit','BTC'), T, contract_multiplier=kw.get('multiplier'), provenance_id=f'{venue}:test'))

def trade(venue, price='100', qty='2', ts=T, side='BUY', instrument_id=None):
    return CanonicalVenueEvidence(venue, CanonicalTrade(f'{venue}-7', instrument_id or f'{venue}:BTCUSDT', ts, Decimal(price), Decimal(qty), side, provenance_id=f'{venue}:test'))

def candle(venue, timeframe='1m', close='105', ot=T, instrument_id=None):
    return CanonicalVenueEvidence(venue, CanonicalCandle(instrument_id or f'{venue}:BTCUSDT', timeframe, ot, ot+timedelta(minutes=1), Decimal('100'), Decimal('110'), Decimal('90'), Decimal(close), Decimal('12'), Decimal('1200'), 10, True, f'{venue}:test'))

def book(venue, bid='100', ask='101', ts=T, instrument_id=None):
    return CanonicalVenueEvidence(venue, CanonicalOrderBook(instrument_id or f'{venue}:BTCUSDT', ts, ((Decimal(bid),Decimal('2')),), ((Decimal(ask),Decimal('1')),), f'{venue}:test'))

def derivatives(venue, funding='0.001', instrument_id=None):
    return CanonicalVenueEvidence(venue, CanonicalDerivatives(instrument_id or f'{venue}:BTCUSDT', T, funding_rate=Decimal(funding), open_interest=Decimal('10'), provenance_id=f'{venue}:test'))

class P3006ConsistencyTests(unittest.TestCase):
    def test_identity(self): self.assertEqual((SID,VERSION),('STEP-P3-006','1.0.0'))
    def test_equivalent_cross_venue_instruments_ignore_venue_specific_ids(self):
        r=compare(instrument('binance'), instrument('mexc'), policy=ComparisonPolicy(max_age=timedelta(minutes=5)), reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.EQUIVALENT); self.assertEqual(r.issues[0].code,ComparisonCode.EQUIVALENT)
    def test_symbol_equal_but_base_quote_incompatible(self):
        r=compare(instrument('binance'),instrument('mexc',base='ETH'))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.BASE_ASSET_MISMATCH,[x.code for x in r.issues])
    def test_market_type_contract_unit_multiplier_mismatch(self):
        r=compare(instrument('binance',market='SPOT',contract='SPOT',unit='BTC',multiplier=None),instrument('mexc',market='FUTURES',contract='PERPETUAL',unit='CONTRACT',multiplier=Decimal('1')))
        codes=[x.code for x in r.issues]
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertTrue({ComparisonCode.MARKET_TYPE_MISMATCH,ComparisonCode.CONTRACT_TYPE_MISMATCH,ComparisonCode.UNIT_MISMATCH,ComparisonCode.MULTIPLIER_MISMATCH}.issubset(codes))
    def test_equivalent_binance_mexc_trade(self):
        r=compare(trade('binance'),trade('mexc'),policy=ComparisonPolicy(max_timestamp_delta=timedelta(seconds=1),max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.EQUIVALENT)
    def test_trade_semantic_instrument_identity_mismatch_blocks_equivalence(self):
        r=compare(trade('binance'),trade('mexc',instrument_id='mexc:ETHUSDT'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.INSTRUMENT_ID_MISMATCH,[x.code for x in r.issues])

    def test_candle_semantic_instrument_identity_mismatch_blocks_equivalence(self):
        r=compare(candle('binance'),candle('mexc',instrument_id='mexc:ETHUSDT'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.INSTRUMENT_ID_MISMATCH,[x.code for x in r.issues])

    def test_orderbook_semantic_instrument_identity_mismatch_blocks_equivalence(self):
        r=compare(book('binance'),book('mexc',instrument_id='mexc:ETHUSDT'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.INSTRUMENT_ID_MISMATCH,[x.code for x in r.issues])

    def test_derivatives_semantic_instrument_identity_mismatch_blocks_equivalence(self):
        r=compare(derivatives('binance'),derivatives('mexc',instrument_id='mexc:ETHUSDT'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.INSTRUMENT_ID_MISMATCH,[x.code for x in r.issues])

    def test_trade_price_quantity_side_mismatch(self):
        r=compare(trade('binance',price='100'),trade('mexc',price='101',qty='3',side='SELL'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        codes=[x.code for x in r.issues]
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertTrue({ComparisonCode.PRICE_MISMATCH,ComparisonCode.QUANTITY_MISMATCH,ComparisonCode.SIDE_MISMATCH}.issubset(codes))
    def test_timeframe_mismatch(self):
        r=compare(candle('binance','1m'),candle('mexc','5m'))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.TIMEFRAME_MISMATCH,[x.code for x in r.issues])
    def test_timestamp_misalignment(self):
        r=compare(trade('binance',ts=T),trade('mexc',ts=T+timedelta(seconds=10)),policy=ComparisonPolicy(max_timestamp_delta=timedelta(seconds=1),max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.TIMESTAMP_MISALIGNMENT,[x.code for x in r.issues])
    def test_stale_evidence(self):
        r=compare(trade('binance',ts=T),trade('mexc',ts=T+timedelta(seconds=1)),policy=ComparisonPolicy(max_age=timedelta(seconds=30)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.LEFT_STALE,[x.code for x in r.issues])
    def test_missing_freshness_reference_is_insufficient(self):
        r=compare(trade('binance'),trade('mexc'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)))
        self.assertEqual(r.status,ComparisonStatus.INSUFFICIENT_EVIDENCE); self.assertIn(ComparisonCode.REQUIRED_EVIDENCE_MISSING,[x.code for x in r.issues])
    def test_unchecked_freshness_is_explicit(self):
        r=compare(trade('binance'),trade('mexc'))
        self.assertEqual(r.status,ComparisonStatus.INSUFFICIENT_EVIDENCE); self.assertIn(ComparisonCode.FRESHNESS_UNCHECKED,[x.code for x in r.issues])
    def test_future_evidence_rejected_from_historical_freshness(self):
        r=compare(trade('binance',ts=T+timedelta(seconds=2)),trade('mexc',ts=T),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T)
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.TIMESTAMP_MISALIGNMENT,[x.code for x in r.issues])
    def test_orderbook_positive_and_bid_ask_sanity(self):
        r=compare(book('binance'),book('mexc'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.EQUIVALENT)
    def test_orderbook_difference_is_market_data_inconsistency_not_opportunity(self):
        r=compare(book('binance',bid='100'),book('mexc',bid='99'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.ORDERBOOK_MISMATCH,[x.code for x in r.issues]); self.assertFalse(hasattr(r,'opportunity'))
    def test_invalid_orderbook_cannot_enter_canonical_comparison(self):
        with self.assertRaises(ValueError): CanonicalOrderBook('X',T,((Decimal('101'),Decimal('1')),),((Decimal('100'),Decimal('1')),),'x')
    def test_derivatives_difference(self):
        r=compare(derivatives('binance'),derivatives('mexc','0.002'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.DERIVATIVES_MISMATCH,[x.code for x in r.issues])
    def test_provenance_is_preserved_and_wire_fields_do_not_exist(self):
        r=compare(trade('binance'),trade('mexc'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.left_provenance_id,'binance:test'); self.assertEqual(r.right_provenance_id,'mexc:test'); self.assertFalse(hasattr(r,'wire'))
    def test_deterministic_repeated_comparison_and_reason_order(self):
        a=compare(trade('binance',price='100',qty='2',side='BUY'),trade('mexc',price='101',qty='3',side='SELL'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        b=compare(trade('binance',price='100',qty='2',side='BUY'),trade('mexc',price='101',qty='3',side='SELL'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(a,b); self.assertEqual([x.dimension for x in a.issues[:3]],['price','quantity','aggressor_side'])
    def test_provider_neutral_input_and_unsupported_canonical_type_rejected(self):
        r=compare(CanonicalVenueEvidence('binance',object()),trade('mexc'))
        self.assertEqual(r.status,ComparisonStatus.REJECTED); self.assertIn(ComparisonCode.TYPE_MISMATCH,[x.code for x in r.issues])
    def test_explicit_availability_is_not_promoted_to_equivalence(self):
        r=compare(CanonicalVenueEvidence('binance',trade('binance').value,available=False),trade('mexc'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.AVAILABILITY_MISMATCH,[x.code for x in r.issues])
    def test_candle_window_and_ohlcv_mismatch(self):
        r=compare(candle('binance',close='105'),candle('mexc',close='106'),policy=ComparisonPolicy(max_age=timedelta(minutes=5)),reference_time=T+timedelta(minutes=1))
        self.assertEqual(r.status,ComparisonStatus.INCONSISTENT); self.assertIn(ComparisonCode.CANDLE_MISMATCH,[x.code for x in r.issues])

if __name__=='__main__': unittest.main()
