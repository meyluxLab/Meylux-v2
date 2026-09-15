"""Structural, schema, and initial identity validation for Phase 3.

This module consumes existing Phase-2 acquisition and Phase-3 canonical
validation semantics. It does not define or replace domain contracts and does
not perform semantic market validation, normalization, persistence, or I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderCapability,
    ProviderError,
    ProviderIdentity,
    Provenance,
)
from contracts.canonical.foundation import (
    ValidationCode,
    ValidationIssue,
    ValidationOutcome,
    validate_semantic_token,
    validation_outcome,
)


ACQUISITION_REQUIRED_FIELDS = (
    "provider",
    "instrument",
    "provenance",
    "event_type",
    "event_time",
    "received_at",
    "state",
    "payload",
)

ACQUISITION_PERMITTED_FIELDS = frozenset(
    {
        *ACQUISITION_REQUIRED_FIELDS,
        "source_sequence",
        "provider_error",
        "capability",
    }
)

ACQUISITION_FIELD_TYPES: dict[str, tuple[type, ...]] = {
    "provider": (ProviderIdentity,),
    "instrument": (InstrumentIdentity,),
    "provenance": (Provenance,),
    "event_type": (EventType,),
    "event_time": (datetime,),
    "received_at": (datetime,),
    "state": (AcquisitionState,),
    "payload": (Mapping,),
    "source_sequence": (str,),
    "provider_error": (ProviderError,),
    "capability": (ProviderCapability,),
}

ACQUISITION_NULLABLE_FIELDS = frozenset(
    {"source_sequence", "provider_error", "capability"}
)


@dataclass(frozen=True, slots=True)
class StructuralValidation:
    """Deterministic structural validation result with optional contract identity."""

    outcome: ValidationOutcome
    identity: str | None = None


def _required_fields(values: Mapping[str, Any], required: Iterable[str]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field in required:
        if field not in values:
            issues.append(
                ValidationIssue(ValidationCode.REQUIRED_MISSING, field, f"{field} is required")
            )
        elif values[field] is None:
            issues.append(
                ValidationIssue(ValidationCode.NULL_NOT_ALLOWED, field, f"{field} cannot be null")
            )
    return tuple(issues)


def _permitted_fields(values: Mapping[str, Any], permitted: Iterable[str]) -> tuple[ValidationIssue, ...]:
    allowed = frozenset(permitted)
    return tuple(
        ValidationIssue(
            ValidationCode.INVALID_VALUE,
            field,
            f"{field} is not a permitted field",
        )
        for field in sorted(values)
        if field not in allowed
    )


def _field_types(
    values: Mapping[str, Any],
    field_types: Mapping[str, tuple[type, ...]],
    nullable: Iterable[str],
) -> tuple[ValidationIssue, ...]:
    nullable_fields = frozenset(nullable)
    issues: list[ValidationIssue] = []
    for field, expected in field_types.items():
        if field not in values or values[field] is None:
            if field in values and values[field] is None and field not in nullable_fields:
                issues.append(
                    ValidationIssue(ValidationCode.NULL_NOT_ALLOWED, field, f"{field} cannot be null")
                )
            continue
        if not isinstance(values[field], expected):
            expected_names = ", ".join(item.__name__ for item in expected)
            issues.append(
                ValidationIssue(
                    ValidationCode.INVALID_TYPE,
                    field,
                    f"{field} must be one of: {expected_names}",
                )
            )
    return tuple(issues)


def _identity_issues(envelope: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    provider = envelope.get("provider")
    instrument = envelope.get("instrument")
    provenance = envelope.get("provenance")

    if isinstance(provider, ProviderIdentity):
        for field in ("provider_id", "adapter_id", "adapter_version"):
            issue = validate_semantic_token(getattr(provider, field), f"provider.{field}")
            if issue is not None:
                issues.append(issue)

    if isinstance(instrument, InstrumentIdentity):
        for field in ("canonical_instrument_id", "provider_instrument_id"):
            issue = validate_semantic_token(getattr(instrument, field), f"instrument.{field}")
            if issue is not None:
                issues.append(issue)

    if isinstance(provenance, Provenance):
        issue = validate_semantic_token(provenance.provenance_id, "provenance.provenance_id")
        if issue is not None:
            issues.append(issue)
        issue = validate_semantic_token(provenance.acquisition_method, "provenance.acquisition_method")
        if issue is not None:
            issues.append(issue)

    return tuple(issues)


def validate_acquisition_structure(values: Mapping[str, Any]) -> StructuralValidation:
    """Validate only the existing AcquisitionEnvelope structural contract.

    The function does not construct an AcquisitionEnvelope because doing so
    would invoke Phase-2 semantic constructor rules. It validates the already
    authorized field set, required/nullable rules, field types, and initial
    provider-neutral identity syntax. Authoritative acquisition identity is
    obtained only from an existing AcquisitionEnvelope instance so its
    established serialization semantics are neither duplicated nor changed.
    """

    if not isinstance(values, Mapping):
        issue = ValidationIssue(
            ValidationCode.INVALID_TYPE,
            "record",
            "record must be a mapping",
        )
        return StructuralValidation(validation_outcome((issue,)))

    issues = [
        *_required_fields(values, ACQUISITION_REQUIRED_FIELDS),
        *_permitted_fields(values, ACQUISITION_PERMITTED_FIELDS),
        *_field_types(values, ACQUISITION_FIELD_TYPES, ACQUISITION_NULLABLE_FIELDS),
        *_identity_issues(values),
    ]

    return StructuralValidation(validation_outcome(issues))


def validate_acquisition_envelope(envelope: AcquisitionEnvelope) -> StructuralValidation:
    """Validate an existing AcquisitionEnvelope instance without reconstruction."""

    if not isinstance(envelope, AcquisitionEnvelope):
        issue = ValidationIssue(
            ValidationCode.INVALID_TYPE,
            "envelope",
            "envelope must be AcquisitionEnvelope",
        )
        return StructuralValidation(validation_outcome((issue,)))

    values = {
        "provider": envelope.provider,
        "instrument": envelope.instrument,
        "provenance": envelope.provenance,
        "event_type": envelope.event_type,
        "event_time": envelope.event_time,
        "received_at": envelope.received_at,
        "state": envelope.state,
        "payload": envelope.payload,
        "source_sequence": envelope.source_sequence,
        "provider_error": envelope.provider_error,
        "capability": envelope.capability,
    }
    result = validate_acquisition_structure(values)
    if result.outcome.valid:
        return StructuralValidation(result.outcome, envelope.event_id)
    return result
