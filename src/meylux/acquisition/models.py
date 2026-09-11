"""Persistence model for Phase 2 raw/staging acquisition evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

SID = "STEP-P2-004"


@dataclass(frozen=True, slots=True)
class RawAcquisitionRecord:
    event_id: str
    provider_id: str
    adapter_id: str
    adapter_version: str
    canonical_instrument_id: str
    provider_instrument_id: str
    event_type: str
    event_time: datetime
    received_at: datetime
    acquisition_state: str
    source_sequence: str | None
    provenance_id: str
    acquisition_method: str
    payload_json: dict[str, Any]
    canonical_bytes: bytes
    identity_hash: str
    persisted_at: datetime | None = None
