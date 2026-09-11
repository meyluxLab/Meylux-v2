"""Queue bridge for Phase 2 acquisition evidence."""
from __future__ import annotations

import base64
from typing import Any, Protocol

from contracts.acquisition import AcquisitionEnvelope
from meylux.queue.model import QueueEnvelope

SID = "STEP-P2-004"
PAYLOAD_CONTRACT = "CTR-P2-001"


class QueuePublisher(Protocol):
    async def publish(self, envelope: QueueEnvelope) -> str: ...


class AcquisitionQueuePublisher:
    """Adapt AcquisitionEnvelope to the existing bounded QueueEnvelope contract.

    Canonical bytes are carried as base64 so no Decimal/tuple payload type is
    reconstructed or normalized by the transport bridge.
    """

    def __init__(self, queue: QueuePublisher) -> None:
        self._queue = queue

    @staticmethod
    def to_queue_envelope(envelope: AcquisitionEnvelope) -> QueueEnvelope:
        canonical = envelope.canonical_bytes()
        return QueueEnvelope(
            message_id=envelope.event_id,
            idempotency_key=envelope.deduplication_key,
            payload_contract=PAYLOAD_CONTRACT,
            payload={
                "event_id": envelope.event_id,
                "canonical_b64": base64.b64encode(canonical).decode("ascii"),
                "provider_id": envelope.provider.provider_id,
                "source_sequence": envelope.source_sequence,
            },
        )

    async def publish(self, envelope: AcquisitionEnvelope) -> str:
        return await self._queue.publish(self.to_queue_envelope(envelope))
