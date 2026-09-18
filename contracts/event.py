"""Provider-neutral normalized canonical event contract for P3-008."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from contracts.canonical.foundation import canonical_json
from contracts.data_quality import DataQualityState


SID = "STEP-P3-008"
VERSION = "1.0.0"
STREAM = "stream:canonical:market_events"


def _stable(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("event Decimal must be finite")
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(k): _stable(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_stable(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {name: _stable(getattr(value, name)) for name in value.__dataclass_fields__}
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise TypeError(f"unsupported event value type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """Immutable, deterministic event envelope containing canonical semantics only."""

    event_id: str
    record_id: str
    event_type: str
    sequence: int
    event_time: datetime
    quality_state: DataQualityState
    provenance_id: str
    source_record_id: str
    lineage_parent_id: str
    payload: Mapping[str, Any]
    canonical_identity: str
    schema_version: str = VERSION

    def __post_init__(self) -> None:
        for value, field in (
            (self.event_id, "event_id"),
            (self.record_id, "record_id"),
            (self.event_type, "event_type"),
            (self.provenance_id, "provenance_id"),
            (self.source_record_id, "source_record_id"),
            (self.lineage_parent_id, "lineage_parent_id"),
            (self.schema_version, "schema_version"),
            (self.canonical_identity, "canonical_identity"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise ValueError("sequence must be a positive integer")
        if not isinstance(self.event_time, datetime) or self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")
        if self.event_time.utcoffset() != timezone.utc.utcoffset(self.event_time):
            raise ValueError("event_time must use UTC")
        if not isinstance(self.quality_state, DataQualityState):
            raise TypeError("quality_state must be DataQualityState")
        if self.quality_state is not DataQualityState.VALID:
            raise ValueError("only canonical-eligible VALID data may be emitted")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "record_id": self.record_id,
            "event_type": self.event_type,
            "sequence": self.sequence,
            "event_time": self.event_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "quality_state": self.quality_state.value,
            "provenance_id": self.provenance_id,
            "source_record_id": self.source_record_id,
            "lineage_parent_id": self.lineage_parent_id,
            "canonical_identity": self.canonical_identity,
            "payload": _stable(self.payload),
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @property
    def payload_identity(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()
