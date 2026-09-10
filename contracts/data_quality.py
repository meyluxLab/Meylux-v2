"""Foundational V2 data-quality representation.

This module is deliberately provider-neutral and deterministic.  It represents
quality/lifecycle facts supplied by validation boundaries; it never derives
freshness from a wall clock and never manufactures missing evidence.
"""

from dataclasses import dataclass
from enum import Enum


class DataLifecycleState(str, Enum):
    """Lifecycle states defined by the frozen V2 architecture."""

    RAW = "RAW"
    STAGED = "STAGED"
    VALIDATING = "VALIDATING"
    NORMALIZED = "NORMALIZED"
    CANONICAL = "CANONICAL"
    QUALITY_DEGRADED = "QUALITY_DEGRADED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class DataQualityState(str, Enum):
    """Quality outcomes defined by the V2 architecture."""

    VALID = "VALID"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"
    CONTRADICTORY = "CONTRADICTORY"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"


_CANONICAL_PROMOTION_BLOCK_STATES = frozenset(
    {DataQualityState.REJECTED, DataQualityState.UNAVAILABLE}
)


@dataclass(frozen=True, slots=True)
class DataQuality:
    """Immutable, explicit quality evidence attached to a data item.

    ``reason_codes`` is descriptive validation evidence, not an instruction to
    repair or replace the underlying data.  Empty reasons are permitted so the
    representation can faithfully carry an upstream state whose reason is not
    available; the quality state itself must never be fabricated.
    """

    quality_state: DataQualityState
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.quality_state, DataQualityState):
            raise TypeError("quality_state must be a DataQualityState")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be a tuple")
        seen: set[str] = set()
        for code in self.reason_codes:
            if not isinstance(code, str):
                raise TypeError("reason codes must be strings")
            if not code.strip():
                raise ValueError("reason codes must be non-empty")
            if code in seen:
                raise ValueError("reason codes must be unique")
            seen.add(code)

    @property
    def blocks_canonical_promotion(self) -> bool:
        """Return whether architecture explicitly forbids canonical promotion."""

        return self.quality_state in _CANONICAL_PROMOTION_BLOCK_STATES


def validate_quality_lifecycle(
    quality: DataQuality, lifecycle_state: DataLifecycleState
) -> None:
    """Validate the explicit quality/lifecycle boundary deterministically.

    The only cross-state rules enforced here are those directly required by
    the architecture: rejected/unavailable data cannot be represented as
    canonical truth.  No freshness, completeness, contradiction, or repair
    policy is inferred beyond the stated quality outcome.
    """

    if not isinstance(quality, DataQuality):
        raise TypeError("quality must be a DataQuality instance")
    if not isinstance(lifecycle_state, DataLifecycleState):
        raise TypeError("lifecycle_state must be a DataLifecycleState")
    if lifecycle_state == DataLifecycleState.CANONICAL and quality.blocks_canonical_promotion:
        raise ValueError(
            "REJECTED or UNAVAILABLE data cannot be represented as CANONICAL"
        )
