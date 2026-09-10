"""Provider-neutral acquisition boundary for Meylux V2.

This module defines transport-facing acquisition semantics only. It does not
validate or normalize market values and performs no I/O, network access,
database access, provider runtime work, or wall-clock reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence


SID = "CTR-P2-001"
VERSION = "1.0.0"


class AcquisitionState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    INVALID = "INVALID"
    DISCONNECTED = "DISCONNECTED"
    RATE_LIMITED = "RATE_LIMITED"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class CapabilityState(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class EventType(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    UPDATE = "UPDATE"
    TRADE = "TRADE"
    ORDER_BOOK = "ORDER_BOOK"
    CANDLE = "CANDLE"
    INSTRUMENT = "INSTRUMENT"
    DERIVATIVES = "DERIVATIVES"


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    provider_id: str
    adapter_id: str
    adapter_version: str

    def __post_init__(self) -> None:
        for value, field in (
            (self.provider_id, "provider_id"),
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    canonical_instrument_id: str
    provider_instrument_id: str

    def __post_init__(self) -> None:
        for value, field in (
            (self.canonical_instrument_id, "canonical_instrument_id"),
            (self.provider_instrument_id, "provider_instrument_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class Provenance:
    provenance_id: str
    provider: ProviderIdentity
    acquisition_method: str

    def __post_init__(self) -> None:
        if not isinstance(self.provenance_id, str) or not self.provenance_id.strip():
            raise ValueError("provenance_id must be a non-empty string")
        if not isinstance(self.acquisition_method, str) or not self.acquisition_method.strip():
            raise ValueError("acquisition_method must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ProviderCapability:
    capability: str
    state: CapabilityState
    detail: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.capability, str) or not self.capability.strip():
            raise ValueError("capability must be a non-empty string")
        if self.detail is not None and not isinstance(self.detail, str):
            raise TypeError("detail must be a string or None")


@dataclass(frozen=True, slots=True)
class ProviderError:
    code: str
    category: str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        for value, field in (
            (self.code, "code"),
            (self.category, "category"),
            (self.message, "message"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be bool")


@dataclass(frozen=True, slots=True)
class AcquisitionEnvelope:
    provider: ProviderIdentity
    instrument: InstrumentIdentity
    provenance: Provenance
    event_type: EventType
    event_time: datetime
    received_at: datetime
    state: AcquisitionState
    payload: Mapping[str, Any]
    source_sequence: Optional[str] = None
    provider_error: Optional[ProviderError] = None
    capability: Optional[ProviderCapability] = None

    def __post_init__(self) -> None:
        _utc(self.event_time, "event_time")
        _utc(self.received_at, "received_at")
        if not isinstance(self.event_type, EventType):
            raise TypeError("event_type must be an EventType")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        object.__setattr__(self, "payload", _freeze(self.payload))
        if not isinstance(self.state, AcquisitionState):
            raise TypeError("state must be an AcquisitionState")
        if self.source_sequence is not None and (
            not isinstance(self.source_sequence, str) or not self.source_sequence
        ):
            raise ValueError("source_sequence must be a non-empty string or None")
        if self.provenance.provider != self.provider:
            raise ValueError("provenance.provider must match provider")

        error_required = {
            AcquisitionState.DEGRADED,
            AcquisitionState.UNAVAILABLE,
            AcquisitionState.STALE,
            AcquisitionState.INVALID,
            AcquisitionState.DISCONNECTED,
            AcquisitionState.RATE_LIMITED,
            AcquisitionState.SEQUENCE_GAP,
            AcquisitionState.INSUFFICIENT_DATA,
        }
        if self.state is AcquisitionState.AVAILABLE and self.provider_error is not None:
            raise ValueError("AVAILABLE acquisition cannot carry provider_error")
        if self.state in error_required and self.provider_error is None:
            raise ValueError(f"{self.state.value} acquisition requires provider_error")

    def canonical_bytes(self) -> bytes:
        """Return stable JSON bytes for the complete envelope representation."""
        return _canonical_json(
            {
                "provider": self.provider,
                "instrument": self.instrument,
                "provenance": self.provenance,
                "event_type": self.event_type.value,
                "event_time": self.event_time,
                "received_at": self.received_at,
                "state": self.state.value,
                "source_sequence": self.source_sequence,
                "payload": self.payload,
                "provider_error": self.provider_error,
                "capability": self.capability,
            }
        )

    def identity_bytes(self) -> bytes:
        """Return stable replay/deduplication identity material.

        Receive time, error detail, and capability state are intentionally
        excluded so retransmission of the same source event keeps its identity.
        Payload remains part of identity when no trustworthy source sequence
        exists and also protects against same-timestamp collisions.
        """
        return _canonical_json(
            {
                "provider_id": self.provider.provider_id,
                "canonical_instrument_id": self.instrument.canonical_instrument_id,
                "provider_instrument_id": self.instrument.provider_instrument_id,
                "event_type": self.event_type.value,
                "event_time": self.event_time,
                "source_sequence": self.source_sequence,
                "payload": self.payload,
            }
        )

    @property
    def event_id(self) -> str:
        return hashlib.sha256(self.identity_bytes()).hexdigest()

    @property
    def deduplication_key(self) -> str:
        return self.event_id


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("payload mapping keys must be strings")
            frozen[key] = _freeze(item)
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (str, int, bool, type(None), Decimal, datetime, Enum)):
        return value
    if isinstance(value, float):
        raise TypeError("binary floating-point values are not allowed")
    raise TypeError(f"unsupported payload type: {type(value).__name__}")


def _canonical_json(value: Any) -> bytes:
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        _utc(value, "datetime")
        return value.isoformat().replace("+00:00", "Z")
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: _normalize(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("payload mapping keys must be strings")
            normalized[key] = _normalize(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal values are not allowed")
        return str(value)
    if isinstance(value, float):
        raise TypeError("binary floating-point values are not allowed")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")
