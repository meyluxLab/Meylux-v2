"""Deterministic provider-to-canonical normalization boundary for P3-005."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType
from contracts.canonical import (
    CanonicalCandle,
    CanonicalDerivatives,
    CanonicalInstrument,
    CanonicalOrderBook,
    CanonicalTrade,
)
from contracts.canonical.foundation import (
    ValidationCode,
    ValidationIssue,
    ValidationResult,
    ProvenanceRef,
    validate_provenance,
    validate_timestamp,
)

SID = "STEP-P3-005"
VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class NormalizationOutcome:
    """Explicit normalization result; rejected mappings never carry canonical truth."""

    result: ValidationResult
    value: Any = None
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return self.result is ValidationResult.VALID and self.value is not None


def normalize(envelope: AcquisitionEnvelope) -> NormalizationOutcome:
    """Map one AVAILABLE provider envelope into an existing canonical contract."""
    if not isinstance(envelope, AcquisitionEnvelope):
        return _reject("envelope", ValidationCode.INVALID_TYPE, "envelope must be AcquisitionEnvelope")
    if envelope.state is not AcquisitionState.AVAILABLE:
        return _reject("state", ValidationCode.INVALID_VALUE, "non-AVAILABLE acquisition cannot become canonical data")
    provenance_issue = validate_provenance(_provenance(envelope), "provenance")
    if provenance_issue is not None:
        return NormalizationOutcome(ValidationResult.INCOMPLETE, issues=(provenance_issue,))
    try:
        if envelope.event_type is EventType.INSTRUMENT:
            value = _instrument(envelope)
        elif envelope.event_type is EventType.TRADE:
            value = _trade(envelope)
        elif envelope.event_type is EventType.CANDLE:
            value = _candle(envelope)
        elif envelope.event_type is EventType.ORDER_BOOK:
            value = _order_book(envelope)
        elif envelope.event_type is EventType.DERIVATIVES:
            value = _derivatives(envelope)
        else:
            return _reject("event_type", ValidationCode.INVALID_VALUE, "event type has no P3-005 canonical mapping")
        return NormalizationOutcome(ValidationResult.VALID, value=value)
    except _MappingFailure as exc:
        return _reject(exc.field, exc.code, str(exc))
    except (TypeError, ValueError, InvalidOperation) as exc:
        return _reject("payload", ValidationCode.INVALID_VALUE, str(exc))


def _instrument(envelope: AcquisitionEnvelope) -> CanonicalInstrument:
    payload = _record(envelope.payload, "instrument")
    record = _select_symbol(payload, envelope.instrument.provider_instrument_id)
    base = _required_text(record, ("baseAsset", "base_asset", "base"), "base_asset")
    quote = _required_text(record, ("quoteAsset", "quote_asset", "quote"), "quote_asset")
    market_type = _required_text(record, ("marketType", "market_type"), "market_type", default=_spot_market(envelope))
    contract_type = _required_text(record, ("contractType", "contract_type"), "contract_type", default=_spot_market(envelope))
    unit = _required_text(record, ("unit",), "unit", default=base)
    price_precision = _optional_int(record, ("pricePrecision", "price_precision"))
    quantity_precision = _optional_int(record, ("quantityPrecision", "quantity_precision"))
    multiplier = _optional_decimal(record, ("contractMultiplier", "contract_multiplier"))
    active = _active_status(record)
    return CanonicalInstrument(
        instrument_id=envelope.instrument.canonical_instrument_id,
        base_asset=base,
        quote_asset=quote,
        market_type=market_type,
        contract_type=contract_type,
        unit=unit,
        as_of=envelope.event_time,
        price_precision=price_precision,
        quantity_precision=quantity_precision,
        contract_multiplier=multiplier,
        active=active,
        provenance_id=envelope.provenance.provenance_id,
    )


def _trade(envelope: AcquisitionEnvelope) -> CanonicalTrade:
    p = _record(envelope.payload, "trade")
    provider = envelope.provider.provider_id
    if provider == "binance":
        price = _decimal(_pick(p, "p", "price"), "price")
        quantity = _decimal(_pick(p, "q", "qty", "quantity"), "quantity")
        trade_id = _required_text(p, ("t", "id", "tradeId", "trade_id"), "trade_id")
        timestamp = _timestamp(_pick(p, "T", "time", "timestamp"), envelope.event_time, "timestamp")
        quote = _optional_decimal(p, ("Y", "quoteQty", "quote_quantity"))
        side = _binance_aggressor_side(p)
    elif provider == "mexc":
        price = _decimal(_pick(p, "price"), "price")
        quantity = _decimal(_pick(p, "qty", "quantity"), "quantity")
        trade_id = _required_text(p, ("id", "tradeId", "trade_id"), "trade_id")
        timestamp = _timestamp(_pick(p, "time", "timestamp"), envelope.event_time, "timestamp")
        quote = _optional_decimal(p, ("quoteQty", "quote_quantity"))
        side = _optional_mexc_side(p)
    else:
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "provider", "unsupported provider mapping")
    return CanonicalTrade(
        trade_id=trade_id,
        instrument_id=envelope.instrument.canonical_instrument_id,
        timestamp=timestamp,
        price=price,
        quantity=quantity,
        aggressor_side=side,
        quote_quantity=quote,
        provenance_id=envelope.provenance.provenance_id,
    )


def _candle(envelope: AcquisitionEnvelope) -> CanonicalCandle:
    p = _record(envelope.payload, "candle")
    provider = envelope.provider.provider_id
    if provider == "binance":
        if isinstance(p.get("k"), Mapping):
            k = p["k"]
            timeframe = _required_text(k, ("i",), "timeframe")
            open_time = _timestamp(_pick(k, "t"), envelope.event_time, "open_time")
            close_time = _timestamp(_pick(k, "T"), envelope.event_time, "close_time")
            open_v = _decimal(_pick(k, "o"), "open")
            high_v = _decimal(_pick(k, "h"), "high")
            low_v = _decimal(_pick(k, "l"), "low")
            close_v = _decimal(_pick(k, "c"), "close")
            volume = _decimal(_pick(k, "v"), "volume")
            quote = _optional_decimal(k, ("q", "quoteVolume"))
            count = _optional_int(k, ("n", "tradeCount"))
            closed = k.get("x", True)
            if not isinstance(closed, bool):
                raise _MappingFailure(ValidationCode.INVALID_TYPE, "is_closed", "is_closed must be bool")
        else:
            raise _MappingFailure(ValidationCode.REQUIRED_MISSING, "timeframe", "Binance REST kline payload does not carry timeframe context")
    elif provider == "mexc":
        data = p.get("data") if isinstance(p.get("data"), Mapping) else None
        if data is not None and "openingPrice" in data:
            timeframe = _required_text(data, ("interval",), "timeframe")
            open_time = _timestamp(_pick(data, "windowStart"), envelope.event_time, "open_time", unit="seconds")
            close_time = _timestamp(_pick(data, "windowEnd"), envelope.event_time, "close_time", unit="seconds")
            open_v = _decimal(_pick(data, "openingPrice"), "open")
            high_v = _decimal(_pick(data, "highestPrice"), "high")
            low_v = _decimal(_pick(data, "lowestPrice"), "low")
            close_v = _decimal(_pick(data, "closingPrice"), "close")
            volume = _decimal(_pick(data, "volume"), "volume")
            quote = _optional_decimal(data, ("amount", "quoteVolume"))
            count = None
            closed = True
        else:
            raise _MappingFailure(ValidationCode.REQUIRED_MISSING, "timeframe", "MEXC REST kline payload does not carry timeframe context")
    else:
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "provider", "unsupported provider mapping")
    return CanonicalCandle(
        instrument_id=envelope.instrument.canonical_instrument_id,
        timeframe=timeframe,
        open_time=open_time,
        close_time=close_time,
        open=open_v,
        high=high_v,
        low=low_v,
        close=close_v,
        volume=volume,
        quote_volume=quote,
        trade_count=count,
        is_closed=closed,
        provenance_id=envelope.provenance.provenance_id,
    )


def _order_book(envelope: AcquisitionEnvelope) -> CanonicalOrderBook:
    p = _record(envelope.payload, "order_book")
    provider = envelope.provider.provider_id
    if provider == "binance":
        bids = _levels(p.get("b", p.get("bids")), "bids")
        asks = _levels(p.get("a", p.get("asks")), "asks")
    elif provider == "mexc":
        data = p.get("data") if isinstance(p.get("data"), Mapping) else p
        bids = _levels(data.get("b", data.get("bidsList", data.get("bids"))), "bids")
        asks = _levels(data.get("a", data.get("asksList", data.get("asks"))), "asks")
    else:
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "provider", "unsupported provider mapping")
    return CanonicalOrderBook(
        instrument_id=envelope.instrument.canonical_instrument_id,
        timestamp=envelope.event_time,
        bids=tuple(bids),
        asks=tuple(asks),
        provenance_id=envelope.provenance.provenance_id,
    )


def _derivatives(envelope: AcquisitionEnvelope) -> CanonicalDerivatives:
    p = _record(envelope.payload, "derivatives")
    if envelope.provider.provider_id not in {"binance", "mexc"}:
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "provider", "unsupported provider mapping")
    allowed = ("funding_rate", "funding_change", "funding_velocity", "open_interest", "open_interest_delta", "basis")
    if not any(key in p for key in allowed):
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "payload", "provider derivatives payload has no explicitly supported canonical fields")
    return CanonicalDerivatives(
        instrument_id=envelope.instrument.canonical_instrument_id,
        timestamp=envelope.event_time,
        funding_rate=_optional_decimal(p, ("funding_rate",)),
        funding_change=_optional_decimal(p, ("funding_change",)),
        funding_velocity=_optional_decimal(p, ("funding_velocity",)),
        open_interest=_optional_decimal(p, ("open_interest",)),
        open_interest_delta=_optional_decimal(p, ("open_interest_delta",)),
        basis=_optional_decimal(p, ("basis",)),
        provenance_id=envelope.provenance.provenance_id,
    )


def _spot_market(envelope: AcquisitionEnvelope) -> str:
    if envelope.provider.provider_id in {"binance", "mexc"}:
        return "SPOT"
    raise _MappingFailure(ValidationCode.INVALID_VALUE, "provider", "unsupported provider market mapping")


def _binance_aggressor_side(p: Mapping[str, Any]) -> str | None:
    value = p.get("m")
    if value is None:
        value = p.get("isBuyerMaker")
    if value is None:
        return None
    if not isinstance(value, bool):
        raise _MappingFailure(ValidationCode.INVALID_TYPE, "aggressor_side", "Binance buyer-maker flag must be bool")
    return "SELL" if value else "BUY"


def _optional_mexc_side(p: Mapping[str, Any]) -> str | None:
    value = p.get("isBuyerMaker")
    if value is None:
        return None
    if not isinstance(value, bool):
        raise _MappingFailure(ValidationCode.INVALID_TYPE, "aggressor_side", "MEXC buyer-maker flag must be bool")
    return "SELL" if value else "BUY"


def _provenance(envelope: AcquisitionEnvelope) -> ProvenanceRef:
    return ProvenanceRef(envelope.provenance.provenance_id, envelope.provider.provider_id, envelope.provenance.acquisition_method)


def _record(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise _MappingFailure(ValidationCode.INVALID_TYPE, field, f"{field} payload must be mapping")
    return payload


def _select_symbol(payload: Mapping[str, Any], provider_symbol: str) -> Mapping[str, Any]:
    symbols = payload.get("symbols")
    if isinstance(symbols, Sequence) and not isinstance(symbols, (str, bytes)):
        for item in symbols:
            if isinstance(item, Mapping) and str(item.get("symbol", "")).upper() == provider_symbol.upper():
                return item
        raise _MappingFailure(ValidationCode.INVALID_VALUE, "instrument", "provider instrument record not found")
    data = payload.get("data")
    if isinstance(data, Mapping):
        if "symbols" in data:
            return _select_symbol(data, provider_symbol)
        if any(key in data for key in ("baseAsset", "base_asset", "quoteAsset", "quote_asset")):
            return data
    return payload


def _required_text(payload: Mapping[str, Any], keys: tuple[str, ...], field: str, default: str | None = None) -> str:
    value = _pick(payload, *keys, default=default)
    if not isinstance(value, str) or not value.strip():
        raise _MappingFailure(ValidationCode.REQUIRED_MISSING, field, f"{field} is required and must be explicit")
    return value.strip()


def _pick(payload: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    if default is not None:
        return default
    raise _MappingFailure(ValidationCode.REQUIRED_MISSING, keys[0], f"required provider field {keys[0]} is missing")


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        code = ValidationCode.FLOAT_NOT_ALLOWED if isinstance(value, float) else ValidationCode.INVALID_TYPE
        raise _MappingFailure(code, field, f"{field} must be an exact Decimal-compatible value")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, str):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise _MappingFailure(ValidationCode.INVALID_VALUE, field, f"{field} is not a valid decimal") from exc
    elif isinstance(value, int):
        result = Decimal(value)
    else:
        raise _MappingFailure(ValidationCode.INVALID_TYPE, field, f"{field} has unsupported numeric type")
    if not result.is_finite():
        raise _MappingFailure(ValidationCode.NON_FINITE_DECIMAL, field, f"{field} must be finite")
    return result


def _optional_decimal(payload: Mapping[str, Any], keys: tuple[str, ...]) -> Decimal | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return _decimal(payload[key], key)
    return None


def _optional_int(payload: Mapping[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            value = payload[key]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise _MappingFailure(ValidationCode.INVALID_TYPE, key, f"{key} must be a non-negative integer")
            return value
    return None


def _timestamp(value: Any, fallback: datetime, field: str, unit: str = "milliseconds") -> datetime:
    if isinstance(value, datetime):
        try:
            return validate_timestamp(value, field)
        except (TypeError, ValueError) as exc:
            raise _MappingFailure(ValidationCode.TIMESTAMP_INVALID, field, str(exc)) from exc
    if isinstance(value, bool) or not isinstance(value, int):
        raise _MappingFailure(ValidationCode.INVALID_TYPE, field, f"{field} timestamp must be integer or datetime")
    divisor = 1000 if unit == "milliseconds" else 1
    try:
        result = datetime.fromtimestamp(value / divisor, tz=fallback.tzinfo)
        return validate_timestamp(result, field)
    except (OverflowError, OSError, ValueError) as exc:
        raise _MappingFailure(ValidationCode.TIMESTAMP_INVALID, field, str(exc)) from exc


def _levels(raw: Any, side: str) -> list[tuple[Decimal, Decimal]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise _MappingFailure(ValidationCode.REQUIRED_MISSING, side, f"{side} levels are required")
    result = []
    for index, level in enumerate(raw):
        if isinstance(level, Mapping):
            price_raw = level.get("price")
            quantity_raw = level.get("quantity")
        elif isinstance(level, Sequence) and not isinstance(level, (str, bytes)) and len(level) >= 2:
            price_raw, quantity_raw = level[0], level[1]
        else:
            raise _MappingFailure(ValidationCode.INVALID_VALUE, side, f"{side}[{index}] is not a price/quantity pair")
        price = _decimal(price_raw, f"{side}[{index}].price")
        quantity = _decimal(quantity_raw, f"{side}[{index}].quantity")
        if quantity <= 0:
            raise _MappingFailure(ValidationCode.INVALID_VALUE, f"{side}[{index}].quantity", "zero/negative order-book quantity is not canonical snapshot data")
        result.append((price, quantity))
    return result


def _active_status(record: Mapping[str, Any]) -> bool:
    if "active" in record:
        if not isinstance(record["active"], bool):
            raise _MappingFailure(ValidationCode.INVALID_TYPE, "active", "active must be bool")
        return record["active"]
    status = record.get("status")
    if status is None:
        raise _MappingFailure(ValidationCode.REQUIRED_MISSING, "status", "status is required for canonical instrument activity")
    if not isinstance(status, str):
        raise _MappingFailure(ValidationCode.INVALID_TYPE, "status", "status must be string")
    normalized = status.upper()
    if normalized in {"TRADING", "ENABLED", "1", "ACTIVE"}:
        return True
    if normalized in {"BREAK", "HALT", "DISABLED", "0", "INACTIVE"}:
        return False
    raise _MappingFailure(ValidationCode.INVALID_VALUE, "status", f"unsupported provider status: {status}")


def _reject(field: str, code: ValidationCode, message: str) -> NormalizationOutcome:
    return NormalizationOutcome(ValidationResult.REJECTED, issues=(ValidationIssue(code, field, message),))


class _MappingFailure(Exception):
    def __init__(self, code: ValidationCode, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
