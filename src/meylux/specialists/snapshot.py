"""Phase-5 deterministic Stage-1 Input Snapshot builder.

The builder consumes already-persisted authoritative records. It performs no I/O,
provider access, wall-clock reads, repair, interpolation, substitution, or
specialist execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping

from contracts.specialist import (
    EvidenceRef,
    FactStatus,
    InputSnapshot,
    SnapshotFact,
    _no_specialist_dependency,
    _normalise,
)


def _freeze(value: Any) -> Any:
    """Recursively detach supported SnapshotRecord content into read-only containers."""
    if isinstance(value, Mapping):
        from types import MappingProxyType
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return value


class SnapshotBuildError(ValueError):
    """Authoritative persisted input cannot be safely represented in a Snapshot."""


class LookaheadFactError(SnapshotBuildError):
    """A fact's knowledge boundary is after the explicit snapshot as_of."""


class ContradictoryFactError(SnapshotBuildError):
    """Same logical fact identity was supplied with different content."""


class AmbiguousFactError(SnapshotBuildError):
    """A logical fact has multiple non-identical authoritative identities."""


class FactReason(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT = "INSUFFICIENT"
    INVALID = "INVALID"
    STALE = "STALE"
    CONTRADICTORY = "CONTRADICTORY"
    MISSING = "MISSING"


class USR03Disposition(str, Enum):
    AVAILABLE_PERSISTED = "AVAILABLE_PERSISTED"
    PRQ_DELIVERED = "PRQ_DELIVERED"
    UNAVAILABLE_DISPOSITIONED = "UNAVAILABLE_DISPOSITIONED"


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    fact_id: str
    status: FactStatus
    value: Any
    event_time: datetime
    knowledge_time: datetime
    evidence_refs: tuple[EvidenceRef, ...]
    reason: str | None
    metadata: Mapping[str, Any]

    def __post_init__(self):
        try:
            status = self.status if isinstance(self.status, FactStatus) else FactStatus(self.status)
        except (TypeError, ValueError) as exc:
            raise SnapshotBuildError(f"unsupported fact status: {self.status!r}") from exc
        if not isinstance(self.fact_id, str) or not self.fact_id.strip():
            raise SnapshotBuildError("fact_id must be a non-empty string")
        if self.fact_id != self.fact_id.strip():
            raise SnapshotBuildError("fact_id must not contain leading/trailing whitespace")
        for value, field in ((self.event_time, "event_time"), (self.knowledge_time, "knowledge_time")):
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
                raise SnapshotBuildError(f"{field} must be an explicit timezone-aware UTC datetime")
        if self.knowledge_time is None:
            raise SnapshotBuildError("knowledge_time is mandatory for SnapshotRecord")
        if not isinstance(self.metadata, Mapping):
            raise SnapshotBuildError("metadata must be a mapping")
        missing_metadata = tuple(name for name in InputSnapshotBuilder.REQUIRED_METADATA_FIELDS if name not in self.metadata)
        if missing_metadata:
            raise SnapshotBuildError(f"authoritative record metadata missing {missing_metadata}")
        if self.metadata["record_id"] != self.fact_id:
            raise SnapshotBuildError("metadata.record_id must match fact_id")
        if self.metadata["event_time"] != self.event_time:
            raise SnapshotBuildError("metadata.event_time must equal the explicit record event_time")
        if self.metadata["knowledge_time"] != self.knowledge_time:
            raise SnapshotBuildError("metadata.knowledge_time must equal the explicit record knowledge_time")
        identity_hash = self.metadata["identity_hash"]
        if not isinstance(identity_hash, str) or len(identity_hash) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in identity_hash):
            raise SnapshotBuildError("metadata.identity_hash must be a 64-character hexadecimal SHA-256 value")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise SnapshotBuildError("authoritative Snapshot fact requires at least one structured EvidenceRef")
        refs = tuple(self.evidence_refs)
        if any(not isinstance(ref, EvidenceRef) for ref in refs):
            raise SnapshotBuildError("evidence_refs must contain EvidenceRef values")
        for ref in refs:
            required = (ref.source_family, ref.record_id, ref.identity_hash, ref.event_time, ref.knowledge_time, ref.timeframe, ref.venue)
            if any(value is None for value in required):
                raise SnapshotBuildError(
                    "P5-002 EvidenceRef is incomplete: source_family, record_id, identity_hash, "
                    "event_time, knowledge_time, timeframe and venue are required"
                )
            if ref.identity_hash != identity_hash:
                raise SnapshotBuildError("EvidenceRef identity_hash must match the authoritative record identity_hash")
            if ref.record_id != self.metadata["record_id"]:
                raise SnapshotBuildError("EvidenceRef record_id must match metadata.record_id")
            if ref.event_time != self.event_time:
                raise SnapshotBuildError("EvidenceRef event_time must match record event_time")
            if ref.knowledge_time != self.knowledge_time:
                raise SnapshotBuildError("EvidenceRef knowledge_time must match record knowledge_time")
            if ref.timeframe != self.metadata["timeframe"]:
                raise SnapshotBuildError("EvidenceRef timeframe must match metadata.timeframe")
            if ref.venue != self.metadata["venue"]:
                raise SnapshotBuildError("EvidenceRef venue must match metadata.venue")
        _no_specialist_dependency(self.value)
        _normalise(self.value)
        _no_specialist_dependency(self.metadata)
        _normalise(self.metadata)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "evidence_refs", tuple(sorted(refs, key=lambda r: r.evidence_id)))
        object.__setattr__(self, "reason", self.reason.strip() if isinstance(self.reason, str) else self.reason)
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if status is not FactStatus.VALID and (not isinstance(self.reason, str) or not self.reason.strip()):
            raise SnapshotBuildError("non-VALID authoritative records require an explicit reason")

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "SnapshotRecord":
        if not isinstance(record, Mapping):
            raise TypeError("authoritative record must be a mapping")
        _no_specialist_dependency(record)

        required = ("fact_id", "status", "event_time", "knowledge_time", "evidence_refs", "metadata")
        missing = tuple(name for name in required if name not in record)
        if missing:
            raise SnapshotBuildError(f"malformed authoritative record: missing {missing}")

        fact_id = record["fact_id"]
        if not isinstance(fact_id, str) or not fact_id.strip():
            raise SnapshotBuildError("fact_id must be a non-empty string")

        try:
            status = record["status"] if isinstance(record["status"], FactStatus) else FactStatus(record["status"])
        except (TypeError, ValueError) as exc:
            raise SnapshotBuildError(f"unsupported fact status: {record['status']!r}") from exc

        event_time = record["event_time"]
        knowledge_time = record["knowledge_time"]
        for value, field in ((event_time, "event_time"), (knowledge_time, "knowledge_time")):
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
                raise SnapshotBuildError(f"{field} must be an explicit timezone-aware UTC datetime")

        reason = record.get("reason")
        if status is not FactStatus.VALID and (not isinstance(reason, str) or not reason.strip()):
            raise SnapshotBuildError("non-VALID authoritative records require an explicit reason")

        metadata = record["metadata"]
        if not isinstance(metadata, Mapping):
            raise SnapshotBuildError("metadata must be a mapping")

        missing_metadata = tuple(name for name in InputSnapshotBuilder.REQUIRED_METADATA_FIELDS if name not in metadata)
        if missing_metadata:
            raise SnapshotBuildError(f"authoritative record metadata missing {missing_metadata}")

        if metadata["event_time"] != event_time:
            raise SnapshotBuildError("metadata.event_time must equal the explicit record event_time")
        if metadata["knowledge_time"] != knowledge_time:
            raise SnapshotBuildError("metadata.knowledge_time must equal the explicit record knowledge_time")
        if event_time == knowledge_time:
            # Equality is allowed only as observed upstream data; the builder never derives it.
            pass

        identity_hash = metadata["identity_hash"]
        if not isinstance(identity_hash, str) or len(identity_hash) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in identity_hash):
            raise SnapshotBuildError("metadata.identity_hash must be a 64-character hexadecimal SHA-256 value")

        raw_refs = record["evidence_refs"]
        if not isinstance(raw_refs, (tuple, list)) or not raw_refs:
            raise SnapshotBuildError("authoritative Snapshot fact requires at least one structured EvidenceRef")
        refs: list[EvidenceRef] = []
        for raw_ref in raw_refs:
            if isinstance(raw_ref, EvidenceRef):
                ref = raw_ref
            elif isinstance(raw_ref, Mapping):
                try:
                    ref = EvidenceRef(**raw_ref)
                except (TypeError, ValueError) as exc:
                    raise SnapshotBuildError("invalid structured EvidenceRef") from exc
            else:
                raise SnapshotBuildError("evidence_refs must contain EvidenceRef values or mappings")

            required_ref = {
                "source_family": ref.source_family,
                "record_id": ref.record_id,
                "event_time": ref.event_time,
                "knowledge_time": ref.knowledge_time,
                "timeframe": ref.timeframe,
                "venue": ref.venue,
            }
            if any(value is None for value in required_ref.values()):
                raise SnapshotBuildError(
                    "P5-002 EvidenceRef is incomplete: source_family, record_id, identity_hash, "
                    "event_time, knowledge_time, timeframe and venue are required"
                )
            if ref.identity_hash != identity_hash:
                raise SnapshotBuildError("EvidenceRef identity_hash must match the authoritative record identity_hash")
            if ref.record_id != metadata["record_id"]:
                raise SnapshotBuildError("EvidenceRef record_id must match metadata.record_id")
            if ref.event_time != event_time:
                raise SnapshotBuildError("EvidenceRef event_time must match record event_time")
            if ref.knowledge_time != knowledge_time:
                raise SnapshotBuildError("EvidenceRef knowledge_time must match record knowledge_time")
            if ref.timeframe != metadata["timeframe"]:
                raise SnapshotBuildError("EvidenceRef timeframe must match metadata.timeframe")
            if ref.venue != metadata["venue"]:
                raise SnapshotBuildError("EvidenceRef venue must match metadata.venue")
            refs.append(ref)

        _normalise(record["value"])
        _normalise(metadata)

        return cls(
            fact_id=fact_id.strip(),
            status=status,
            value=record["value"],
            event_time=event_time,
            knowledge_time=knowledge_time,
            evidence_refs=tuple(sorted(refs, key=lambda r: r.evidence_id)),
            reason=reason.strip() if isinstance(reason, str) else reason,
            metadata=dict(metadata),
        )


class InputSnapshotBuilder:
    CONTRACT_VERSION = "1.2.0"
    VERSION = CONTRACT_VERSION
    REQUIRED_METADATA_FIELDS = (
        "symbol", "venue", "product", "timeframe",
        "source_table", "record_id", "identity_hash", "version",
        "event_time", "knowledge_time",
    )
    REQUIRED_EVIDENCE_FIELDS = (
        "source_family", "record_id", "identity_hash",
        "event_time", "knowledge_time", "timeframe", "venue",
    )

    @staticmethod
    def _canonical_record(record: SnapshotRecord) -> dict[str, Any]:
        return {
            "fact_id": record.fact_id,
            "status": record.status.value,
            "value": record.value,
            "event_time": record.event_time,
            "knowledge_time": record.knowledge_time,
            "evidence_refs": [r.as_dict() for r in record.evidence_refs],
            "reason": record.reason,
            "metadata": record.metadata,
        }

    @staticmethod
    def _deduplicate(records: Iterable[SnapshotRecord]) -> tuple[SnapshotRecord, ...]:
        by_fact: dict[str, SnapshotRecord] = {}
        for record in records:
            existing = by_fact.get(record.fact_id)
            if existing is None:
                by_fact[record.fact_id] = record
                continue
            if InputSnapshotBuilder._canonical_record(existing) == InputSnapshotBuilder._canonical_record(record):
                continue
            if existing.metadata.get("identity_hash") == record.metadata.get("identity_hash"):
                raise ContradictoryFactError(
                    f"duplicate fact_id {record.fact_id!r} has the same identity_hash but different content"
                )
            raise AmbiguousFactError(
                f"multiple authoritative records map to fact_id {record.fact_id!r} without an unambiguous identity"
            )
        return tuple(sorted(by_fact.values(), key=lambda r: (r.event_time, r.fact_id, r.metadata["record_id"])))

    @staticmethod
    def _validate_temporal_boundary(records: Iterable[SnapshotRecord], as_of: datetime) -> None:
        for record in records:
            if record.knowledge_time > as_of:
                raise LookaheadFactError(
                    f"fact {record.fact_id!r} has knowledge_time {record.knowledge_time.isoformat()} "
                    f"after snapshot as_of {as_of.isoformat()}"
                )

    @staticmethod
    def _to_snapshot_fact(record: SnapshotRecord) -> SnapshotFact:
        return SnapshotFact(
            fact_id=record.fact_id,
            status=record.status,
            value=record.value,
            knowledge_time=record.knowledge_time,
            evidence_refs=record.evidence_refs,
            reason=record.reason,
            metadata=record.metadata,
        )

    def build(
        self,
        *,
        as_of: datetime,
        records: Iterable[SnapshotRecord | Mapping[str, Any]],
        version: str | None = None,
    ) -> InputSnapshot:
        if not isinstance(as_of, datetime):
            raise TypeError("as_of must be an explicit datetime")
        if as_of.tzinfo is None or as_of.utcoffset() != timezone.utc.utcoffset(as_of):
            raise ValueError("as_of must be timezone-aware UTC")
        if not isinstance(records, Iterable):
            raise TypeError("records must be iterable")

        normalized = tuple(
            item if isinstance(item, SnapshotRecord) else SnapshotRecord.from_mapping(item)
            for item in records
        )
        deduplicated = self._deduplicate(normalized)
        self._validate_temporal_boundary(deduplicated, as_of)
        facts = tuple(self._to_snapshot_fact(item) for item in deduplicated)

        provenance = tuple(
            sorted(
                {ref.evidence_id: ref for fact in facts for ref in fact.evidence_refs}.values(),
                key=lambda ref: ref.evidence_id,
            )
        )
        return InputSnapshot.build(
            as_of=as_of,
            version=version or self.VERSION,
            facts=facts,
            provenance_refs=provenance,
        )

    @staticmethod
    def classify_absence(
        *,
        supported: bool | None,
        available: bool | None,
        sufficient: bool | None = None,
        valid: bool | None = None,
        stale: bool | None = None,
    ) -> tuple[FactStatus, str]:
        if supported is False:
            return FactStatus.UNAVAILABLE, FactReason.UNSUPPORTED.value
        if available is False:
            return FactStatus.UNAVAILABLE, FactReason.UNAVAILABLE.value
        if sufficient is False:
            return FactStatus.INSUFFICIENT_DATA, FactReason.INSUFFICIENT.value
        if valid is False:
            return FactStatus.INVALID, FactReason.INVALID.value
        if stale is True:
            return FactStatus.STALE, FactReason.STALE.value
        return FactStatus.VALID, "VALID"
