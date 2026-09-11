"""MEXC public Spot market-data acquisition adapter for Meylux V2 P2-003."""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from contracts.acquisition import (
    AcquisitionEnvelope, AcquisitionState, CapabilityState, EventType,
    InstrumentIdentity, ProviderCapability, ProviderError, ProviderIdentity,
    Provenance,
)
from meylux.acquisition.provider import ProviderAdapter

SID = "STEP-P2-003"
VERSION = "1.1.0"
PROVIDER_ID = "mexc"
ADAPTER_ID = "mexc-acquisition"
REST_BASE_URL = "https://api.mexc.com"
# This is MEXC Spot V3. Futures uses a different service (wss://contract.mexc.com/edge)
# and is intentionally outside this Spot acquisition adapter.
WS_BASE_URL = "wss://wbs-api.mexc.com/ws"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.initial_backoff_seconds < 0:
            raise ValueError("invalid retry policy")
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= initial_backoff_seconds")

    def delay(self, attempt: int) -> float:
        return min(self.initial_backoff_seconds * (2 ** max(0, attempt - 1)), self.max_backoff_seconds)


class MEXCTransportError(RuntimeError):
    pass


class _MEXCProviderFailure(MEXCTransportError):
    def __init__(self, state: AcquisitionState, provider_error: ProviderError) -> None:
        super().__init__(provider_error.message)
        self.state = state
        self.provider_error = provider_error


class _ProtoReader:
    """Small dependency-free protobuf wire decoder for the governed MEXC schemas."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def fields(self):
        while self.pos < len(self.data):
            key = self._varint()
            number, wire = key >> 3, key & 7
            if wire == 0:
                value = self._varint()
            elif wire == 1:
                value = self._take(8)
            elif wire == 2:
                length = self._varint()
                value = self._take(length)
            elif wire == 5:
                value = self._take(4)
            else:
                raise ValueError(f"unsupported protobuf wire type: {wire}")
            yield number, wire, value

    def _varint(self) -> int:
        value = 0
        shift = 0
        while True:
            if self.pos >= len(self.data) or shift > 63:
                raise ValueError("invalid protobuf varint")
            byte = self.data[self.pos]
            self.pos += 1
            value |= (byte & 0x7F) << shift
            if byte < 0x80:
                return value
            shift += 7

    def _take(self, length: int) -> bytes:
        end = self.pos + length
        if length < 0 or end > len(self.data):
            raise ValueError("truncated protobuf field")
        value = self.data[self.pos:end]
        self.pos = end
        return value


def _proto_string(data: bytes) -> str:
    return data.decode("utf-8")


def _decode_item(data: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {}
    names = {1: "price", 2: "quantity", 3: "tradeType", 4: "time", 5: "tradeId"}
    for number, wire, value in _ProtoReader(data).fields():
        name = names.get(number)
        if name is None:
            continue
        if number in {1, 2, 5}:
            result[name] = _proto_string(value)
        elif number == 3:
            result[name] = int(value)
        else:
            result[name] = int(value)
    return result


def _decode_depth_item(data: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, wire, value in _ProtoReader(data).fields():
        if number == 1:
            result["price"] = _proto_string(value)
        elif number == 2:
            result["quantity"] = _proto_string(value)
    return result


def _decode_public_body(field_number: int, data: bytes) -> dict[str, Any]:
    if field_number == 314:
        result: dict[str, Any] = {"dealsList": [], "eventtype": ""}
        for number, wire, value in _ProtoReader(data).fields():
            if number == 1:
                result["dealsList"].append(_decode_item(value))
            elif number == 2:
                result["eventtype"] = _proto_string(value)
        return result
    if field_number == 313:
        result = {"asksList": [], "bidsList": [], "eventtype": "", "fromVersion": "", "toVersion": ""}
        for number, wire, value in _ProtoReader(data).fields():
            if number == 1:
                result["asksList"].append(_decode_depth_item(value))
            elif number == 2:
                result["bidsList"].append(_decode_depth_item(value))
            elif number == 3:
                result["eventtype"] = _proto_string(value)
            elif number == 4:
                result["fromVersion"] = _proto_string(value)
            elif number == 5:
                result["toVersion"] = _proto_string(value)
            elif number == 6:
                result["lastOrderCreateTime"] = int(value)
        return result
    if field_number == 303:
        result = {"asksList": [], "bidsList": [], "eventtype": "", "version": ""}
        for number, wire, value in _ProtoReader(data).fields():
            if number == 1:
                result["asksList"].append(_decode_depth_item(value))
            elif number == 2:
                result["bidsList"].append(_decode_depth_item(value))
            elif number == 3:
                result["eventtype"] = _proto_string(value)
            elif number == 4:
                result["version"] = _proto_string(value)
        return result
    if field_number == 308:
        names = {1: "interval", 2: "windowStart", 3: "openingPrice", 4: "closingPrice", 5: "highestPrice", 6: "lowestPrice", 7: "volume", 8: "amount", 9: "windowEnd"}
        result = {}
        for number, wire, value in _ProtoReader(data).fields():
            name = names.get(number)
            if name is None:
                continue
            result[name] = int(value) if number in {2, 9} else _proto_string(value)
        return result
    raise ValueError(f"unsupported MEXC protobuf body field: {field_number}")


class MEXCAdapter(ProviderAdapter):
    """Provider-isolated public MEXC Spot REST/Protobuf-WebSocket adapter."""

    def __init__(self, *, rest_base_url: str = REST_BASE_URL, ws_base_url: str = WS_BASE_URL,
                 timeout_seconds: float = 10.0, retry_policy: RetryPolicy | None = None,
                 clock: Callable[[], datetime] | None = None,
                 sleeper: Callable[[float], None] | None = None,
                 async_sleeper: Callable[[float], Any] | None = None,
                 http_get: Callable[[str, float], bytes] | None = None,
                 websocket_connect: Callable[[str], Any] | None = None,
                 logger: Any = None) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        self._rest_base_url = rest_base_url.rstrip("/")
        self._ws_base_url = ws_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._retry_policy = retry_policy or RetryPolicy()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._sleeper = sleeper or time.sleep
        self._async_sleeper = async_sleeper or asyncio.sleep
        self._http_get = http_get or self._default_http_get
        self._websocket_connect = websocket_connect or self._default_websocket_connect
        self._logger = logger

    @property
    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(PROVIDER_ID, ADAPTER_ID, VERSION)

    def capabilities(self) -> Sequence[ProviderCapability]:
        return tuple(ProviderCapability(name, CapabilityState.SUPPORTED) for name in (
            "REST_BOOTSTRAP", "LIVE_STREAM", "INSTRUMENT_METADATA", "ORDER_BOOK_SNAPSHOT", "TRADES", "CANDLES"))

    def fetch_exchange_info(self, symbol: str | None = None) -> AcquisitionEnvelope:
        symbol = self._normalize_symbol(symbol) if symbol is not None else None
        try:
            payload = self._request_json("/api/v3/exchangeInfo", {"symbol": symbol} if symbol else {})
        except _MEXCProviderFailure as exc:
            return self._failure(self._instrument(symbol or "EXCHANGE"), EventType.INSTRUMENT, exc)
        now = self._utc_now()
        event_time = self._epoch_ms(payload["serverTime"]) if isinstance(payload, Mapping) and payload.get("serverTime") is not None else now
        return self._envelope(self._instrument(symbol or "EXCHANGE"), EventType.INSTRUMENT, event_time, now, payload if isinstance(payload, Mapping) else {"data": payload}, "REST_EXCHANGE_INFO")

    def fetch_order_book(self, symbol: str, *, limit: int = 100) -> AcquisitionEnvelope:
        symbol = self._normalize_symbol(symbol)
        if not 1 <= limit <= 5000:
            raise ValueError("limit must be between 1 and 5000")
        try:
            payload = self._request_json("/api/v3/depth", {"symbol": symbol, "limit": limit})
        except _MEXCProviderFailure as exc:
            return self._failure(self._instrument(symbol), EventType.ORDER_BOOK, exc)
        if not isinstance(payload, Mapping):
            return self._invalid(self._instrument(symbol), EventType.ORDER_BOOK, "MEXC_INVALID_DEPTH_PAYLOAD", "depth response must be an object")
        now = self._utc_now()
        return self._envelope(self._instrument(symbol), EventType.ORDER_BOOK, now, now, payload, "REST_ORDER_BOOK", self._string_or_none(payload.get("lastUpdateId")))

    def fetch_trades(self, symbol: str, *, limit: int = 500) -> tuple[AcquisitionEnvelope, ...]:
        symbol = self._normalize_symbol(symbol)
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        try:
            rows = self._request_json("/api/v3/trades", {"symbol": symbol, "limit": limit})
        except _MEXCProviderFailure as exc:
            return (self._failure(self._instrument(symbol), EventType.TRADE, exc),)
        if not isinstance(rows, list):
            return (self._invalid(self._instrument(symbol), EventType.TRADE, "MEXC_INVALID_TRADES_PAYLOAD", "trades response must be a list"),)
        received = self._utc_now()
        result = []
        for row in rows:
            if not isinstance(row, Mapping):
                return (self._invalid(self._instrument(symbol), EventType.TRADE, "MEXC_INVALID_TRADE_ROW", "trade row must be an object"),)
            try:
                event_time = self._epoch_ms(row["time"]) if row.get("time") is not None else received
            except MEXCTransportError as exc:
                return (self._invalid(self._instrument(symbol), EventType.TRADE, "MEXC_INVALID_TRADE_TIMESTAMP", str(exc)),)
            result.append(self._envelope(self._instrument(symbol), EventType.TRADE, event_time, received, row, "REST_TRADES", self._string_or_none(row.get("id"))))
        return tuple(result)

    def fetch_klines(self, symbol: str, interval: str, *, limit: int = 500) -> tuple[AcquisitionEnvelope, ...]:
        symbol = self._normalize_symbol(symbol)
        if not interval or any(ch.isspace() for ch in interval):
            raise ValueError("interval must be a non-empty MEXC interval")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        try:
            rows = self._request_json("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        except _MEXCProviderFailure as exc:
            return (self._failure(self._instrument(symbol), EventType.CANDLE, exc),)
        if not isinstance(rows, list):
            return (self._invalid(self._instrument(symbol), EventType.CANDLE, "MEXC_INVALID_KLINES_PAYLOAD", "klines response must be a list"),)
        received = self._utc_now()
        result = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                return (self._invalid(self._instrument(symbol), EventType.CANDLE, "MEXC_INVALID_KLINE_ROW", "kline row must contain at least seven fields"),)
            try:
                event_time = self._epoch_ms(row[0])
            except MEXCTransportError as exc:
                return (self._invalid(self._instrument(symbol), EventType.CANDLE, "MEXC_INVALID_KLINE_TIMESTAMP", str(exc)),)
            result.append(self._envelope(self._instrument(symbol), EventType.CANDLE, event_time, received, {"row": row}, "REST_KLINES", self._string_or_none(row[0])))
        return tuple(result)

    def bootstrap(self, symbol: str, *, depth_limit: int = 100) -> tuple[AcquisitionEnvelope, AcquisitionEnvelope]:
        info, depth = self.fetch_exchange_info(symbol), self.fetch_order_book(symbol, limit=depth_limit)
        if info.state is AcquisitionState.AVAILABLE and depth.state is AcquisitionState.AVAILABLE:
            self._telemetry("mexc.bootstrap.available", symbol=symbol.upper())
        return info, depth

    async def stream(self, symbols: Sequence[str], *, streams: Sequence[str] = ("trade", "depth", "kline_1m"), max_messages: int | None = None, max_reconnects: int = 3) -> AsyncIterator[AcquisitionEnvelope]:
        if not symbols or max_reconnects < 0:
            raise ValueError("symbols must not be empty and max_reconnects must be >= 0")
        normalized = tuple(self._normalize_symbol(s) for s in symbols)
        channels = tuple(self._stream_name(s, stream) for s in normalized for stream in streams)
        if not channels:
            raise ValueError("streams must not be empty")
        if len(channels) > 30:
            raise ValueError("MEXC websocket subscription count must not exceed 30")
        reconnects = messages = 0
        while True:
            try:
                async with self._websocket_connect(self._ws_base_url) as websocket:
                    self._telemetry("mexc.stream.connected", subscription_count=len(channels))
                    await websocket.send(json.dumps({"method": "SUBSCRIPTION", "params": list(channels)}))
                    async for raw in websocket:
                        envelope = self.parse_stream_message(raw)
                        if envelope is None:
                            continue
                        messages += 1
                        yield envelope
                        if max_messages is not None and messages >= max_messages:
                            return
                reconnects += 1
                if reconnects > max_reconnects:
                    yield self._reconnect_failure(normalized[0])
                    return
                await self._async_sleeper(self._retry_policy.delay(reconnects))
            except asyncio.CancelledError:
                raise
            except _MEXCProviderFailure as exc:
                yield self._failure(self._instrument(normalized[0]), EventType.UPDATE, exc)
                return
            except Exception as exc:
                reconnects += 1
                self._telemetry("mexc.stream.error", error_type=type(exc).__name__, reconnect=reconnects)
                if reconnects > max_reconnects:
                    yield self._reconnect_failure(normalized[0])
                    return
                await self._async_sleeper(self._retry_policy.delay(reconnects))

    def parse_stream_message(self, raw_message: str | bytes) -> AcquisitionEnvelope | None:
        if isinstance(raw_message, str):
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError as exc:
                raise _MEXCProviderFailure(AcquisitionState.INVALID, ProviderError("MEXC_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "stream control message is not valid JSON")) from exc
            if isinstance(message, Mapping) and (message.get("msg") == "PONG" or message.get("channel") in {"pong", "PONG"}):
                return None
            # MEXC Spot protobuf subscriptions acknowledge with a JSON control
            # response before the first protobuf market-data frame. This is
            # provider control information, not a market-data payload.
            if (
                isinstance(message, Mapping)
                and "id" in message
                and message.get("code") == 0
                and isinstance(message.get("msg"), str)
                and message.get("msg")
            ):
                return None
            raise _MEXCProviderFailure(AcquisitionState.INVALID, ProviderError("MEXC_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "MEXC market-data stream payload must be protobuf bytes"))
        if not isinstance(raw_message, (bytes, bytearray)):
            raise _MEXCProviderFailure(AcquisitionState.INVALID, ProviderError("MEXC_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "unsupported websocket payload type"))
        try:
            wrapper: dict[str, Any] = {"channel": None, "symbol": None, "createTime": None, "sendTime": None, "body": None, "bodyField": None}
            for number, wire, value in _ProtoReader(bytes(raw_message)).fields():
                if number == 1:
                    wrapper["channel"] = _proto_string(value)
                elif number == 3:
                    wrapper["symbol"] = _proto_string(value)
                elif number == 5:
                    wrapper["createTime"] = int(value)
                elif number == 6:
                    wrapper["sendTime"] = int(value)
                elif number in {303, 308, 313, 314}:
                    wrapper["bodyField"] = number
                    wrapper["body"] = _decode_public_body(number, value)
            channel, symbol = wrapper["channel"], wrapper["symbol"]
            if not isinstance(channel, str) or not isinstance(symbol, str) or wrapper["body"] is None:
                raise ValueError("MEXC protobuf wrapper is missing required market-data fields")
            symbol = self._normalize_symbol(symbol)
            event_type = self._event_type_for_channel(channel)
            body = wrapper["body"]
            event_time = self._epoch_ms(wrapper["createTime"] or wrapper["sendTime"]) if (wrapper["createTime"] or wrapper["sendTime"]) else self._utc_now()
            sequence = self._stream_sequence(body)
            payload = {"channel": channel, "symbol": symbol, "sendtime": wrapper["sendTime"], "data": body}
            return self._envelope(self._instrument(symbol), event_type, event_time, self._utc_now(), payload, "WEBSOCKET_PROTOBUF", sequence)
        except _MEXCProviderFailure:
            raise
        except (ValueError, UnicodeDecodeError, OverflowError) as exc:
            raise _MEXCProviderFailure(AcquisitionState.INVALID, ProviderError("MEXC_INVALID_PROTOBUF", "INVALID_PAYLOAD", str(exc))) from exc

    def _stream_name(self, symbol: str, stream: str) -> str:
        if stream == "trade":
            return f"spot@public.aggre.deals.v3.api.pb@100ms@{symbol}"
        if stream == "depth":
            return f"spot@public.aggre.depth.v3.api.pb@100ms@{symbol}"
        if stream == "kline_1m":
            return f"spot@public.kline.v3.api.pb@{symbol}@Min1"
        raise ValueError(f"unsupported MEXC stream: {stream}")

    @staticmethod
    def _event_type_for_channel(channel: str) -> EventType:
        if ".deals." in channel:
            return EventType.TRADE
        if ".depth." in channel or ".bookTicker." in channel:
            return EventType.ORDER_BOOK
        if ".kline." in channel:
            return EventType.CANDLE
        return EventType.UPDATE

    @staticmethod
    def _stream_sequence(data: Mapping[str, Any]) -> str | None:
        for key in ("toVersion", "version"):
            value = data.get(key)
            if value is not None:
                return str(value)
        deals = data.get("dealsList")
        if isinstance(deals, Sequence) and deals:
            trade_id = deals[-1].get("tradeId") if isinstance(deals[-1], Mapping) else None
            if trade_id is not None:
                return str(trade_id)
        return None

    def _request_json(self, path: str, params: Mapping[str, Any]) -> Any:
        query = {k: v for k, v in params.items() if v is not None}
        url = f"{self._rest_base_url}{path}" + (f"?{urlencode(query)}" if query else "")
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                raw = self._http_get(url, self._timeout_seconds)
                payload = json.loads(raw.decode("utf-8"))
                if isinstance(payload, Mapping) and payload.get("code") not in (None, 0, 200, "0", "200"):
                    raise _MEXCProviderFailure(AcquisitionState.UNAVAILABLE, ProviderError(f"MEXC_API_{payload.get('code')}", "PROVIDER_API", str(payload.get("msg") or "MEXC API error")))
                return payload
            except _MEXCProviderFailure as exc:
                if attempt >= self._retry_policy.max_attempts or not exc.provider_error.retryable:
                    raise
                failure = exc
            except HTTPError as exc:
                state, category, retryable = self._http_failure(exc.code)
                failure = _MEXCProviderFailure(state, ProviderError(f"MEXC_HTTP_{exc.code}", category, f"MEXC HTTP {exc.code}", retryable))
                if not retryable or attempt >= self._retry_policy.max_attempts:
                    raise failure from exc
            except (URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                invalid = isinstance(exc, (UnicodeDecodeError, json.JSONDecodeError))
                failure = _MEXCProviderFailure(AcquisitionState.INVALID if invalid else AcquisitionState.UNAVAILABLE, ProviderError("MEXC_REST_FAILURE", "INVALID_PAYLOAD" if invalid else "TRANSPORT", str(exc), retryable=not invalid))
                if attempt >= self._retry_policy.max_attempts or not failure.provider_error.retryable:
                    raise failure from exc
            self._sleeper(self._retry_policy.delay(attempt))
        raise MEXCTransportError("MEXC request failed")

    @staticmethod
    def _http_failure(status: int) -> tuple[AcquisitionState, str, bool]:
        if status == 429:
            return AcquisitionState.RATE_LIMITED, "RATE_LIMIT", True
        if 500 <= status <= 599:
            return AcquisitionState.DEGRADED, "UPSTREAM_5XX", True
        if 400 <= status <= 499:
            return AcquisitionState.UNAVAILABLE, "HTTP_CLIENT", False
        return AcquisitionState.UNAVAILABLE, "HTTP", False

    @staticmethod
    def _default_http_get(url: str, timeout: float) -> bytes:
        with urlopen(Request(url, headers={"Accept": "application/json", "User-Agent": "Meylux-V2"}), timeout=timeout) as response:
            return response.read()

    @staticmethod
    def _default_websocket_connect(url: str) -> Any:
        try:
            import websockets
        except ImportError as exc:
            raise MEXCTransportError("websockets dependency is required for live MEXC streaming") from exc
        return websockets.connect(url, ping_interval=20)

    def _instrument(self, symbol: str) -> InstrumentIdentity:
        normalized = self._normalize_symbol(symbol)
        return InstrumentIdentity(normalized, normalized)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        normalized = symbol.strip().upper()
        if any(ch.isspace() for ch in normalized):
            raise ValueError("symbol must not contain whitespace")
        return normalized

    def _provenance(self, method: str) -> Provenance:
        return Provenance(f"mexc:{method}", self.identity, method)

    def _envelope(self, instrument: InstrumentIdentity, event_type: EventType, event_time: datetime,
                  received_at: datetime, payload: Mapping[str, Any], method: str,
                  source_sequence: str | None = None) -> AcquisitionEnvelope:
        return AcquisitionEnvelope(self.identity, instrument, self._provenance(method), event_type,
                                   event_time, received_at, AcquisitionState.AVAILABLE, payload, source_sequence)

    def _failure(self, instrument: InstrumentIdentity, event_type: EventType, exc: _MEXCProviderFailure) -> AcquisitionEnvelope:
        return AcquisitionEnvelope(self.identity, instrument, self._provenance("FAILURE"), event_type,
                                   self._utc_now(), self._utc_now(), exc.state, {}, provider_error=exc.provider_error)

    def _invalid(self, instrument: InstrumentIdentity, event_type: EventType, code: str, message: str) -> AcquisitionEnvelope:
        failure = _MEXCProviderFailure(AcquisitionState.INVALID, ProviderError(code, "INVALID_PAYLOAD", message))
        return self._failure(instrument, event_type, failure)

    def _reconnect_failure(self, symbol: str) -> AcquisitionEnvelope:
        failure = _MEXCProviderFailure(AcquisitionState.DISCONNECTED, ProviderError("MEXC_RECONNECT_LIMIT", "TRANSPORT", "MEXC websocket reconnect limit exceeded"))
        return self._failure(self._instrument(symbol), EventType.UPDATE, failure)

    def _epoch_ms(self, value: Any) -> datetime:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MEXCTransportError("MEXC timestamp must be numeric milliseconds")
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)

    @staticmethod
    def _string_or_none(value: Any) -> str | None:
        return None if value is None else str(value)

    def _utc_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise MEXCTransportError("clock must return timezone-aware datetime")
        return value.astimezone(timezone.utc)

    def _telemetry(self, _event: str, **_fields: Any) -> None:
        if self._logger is not None:
            debug = getattr(self._logger, "debug", None)
            if callable(debug):
                debug(_event, extra=_fields)
