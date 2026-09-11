"""Bounded Phase 2 acquisition collector and persistence worker."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Mapping, Protocol, Sequence

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


class AcquisitionCollector:
    """Provider-isolated, bounded fan-in collector.

    The collector never normalizes provider payloads. Each provider stream is
    independently supervised; a provider failure cannot stop the other stream.
    """

    def __init__(
        self,
        adapters: Mapping[str, StreamAdapter],
        sink: CollectorSink,
        *,
        max_queue_size: int = 256,
        max_concurrency: int = 1,
    ) -> None:
        if not adapters:
            raise ValueError("at least one provider adapter is required")
        if max_queue_size < 1 or max_concurrency < 1:
            raise ValueError("queue and concurrency bounds must be positive")
        self._adapters = dict(adapters)
        self._sink = sink
        self._queue: asyncio.Queue[AcquisitionEnvelope | None] = asyncio.Queue(maxsize=max_queue_size)
        self._max_concurrency = max_concurrency
        self._stats = CollectorStats()
        self._stop = asyncio.Event()

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def max_queue_size(self) -> int:
        return self._queue.maxsize

    @property
    def stats(self) -> CollectorStats:
        return self._stats

    async def publish(self, envelope: AcquisitionEnvelope) -> None:
        """Block rather than drop when the bounded collector queue is full."""
        if self._queue.full():
            self._stats = CollectorStats(
                self._stats.published,
                self._stats.persisted,
                self._stats.duplicates,
                self._stats.failures,
                self._stats.overloaded + 1,
            )
            emit(_LOG, Severity.WARNING, "collector.backpressure", provider=envelope.provider.provider_id, event_id=envelope.event_id, queue_size=self.queue_size, max_queue_size=self.max_queue_size)
        await self._queue.put(envelope)
        self._stats = CollectorStats(
            self._stats.published + 1,
            self._stats.persisted,
            self._stats.duplicates,
            self._stats.failures,
            self._stats.overloaded,
        )

    async def _consume(self) -> None:
        while not self._stop.is_set():
            envelope = await self._queue.get()
            try:
                if envelope is None:
                    return
                result = await self._sink.persist(envelope)
                self._stats = CollectorStats(
                    self._stats.published,
                    self._stats.persisted + int(result.inserted),
                    self._stats.duplicates + int(not result.inserted),
                    self._stats.failures,
                    self._stats.overloaded,
                )
                emit(_LOG, Severity.INFO, "collector.persisted", provider=envelope.provider.provider_id, event_id=envelope.event_id, outcome="INSERTED" if result.inserted else "DUPLICATE")
            except Exception as exc:
                self._stats = CollectorStats(
                    self._stats.published,
                    self._stats.persisted,
                    self._stats.duplicates,
                    self._stats.failures + 1,
                    self._stats.overloaded,
                )
                emit(_LOG, Severity.ERROR, "collector.persistence_failure", provider=envelope.provider.provider_id if envelope else "unknown", event_id=envelope.event_id if envelope else None, error_type=type(exc).__name__)
                # Persistence errors are isolated to this event. The repository
                # owns its transaction/retry policy; the collector must not spin
                # indefinitely on a poison event.
            finally:
                self._queue.task_done()

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
                self._stats = CollectorStats(
                    self._stats.published,
                    self._stats.persisted,
                    self._stats.duplicates,
                    self._stats.failures + 1,
                    self._stats.overloaded,
                )
                emit(_LOG, Severity.ERROR, "collector.provider_failure", provider=getattr(adapter.identity, "provider_id", "unknown"), error_type=type(exc).__name__)

        try:
            await asyncio.gather(*(run_provider(adapter) for adapter in self._adapters.values()))
            await self._queue.join()
            emit(_LOG, Severity.INFO, "collector.run_complete", providers=len(self._adapters), published=self._stats.published, persisted=self._stats.persisted, duplicates=self._stats.duplicates, failures=self._stats.failures, overloaded=self._stats.overloaded)
            return self._stats
        finally:
            self._stop.set()
            for _ in consumers:
                await self._queue.put(None)
            await asyncio.gather(*consumers, return_exceptions=True)


__all__ = ["AcquisitionCollector", "CollectorStats", "RawStagingRepository"]
