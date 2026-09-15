"""Temporal, sequence, and completeness validation for Phase 3.

This module consumes the provider-neutral AcquisitionEnvelope and the existing
P3-001 validation foundation. It is deterministic and side-effect free. Any
sequence or cadence semantics that are not encoded by an authoritative
contract must be supplied explicitly by the caller; this module never invents
numeric ordering, cadence, or clock-skew policy.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from contracts.acquisition import AcquisitionEnvelope
from contracts.canonical.foundation import (
    ValidationCode,
    ValidationIssue,
    ValidationOutcome,
    validate_timestamp,
    validation_outcome,
)

SequenceSuccessor = Callable[[str], str | None]
CadenceSuccessor = Callable[[datetime], datetime | None]


@dataclass(frozen=True, slots=True)
class TemporalValidation:
    """Deterministic temporal/sequence validation result."""

    outcome: ValidationOutcome


def _issue(code: ValidationCode, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code, field, message)


def validate_temporal_evidence(
    envelope: AcquisitionEnvelope,
    *,
    reference_time: datetime | None = None,
) -> TemporalValidation:
    """Validate timestamp semantics without reading the wall clock.

    ``reference_time`` is optional and explicit. Future-time validation is only
    performed when an authoritative caller supplies that reference; no implicit
    current-time policy is introduced here.
    """

    if not isinstance(envelope, AcquisitionEnvelope):
        return TemporalValidation(
            validation_outcome(
                (_issue(ValidationCode.INVALID_TYPE, "envelope", "envelope must be AcquisitionEnvelope"),)
            )
        )

    issues: list[ValidationIssue] = []
    try:
        validate_timestamp(envelope.event_time, "event_time")
        validate_timestamp(envelope.received_at, "received_at")
    except (TypeError, ValueError) as exc:
        issues.append(_issue(ValidationCode.TIMESTAMP_INVALID, "timestamp", str(exc)))

    if envelope.event_time > envelope.received_at:
        issues.append(
            _issue(
                ValidationCode.INVALID_VALUE,
                "event_time",
                "event_time cannot be later than received_at",
            )
        )

    if reference_time is not None:
        try:
            validate_timestamp(reference_time, "reference_time")
        except (TypeError, ValueError) as exc:
            issues.append(_issue(ValidationCode.TIMESTAMP_INVALID, "reference_time", str(exc)))
        else:
            if envelope.event_time > reference_time:
                issues.append(
                    _issue(
                        ValidationCode.INVALID_VALUE,
                        "event_time",
                        "event_time cannot be later than the supplied reference_time",
                    )
                )

    return TemporalValidation(validation_outcome(issues))


def validate_temporal_order(
    envelopes: Sequence[AcquisitionEnvelope],
) -> TemporalValidation:
    """Validate chronological ordering of an already ordered evidence sequence."""

    issues: list[ValidationIssue] = []
    previous: AcquisitionEnvelope | None = None
    for index, envelope in enumerate(envelopes):
        if not isinstance(envelope, AcquisitionEnvelope):
            issues.append(
                _issue(ValidationCode.INVALID_TYPE, f"envelopes[{index}]", "item must be AcquisitionEnvelope")
            )
            continue
        result = validate_temporal_evidence(envelope)
        issues.extend(result.outcome.issues)
        if previous is not None and envelope.event_time < previous.event_time:
            issues.append(
                _issue(
                    ValidationCode.INVALID_VALUE,
                    f"envelopes[{index}].event_time",
                    "event_time is out of chronological order",
                )
            )
        previous = envelope
    return TemporalValidation(validation_outcome(issues))


def validate_sequence(
    envelopes: Sequence[AcquisitionEnvelope],
    *,
    sequence_successor: SequenceSuccessor | None = None,
) -> TemporalValidation:
    """Validate source-sequence duplicates, ordering, and optional continuity.

    Source sequence values are contractually opaque strings. Therefore ordering
    and continuity semantics are only enforced when the authoritative caller
    supplies ``sequence_successor``. Exact duplicate sequence values are always
    detectable without inventing numeric semantics.
    """

    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    previous_by_stream: dict[tuple[str, str], str] = {}

    for index, envelope in enumerate(envelopes):
        if not isinstance(envelope, AcquisitionEnvelope):
            issues.append(
                _issue(ValidationCode.INVALID_TYPE, f"envelopes[{index}]", "item must be AcquisitionEnvelope")
            )
            continue
        if envelope.source_sequence is None:
            continue

        stream = (
            envelope.provider.provider_id,
            envelope.instrument.canonical_instrument_id,
        )
        duplicate_key = (*stream, envelope.source_sequence)
        if duplicate_key in seen:
            issues.append(
                _issue(
                    ValidationCode.INVALID_VALUE,
                    "source_sequence",
                    "duplicate source_sequence within the provider/instrument stream",
                )
            )
        seen.add(duplicate_key)

        previous = previous_by_stream.get(stream)
        if previous is not None and sequence_successor is not None:
            try:
                expected = sequence_successor(previous)
            except Exception as exc:
                issues.append(
                    _issue(
                        ValidationCode.INVALID_VALUE,
                        "source_sequence",
                        f"authoritative sequence successor evaluation failed: {exc}",
                    )
                )
            else:
                if expected is not None and envelope.source_sequence != expected:
                    issues.append(
                        _issue(
                            ValidationCode.INVALID_VALUE,
                            "source_sequence",
                            "source sequence is discontinuous or out of order",
                        )
                    )
        previous_by_stream[stream] = envelope.source_sequence

    return TemporalValidation(validation_outcome(issues))


def validate_completeness(
    envelopes: Sequence[AcquisitionEnvelope],
    *,
    cadence_successor: CadenceSuccessor | None = None,
) -> TemporalValidation:
    """Validate completeness without manufacturing missing data.

    Cadence continuity is delegated to an authoritative cadence function. If no
    authoritative cadence is supplied, no invented gap policy is applied.
    """

    issues: list[ValidationIssue] = []
    if cadence_successor is not None:
        previous: AcquisitionEnvelope | None = None
        for index, envelope in enumerate(envelopes):
            if not isinstance(envelope, AcquisitionEnvelope):
                continue
            if previous is not None:
                try:
                    expected = cadence_successor(previous.event_time)
                except Exception as exc:
                    issues.append(
                        _issue(
                            ValidationCode.INVALID_VALUE,
                            f"envelopes[{index}].event_time",
                            f"authoritative cadence evaluation failed: {exc}",
                        )
                    )
                else:
                    if expected is not None and envelope.event_time != expected:
                        issues.append(
                            _issue(
                                ValidationCode.INVALID_VALUE,
                                f"envelopes[{index}].event_time",
                                "temporal evidence is not cadence-continuous",
                            )
                        )
            previous = envelope

    return TemporalValidation(validation_outcome(issues))


def validate_temporal_sequence_completeness(
    envelopes: Iterable[AcquisitionEnvelope],
    *,
    reference_time: datetime | None = None,
    sequence_successor: SequenceSuccessor | None = None,
    cadence_successor: CadenceSuccessor | None = None,
) -> TemporalValidation:
    """Run the complete P3-003 deterministic validation boundary."""

    items = tuple(envelopes)
    issues: list[ValidationIssue] = []

    for index, envelope in enumerate(items):
        if not isinstance(envelope, AcquisitionEnvelope):
            issues.append(_issue(ValidationCode.INVALID_TYPE, f"envelopes[{index}]", "item must be AcquisitionEnvelope"))
            continue
        issues.extend(validate_temporal_evidence(envelope, reference_time=reference_time).outcome.issues)

    issues.extend(validate_temporal_order(items).outcome.issues)
    issues.extend(validate_sequence(items, sequence_successor=sequence_successor).outcome.issues)
    issues.extend(validate_completeness(items, cadence_successor=cadence_successor).outcome.issues)
    return TemporalValidation(validation_outcome(issues))
