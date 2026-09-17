"""Provider-neutral deterministic cross-venue consistency/equivalence validation for P3-006.

Consumes already-canonical P3-005 representations. No I/O, provider access,
wall-clock reads, persistence, scoring, opportunity analysis, or contract mutation.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from contracts.canonical import CanonicalCandle, CanonicalDerivatives, CanonicalInstrument, CanonicalOrderBook, CanonicalTrade

SID = "STEP-P3-006"
VERSION = "1.0.0"

class ComparisonStatus(str, Enum):
    EQUIVALENT = "equivalent"
    INCONSISTENT = "inconsistent"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REJECTED = "rejected"

class ComparisonCode(str, Enum):
    EQUIVALENT="equivalent"
    REQUIRED_EVIDENCE_MISSING="required_evidence_missing"
    INVALID_CANONICAL="invalid_canonical"
    TYPE_MISMATCH="type_mismatch"
    VENUE_ID_MISSING="venue_id_missing"
    INSTRUMENT_ID_MISSING="instrument_id_missing"
    INSTRUMENT_ID_MISMATCH="instrument_id_mismatch"
    BASE_ASSET_MISMATCH="base_asset_mismatch"
    QUOTE_ASSET_MISMATCH="quote_asset_mismatch"
    MARKET_TYPE_MISMATCH="market_type_mismatch"
    CONTRACT_TYPE_MISMATCH="contract_type_mismatch"
    UNIT_MISMATCH="unit_mismatch"
    MULTIPLIER_MISMATCH="multiplier_mismatch"
    TIMEFRAME_MISMATCH="timeframe_mismatch"
    TIMESTAMP_MISALIGNMENT="timestamp_misalignment"
    FRESHNESS_UNCHECKED="freshness_unchecked"
    LEFT_STALE="left_stale"
    RIGHT_STALE="right_stale"
    PRICE_MISMATCH="price_mismatch"
    QUANTITY_MISMATCH="quantity_mismatch"
    SIDE_MISMATCH="side_mismatch"
    BID_ASK_INVALID="bid_ask_invalid"
    ORDERBOOK_MISMATCH="orderbook_mismatch"
    CANDLE_MISMATCH="candle_mismatch"
    DERIVATIVES_MISMATCH="derivatives_mismatch"
    AVAILABILITY_MISMATCH="availability_mismatch"
    PROVENANCE_MISSING="provenance_missing"

@dataclass(frozen=True, slots=True)
class ComparisonIssue:
    code: ComparisonCode
    dimension: str
    message: str

@dataclass(frozen=True, slots=True)
class CanonicalVenueEvidence:
    """Explicit venue context around an existing canonical value."""
    venue_id: str
    value: object
    available: bool = True
    def __post_init__(self) -> None:
        if not isinstance(self.venue_id, str) or not self.venue_id.strip(): raise ValueError("venue_id must be a non-empty string")
        if not isinstance(self.available, bool): raise TypeError("available must be bool")

@dataclass(frozen=True, slots=True)
class ComparisonPolicy:
    """Caller-supplied temporal policy; no P3-006 threshold is invented."""
    max_timestamp_delta: Optional[timedelta] = None
    max_age: Optional[timedelta] = None
    require_freshness_evidence: bool = False
    def __post_init__(self) -> None:
        for value, field in ((self.max_timestamp_delta,"max_timestamp_delta"),(self.max_age,"max_age")):
            if value is not None and (not isinstance(value,timedelta) or value < timedelta(0)): raise ValueError(f"{field} must be a non-negative timedelta")
        if not isinstance(self.require_freshness_evidence,bool): raise TypeError("require_freshness_evidence must be bool")
        if self.require_freshness_evidence and self.max_age is None: raise ValueError("max_age is required when freshness evidence is mandatory")

@dataclass(frozen=True, slots=True)
class ComparisonResult:
    status: ComparisonStatus
    issues: tuple[ComparisonIssue,...] = ()
    left_venue: str = ""
    right_venue: str = ""
    left_provenance_id: Optional[str] = None
    right_provenance_id: Optional[str] = None
    @property
    def equivalent(self) -> bool: return self.status is ComparisonStatus.EQUIVALENT
    @property
    def valid(self) -> bool: return self.status is not ComparisonStatus.REJECTED

def compare(left: CanonicalVenueEvidence, right: CanonicalVenueEvidence, *, policy: Optional[ComparisonPolicy]=None, reference_time: Optional[datetime]=None) -> ComparisonResult:
    """Compare two canonical venue representations deterministically.

    Cross-venue instrument IDs may differ; semantic identity fields govern
    equivalence. Freshness is assessed only against caller-supplied time/policy.
    """
    if not isinstance(left,CanonicalVenueEvidence) or not isinstance(right,CanonicalVenueEvidence):
        return ComparisonResult(ComparisonStatus.REJECTED,(ComparisonIssue(ComparisonCode.INVALID_CANONICAL,"input","both inputs must be CanonicalVenueEvidence"),))
    policy = policy or ComparisonPolicy()
    if policy.max_age is not None and reference_time is None:
        return _result(left,right,[ComparisonIssue(ComparisonCode.REQUIRED_EVIDENCE_MISSING,"freshness","reference_time is required for the supplied freshness policy")])
    issues=[]
    if not left.available or not right.available: issues.append(ComparisonIssue(ComparisonCode.AVAILABILITY_MISMATCH,"availability","one or both venue representations are explicitly unavailable"))
    if type(left.value) is not type(right.value):
        issues.append(ComparisonIssue(ComparisonCode.TYPE_MISMATCH,"canonical_type","canonical representations have different semantic types")); return _result(left,right,issues)
    _identity(left.value,right.value,issues); _payload(left.value,right.value,issues); _temporal(left.value,right.value,policy,reference_time,issues); _check_provenance(left.value,right.value,issues)
    return _result(left,right,issues)

_HARD=frozenset({ComparisonCode.INVALID_CANONICAL,ComparisonCode.TYPE_MISMATCH,ComparisonCode.VENUE_ID_MISSING,ComparisonCode.INSTRUMENT_ID_MISSING,ComparisonCode.PROVENANCE_MISSING})
_INSUFFICIENT=frozenset({ComparisonCode.REQUIRED_EVIDENCE_MISSING,ComparisonCode.FRESHNESS_UNCHECKED})
_INCONSISTENT=frozenset({ComparisonCode.BASE_ASSET_MISMATCH,ComparisonCode.QUOTE_ASSET_MISMATCH,ComparisonCode.MARKET_TYPE_MISMATCH,ComparisonCode.CONTRACT_TYPE_MISMATCH,ComparisonCode.UNIT_MISMATCH,ComparisonCode.MULTIPLIER_MISMATCH,ComparisonCode.TIMEFRAME_MISMATCH,ComparisonCode.TIMESTAMP_MISALIGNMENT,ComparisonCode.LEFT_STALE,ComparisonCode.RIGHT_STALE,ComparisonCode.PRICE_MISMATCH,ComparisonCode.QUANTITY_MISMATCH,ComparisonCode.SIDE_MISMATCH,ComparisonCode.BID_ASK_INVALID,ComparisonCode.ORDERBOOK_MISMATCH,ComparisonCode.CANDLE_MISMATCH,ComparisonCode.DERIVATIVES_MISMATCH,ComparisonCode.AVAILABILITY_MISMATCH})

def _result(left,right,issues):
    if any(x.code in _HARD for x in issues): status=ComparisonStatus.REJECTED
    elif any(x.code in _INCONSISTENT for x in issues): status=ComparisonStatus.INCONSISTENT
    elif any(x.code in _INSUFFICIENT for x in issues): status=ComparisonStatus.INSUFFICIENT_EVIDENCE
    else:
        status=ComparisonStatus.EQUIVALENT; issues=[ComparisonIssue(ComparisonCode.EQUIVALENT,"overall","canonical semantic evidence is equivalent")]
    return ComparisonResult(status,tuple(issues),left.venue_id,right.venue_id,_provenance_id(left.value),_provenance_id(right.value))

def _identity(left,right,issues):
    if not isinstance(left,CanonicalInstrument): return
    if not left.instrument_id or not right.instrument_id: issues.append(ComparisonIssue(ComparisonCode.INSTRUMENT_ID_MISSING,"instrument_id","canonical instrument identity must be explicit"))
    elif left.instrument_id!=right.instrument_id: issues.append(ComparisonIssue(ComparisonCode.INSTRUMENT_ID_MISMATCH,"instrument_id","venue-specific canonical instrument identifiers differ; semantic identity fields govern equivalence"))
    for field,code in (("base_asset",ComparisonCode.BASE_ASSET_MISMATCH),("quote_asset",ComparisonCode.QUOTE_ASSET_MISMATCH),("market_type",ComparisonCode.MARKET_TYPE_MISMATCH),("contract_type",ComparisonCode.CONTRACT_TYPE_MISMATCH),("unit",ComparisonCode.UNIT_MISMATCH)):
        if getattr(left,field)!=getattr(right,field): issues.append(ComparisonIssue(code,field,f"{field} differs: {getattr(left,field)!r} != {getattr(right,field)!r}"))
    if left.contract_multiplier!=right.contract_multiplier: issues.append(ComparisonIssue(ComparisonCode.MULTIPLIER_MISMATCH,"contract_multiplier",f"contract_multiplier differs: {left.contract_multiplier!r} != {right.contract_multiplier!r}"))
    if left.active!=right.active: issues.append(ComparisonIssue(ComparisonCode.AVAILABILITY_MISMATCH,"active",f"instrument active state differs: {left.active!r} != {right.active!r}"))

def _payload(left,right,issues):
    if isinstance(left,CanonicalInstrument): return
    if isinstance(left,CanonicalTrade):
        _eq("price",left.price,right.price,ComparisonCode.PRICE_MISMATCH,issues); _eq("quantity",left.quantity,right.quantity,ComparisonCode.QUANTITY_MISMATCH,issues); _eq("aggressor_side",left.aggressor_side,right.aggressor_side,ComparisonCode.SIDE_MISMATCH,issues); return
    if isinstance(left,CanonicalCandle):
        if left.timeframe!=right.timeframe: issues.append(ComparisonIssue(ComparisonCode.TIMEFRAME_MISMATCH,"timeframe","candle timeframes differ"))
        for f in ("open","high","low","close","volume","quote_volume","trade_count","is_closed"): _eq("candle."+f,getattr(left,f),getattr(right,f),ComparisonCode.CANDLE_MISMATCH,issues)
        if left.open_time!=right.open_time or left.close_time!=right.close_time: issues.append(ComparisonIssue(ComparisonCode.TIMESTAMP_MISALIGNMENT,"candle_window","candle windows differ"))
        return
    if isinstance(left,CanonicalOrderBook):
        if not _book_sane(left) or not _book_sane(right): issues.append(ComparisonIssue(ComparisonCode.BID_ASK_INVALID,"order_book","canonical order-book bid/ask prerequisites are not sane"))
        if left.bids!=right.bids or left.asks!=right.asks: issues.append(ComparisonIssue(ComparisonCode.ORDERBOOK_MISMATCH,"order_book","canonical bid/ask levels differ"))
        return
    if isinstance(left,CanonicalDerivatives):
        for f in ("funding_rate","funding_change","funding_velocity","open_interest","open_interest_delta","basis"): _eq("derivatives."+f,getattr(left,f),getattr(right,f),ComparisonCode.DERIVATIVES_MISMATCH,issues)

def _temporal(left,right,policy,reference_time,issues):
    l,r=_timestamps(left,right)
    if l is None or r is None: issues.append(ComparisonIssue(ComparisonCode.REQUIRED_EVIDENCE_MISSING,"timestamp","canonical timestamp evidence is required")); return
    if l.tzinfo is None or r.tzinfo is None or l.utcoffset()!=timezone.utc.utcoffset(l) or r.utcoffset()!=timezone.utc.utcoffset(r): issues.append(ComparisonIssue(ComparisonCode.INVALID_CANONICAL,"timestamp","timestamps must be timezone-aware UTC")); return
    if policy.max_timestamp_delta is not None and abs(l-r)>policy.max_timestamp_delta: issues.append(ComparisonIssue(ComparisonCode.TIMESTAMP_MISALIGNMENT,"timestamp","event timestamps exceed caller-supplied tolerance"))
    if policy.max_age is None:
        issues.append(ComparisonIssue(ComparisonCode.REQUIRED_EVIDENCE_MISSING if policy.require_freshness_evidence else ComparisonCode.FRESHNESS_UNCHECKED,"freshness","freshness was not assessed because no caller-supplied max_age policy was provided")); return
    if reference_time is None: issues.append(ComparisonIssue(ComparisonCode.REQUIRED_EVIDENCE_MISSING,"freshness","reference_time is required for freshness assessment")); return
    if reference_time.tzinfo is None or reference_time.utcoffset()!=timezone.utc.utcoffset(reference_time): issues.append(ComparisonIssue(ComparisonCode.INVALID_CANONICAL,"reference_time","reference_time must be UTC")); return
    if l>reference_time or r>reference_time: issues.append(ComparisonIssue(ComparisonCode.TIMESTAMP_MISALIGNMENT,"freshness","future-dated evidence cannot be treated as fresh historical evidence")); return
    if reference_time-l>policy.max_age: issues.append(ComparisonIssue(ComparisonCode.LEFT_STALE,"freshness","left evidence exceeds caller-supplied max_age"))
    if reference_time-r>policy.max_age: issues.append(ComparisonIssue(ComparisonCode.RIGHT_STALE,"freshness","right evidence exceeds caller-supplied max_age"))

def _check_provenance(left,right,issues):
    if not _provenance_id(left) or not _provenance_id(right): issues.append(ComparisonIssue(ComparisonCode.PROVENANCE_MISSING,"provenance","both canonical values must carry provenance"))

def _provenance_id(value):
    p=getattr(value,"provenance_id",None); return p if isinstance(p,str) and p else None

def _timestamps(left,right):
    def one(v):
        if isinstance(v,CanonicalInstrument): return v.as_of
        if isinstance(v,CanonicalCandle): return v.open_time
        if isinstance(v,(CanonicalTrade,CanonicalOrderBook,CanonicalDerivatives)): return v.timestamp
        return None
    return one(left),one(right)

def _eq(field,left,right,code,issues):
    if left!=right: issues.append(ComparisonIssue(code,field,f"{field} differs: {left!r} != {right!r}"))

def _book_sane(book):
    return bool(book.bids or book.asks) and (not book.bids or not book.asks or book.bids[0][0]<book.asks[0][0])
