from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType
from contracts.canonical.orderbook import CanonicalOrderBook

SID = "A-P2-MEXC-ORDERBOOK"
VERSION = "1.0.0"


class ReconstructionStatus(str, Enum):
    READY = "READY"
    STALE_IGNORED = "STALE_IGNORED"
    DUPLICATE_IGNORED = "DUPLICATE_IGNORED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    RECOVERED = "RECOVERED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    DISCONNECTED = "DISCONNECTED"


@dataclass(frozen=True, slots=True)
class ReconstructionResult:
    status: ReconstructionStatus
    version: int | None
    canonical: CanonicalOrderBook | None = None
    reason: str | None = None
    recovery_attempted: bool = False
    recovery_succeeded: bool = False


@dataclass(frozen=True, slots=True)
class _BookState:
    instrument_id: str
    version: int
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]
    timestamp: datetime
    provenance_id: str
    evidence_event_ids: tuple[str, ...]


class MEXCOrderBookReconstructor:
    """Provider-isolated deterministic MEXC Spot snapshot/depth state machine."""

    def __init__(self, instrument_id: str, *, max_evidence_ids: int = 256) -> None:
        if not isinstance(instrument_id, str) or not instrument_id.strip():
            raise ValueError("instrument_id must be non-empty")
        if isinstance(max_evidence_ids, bool) or not isinstance(max_evidence_ids, int) or max_evidence_ids < 1:
            raise ValueError("max_evidence_ids must be a positive integer")
        self.instrument_id = instrument_id.strip().upper()
        self._max_evidence_ids = max_evidence_ids
        self._state: _BookState | None = None
        self._recovery_required = False
        self._bootstrap_overlap_pending = False
        self._recovery_attempts = 0
        self._last_recovery_reason: str | None = None

    @property
    def version(self) -> int | None:
        return None if self._state is None else self._state.version

    @property
    def ready(self) -> bool:
        return self._state is not None and not self._recovery_required

    @property
    def recovery_attempts(self) -> int:
        return self._recovery_attempts

    @property
    def last_recovery_reason(self) -> str | None:
        return self._last_recovery_reason

    def reset(self) -> None:
        self._state = None
        self._recovery_required = False
        self._bootstrap_overlap_pending = False
        self._last_recovery_reason = None

    def apply_snapshot(self, envelope: AcquisitionEnvelope) -> ReconstructionResult:
        bad = self._validate_envelope(envelope)
        if bad:
            return bad
        if envelope.state is not AcquisitionState.AVAILABLE:
            return ReconstructionResult(ReconstructionStatus.UNAVAILABLE, self.version, reason="snapshot acquisition is not AVAILABLE")
        try:
            version = _version(envelope.payload.get("lastUpdateId"), "lastUpdateId")
            bids = _levels(envelope.payload.get("bids"), "bids", allow_zero=False)
            asks = _levels(envelope.payload.get("asks"), "asks", allow_zero=False)
            symbol = _symbol(envelope.payload)
            if symbol is not None and symbol != self.instrument_id:
                return self._invalidate("snapshot instrument mismatch")
            _validate_book(bids, asks)
        except (TypeError, ValueError, InvalidOperation) as exc:
            return self._invalidate(str(exc))
        self._state = _BookState(
            self.instrument_id, version, bids, asks, _utc(envelope.event_time),
            envelope.provenance.provenance_id, (envelope.event_id,),
        )
        self._recovery_required = False
        self._bootstrap_overlap_pending = True
        self._last_recovery_reason = None
        return ReconstructionResult(ReconstructionStatus.READY, version, self._canonical())

    def apply_depth(self, envelope: AcquisitionEnvelope) -> ReconstructionResult:
        bad = self._validate_envelope(envelope)
        if bad:
            return bad
        if envelope.state is AcquisitionState.DISCONNECTED:
            self._require_recovery("websocket disconnected")
            return ReconstructionResult(ReconstructionStatus.DISCONNECTED, None, reason=self._last_recovery_reason)
        if envelope.state is not AcquisitionState.AVAILABLE:
            return ReconstructionResult(ReconstructionStatus.UNAVAILABLE, self.version, reason="depth acquisition is not AVAILABLE")
        if self._state is None or self._recovery_required:
            return ReconstructionResult(ReconstructionStatus.RECOVERY_REQUIRED, None, reason="no authoritative snapshot state is available")
        try:
            data = _depth_data(envelope.payload)
            symbol = _symbol(envelope.payload)
            if symbol is not None and symbol != self.instrument_id:
                return self._invalidate("depth instrument mismatch")
            start = _version(data.get("fromVersion"), "fromVersion")
            end = _version(data.get("toVersion"), "toVersion")
            if start > end:
                raise ValueError("fromVersion must not exceed toVersion")
            bids = _levels(data.get("bidsList"), "bidsList", allow_zero=True)
            asks = _levels(data.get("asksList"), "asksList", allow_zero=True)
        except (TypeError, ValueError, InvalidOperation) as exc:
            return self._invalidate(str(exc))

        previous = self._state.version
        if end <= previous:
            status = ReconstructionStatus.DUPLICATE_IGNORED if end == previous else ReconstructionStatus.STALE_IGNORED
            return ReconstructionResult(status, previous, self._canonical(), reason="update is older than or equal to established version")
        required = previous + 1
        if start > required:
            self._require_recovery(f"continuity gap: expected {required}, received fromVersion {start}")
            return ReconstructionResult(ReconstructionStatus.RECOVERY_REQUIRED, None, reason=self._last_recovery_reason)
        # MEXC snapshot bootstrap may be followed by an update spanning the snapshot boundary.
        # After the first accepted live update, overlap is not accepted as a substitute for exact continuity.
        if start < required and not self._bootstrap_overlap_pending:
            self._require_recovery("unsupported version overlap after established live state")
            return ReconstructionResult(ReconstructionStatus.RECOVERY_REQUIRED, None, reason=self._last_recovery_reason)

        bid_map, ask_map = dict(self._state.bids), dict(self._state.asks)
        try:
            _apply(bid_map, bids)
            _apply(ask_map, asks)
            next_bids = _sorted(bid_map, True)
            next_asks = _sorted(ask_map, False)
            _validate_book(next_bids, next_asks)
        except (TypeError, ValueError, InvalidOperation) as exc:
            self._require_recovery(f"invalid reconstructed book: {exc}")
            return ReconstructionResult(ReconstructionStatus.RECOVERY_REQUIRED, None, reason=self._last_recovery_reason)

        ids = (self._state.evidence_event_ids + (envelope.event_id,))[-self._max_evidence_ids:]
        self._state = _BookState(
            self.instrument_id, end, next_bids, next_asks, _utc(envelope.event_time),
            envelope.provenance.provenance_id, ids,
        )
        self._bootstrap_overlap_pending = False
        return ReconstructionResult(ReconstructionStatus.READY, end, self._canonical())

    def apply_depth_with_recovery(self, envelope: AcquisitionEnvelope, snapshot_loader: Callable[[], AcquisitionEnvelope]) -> ReconstructionResult:
        if not callable(snapshot_loader):
            raise TypeError("snapshot_loader must be callable")
        result = self.apply_depth(envelope)
        if result.status is not ReconstructionStatus.RECOVERY_REQUIRED:
            return result
        self._recovery_attempts += 1
        try:
            snapshot = snapshot_loader()
        except Exception as exc:
            self._require_recovery(f"recovery snapshot failed: {type(exc).__name__}: {exc}")
            return ReconstructionResult(ReconstructionStatus.UNAVAILABLE, None, reason=self._last_recovery_reason, recovery_attempted=True)
        recovered = self.apply_snapshot(snapshot)
        if recovered.status is ReconstructionStatus.READY:
            return ReconstructionResult(ReconstructionStatus.RECOVERED, recovered.version, recovered.canonical, result.reason, True, True)
        self._require_recovery(f"recovery snapshot rejected: {recovered.reason or recovered.status.value}")
        status = ReconstructionStatus.UNAVAILABLE if recovered.status is ReconstructionStatus.UNAVAILABLE else ReconstructionStatus.INVALID
        return ReconstructionResult(status, None, reason=self._last_recovery_reason, recovery_attempted=True)

    def canonical(self) -> CanonicalOrderBook | None:
        return self._canonical() if self.ready else None

    def evidence_event_ids(self) -> tuple[str, ...]:
        return () if self._state is None else self._state.evidence_event_ids

    def _canonical(self) -> CanonicalOrderBook | None:
        if self._state is None or self._recovery_required:
            return None
        return CanonicalOrderBook(self._state.instrument_id, self._state.timestamp, self._state.bids, self._state.asks, self._state.provenance_id)

    def _require_recovery(self, reason: str) -> None:
        self._state = None
        self._recovery_required = True
        self._bootstrap_overlap_pending = False
        self._last_recovery_reason = reason

    def _invalidate(self, reason: str) -> ReconstructionResult:
        self._require_recovery(reason)
        return ReconstructionResult(ReconstructionStatus.INVALID, None, reason=reason)

    def _validate_envelope(self, envelope: AcquisitionEnvelope) -> ReconstructionResult | None:
        if not isinstance(envelope, AcquisitionEnvelope):
            return ReconstructionResult(ReconstructionStatus.INVALID, self.version, reason="envelope must be AcquisitionEnvelope")
        if envelope.event_type is not EventType.ORDER_BOOK:
            return ReconstructionResult(ReconstructionStatus.INVALID, self.version, reason="envelope event_type must be ORDER_BOOK")
        if envelope.provider.provider_id != "mexc":
            return ReconstructionResult(ReconstructionStatus.INVALID, self.version, reason="provider must be mexc")
        if envelope.instrument.canonical_instrument_id.upper() != self.instrument_id:
            return ReconstructionResult(ReconstructionStatus.INVALID, self.version, reason="provider instrument mismatch")
        if not isinstance(envelope.payload, Mapping):
            return ReconstructionResult(ReconstructionStatus.INVALID, self.version, reason="payload must be a mapping")
        return None


def _version(value: Any, field: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a non-negative integer version")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field} must be non-negative")
        return value
    if not isinstance(value, str) or not value or not value.isascii() or not value.isdigit():
        raise ValueError(f"{field} must be an integer decimal string")
    return int(value)


def _levels(raw: Any, field: str, *, allow_zero: bool) -> tuple[tuple[Decimal, Decimal], ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError(f"{field} must be a sequence")
    out, seen = [], set()
    for index, item in enumerate(raw):
        if isinstance(item, Mapping):
            price_raw, qty_raw = item.get("price"), item.get("quantity")
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)) and len(item) == 2:
            price_raw, qty_raw = item[0], item[1]
        else:
            raise ValueError(f"{field}[{index}] must be a price/quantity pair")
        price, qty = _decimal(price_raw, f"{field}[{index}].price"), _decimal(qty_raw, f"{field}[{index}].quantity")
        if price <= 0 or qty < 0 or (not allow_zero and qty == 0):
            raise ValueError(f"{field}[{index}] has invalid price/quantity")
        if price in seen:
            raise ValueError(f"{field} contains duplicate price {price}")
        seen.add(price)
        out.append((price, qty))
    return tuple(out)


def _apply(book: dict[Decimal, Decimal], updates: Sequence[tuple[Decimal, Decimal]]) -> None:
    for price, qty in updates:
        if qty == 0:
            book.pop(price, None)
        else:
            book[price] = qty


def _sorted(book: Mapping[Decimal, Decimal], descending: bool) -> tuple[tuple[Decimal, Decimal], ...]:
    return tuple(sorted(((p, q) for p, q in book.items() if q > 0), key=lambda x: x[0], reverse=descending))


def _validate_book(bids: tuple[tuple[Decimal, Decimal], ...], asks: tuple[tuple[Decimal, Decimal], ...]) -> None:
    if not bids and not asks:
        raise ValueError("order book must contain at least one level")
    if bids and asks and bids[0][0] >= asks[0][0]:
        raise ValueError("best bid must be lower than best ask")
    for levels, descending in ((bids, True), (asks, False)):
        prices = [p for p, _ in levels]
        if prices != sorted(prices, reverse=descending) or len(prices) != len(set(prices)):
            raise ValueError("order book levels are invalid or non-deterministic")


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field} must be exact Decimal-compatible data")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} is not a valid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def _symbol(payload: Mapping[str, Any]) -> str | None:
    symbol = payload.get("symbol")
    if symbol is None and isinstance(payload.get("data"), Mapping):
        symbol = payload["data"].get("symbol")
    if symbol is None:
        return None
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string when present")
    return symbol.strip().upper()


def _depth_data(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise ValueError("depth payload data must be a mapping")
    if "fromVersion" not in data or "toVersion" not in data:
        raise ValueError("depth payload must contain fromVersion and toVersion")
    return data


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("event_time must be timezone-aware UTC")
    return value
