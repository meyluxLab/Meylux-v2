"""Provider abstraction boundary for Meylux V2 acquisition.

Provider implementations own external I/O and wire-format translation. This
module intentionally contains no provider-specific implementation or runtime
connectivity.
"""
from __future__ import annotations

from typing import Protocol, Sequence

from contracts.acquisition import ProviderCapability, ProviderIdentity


SID = "CMP-P2-001"
VERSION = "1.0.0"


class ProviderAdapter(Protocol):
    """Minimal provider-neutral adapter contract for later Phase 2 steps."""

    @property
    def identity(self) -> ProviderIdentity:
        """Return the immutable provider/adapter identity."""
        ...

    def capabilities(self) -> Sequence[ProviderCapability]:
        """Return provider capabilities without performing provider I/O."""
        ...
