"""Binance acquisition adapter for Meylux V2 Phase 2 Step 2.

Binance-specific HTTP/WebSocket behavior is isolated here. The adapter emits
only the already-governed provider-neutral ``AcquisitionEnvelope`` and never
performs validation/normalization or persistence.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    CapabilityState,
    EventType,
    InstrumentIdentity,
    ProviderCapability,
    ProviderError,
    ProviderIdentity,
    Provenance,
)
from meylux.acquisition.provider import ProviderAdapter


SID = "STEP-P2-002"
VERSION = "1.0.0"
PROVIDER_ID = "binance"
ADAPTER_ID = "binance-acquisition"
REST_BASE_URL = "https://api.binance.com"
WS_BASE_URL = "wss://stream.binance.com:9443/stream"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded retry policy for provider transport failures."""

    max_attempts: int = 3
    initial_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.initial_backoff_seconds < 0:
            raise ValueError("initial_backoff_seconds must be >= 0")
        if self.max_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= initial_backoff_seconds")

    def delay(self, attempt_number: int) -> float:
        return min(
            self.initial_backoff_seconds * (2 ** max(0, attempt_number - 1)),
            self.max_backoff_seconds,
        )


class BinanceTransportError(RuntimeError):
    """Provider transport failure after the bounded retry policy is exhausted."""


class _BinanceProviderFailure(BinanceTransportError):
    """Internal provider failure carrying canonical acquisition semantics."""

    def __init__(self, state: AcquisitionState, provider_error: ProviderError) -> None:
        super().__init__(provider_error.message)
        self.state = state
        self.provider_error = provider_error


class BinanceAdapter(ProviderAdapter):
    """Provider-isolated Binance market-data adapter."""

    def __init__(
        self,
        *,
        rest_base_url: str = REST_BASE_URL,
        ws_base_url: str = WS_BASE_URL,
        timeout_seconds: float = 10.0,
        retry_policy: RetryPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        async_sleeper: Callable[[float], Any] | None = None,
        http_get: Callable[[str, float], bytes] | None = None,
        websocket_connect: Callable[[str], Any] | None = None,
        logger: Any = None,
    ) -> None:
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
        return ProviderIdentity(
            provider_id=PROVIDER_ID,
            adapter_id=ADAPTER_ID,
            adapter_version=VERSION,
        )

    def capabilities(self) -> Sequence[ProviderCapability]:
        return (
            ProviderCapability("REST_BOOTSTRAP", CapabilityState.SUPPORTED),
            ProviderCapability("LIVE_STREAM", CapabilityState.SUPPORTED),
            ProviderCapability("INSTRUMENT_METADATA", CapabilityState.SUPPORTED),
            ProviderCapability("ORDER_BOOK_SNAPSHOT", CapabilityState.SUPPORTED),
            ProviderCapability("TRADES", CapabilityState.SUPPORTED),
            ProviderCapability("CANDLES", CapabilityState.SUPPORTED),
        )

    def fetch_exchange_info(self, symbol: str | None = None) -> AcquisitionEnvelope:
        """Fetch Binance spot exchange metadata as raw/staging acquisition."""
        symbol = self._normalize_symbol(symbol) if symbol is not None else None
        params = {"symbol": symbol} if symbol else {}
        try:
            payload = self._request_json("/api/v3/exchangeInfo", params)
        except _BinanceProviderFailure as exc:
            return self._failure_envelope(
                instrument=self._exchange_info_instrument(symbol),
                event_type=EventType.INSTRUMENT,
                failure=exc,
            )
        now = self._utc_now()
        provider_symbol = symbol or "*"
        canonical_symbol = symbol or "BINANCE:EXCHANGE_INFO"
        return self._envelope(
            instrument=InstrumentIdentity(canonical_symbol, provider_symbol),
            event_type=EventType.INSTRUMENT,
            event_time=now,
            received_at=now,
            payload=payload,
            state=AcquisitionState.AVAILABLE,
        )

    def fetch_order_book(self, symbol: str, *, limit: int = 100) -> AcquisitionEnvelope:
        """Fetch a Binance order-book snapshot without normalizing its values."""
        symbol = self._normalize_symbol(symbol)
        if limit not in {5, 10, 20, 50, 100, 500, 1000, 5000}:
            raise ValueError("limit must be one of Binance's supported depth limits")
        try:
            payload = self._request_json("/api/v3/depth", {"symbol": symbol, "limit": limit})
        except _BinanceProviderFailure as exc:
            return self._failure_envelope(
                instrument=self._instrument(symbol),
                event_type=EventType.ORDER_BOOK,
                failure=exc,
            )
        now = self._utc_now()
        event_ms = payload.get("E") or payload.get("T")
        event_time = self._epoch_ms(event_ms) if event_ms is not None else now
        sequence = payload.get("lastUpdateId")
        return self._envelope(
            instrument=self._instrument(symbol),
            event_type=EventType.ORDER_BOOK,
            event_time=event_time,
            received_at=now,
            payload=payload,
            source_sequence=str(sequence) if sequence is not None else None,
            state=AcquisitionState.AVAILABLE,
        )

    def fetch_trades(self, symbol: str, *, limit: int = 100) -> tuple[AcquisitionEnvelope, ...]:
        """Fetch recent Binance trades as provider-neutral trade envelopes."""
        symbol = self._normalize_symbol(symbol)
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        try:
            rows = self._request_json("/api/v3/trades", {"symbol": symbol, "limit": limit})
        except _BinanceProviderFailure as exc:
            return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.TRADE, failure=exc),)
        if not isinstance(rows, list):
            failure = _BinanceProviderFailure(
                AcquisitionState.INVALID,
                ProviderError("BINANCE_INVALID_TRADES_PAYLOAD", "INVALID_PAYLOAD", "Binance trades response was not a list"),
            )
            return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.TRADE, failure=failure),)
        received = self._utc_now()
        envelopes: list[AcquisitionEnvelope] = []
        for row in rows:
            if not isinstance(row, Mapping):
                failure = _BinanceProviderFailure(
                    AcquisitionState.INVALID,
                    ProviderError("BINANCE_INVALID_TRADES_PAYLOAD", "INVALID_PAYLOAD", "Binance trade row is malformed"),
                )
                return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.TRADE, failure=failure),)
            envelopes.append(
                self._envelope(
                    instrument=self._instrument(symbol),
                    event_type=EventType.TRADE,
                    event_time=self._epoch_ms(row.get("time")) if row.get("time") is not None else received,
                    received_at=received,
                    payload=row,
                    source_sequence=str(row["id"]) if row.get("id") is not None else None,
                    state=AcquisitionState.AVAILABLE,
                )
            )
        return tuple(envelopes)

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 500,
    ) -> tuple[AcquisitionEnvelope, ...]:
        """Fetch Binance candlesticks without assigning Phase 3 semantics."""
        symbol = self._normalize_symbol(symbol)
        if not interval or any(ch.isspace() for ch in interval):
            raise ValueError("interval must be a non-empty Binance interval")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        try:
            rows = self._request_json(
                "/api/v3/klines",
                {"symbol": symbol, "interval": interval, "limit": limit},
            )
        except _BinanceProviderFailure as exc:
            return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.CANDLE, failure=exc),)
        if not isinstance(rows, list):
            failure = _BinanceProviderFailure(
                AcquisitionState.INVALID,
                ProviderError("BINANCE_INVALID_KLINES_PAYLOAD", "INVALID_PAYLOAD", "Binance klines response was not a list"),
            )
            return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.CANDLE, failure=failure),)
        received = self._utc_now()
        envelopes: list[AcquisitionEnvelope] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                failure = _BinanceProviderFailure(
                    AcquisitionState.INVALID,
                    ProviderError("BINANCE_INVALID_KLINE_ROW", "INVALID_PAYLOAD", "Binance kline row is malformed"),
                )
                return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.CANDLE, failure=failure),)
            open_time = row[0]
            try:
                event_time = self._epoch_ms(open_time)
            except BinanceTransportError:
                failure = _BinanceProviderFailure(
                    AcquisitionState.INVALID,
                    ProviderError("BINANCE_INVALID_KLINE_TIMESTAMP", "INVALID_PAYLOAD", "Binance kline timestamp is invalid"),
                )
                return (self._failure_envelope(instrument=self._instrument(symbol), event_type=EventType.CANDLE, failure=failure),)
            envelopes.append(
                self._envelope(
                    instrument=self._instrument(symbol),
                    event_type=EventType.CANDLE,
                    event_time=event_time,
                    received_at=received,
                    payload=row,
                    source_sequence=str(open_time),
                    state=AcquisitionState.AVAILABLE,
                )
            )
        return tuple(envelopes)

    def bootstrap(self, symbol: str, *, depth_limit: int = 100) -> tuple[AcquisitionEnvelope, AcquisitionEnvelope]:
        """Acquire exchange metadata and an order-book snapshot for one symbol."""
        info = self.fetch_exchange_info(symbol)
        depth = self.fetch_order_book(symbol, limit=depth_limit)
        if info.state is AcquisitionState.AVAILABLE and depth.state is AcquisitionState.AVAILABLE:
            self._telemetry("binance.bootstrap.available", symbol=symbol.upper())
        return info, depth

    async def stream(
        self,
        symbols: Sequence[str],
        *,
        streams: Sequence[str] = ("trade", "depth", "kline_1m"),
        max_messages: int | None = None,
        max_reconnects: int = 3,
    ) -> AsyncIterator[AcquisitionEnvelope]:
        """Yield live Binance market-stream events with bounded reconnects.

        ``max_reconnects`` is a hard upper bound for a single invocation; a
        caller must explicitly invoke ``stream`` again to start another cycle.
        Both exceptional and clean connection termination consume one reconnect
        attempt, so no disconnect path can bypass the configured bound.
        """
        if not symbols:
            raise ValueError("symbols must not be empty")
        if max_reconnects < 0:
            raise ValueError("max_reconnects must be >= 0")
        normalized_symbols = tuple(self._normalize_symbol(s).lower() for s in symbols)
        stream_names = tuple(self._stream_name(symbol, stream) for symbol in normalized_symbols for stream in streams)
        if not stream_names:
            raise ValueError("streams must not be empty")
        if len(stream_names) > 1024:
            raise ValueError("Binance stream count must not exceed 1024")
        url = f"{self._ws_base_url}?{urlencode({'streams': '/'.join(stream_names)})}"
        reconnects = 0
        messages = 0
        while True:
            try:
                async with self._websocket_connect(url) as websocket:
                    self._telemetry("binance.stream.connected", stream_count=len(stream_names))
                    async for raw_message in websocket:
                        envelope = self.parse_stream_message(raw_message)
                        if envelope is None:
                            continue
                        messages += 1
                        yield envelope
                        if max_messages is not None and messages >= max_messages:
                            self._telemetry("binance.stream.stopped", reason="message_limit", messages=messages)
                            return
                self._telemetry("binance.stream.disconnected", reconnect=reconnects + 1)
                reconnects += 1
                if reconnects > max_reconnects:
                    failure = _BinanceProviderFailure(
                        AcquisitionState.DISCONNECTED,
                        ProviderError(
                            "BINANCE_RECONNECT_EXHAUSTED",
                            "DISCONNECTED",
                            "Binance WebSocket connection terminated and reconnect limit was exhausted",
                            retryable=False,
                        ),
                    )
                    self._telemetry("binance.stream.stopped", reason="reconnect_exhausted", reconnects=reconnects)
                    yield self._failure_envelope(
                        instrument=self._instrument(normalized_symbols[0].upper()),
                        event_type=EventType.UPDATE,
                        failure=failure,
                    )
                    return
                self._telemetry("binance.stream.reconnect", attempt=reconnects)
                await self._async_sleeper(self._retry_policy.delay(reconnects))
            except asyncio.CancelledError:
                self._telemetry("binance.stream.cancelled")
                raise
            except Exception as exc:
                self._telemetry(
                    "binance.stream.error",
                    error_type=type(exc).__name__,
                    reconnect=reconnects,
                )
                reconnects += 1
                if reconnects > max_reconnects:
                    failure = _BinanceProviderFailure(
                        AcquisitionState.DISCONNECTED,
                        ProviderError(
                            "BINANCE_RECONNECT_EXHAUSTED",
                            "DISCONNECTED",
                            "Binance WebSocket failure and reconnect limit was exhausted",
                            retryable=False,
                        ),
                    )
                    self._telemetry("binance.stream.stopped", reason="reconnect_exhausted", reconnects=reconnects)
                    yield self._failure_envelope(
                        instrument=self._instrument(normalized_symbols[0].upper()),
                        event_type=EventType.UPDATE,
                        failure=failure,
                    )
                    return
                self._telemetry("binance.stream.reconnect", attempt=reconnects)
                await self._async_sleeper(self._retry_policy.delay(reconnects))

    def parse_stream_message(self, raw_message: str | bytes) -> AcquisitionEnvelope | None:
        """Map a Binance raw/combined stream message into AcquisitionEnvelope."""
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8")
        try:
            message = json.loads(raw_message)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _BinanceProviderFailure(
                AcquisitionState.INVALID,
                ProviderError("BINANCE_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "Binance stream message is not valid JSON"),
            ) from exc
        if not isinstance(message, Mapping):
            raise _BinanceProviderFailure(
                AcquisitionState.INVALID,
                ProviderError("BINANCE_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "Binance stream message must be a JSON object"),
            )
        data = message.get("data", message)
        if not isinstance(data, Mapping):
            raise _BinanceProviderFailure(
                AcquisitionState.INVALID,
                ProviderError("BINANCE_INVALID_STREAM_PAYLOAD", "INVALID_PAYLOAD", "Binance stream data must be a JSON object"),
            )
        event = data.get("e")
        symbol = data.get("s")
        if not isinstance(event, str) or not isinstance(symbol, str):
            return None
        symbol = self._normalize_symbol(symbol)
        event_time = self._epoch_ms(data.get("E")) if data.get("E") is not None else self._utc_now()
        sequence = self._sequence_for_stream_event(event, data)
        event_type = {
            "trade": EventType.TRADE,
            "aggTrade": EventType.TRADE,
            "depthUpdate": EventType.ORDER_BOOK,
            "kline": EventType.CANDLE,
            "bookTicker": EventType.UPDATE,
        }.get(event, EventType.UPDATE)
        return self._envelope(
            instrument=self._instrument(symbol),
            event_type=event_type,
            event_time=event_time,
            received_at=self._utc_now(),
            payload=data,
            source_sequence=sequence,
            state=AcquisitionState.AVAILABLE,
        )

    def _request_json(self, path: str, params: Mapping[str, Any]) -> Any:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self._rest_base_url}{path}{'?' + query if query else ''}"
        last_error: Exception | None = None
        failure_state = AcquisitionState.UNAVAILABLE
        failure_code = "BINANCE_TRANSPORT_FAILURE"
        failure_category = "TRANSPORT"
        retryable_failure = True
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                raw = self._http_get(url, self._timeout_seconds)
                try:
                    return json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise _BinanceProviderFailure(
                        AcquisitionState.INVALID,
                        ProviderError("BINANCE_INVALID_REST_PAYLOAD", "INVALID_PAYLOAD", "Binance REST response is not valid JSON"),
                    ) from exc
            except _BinanceProviderFailure:
                raise
            except HTTPError as exc:
                last_error = exc
                if exc.code in {418, 429}:
                    failure_state = AcquisitionState.RATE_LIMITED
                    failure_code = f"BINANCE_HTTP_{exc.code}"
                    failure_category = "RATE_LIMIT"
                    retryable_failure = True
                elif 500 <= exc.code <= 599:
                    failure_state = AcquisitionState.UNAVAILABLE
                    failure_code = f"BINANCE_HTTP_{exc.code}"
                    failure_category = "SERVER_ERROR"
                    retryable_failure = True
                else:
                    failure_state = AcquisitionState.INVALID
                    failure_code = f"BINANCE_HTTP_{exc.code}"
                    failure_category = "HTTP_ERROR"
                    retryable_failure = False
                if not retryable_failure or attempt >= self._retry_policy.max_attempts:
                    break
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                failure_state = AcquisitionState.UNAVAILABLE
                failure_code = "BINANCE_TRANSPORT_FAILURE"
                failure_category = "TRANSPORT"
                retryable_failure = True
                if attempt >= self._retry_policy.max_attempts:
                    break
            self._telemetry("binance.rest.retry", attempt=attempt)
            self._sleeper(self._retry_policy.delay(attempt))
        message = f"Binance REST acquisition failed after bounded retry policy: {type(last_error).__name__ if last_error else 'unknown'}"
        raise _BinanceProviderFailure(
            failure_state,
            ProviderError(failure_code, failure_category, message, retryable=retryable_failure),
        ) from last_error

    @staticmethod
    def _default_http_get(url: str, timeout: float) -> bytes:
        request = Request(url, method="GET", headers={"Accept": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    @staticmethod
    def _default_websocket_connect(url: str) -> Any:
        try:
            from websockets.asyncio.client import connect
        except ImportError as exc:
            raise RuntimeError("websockets package is required for Binance live-stream acquisition") from exc
        return connect(url, ping_interval=20, ping_timeout=20, max_size=4 * 1024 * 1024)

    def _envelope(
        self,
        *,
        instrument: InstrumentIdentity,
        event_type: EventType,
        event_time: datetime,
        received_at: datetime,
        payload: Mapping[str, Any] | Sequence[Any],
        state: AcquisitionState,
        source_sequence: str | None = None,
        provider_error: ProviderError | None = None,
    ) -> AcquisitionEnvelope:
        if not isinstance(payload, Mapping):
            payload = {"raw": payload}
        return AcquisitionEnvelope(
            provider=self.identity,
            instrument=instrument,
            provenance=Provenance(
                provenance_id=f"{PROVIDER_ID}:{ADAPTER_ID}",
                provider=self.identity,
                acquisition_method="REST" if event_type in {EventType.INSTRUMENT, EventType.ORDER_BOOK} else "STREAM_OR_REST",
            ),
            event_type=event_type,
            event_time=event_time,
            received_at=received_at,
            state=state,
            payload=payload,
            source_sequence=source_sequence,
            provider_error=provider_error,
        )

    def _failure_envelope(
        self,
        *,
        instrument: InstrumentIdentity,
        event_type: EventType,
        failure: _BinanceProviderFailure,
    ) -> AcquisitionEnvelope:
        now = self._utc_now()
        return self._envelope(
            instrument=instrument,
            event_type=event_type,
            event_time=now,
            received_at=now,
            payload={},
            state=failure.state,
            provider_error=failure.provider_error,
        )

    def _telemetry(self, event: str, **fields: Any) -> None:
        if self._logger is None:
            return
        from meylux.observability import Severity, emit
        emit(self._logger, Severity.INFO, event, provider=PROVIDER_ID, adapter=ADAPTER_ID, **fields)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        normalized = symbol.strip().upper()
        if any(ch.isspace() for ch in normalized):
            raise ValueError("symbol must not contain whitespace")
        return normalized

    @staticmethod
    def _instrument(symbol: str) -> InstrumentIdentity:
        return InstrumentIdentity(
            canonical_instrument_id=f"BINANCE:{symbol}",
            provider_instrument_id=symbol,
        )

    @staticmethod
    def _exchange_info_instrument(symbol: str | None) -> InstrumentIdentity:
        provider_symbol = symbol or "*"
        canonical_symbol = symbol or "BINANCE:EXCHANGE_INFO"
        return InstrumentIdentity(canonical_symbol, provider_symbol)

    @staticmethod
    def _epoch_ms(value: Any) -> datetime:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise BinanceTransportError("Binance timestamp must be a non-negative integer milliseconds value")
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)

    @staticmethod
    def _stream_name(symbol: str, stream: str) -> str:
        if not isinstance(stream, str) or not stream.strip():
            raise ValueError("stream must be a non-empty string")
        normalized = stream.strip().lower()
        if "@" in normalized or any(ch.isspace() for ch in normalized):
            raise ValueError("stream must be a Binance stream suffix without '@'")
        return f"{symbol}@{normalized}"

    @staticmethod
    def _sequence_for_stream_event(event: str, data: Mapping[str, Any]) -> str | None:
        if event == "trade" and data.get("t") is not None:
            return str(data["t"])
        if event == "aggTrade" and data.get("a") is not None:
            return str(data["a"])
        if event == "depthUpdate":
            if data.get("u") is not None:
                return str(data["u"])
            if data.get("U") is not None:
                return str(data["U"])
        if event == "kline" and isinstance(data.get("k"), Mapping):
            kline = data["k"]
            if kline.get("L") is not None:
                return str(kline["L"])
            if kline.get("t") is not None:
                return str(kline["t"])
        return None

    def _utc_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("adapter clock must return timezone-aware datetime")
        return value.astimezone(timezone.utc)
