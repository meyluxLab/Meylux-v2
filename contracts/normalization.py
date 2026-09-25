"""Deterministic Binance/MEXC provider-to-canonical mapping for P3-005."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType
from contracts.canonical import CanonicalCandle, CanonicalDerivatives, CanonicalInstrument, CanonicalOrderBook, CanonicalTrade
from contracts.canonical.foundation import ProvenanceRef, ValidationCode, ValidationIssue, ValidationResult, validate_provenance, validate_timestamp
SID="STEP-P3-005"
VERSION="1.0.0"
@dataclass(frozen=True, slots=True)
class NormalizationOutcome:
    result: ValidationResult
    value: Any=None
    issues: tuple[ValidationIssue,...]=()
    @property
    def valid(self)->bool:return self.result is ValidationResult.VALID and self.value is not None
def normalize(e: AcquisitionEnvelope)->NormalizationOutcome:
    if not isinstance(e,AcquisitionEnvelope):return _reject("envelope",ValidationCode.INVALID_TYPE,"envelope must be AcquisitionEnvelope")
    if e.state is not AcquisitionState.AVAILABLE:return _reject("state",ValidationCode.INVALID_VALUE,"non-AVAILABLE acquisition cannot become canonical data")
    issue=validate_provenance(ProvenanceRef(e.provenance.provenance_id,e.provider.provider_id,e.provenance.acquisition_method),"provenance")
    if issue:return NormalizationOutcome(ValidationResult.INCOMPLETE,issues=(issue,))
    try:
        fn={EventType.INSTRUMENT:_instrument,EventType.TRADE:_trade,EventType.CANDLE:_candle,EventType.ORDER_BOOK:_order_book,EventType.DERIVATIVES:_derivatives}.get(e.event_type)
        if fn is None:return _reject("event_type",ValidationCode.INVALID_VALUE,"event type has no P3-005 canonical mapping")
        return NormalizationOutcome(ValidationResult.VALID,value=fn(e))
    except _MappingFailure as x:return _reject(x.field,x.code,str(x))
    except (TypeError,ValueError,InvalidOperation) as x:return _reject("payload",ValidationCode.INVALID_VALUE,str(x))
def _instrument(e):
    p=_record(e.payload,"instrument");r=_select_symbol(p,e.instrument.provider_instrument_id);base=_text(r,("baseAsset","base_asset","base"),"base_asset");quote=_text(r,("quoteAsset","quote_asset","quote"),"quote_asset")
    return CanonicalInstrument(e.instrument.canonical_instrument_id,base,quote,_text(r,("marketType","market_type"),"market_type",_spot(e)),_text(r,("contractType","contract_type"),"contract_type",_spot(e)),_text(r,("unit",),"unit",base),e.event_time,_int(r,("pricePrecision","price_precision")),_int(r,("quantityPrecision","quantity_precision")),_decimal_optional(r,("contractMultiplier","contract_multiplier")),_active(r),e.provenance.provenance_id)
def _trade(e):
    p=_record(e.payload,"trade")
    if e.provider.provider_id=="binance":price=_decimal(_pick(p,"p","price"),"price");qty=_decimal(_pick(p,"q","qty","quantity"),"quantity");tid=_string(_pick(p,"t","id","tradeId","trade_id"),"trade_id");ts=_timestamp(_pick(p,"T","time","timestamp"),e.event_time,"timestamp");quote=_decimal_optional(p,("Y","quoteQty","quote_quantity"));side=_binance_side(p)
    elif e.provider.provider_id=="mexc":price=_decimal(_pick(p,"price"),"price");qty=_decimal(_pick(p,"qty","quantity"),"quantity");tid=_string(_pick(p,"id","tradeId","trade_id"),"trade_id");ts=_timestamp(_pick(p,"time","timestamp"),e.event_time,"timestamp");quote=_decimal_optional(p,("quoteQty","quote_quantity"));side=_mexc_side(p)
    else:raise _MappingFailure(ValidationCode.INVALID_VALUE,"provider","unsupported provider mapping")
    return CanonicalTrade(tid,e.instrument.canonical_instrument_id,ts,price,qty,side,quote,e.provenance.provenance_id)
def _candle(e):
    p=_record(e.payload,"candle")
    if e.provider.provider_id=="binance" and isinstance(p.get("k"),Mapping):
        k=p["k"];tf=_text(k,("i",),"timeframe");ot=_timestamp(_pick(k,"t"),e.event_time,"open_time");ct=_timestamp(_pick(k,"T"),e.event_time,"close_time");op,hi,lo,cl,vol=(_decimal(_pick(k,x),x) for x in ("o","h","l","c","v"));quote=_decimal_optional(k,("q","quoteVolume"));count=_int(k,("n","tradeCount"));closed=k.get("x")
    elif e.provider.provider_id=="mexc" and isinstance(p.get("data"),Mapping) and "openingPrice" in p["data"]:
        k=p["data"];tf=_text(k,("interval",),"timeframe");ot=_timestamp(_pick(k,"windowStart"),e.event_time,"open_time","seconds");ct=_timestamp(_pick(k,"windowEnd"),e.event_time,"close_time","seconds");op,hi,lo,cl,vol=(_decimal(_pick(k,x),x) for x in ("openingPrice","highestPrice","lowestPrice","closingPrice","volume"));quote=_decimal_optional(k,("amount","quoteVolume"));count=None;closed=True
    else:raise _MappingFailure(ValidationCode.REQUIRED_MISSING,"timeframe","provider candle payload does not carry explicit timeframe context")
    if not isinstance(closed,bool):raise _MappingFailure(ValidationCode.INVALID_TYPE,"is_closed","is_closed must be bool")
    return CanonicalCandle(e.instrument.canonical_instrument_id,tf,ot,ct,op,hi,lo,cl,vol,quote,count,closed,e.provenance.provenance_id)
def _order_book(e):
    p=_record(e.payload,"order_book")
    if e.provider.provider_id=="binance":bids,asks=_levels(p.get("b",p.get("bids")),"bids"),_levels(p.get("a",p.get("asks")),"asks")
    elif e.provider.provider_id=="mexc":
        p=p.get("data") if isinstance(p.get("data"),Mapping) else p;bids,asks=_levels(p.get("b",p.get("bidsList",p.get("bids"))),"bids"),_levels(p.get("a",p.get("asksList",p.get("asks"))),"asks")
    else:raise _MappingFailure(ValidationCode.INVALID_VALUE,"provider","unsupported provider mapping")
    return CanonicalOrderBook(e.instrument.canonical_instrument_id,e.event_time,tuple(bids),tuple(asks),e.provenance.provenance_id)
def _derivatives(e):
    p=_record(e.payload,"derivatives");keys=("funding_rate","funding_change","funding_velocity","open_interest","open_interest_delta","basis")
    if e.provider.provider_id not in {"binance","mexc"} or not any(k in p for k in keys):raise _MappingFailure(ValidationCode.INVALID_VALUE,"payload","no explicitly supported derivatives mapping")
    return CanonicalDerivatives(e.instrument.canonical_instrument_id,e.event_time,*(_decimal_optional(p,(k,)) for k in keys),e.provenance.provenance_id)
def _spot(e):
    if e.provider.provider_id in {"binance","mexc"}:return "SPOT"
    raise _MappingFailure(ValidationCode.INVALID_VALUE,"provider","unsupported provider market mapping")
def _binance_side(p):
    v=p.get("m",p.get("isBuyerMaker"))
    if v is None:return None
    if not isinstance(v,bool):raise _MappingFailure(ValidationCode.INVALID_TYPE,"aggressor_side","Binance buyer-maker flag must be bool")
    return "SELL" if v else "BUY"
def _mexc_side(p):
    v=p.get("isBuyerMaker")
    if v is None:return None
    if not isinstance(v,bool):raise _MappingFailure(ValidationCode.INVALID_TYPE,"aggressor_side","MEXC buyer-maker flag must be bool")
    return "SELL" if v else "BUY"
def _record(p,field):
    if not isinstance(p,Mapping):raise _MappingFailure(ValidationCode.INVALID_TYPE,field,f"{field} payload must be mapping")
    return p
def _select_symbol(p,symbol):
    rows=p.get("symbols")
    if isinstance(rows,Sequence) and not isinstance(rows,(str,bytes)):
        for r in rows:
            if isinstance(r,Mapping) and str(r.get("symbol","")).upper()==symbol.upper():return r
        raise _MappingFailure(ValidationCode.INVALID_VALUE,"instrument","provider instrument record not found")
    data=p.get("data")
    if isinstance(data,Mapping) and "symbols" in data:return _select_symbol(data,symbol)
    if isinstance(data,Mapping) and any(k in data for k in ("baseAsset","base_asset","quoteAsset","quote_asset")):return data
    return p
def _pick(p,*keys):
    for k in keys:
        if k in p and p[k] is not None:return p[k]
    raise _MappingFailure(ValidationCode.REQUIRED_MISSING,keys[0],f"required provider field {keys[0]} is missing")
def _text(p,keys,field,default=None):
    v=next((p[k] for k in keys if k in p and p[k] is not None),default)
    if not isinstance(v,str) or not v.strip():raise _MappingFailure(ValidationCode.REQUIRED_MISSING,field,f"{field} must be explicit")
    return v.strip()
def _string(v,field):
    if isinstance(v,bool) or not isinstance(v,(str,int)):raise _MappingFailure(ValidationCode.INVALID_TYPE,field,f"{field} must be string-compatible")
    s=str(v).strip()
    if not s:raise _MappingFailure(ValidationCode.REQUIRED_MISSING,field,f"{field} must not be empty")
    return s
def _decimal(v,field):
    if isinstance(v,bool) or isinstance(v,float):raise _MappingFailure(ValidationCode.FLOAT_NOT_ALLOWED if isinstance(v,float) else ValidationCode.INVALID_TYPE,field,f"{field} must be exact Decimal-compatible data")
    try:d=v if isinstance(v,Decimal) else Decimal(str(v))
    except (InvalidOperation,ValueError) as x:raise _MappingFailure(ValidationCode.INVALID_VALUE,field,f"{field} is not a valid decimal") from x
    if not d.is_finite():raise _MappingFailure(ValidationCode.NON_FINITE_DECIMAL,field,f"{field} must be finite")
    return d
def _decimal_optional(p,keys):
    for k in keys:
        if k in p and p[k] is not None:return _decimal(p[k],k)
    return None
def _int(p,keys):
    for k in keys:
        if k in p and p[k] is not None:
            v=p[k]
            if not isinstance(v,int) or isinstance(v,bool) or v<0:raise _MappingFailure(ValidationCode.INVALID_TYPE,k,f"{k} must be non-negative integer")
            return v
    return None
def _timestamp(v,fallback,field,unit="milliseconds"):
    if isinstance(v,datetime):
        try:return validate_timestamp(v,field)
        except (TypeError,ValueError) as x:raise _MappingFailure(ValidationCode.TIMESTAMP_INVALID,field,str(x)) from x
    if isinstance(v,bool) or not isinstance(v,int):raise _MappingFailure(ValidationCode.INVALID_TYPE,field,f"{field} timestamp must be integer or datetime")
    try:return validate_timestamp(datetime.fromtimestamp(v/(1000 if unit=="milliseconds" else 1),tz=fallback.tzinfo),field)
    except (OverflowError,OSError,ValueError) as x:raise _MappingFailure(ValidationCode.TIMESTAMP_INVALID,field,str(x)) from x
def _levels(raw,side):
    if not isinstance(raw,Sequence) or isinstance(raw,(str,bytes)):raise _MappingFailure(ValidationCode.REQUIRED_MISSING,side,f"{side} levels are required")
    out=[]
    for i,level in enumerate(raw):
        if isinstance(level,Mapping):price,qty=level.get("price"),level.get("quantity")
        elif isinstance(level,Sequence) and not isinstance(level,(str,bytes)) and len(level)>=2:price,qty=level[0],level[1]
        else:raise _MappingFailure(ValidationCode.INVALID_VALUE,side,f"{side}[{i}] is not a price/quantity pair")
        price,qty=_decimal(price,f"{side}[{i}].price"),_decimal(qty,f"{side}[{i}].quantity")
        if qty<=0:raise _MappingFailure(ValidationCode.INVALID_VALUE,f"{side}[{i}].quantity","non-positive quantity cannot become canonical snapshot data")
        out.append((price,qty))
    return out
def _active(p):
    v=p.get("active")
    if v is not None:
        if not isinstance(v,bool):raise _MappingFailure(ValidationCode.INVALID_TYPE,"active","active must be bool")
        return v
    s=p.get("status")
    if not isinstance(s,str):raise _MappingFailure(ValidationCode.REQUIRED_MISSING,"status","status is required for canonical instrument activity")
    if s.upper() in {"TRADING","ENABLED","ACTIVE","1"}:return True
    if s.upper() in {"BREAK","HALT","DISABLED","INACTIVE","0"}:return False
    raise _MappingFailure(ValidationCode.INVALID_VALUE,"status",f"unsupported provider status: {s}")
def _reject(field,code,message):return NormalizationOutcome(ValidationResult.REJECTED,issues=(ValidationIssue(code,field,message),))
class _MappingFailure(Exception):
    def __init__(self,code,field,message):super().__init__(message);self.code=code;self.field=field
