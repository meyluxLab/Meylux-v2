"""Shared canonical identity, validation, numeric, provenance, and lineage rules.

This module is provider-neutral and side-effect free. It defines reusable
semantics for STEP-P3-001 without introducing a new governed Stable ID.

Correction evidence remains limited to the authorized STEP-P3-001 boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping


class ValidationResult(str, Enum):
    """Authoritative Phase-3 quality outcome vocabulary."""

    VALID = "valid"
    DEGRADED = "degraded"
    STALE = "stale"
    INCOMPLETE = "incomplete"
    CONTRADICTORY = "contradictory"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class ValidationCode(str, Enum):
    """Deterministic validation reason taxonomy."""

    OK = "ok"
    REQUIRED_MISSING = "required_missing"
    NULL_NOT_ALLOWED = "null_not_allowed"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    NON_FINITE_DECIMAL = "non_finite_decimal"
    FLOAT_NOT_ALLOWED = "float_not_allowed"
    TIMESTAMP_NOT_UTC = "timestamp_not_utc"
    TIMESTAMP_INVALID = "timestamp_invalid"
    IDENTITY_INVALID = "identity_invalid"
    PROVENANCE_MISSING = "provenance_missing"
    LINEAGE_MISSING = "lineage_missing"
    PROVIDER_FIELD = "provider_field"
    PRECISION_INVALID = "precision_invalid"
    SCALE_INVALID = "scale_invalid"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One deterministic validation finding."""

    code: ValidationCode
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """Validation result with explicit quality state and immutable findings."""

    result: ValidationResult
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return self.result is ValidationResult.VALID


_INCOMPLETE_CODES = frozenset(
    {
        ValidationCode.REQUIRED_MISSING,
        ValidationCode.NULL_NOT_ALLOWED,
        ValidationCode.PROVENANCE_MISSING,
        ValidationCode.LINEAGE_MISSING,
    }
)


def validation_outcome(issues: Iterable[ValidationIssue]) -> ValidationOutcome:
    """Map deterministic primitive findings to the authoritative outcome model.

    Missing required evidence is INCOMPLETE. Any other validation finding is
    REJECTED. An empty finding set is VALID. No repair, fallback, freshness,
    contradiction, or provider-specific state is inferred here.
    """

    normalized = tuple(issues)
    if not normalized:
        return ValidationOutcome(ValidationResult.VALID)
    if any(issue.code not in _INCOMPLETE_CODES for issue in normalized):
        return ValidationOutcome(ValidationResult.REJECTED, normalized)
    return ValidationOutcome(ValidationResult.INCOMPLETE, normalized)


@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    """Required upstream evidence reference for canonical semantic data."""

    provenance_id: str
    source: str
    method: str

    def __post_init__(self) -> None:
        _require_token(self.provenance_id, "provenance_id")
        _require_token(self.source, "source")
        _require_token(self.method, "method")


@dataclass(frozen=True, slots=True)
class LineageRef:
    """Immutable lineage reference linking canonical data to its parent evidence."""

    parent_id: str
    validation_stage: str

    def __post_init__(self) -> None:
        _require_token(self.parent_id, "parent_id")
        _require_token(self.validation_stage, "validation_stage")


_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


def _require_token(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be str")
    if not value or not _TOKEN.fullmatch(value):
        raise ValueError(f"{field} must be a non-empty semantic token")
    return value


def validate_semantic_token(value: object, field: str) -> ValidationIssue | None:
    """Validate provider-neutral identity/classification token syntax."""

    if not isinstance(value, str):
        return ValidationIssue(ValidationCode.INVALID_TYPE, field, f"{field} must be str")
    if not value or not _TOKEN.fullmatch(value):
        return ValidationIssue(ValidationCode.IDENTITY_INVALID, field, f"{field} has invalid semantic token syntax")
    return None


def validate_allowed(value: object, field: str, allowed: Iterable[str]) -> ValidationIssue | None:
    """Validate a semantic value against an explicitly governed vocabulary.

    The caller supplies the authoritative vocabulary; this module never
    invents provider or venue-specific values.
    """

    issue = validate_semantic_token(value, field)
    if issue is not None:
        return issue
    allowed_set = frozenset(allowed)
    if value not in allowed_set:
        return ValidationIssue(ValidationCode.INVALID_VALUE, field, f"{field} is not in the governed vocabulary")
    return None


def require_decimal(value: object, field: str) -> Decimal:
    """Require an exact finite Decimal; floats and non-finite values are rejected."""

    if isinstance(value, float):
        raise TypeError(f"{field} must be Decimal; float is forbidden")
    if not isinstance(value, Decimal):
        raise TypeError(f"{field} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field} must be finite")
    return value


def validate_decimal_scale(value: object, field: str, scale: int) -> Decimal:
    """Validate a Decimal against an explicit maximum fractional scale.

    No rounding or quantization is performed. A value whose exponent exceeds
    the declared scale is rejected so invalid precision is never silently
    repaired.
    """

    if not isinstance(scale, int) or isinstance(scale, bool) or scale < 0:
        raise ValueError("scale must be a non-negative integer")
    decimal_value = require_decimal(value, field)
    fractional_digits = max(0, -decimal_value.as_tuple().exponent)
    if fractional_digits > scale:
        raise ValueError(f"{field} exceeds declared scale {scale}")
    return decimal_value


def validate_timestamp(value: object, field: str = "timestamp") -> datetime:
    """Require an aware UTC datetime without consulting the wall clock."""

    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field} must use UTC")
    return value


def validate_provenance(value: object, field: str = "provenance") -> ValidationIssue | None:
    """Validate that canonical data carries a valid immutable provenance reference."""

    if value is None:
        return ValidationIssue(ValidationCode.PROVENANCE_MISSING, field, f"{field} is required")
    if not isinstance(value, ProvenanceRef):
        return ValidationIssue(ValidationCode.INVALID_TYPE, field, f"{field} must be ProvenanceRef")
    return None


def canonical_json(value: Mapping[str, Any]) -> str:
    """Serialize identity material deterministically without provider aliases."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deterministic_identity(parts: Mapping[str, Any]) -> str:
    """Return SHA-256 of canonical semantic identity material."""

    if not isinstance(parts, Mapping) or not parts:
        raise ValueError("identity material must be a non-empty mapping")
    payload = canonical_json(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_required_fields(values: Mapping[str, Any], required: Iterable[str]) -> tuple[ValidationIssue, ...]:
    """Report absent and explicit-null required fields without fabricating values."""

    issues: list[ValidationIssue] = []
    for field in required:
        if field not in values:
            issues.append(ValidationIssue(ValidationCode.REQUIRED_MISSING, field, f"{field} is required"))
        elif values[field] is None:
            issues.append(ValidationIssue(ValidationCode.NULL_NOT_ALLOWED, field, f"{field} cannot be null"))
    return tuple(issues)
