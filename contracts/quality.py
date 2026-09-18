
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
    return QualityAssessment(
        quality,
        lifecycle,
        canonical_eligible,
        _explanation(inp.signals),
        lineage,
        inp.provenance.provenance_id if inp.provenance is not None else None,
        inp.source_record_id,
        inp.lineage_parent_id,
    )


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
        "source_record_id": assessment.source_record_id,
    }
    key = hashlib.sha256(
        json.dumps(key_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return QuarantineRecord(
        key,
        assessment.quality.quality_state,
        assessment.quality.reason_codes,
        assessment.provenance_id,
        assessment.source_record_id,
        assessment.lineage_parent_id,
        payload_fingerprint,