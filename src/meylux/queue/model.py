"""Deterministic queue/worker contracts for the V2 async foundation."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class WorkerSpec:
    """Worker ownership declaration; no Stable ID is invented."""
    logical_name: str
    primary_responsibility: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    allowed_dependencies: tuple[str, ...]
    forbidden_responsibilities: tuple[str, ...]
    side_effects: tuple[str, ...]
    resource_budget: str
    failure_isolation: str

    def __post_init__(self) -> None:
        if not self.logical_name.strip() or not self.primary_responsibility.strip():
            raise ValueError("worker identity and responsibility are required")
        if not self.resource_budget.strip() or not self.failure_isolation.strip():
            raise ValueError("worker resource and failure-isolation rules are required")


@dataclass(frozen=True, slots=True)
class QueuePolicy:
    """Explicit, bounded queue safety and ownership policy."""
    name: str
    owner: str
    producer: str
    consumer: str
    purpose: str
    payload_contract: str
    dlq_name: str
    max_backlog: int
    max_concurrency: int
    max_attempts: int
    timeout_seconds: float
    backoff_seconds: float
    retention_seconds: int
    ordering: str = "FIFO_ENQUEUE_AND_DELIVERY"
    idempotency_required: bool = True
    recovery_method: str = "consumer-group stale-claim"

    def __post_init__(self) -> None:
        fields = (self.name, self.owner, self.producer, self.consumer, self.purpose, self.payload_contract, self.dlq_name)
        if any(not value.strip() for value in fields):
            raise ValueError("queue ownership and semantic fields must be non-empty")
        if self.max_backlog < 1 or self.max_concurrency < 1 or self.max_attempts < 1:
            raise ValueError("bounds must be positive")
        if self.timeout_seconds <= 0 or self.backoff_seconds < 0 or self.retention_seconds < 1:
            raise ValueError("timeout/backoff/retention bounds are invalid")
        if self.ordering != "FIFO_ENQUEUE_AND_DELIVERY":
            raise ValueError("ordering must explicitly be FIFO enqueue and delivery order")
        if not self.recovery_method.strip():
            raise ValueError("recovery method is required")


@dataclass(frozen=True, slots=True)
class QueueEnvelope:
    """Transport-neutral job envelope with explicit retry/idempotency state."""
    message_id: str
    idempotency_key: str
    payload_contract: str
    payload: Mapping[str, Any]
    attempt: int = 1

    def __post_init__(self) -> None:
        if not self.message_id.strip() or not self.idempotency_key.strip():
            raise ValueError("message_id and idempotency_key must be non-empty")
        if not self.payload_contract.strip() or not isinstance(self.payload, Mapping):
            raise ValueError("payload contract and payload are required")
        if self.attempt < 1:
            raise ValueError("attempt must be positive")

    def to_json(self) -> str:
        return json.dumps({
            "message_id": self.message_id,
            "idempotency_key": self.idempotency_key,
            "payload_contract": self.payload_contract,
            "payload": dict(self.payload),
            "attempt": self.attempt,
        }, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "QueueEnvelope":
        raw = json.loads(value)
        return cls(
            message_id=raw["message_id"],
            idempotency_key=raw["idempotency_key"],
            payload_contract=raw["payload_contract"],
            payload=raw["payload"],
            attempt=raw["attempt"],
        )


class QueueOverloaded(RuntimeError):
    """Raised when the explicit backlog bound rejects new work."""


class DuplicateMessage(RuntimeError):
    """Raised when an idempotency key is already accepted by the queue."""


@dataclass(frozen=True, slots=True)
class ProcessingOutcome:
    status: str
    attempt: int
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ACKED", "RETRY", "DLQ"}:
            raise ValueError("invalid processing outcome")
