"""Authoritative Phase-3 canonical persistence boundary."""

from .canonical import (
    CanonicalPersistence,
    CanonicalRecord,
    PersistenceResult,
    UnsupportedCanonicalState,
)

__all__ = [
    "CanonicalPersistence",
    "CanonicalRecord",
    "PersistenceResult",
    "UnsupportedCanonicalState",
]
