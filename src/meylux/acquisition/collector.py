"""Bounded Phase 2 acquisition collector and persistence worker."""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Any, AsyncIterator, Deque, Mapping, Protocol, Sequence

from contracts.acquisition import AcquisitionEnvelope
from meylux.acquisition.persistence import PersistenceResult, RawStagingRepository
from meylux.observability import Severity, configure_logging, emit

SID = "STEP-P2-004"
_LOG = configure_logging(logger_name="meylux.acquisition.collector")


class StreamAdapter(Protocol):
    @property
    def identity(self) -> Any: ...

    async def stream(self, symbols: Sequence[str], **kwargs: Any) -> AsyncIterator[AcquisitionEnvelope]: ...


class CollectorSink(Protocol):
    async def persist(self, envelope: AcquisitionEnvelope) -> PersistenceResult: ...


@dataclass(frozen=True, slots=True)
class CollectorStats:
    published: int = 0
    persisted: int = 0
    duplicates: int = 0
    failures: int = 0
    overloaded: int = 0
    recovered: int = 0
    recovery_pending: int = 0


class PersistenceRecoveryOverflow(RuntimeError):
    """Raised instead of silently discarding an unrecoverable acquisition event."""


class AcquisitionCollector:
    """Provider-isolated, bounded fan-in collector.

    The collector never normalizes provider payloads. Each provider stream is
    independently supervised; a provider failure cannot stop the other stream.
    Persistence failures receive bounded retries and, if still unsuccessful,
    are retained in a bounded recovery buffer for explicit replay.
    """

    def __init__(
        self,
        adapters: Mapping[str, StreamAdapter],
        sink: CollectorSink,
        *,
        max_queue_size: int = 256,
        max_concurrency: int = 1,
        max_persistence_retries: int = 2,
        max_recovery_size: int | None = None,
    ) -> None:
        if not adapters:
            raise ValueError("at least one provider adapter is required")
        if max_queue_size < 1 or max_concurrency < 1:
            raise ValueError("queue and concurrency bounds must be positive")
        if max_persistence_retries < 0:
            raise ValueError("max_persistence_retries must be non-negative")
        if max_recovery_size is not None and max_recovery_size < 1:
            raise ValueError("max_recovery_size must be positive")
        self._adapters = dict(adapters)
        self._sink = sink
        self._queue: asyncio.Queue[AcquisitionEnvelope | None] = asyncio.Queue(maxsize=max_queue_size)
        self._max_concurrency = max_concurrency
        self._max_persistence_retries = max_persistence_retries
        self._max_recovery_size = max_recovery_size if max_recovery_size is not None else max_queue_size
        self._recovery: Deque[AcquisitionEnvelope] = deque()
        self._retry_counts: dict[str, int] = {}
        self._stats = CollectorStats()
        self._stop = asyncio.Event()

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def max_queue_size(self) -> int:
        return self._queue.maxsize

    @property
    def recovery_size(self) -> int:
        return len(self._recovery)

    @property
    def max_recovery_size(self) -> int:
        return self._max_recovery_size

    @property
    def recovery_items(self) -> tuple[AcquisitionEnvelope, ...]:
        return tuple(self._recovery)

    @property
    def stats(self) -> CollectorStats:
        return self._stats

    def _set_stats(self, **changes: int) -> None:
        values = {
            "published": self._stats.published,
            "persisted": self._stats.persisted,
            "duplicates": self._stats.duplicates,
            "failures": self._stats.failures,
            "overloaded": self._stats.overloaded,
            "recovered": self._stats.recovered,
            "recovery_pending": self._stats.recovery_pending,
        }
        values.update(changes)
        self._stats = CollectorStats(**values)

    async def publish(self, envelope: AcquisitionEnvelope) -> None:
        """Block rather than drop when the bounded collector queue is full."""
        if self._queue.full():
            self._set_stats(overloaded=self._stats.overloaded + 1)
            emit(_LOG, Severity.WARNING, "collector.backpressure", provider=envelope.provider.provider_id, event_id=envelope.event_id, queue_size=self.queue_size, max_queue_size=self.max_queue_size)
        await self._queue.put(envelope)
        self._set_stats(published=self._stats.published + 1)

    async def _persist_with_recovery(self, envelope: AcquisitionEnvelope) -> bool:
        """Persist once with bounded retries; return whether the event resolved."""
        event_id = envelope.event_id
        for attempt in range(self._max_persistence_retries + 1):
            try:
                result = await self._sink.persist(envelope)
                self._retry_counts.pop(event_id, None)
                self._set_stats(
                    persisted=self._stats.persisted + int(result.inserted),
                    duplicates=self._stats.duplicates + int(not result.inserted),
                    recovered=self._stats.recovered + int(attempt > 0),
                    recovery_pending=len(self._recovery),
                )
                emit(_LOG, Severity.INFO, "collector.persisted", provider=envelope.provider.provider_id, event_id=event_id, outcome="INSERTED" if result.inserted else "DUPLICATE", attempts=attempt + 1)
                return True
            except Exception as exc:
                self._set_stats(failures=self._stats.failures + 1)
                if attempt < self._max_persistence_retries:
                    self._retry_counts[event_id] = attempt + 1
                    emit(_LOG, Severity.WARNING, "collector.persistence_retry", provider=envelope.provider.provider_id, event_id=event_id, attempt=attempt + 1, max_retries=self._max_persistence_retries, error_type=type(exc).__name__)
                    continue
                if len(self._recovery) >= self._max_recovery_size:
                    emit(_LOG, Severity.CRITICAL, "collector.recovery_overflow", provider=envelope.provider.provider_id, event_id=event_id, recovery_size=self.recovery_size, max_recovery_size=self.max_recovery_size, error_type=type(exc).__name__)
                    self._stop.set()
                    raise PersistenceRecoveryOverflow(
                        f"bounded persistence recovery capacity exhausted for event {event_id}"
                    ) from exc
                self._recovery.append(envelope)
                self._retry_counts.pop(event_id, None)
                self._set_stats(recovery_pending=len(self._recovery))
                emit(_LOG, Severity.ERROR, "collector.persistence_recovery_pending", provider=envelope.provider.provider_id, event_id=event_id, attempts=attempt + 1)
                return False
        return False

    async def _consume(self) -> None:
        while not self._stop.is_set():
            envelope = await self._queue.get()
            try:
                if envelope is None:
                    return
                await self._persist_with_recovery(envelope)
            finally:
                self._queue.task_done()

    async def replay_recovery(self) -> int:
        """Replay each currently retained failed event at most once."""
        resolved = 0
        pending_at_start = len(self._recovery)
        for _ in range(pending_at_start):
            item = self._recovery.popleft()
            self._set_stats(recovery_pending=len(self._recovery))
            if await self._persist_with_recovery(item):
                resolved += 1
        self._set_stats(recovery_pending=len(self._recovery))
        return resolved

    async def collect_once(
        self,
        symbols: Sequence[str],
        *,
        max_messages_per_provider: int = 1,
        max_reconnects: int = 0,
    ) -> CollectorStats:
        """Collect a finite sample from every configured provider."""
        if not symbols:
            raise ValueError("symbols must not be empty")
        if max_messages_per_provider < 1 or max_reconnects < 0:
            raise ValueError("message/reconnect bounds are invalid")
        self._stop.clear()
        consumers = [asyncio.create_task(self._consume()) for _ in range(self._max_concurrency)]

        async def run_provider(adapter: StreamAdapter) -> None:
            try:
                async for envelope in adapter.stream(
                    symbols,
                    max_messages=max_messages_per_provider,
                    max_reconnects=max_reconnects,
                ):
                    await self.publish(envelope)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._set_stats(failures=self._stats.failures + 1)
                emit(_LOG, Severity.ERROR, "collector.provider_failure", provider=getattr(getattr(adapter, "identity", None), "provider_id", "unknown"), error_type=type(exc).__name__)

        try:
            await asyncio.gather(*(run_provider(adapter) for adapter in self._adapters.values()))
            await self._queue.join()
            emit(_LOG, Severity.INFO, "collector.run_complete", providers=len(self._adapters), published=self._stats.published, persisted=self._stats.persisted, duplicates=self._stats.duplicates, failures=self._stats.failures, overloaded=self._stats.overloaded, recovery_pending=self.recovery_size)
            return self._stats
        finally:
            self._stop.set()
            for _ in consumers:
                await self._queue.put(None)
            await asyncio.gather(*consumers, return_exceptions=True)


__all__ = ["AcquisitionCollector", "CollectorStats", "PersistenceRecoveryOverflow", "RawStagingRepository"]
