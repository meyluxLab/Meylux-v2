    """In-memory bounded isolation boundary for normalization/DLQ handoff.

    This is deliberately not persistence. Capacity exhaustion is explicit and
    never causes an upstream record to be promoted or silently discarded.
    """

    def __init__(self, max_records: int = 1024) -> None:
        if isinstance(max_records, bool) or not isinstance(max_records, int) or max_records < 1:
            raise ValueError("max_records must be a positive integer")
        self._max_records = max_records
        self._records: dict[str, QuarantineRecord] = {}

    @property
    def capacity(self) -> int:
        return self._max_records

    @property
    def size(self) -> int:
        return len(self._records)

    def enqueue(self, record: QuarantineRecord) -> str:
        if not isinstance(record, QuarantineRecord):
            raise TypeError("record must be QuarantineRecord")
        if record.deduplication_key in self._records:
            return "DUPLICATE"
        if len(self._records) >= self._max_records:
            raise OverflowError("normalization_dlq capacity exhausted")
        self._records[record.deduplication_key] = record
        return "ENQUEUED"

    def snapshot(self) -> tuple[QuarantineRecord, ...]:
        return tuple(self._records.values())


def _stable_json(value: Any) -> Any:
    if isinstance(value, Enum):
        return _stable_json(value.value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal is not fingerprintable")
        return format(value, "f")
    if is_dataclass(value):
        return {field.name: _stable_json(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _stable_json(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_stable_json(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return repr(value)


def fingerprint_payload(value: Any) -> str:
    encoded = json.dumps(
        _stable_json(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _quality_state(inp: QualityInput) -> tuple[DataQualityState, tuple[str, ...]]:
    """Apply deterministic precedence from strongest safety evidence downward.

    Record availability and explicit validation outcomes are authoritative for
    safety classification. Capability degradation may downgrade only otherwise
    valid evidence; it never weakens rejected, incomplete, contradictory or
    unavailable validation evidence.
    """
    if not inp.record_available:
        return DataQualityState.UNAVAILABLE, ("provider_unavailable",)
    if inp.validation is None:
        return DataQualityState.INCOMPLETE, ("required_evidence_missing",)
    validation_state = {
        ValidationResult.CONTRADICTORY: (DataQualityState.CONTRADICTORY, "contradictory_validation"),
        ValidationResult.REJECTED: (DataQualityState.REJECTED, "validation_rejected"),
        ValidationResult.INCOMPLETE: (DataQualityState.INCOMPLETE, "required_evidence_missing"),
        ValidationResult.UNAVAILABLE: (DataQualityState.UNAVAILABLE, "provider_unavailable"),
        ValidationResult.STALE: (DataQualityState.STALE, "stale_evidence"),
        ValidationResult.DEGRADED: (DataQualityState.DEGRADED, "quality_degraded"),
        ValidationResult.VALID: (DataQualityState.VALID, None),
    }
    state, reason = validation_state[inp.validation.result]
    if state in {
        DataQualityState.CONTRADICTORY,
        DataQualityState.REJECTED,
        DataQualityState.INCOMPLETE,
        DataQualityState.UNAVAILABLE,
    }:
        return state, (reason,)
    if inp.capability_state is CapabilityState.UNSUPPORTED:
        return DataQualityState.UNAVAILABLE, ("provider_unsupported",)
    if inp.capability_state is CapabilityState.UNAVAILABLE:
        return DataQualityState.UNAVAILABLE, ("provider_unavailable",)
    if inp.capability_state is CapabilityState.DEGRADED:
        return DataQualityState.DEGRADED, ("quality_degraded",)
    return state, (reason,) if reason else ()

def _explanation(signals: QualitySignals) -> QualityExplanation:
    values = tuple((name, getattr(signals, name)) for name in QUALITY_DIMENSIONS)
    present = [value for _, value in values if value is not None]
    score = None
    if len(present) == len(QUALITY_DIMENSIONS):
        score = (sum(present, Decimal("0.00")) / Decimal(len(present))).quantize(Decimal("0.01"))
    return QualityExplanation(values, score)


def assess_quality(inp: QualityInput) -> QualityAssessment:
    if not isinstance(inp, QualityInput):
        raise TypeError("inp must be QualityInput")
    state, base_reasons = _quality_state(inp)
    issue_reasons = tuple(
        f"validation_{getattr(issue.code, 'value', str(issue.code))}:{issue.field}"
        for issue in (inp.validation.issues if inp.validation else ())
    )
    reasons = tuple(sorted(
        set((*base_reasons, *issue_reasons)),
        key=lambda x: (_REASON_ORDER.get(x, 1000), x),
    ))
    quality = DataQuality(state, reasons)
    lifecycle = {
        DataQualityState.VALID: DataLifecycleState.CANONICAL,
        DataQualityState.DEGRADED: DataLifecycleState.QUALITY_DEGRADED,
        DataQualityState.STALE: DataLifecycleState.QUALITY_DEGRADED,
        DataQualityState.INCOMPLETE: DataLifecycleState.REJECTED,
        DataQualityState.CONTRADICTORY: DataLifecycleState.REJECTED,
        DataQualityState.REJECTED: DataLifecycleState.REJECTED,
        DataQualityState.UNAVAILABLE: DataLifecycleState.REJECTED,
    }[state]
    canonical_eligible = state is DataQualityState.VALID
    if state is DataQualityState.VALID and (
        inp.provenance is None or inp.source_record_id is None or inp.lineage_parent_id is None
    ):
        reasons = tuple(sorted(
            set((*reasons, "lineage_missing")),
            key=lambda x: (_REASON_ORDER.get(x, 1000), x),
        ))
        quality = DataQuality(DataQualityState.INCOMPLETE, reasons)
        lifecycle = DataLifecycleState.REJECTED
        canonical_eligible = False
    validate_quality_lifecycle(quality, lifecycle)
    lineage = None
    if inp.provenance is not None and inp.source_record_id is not None and inp.lineage_parent_id is not None:
        lineage = QualityLineage(
            inp.source_record_id,
            inp.lineage_parent_id,
            inp.provenance.provenance_id,
            inp.validation.result.value if inp.validation else "unavailable",
            quality.quality_state,
        )
    return QualityAssessment(quality, lifecycle, canonical_eligible, _explanation(inp.signals), lineage)


def quarantine_record(
    assessment: QualityAssessment, payload: Any, *, attempt: int = 1
) -> QuarantineRecord:
    if not isinstance(assessment, QualityAssessment):
        raise TypeError("assessment must be QualityAssessment")
    if assessment.canonical_eligible:
        raise ValueError("canonical-eligible evidence cannot be quarantined")
    payload_fingerprint = fingerprint_payload(payload)
    key_material = {
        "quality_state": assessment.quality.quality_state.value,
        "reasons": assessment.quality.reason_codes,
        "payload": payload_fingerprint,
        "source_record_id": assessment.lineage.source_record_id if assessment.lineage else None,
    }
    key = hashlib.sha256(
        json.dumps(key_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return QuarantineRecord(
        key,
        assessment.quality.quality_state,
        assessment.quality.reason_codes,
        assessment.lineage.provenance_id if assessment.lineage else None,
        assessment.lineage.source_record_id if assessment.lineage else None,
        assessment.lineage.lineage_parent_id if assessment.lineage else None,
        payload_fingerprint,
        attempt,
    )


def route_assessment(
    assessment: QualityAssessment,
    payload: Any,
    quarantine: BoundedQuarantine,
    *,
    attempt: int = 1,
) -> str:
    """Route one assessment without persistence or silent loss."""

    if not isinstance(quarantine, BoundedQuarantine):
        raise TypeError("quarantine must be BoundedQuarantine")
    if assessment.canonical_eligible:
        return "CANONICAL"
    if assessment.quality.quality_state in {DataQualityState.DEGRADED, DataQualityState.STALE}:
        return "QUALITY_DEGRADED"
    quarantine.enqueue(quarantine_record(assessment, payload, attempt=attempt))
    return "QUARANTINED"