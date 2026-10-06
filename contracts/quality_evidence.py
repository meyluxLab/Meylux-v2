"""Authoritative Phase-3 quality/acquisition evidence contract.

The quality-evidence fact is a deterministic classification of one immutable
P2 AcquisitionEnvelope. For this evidence family, the earliest legitimate
knowledge boundary is the acquisition receipt boundary: received_at.

This equality is an explicit P3 semantic rule, not an operational timestamp
substitution: event_time, received_at/observed_at, knowledge_time and
persistence time remain separately represented.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from contracts.acquisition import AcquisitionEnvelope
from contracts.data_quality import DataLifecycleState, DataQualityState
from contracts.quality import QualityAssessment, fingerprint_payload


SOURCE_FAMILY = "P3:QUALITY_EVIDENCE"
SOURCE_TYPE = "meylux.data_quality_evidence"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must be timezone-aware UTC")


def _token(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_context(payload: Mapping[str, Any], *keys: str) -> str | None:
    values = []
    for key in keys:
        if key in payload and payload[key] is not None:
            if not isinstance(payload[key], str) or not payload[key].strip():
                raise ValueError(f"{key} must be a non-empty string when supplied")
            values.append(payload[key].strip())
    if not values:
        return None
    if len(set(values)) != 1:
        raise ValueError(f"conflicting explicit context values: {', '.join(keys)}")
    return values[0]

def _timeframe_context(payload: Mapping[str, Any]) -> str | None:
    """Resolve timeframe from explicit, mutually consistent envelope context.

    Binance candle envelopes carry their interval at k.i; provider-neutral
    adapters may expose timeframe or interval at the payload root. All supplied
    representations are checked together to prevent silently choosing a value
    when authoritative context contradicts itself.
    """
    candidates: list[tuple[str, Any]] = [
        (key, payload[key])
        for key in ("timeframe", "interval")
        if key in payload and payload[key] is not None
    ]
    if "k" in payload:
        kline = payload["k"]
        if not isinstance(kline, Mapping):
            raise ValueError("k must be an object when supplied for timeframe context")
        if "i" in kline and kline["i"] is not None:
            candidates.append(("k.i", kline["i"]))

    values: list[tuple[str, str]] = []
    for key, value in candidates:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string when supplied")
        values.append((key, value.strip()))
    if not values:
        return None
    if len({value for _, value in values}) != 1:
        fields = ", ".join(key for key, _ in values)
        raise ValueError(f"conflicting explicit timeframe values: {fields}")
    return values[0][1]


@dataclass(frozen=True, slots=True)
class QualityEvidenceRecord:
    """Persistable, deterministic quality/acquisition fact.

    knowledge_time == received_at is authoritative for this family because
    the assessment is a pure deterministic function of the immutable
    AcquisitionEnvelope and its explicit validation inputs. No persistence
    or wall-clock timestamp participates in the semantic.
    """

    evidence_id: str
    logical_fact_key: str
    source_record_id: str
    source_identity_hash: str
    provider_id: str
    adapter_id: str
    adapter_version: str
    canonical_instrument_id: str
    provider_instrument_id: str
    event_type: str
    event_time: datetime
    received_at: datetime
    knowledge_time: datetime
    acquisition_state: str
    quality_state: DataQualityState
    lifecycle_state: DataLifecycleState
    quality_score: Any
    reason_codes: tuple[str, ...]
    validation_result: str | None
    provenance_id: str
    lineage_parent_id: str | None
    payload_fingerprint: str
    timeframe: str | None
    venue: str | None

    def __post_init__(self) -> None:
        _token(self.evidence_id, "evidence_id")
        _token(self.logical_fact_key, "logical_fact_key")
        _token(self.source_record_id, "source_record_id")
        _token(self.source_identity_hash, "source_identity_hash")
        if len(self.source_identity_hash) != 64 or any(c not in "0123456789abcdef" for c in self.source_identity_hash.lower()):
            raise ValueError("source_identity_hash must be a SHA-256 hexadecimal value")
        for value, field in (
            (self.provider_id, "provider_id"),
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
            (self.canonical_instrument_id, "canonical_instrument_id"),
            (self.provider_instrument_id, "provider_instrument_id"),
            (self.event_type, "event_type"),
            (self.acquisition_state, "acquisition_state"),
            (self.provenance_id, "provenance_id"),
            (self.payload_fingerprint, "payload_fingerprint"),
        ):
            _token(value, field)
        for value, field in ((self.event_time, "event_time"), (self.received_at, "received_at"), (self.knowledge_time, "knowledge_time")):
            _utc(value, field)
        if self.knowledge_time != self.received_at:
            raise ValueError("quality-evidence knowledge_time must equal the authoritative receipt boundary")
        if not isinstance(self.quality_state, DataQualityState):
            raise TypeError("quality_state must be DataQualityState")
        if not isinstance(self.lifecycle_state, DataLifecycleState):
            raise TypeError("lifecycle_state must be DataLifecycleState")
        if not isinstance(self.reason_codes, tuple) or any(not isinstance(v, str) or not v.strip() for v in self.reason_codes):
            raise TypeError("reason_codes must be a tuple of non-empty strings")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must be unique")
        if self.validation_result is not None:
            _token(self.validation_result, "validation_result")
        if self.lineage_parent_id is not None:
            _token(self.lineage_parent_id, "lineage_parent_id")
        for value, field in ((self.timeframe, "timeframe"), (self.venue, "venue")):
            if value is not None:
                _token(value, field)

    @property
    def event_knowledge_distinct(self) -> bool:
        return self.event_time != self.knowledge_time


def build_quality_evidence(
    envelope: AcquisitionEnvelope,
    assessment: QualityAssessment,
) -> QualityEvidenceRecord:
    """Build one deterministic evidence fact from authoritative P2/P3 inputs."""
    if not isinstance(envelope, AcquisitionEnvelope):
        raise TypeError("envelope must be AcquisitionEnvelope")
    if not isinstance(assessment, QualityAssessment):
        raise TypeError("assessment must be QualityAssessment")

    timeframe = _timeframe_context(envelope.payload)
    venue = _optional_context(envelope.payload, "venue", "venue_context")
    if envelope.event_type.value == "TRADE" and envelope.provider.provider_id == "binance":
        if venue != "BINANCE":
            raise ValueError("Binance Spot trade quality evidence requires explicit BINANCE venue context")
    if venue == "BINANCE" and envelope.provider.provider_id != "binance":
        raise ValueError("BINANCE venue context is authorized only for Binance provider evidence")

    source_identity_hash = envelope.event_id
    logical_material = {
        "source_record_id": envelope.event_id,
        "canonical_instrument_id": envelope.instrument.canonical_instrument_id,
        "event_type": envelope.event_type.value,
        "event_time": envelope.event_time.isoformat(),
    }
    logical_fact_key = hashlib.sha256(
        json.dumps(logical_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    semantic_material = {
        "logical_fact_key": logical_fact_key,
        "source_identity_hash": source_identity_hash,
        "quality_state": assessment.quality.quality_state.value,
        "lifecycle_state": assessment.lifecycle.value,
        "quality_score": str(assessment.explanation.score) if assessment.explanation.score is not None else None,
        "reason_codes": assessment.quality.reason_codes,
        "validation_result": assessment.lineage.validation_result if assessment.lineage else None,
        "provenance_id": assessment.provenance_id,
        "source_record_id": assessment.source_record_id,
        "lineage_parent_id": assessment.lineage_parent_id,
        "payload_fingerprint": fingerprint_payload(envelope.payload),
        "event_time": envelope.event_time.isoformat(),
        "received_at": envelope.received_at.isoformat(),
        "knowledge_time": envelope.received_at.isoformat(),
        "timeframe": timeframe,
        "venue": venue,
    }
    evidence_id = hashlib.sha256(
        json.dumps(semantic_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return QualityEvidenceRecord(
        evidence_id=evidence_id,
        logical_fact_key=logical_fact_key,
        source_record_id=envelope.event_id,
        source_identity_hash=source_identity_hash,
        provider_id=envelope.provider.provider_id,
        adapter_id=envelope.provider.adapter_id,
        adapter_version=envelope.provider.adapter_version,
        canonical_instrument_id=envelope.instrument.canonical_instrument_id,
        provider_instrument_id=envelope.instrument.provider_instrument_id,
        event_type=envelope.event_type.value,
        event_time=envelope.event_time,
        received_at=envelope.received_at,
        knowledge_time=envelope.received_at,
        acquisition_state=envelope.state.value,
        quality_state=assessment.quality.quality_state,
        lifecycle_state=assessment.lifecycle,
        quality_score=assessment.explanation.score,
        reason_codes=assessment.quality.reason_codes,
        validation_result=assessment.lineage.validation_result if assessment.lineage else None,
        provenance_id=assessment.provenance_id or envelope.provenance.provenance_id,
        lineage_parent_id=assessment.lineage_parent_id,
        payload_fingerprint=fingerprint_payload(envelope.payload),
        timeframe=timeframe,
        venue=venue,
    )
