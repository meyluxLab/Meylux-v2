"""Deterministic Stage-1 S-10 Data Quality Analyst."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping

from meylux.queue import NonRetryableProcessingError
from contracts.specialist import (
    EvidenceRef,
    FactStatus,
    InputSnapshot,
    SnapshotFact,
    SpecialistConfigRef,
    SpecialistFinding,
    SpecialistOutput,
    SpecialistStatus,
    canonical_json,
)


class S10SemanticError(NonRetryableProcessingError):
    """Non-retryable input/contract failure for the S-10 runtime boundary."""


_STATUS_RANK = {
    FactStatus.VALID: 0,
    FactStatus.PARTIAL: 2,
    FactStatus.STALE: 2,
    FactStatus.INSUFFICIENT_DATA: 3,
    FactStatus.INVALID: 4,
    FactStatus.CONTRADICTORY: 5,
    FactStatus.UNAVAILABLE: 6,
}

_STATE_CODE = {
    FactStatus.STALE: "STALE_INPUT",
    FactStatus.INSUFFICIENT_DATA: "INCOMPLETE_HISTORY",
    FactStatus.CONTRADICTORY: "CONTRADICTORY_INPUT",
    FactStatus.UNAVAILABLE: "UNAVAILABLE_INPUT",
    FactStatus.INVALID: "INVALID_INPUT",
    FactStatus.PARTIAL: "PARTIAL_INPUT",
}


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise S10SemanticError(f"{field} must be explicit UTC datetime")
    return value



def _decode_normalised(value: Any) -> Any:
    if isinstance(value, Mapping):
        if set(value) == {"__decimal__"}:
            try:
                return Decimal(value["__decimal__"])
            except Exception as exc:
                raise S10SemanticError("invalid canonical Decimal encoding") from exc
        return {key: _decode_normalised(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode_normalised(item) for item in value]
    return value

def _ref(raw: Mapping[str, Any]) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=raw["evidence_id"],
        source_type=raw["source_type"],
        source_reference=raw["source_reference"],
        identity_hash=raw["identity_hash"],
        observed_at_utc=_utc(raw["observed_at_utc"], "observed_at_utc") if raw.get("observed_at_utc") else None,
        content_version=raw.get("content_version"),
        source_family=raw.get("source_family"),
        record_id=raw.get("record_id"),
        event_time=_utc(raw["event_time"], "event_time") if raw.get("event_time") else None,
        knowledge_time=_utc(raw["knowledge_time"], "knowledge_time") if raw.get("knowledge_time") else None,
        timeframe=raw.get("timeframe"),
        venue=raw.get("venue"),
    )


def snapshot_from_json(value: str) -> InputSnapshot:
    """Reconstruct and revalidate a canonical InputSnapshot from queue transport."""
    try:
        raw = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise S10SemanticError("snapshot_json is not valid JSON") from exc
    if not isinstance(raw, Mapping):
        raise S10SemanticError("snapshot payload must be an object")

    try:
        as_of = _utc(datetime.fromisoformat(raw["as_of"].replace("Z", "+00:00")), "as_of")
        facts = []
        for item in raw["facts"]:
            refs = tuple(_ref(ref) for ref in item["evidence_refs"])
            metadata = dict(_decode_normalised(item.get("metadata") or {}))
            event_time = metadata.get("event_time")
            if isinstance(event_time, str):
                metadata["event_time"] = _utc(datetime.fromisoformat(event_time.replace("Z", "+00:00")), "metadata.event_time")
            knowledge_time = metadata.get("knowledge_time")
            if isinstance(knowledge_time, str):
                metadata["knowledge_time"] = _utc(datetime.fromisoformat(knowledge_time.replace("Z", "+00:00")), "metadata.knowledge_time")
            facts.append(
                SnapshotFact(
                    fact_id=item["fact_id"],
                    status=FactStatus(item["status"]),
                    value=_decode_normalised(item.get("value")),
                    knowledge_time=_utc(
                        datetime.fromisoformat(item["knowledge_time"].replace("Z", "+00:00")),
                        "knowledge_time",
                    ),
                    evidence_refs=refs,
                    reason=item.get("reason"),
                    metadata=metadata,
                )
            )
        provenance = tuple(_ref(ref) for ref in raw.get("provenance_refs", []))
        snapshot = InputSnapshot.build(
            as_of=as_of,
            version=raw["version"],
            facts=tuple(facts),
            provenance_refs=provenance,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise S10SemanticError(f"malformed authoritative InputSnapshot: {exc}") from exc

    if raw.get("snapshot_id") != snapshot.snapshot_id:
        raise S10SemanticError("snapshot identity mismatch after canonical reconstruction")
    return snapshot


class S10DataQualityAnalyst:
    """Reference specialist: classify only facts present in the authoritative Snapshot."""

    specialist_id = "S-10"
    output_version = "1.0.0"

    def __init__(self, config: SpecialistConfigRef, *, max_findings: int = 100, max_evidence_refs: int = 100) -> None:
        if max_findings < 1 or max_evidence_refs < 1:
            raise ValueError("S-10 output bounds must be positive")
        self.config = config
        self.max_findings = max_findings
        self.max_evidence_refs = max_evidence_refs

    def analyze(self, snapshot: InputSnapshot) -> SpecialistOutput:
        if not isinstance(snapshot, InputSnapshot):
            raise S10SemanticError("S-10 requires InputSnapshot")
        if snapshot.as_of.tzinfo is None or snapshot.as_of.utcoffset() != timezone.utc.utcoffset(snapshot.as_of):
            raise S10SemanticError("snapshot.as_of must be UTC")
        if any(f.knowledge_time > snapshot.as_of for f in snapshot.facts):
            raise S10SemanticError("lookahead fact reached S-10")

        provenance = {ref.evidence_id: ref for ref in snapshot.provenance_refs}
        refs: dict[str, EvidenceRef] = {}
        for fact in snapshot.facts:
            for ref in fact.evidence_refs:
                if ref.evidence_id not in provenance:
                    raise S10SemanticError(f"unresolved evidence reference: {ref.evidence_id}")
                canonical = provenance[ref.evidence_id]
                if canonical.identity_hash != ref.identity_hash or canonical.record_id != ref.record_id:
                    raise S10SemanticError(f"evidence reference identity mismatch: {ref.evidence_id}")
                if ref.knowledge_time is None or ref.knowledge_time > snapshot.as_of:
                    raise S10SemanticError(f"evidence reference violates as_of boundary: {ref.evidence_id}")
                refs[ref.evidence_id] = canonical

        ordered = tuple(sorted(snapshot.facts, key=lambda fact: fact.fact_id))
        if len(refs) > self.max_evidence_refs:
            raise S10SemanticError("S-10 evidence reference bound exceeded")
        worst = max(ordered, key=lambda fact: (_STATUS_RANK[fact.status], fact.fact_id)).status if ordered else FactStatus.UNAVAILABLE
        counts: dict[str, int] = {}
        for fact in ordered:
            counts[fact.status.value] = counts.get(fact.status.value, 0) + 1

        findings = [
            SpecialistFinding(
                code="OVERALL_QUALITY",
                status=SpecialistStatus.SUCCESS if worst is FactStatus.VALID else SpecialistStatus.PARTIAL,
                value={
                    "worst_status": worst.value,
                    "fact_count": len(ordered),
                    "status_counts": dict(sorted(counts.items())),
                    "as_of": snapshot.as_of,
                },
                reason="deterministic worst-status classification over Snapshot facts",
                evidence_refs=tuple(sorted(refs.values(), key=lambda ref: ref.evidence_id)),
            )
        ]

        for fact in ordered:
            if fact.status is FactStatus.VALID:
                continue
            findings.append(
                SpecialistFinding(
                    code=_STATE_CODE.get(fact.status, "NON_VALID_INPUT"),
                    status=SpecialistStatus.PARTIAL,
                    value={
                        "fact_id": fact.fact_id,
                        "status": fact.status.value,
                        "reason": fact.reason,
                        "knowledge_time": fact.knowledge_time,
                    },
                    reason=f"authoritative Snapshot fact is {fact.status.value}",
                    evidence_refs=tuple(sorted(fact.evidence_refs, key=lambda ref: ref.evidence_id)),
                )
            )

        if len(findings) > self.max_findings:
            raise S10SemanticError("S-10 finding bound exceeded")
        if worst is FactStatus.VALID:
            status = SpecialistStatus.SUCCESS
            reason = "all Snapshot facts are VALID"
        elif worst is FactStatus.UNAVAILABLE:
            status = SpecialistStatus.UNAVAILABLE_INPUT
            reason = "at least one required Snapshot fact is UNAVAILABLE"
        elif worst is FactStatus.INSUFFICIENT_DATA:
            status = SpecialistStatus.INSUFFICIENT_DATA
            reason = "at least one Snapshot fact has insufficient historical/input coverage"
        else:
            status = SpecialistStatus.PARTIAL
            reason = f"worst Snapshot quality state is {worst.value}"

        output = SpecialistOutput(
            specialist_id=self.specialist_id,
            output_version=self.output_version,
            snapshot_id=snapshot.snapshot_id,
            snapshot_version=snapshot.version,
            config=self.config,
            status=status,
            reason=reason,
            findings=tuple(findings),
            evidence_refs=tuple(sorted(refs.values(), key=lambda ref: ref.evidence_id)),
        )
        canonical_json(output.as_dict())
        return output
