"""Bounded Binance Spot trade acquisition vertical slice for P2/PRQ-2.

The pipeline deliberately composes existing provider, raw-staging, P3 quality,
quality-evidence, normalization, and canonical persistence contracts. It does
not introduce a second truth source or synthesize missing market evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol, Sequence

from contracts.acquisition import AcquisitionEnvelope, AcquisitionState
from contracts.canonical.foundation import ProvenanceRef
from contracts.canonical.foundation import ValidationResult
from contracts.normalization import NormalizationOutcome, normalize
from contracts.quality import QualityInput, QualitySignals, assess_quality
from contracts.quality_evidence import build_quality_evidence
from meylux.acquisition.binance import BinanceAdapter
from meylux.persistence.canonical import CanonicalPersistence
from meylux.persistence.factory import build_canonical_event
from meylux.acquisition.persistence import RawStagingRepository
from meylux.persistence.quality_evidence import QualityEvidencePersistence

SID = "TO-P2-014"
AUTHORIZED_SYMBOLS = frozenset({"BTCUSDT", "SOLUSDT"})


class TradeAcquisitionConnection(Protocol):
    async def execute(self, query: str, *args: Any) -> Any: ...
    async def fetchrow(self, query: str, *args: Any) -> Any: ...
    async def fetch(self, query: str, *args: Any) -> Any: ...
    def transaction(self) -> Any: ...


@dataclass(frozen=True, slots=True)
class TradeAcquisitionResult:
    symbols: tuple[str, ...]
    envelopes: int
    available_trades: int
    raw_inserted: int
    raw_duplicates: int
    quality_evidence_inserted: int
    canonical_inserted: int
    canonical_duplicates: int
    invalid_or_unavailable: int
    earliest_event_time: datetime | None
    latest_event_time: datetime | None

    @property
    def observed_history_seconds(self) -> int:
        if self.earliest_event_time is None or self.latest_event_time is None:
            return 0
        return max(0, int((self.latest_event_time - self.earliest_event_time).total_seconds()))


class TradeAcquisitionPipeline:
    """One bounded acquisition pass over the explicitly authorized symbols."""

    def __init__(
        self,
        connection: TradeAcquisitionConnection,
        *,
        adapter: BinanceAdapter | None = None,
        trade_limit: int = 1000,
    ) -> None:
        if isinstance(trade_limit, bool) or not isinstance(trade_limit, int) or not 1 <= trade_limit <= 1000:
            raise ValueError("trade_limit must be an integer in 1..1000")
        self._connection = connection
        self._adapter = adapter or BinanceAdapter()
        self._trade_limit = trade_limit

    @staticmethod
    def validate_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
        if isinstance(symbols, (str, bytes)) or not symbols:
            raise ValueError("symbols must be a non-empty sequence")
        normalized = tuple(str(symbol).strip().upper() for symbol in symbols)
        if any(not symbol for symbol in normalized):
            raise ValueError("symbols must not contain empty values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("symbols must not contain duplicates")
        unauthorized = sorted(set(normalized) - AUTHORIZED_SYMBOLS)
        if unauthorized:
            raise ValueError(f"unauthorized Binance Spot trade symbols: {', '.join(unauthorized)}")
        return normalized

    async def acquire_once(self, symbols: Sequence[str]) -> TradeAcquisitionResult:
        normalized_symbols = self.validate_symbols(symbols)
        raw = RawStagingRepository(self._connection)
        quality_repo = QualityEvidencePersistence(self._connection)
        canonical_repo = CanonicalPersistence(self._connection)

        envelopes: list[AcquisitionEnvelope] = []
        for symbol in normalized_symbols:
            envelopes.extend(self._adapter.fetch_trades(symbol, limit=self._trade_limit))

        raw_inserted = raw_duplicates = quality_inserted = canonical_inserted = canonical_duplicates = invalid = 0
        available = 0
        times: list[datetime] = []
        canonical_sequence = 0

        for envelope in envelopes:
            raw_result = await raw.persist(envelope)
            if raw_result.inserted:
                raw_inserted += 1
            else:
                raw_duplicates += 1

            outcome: NormalizationOutcome = normalize(envelope)
            provenance = ProvenanceRef(
                envelope.provenance.provenance_id,
                envelope.provider.provider_id,
                envelope.provenance.acquisition_method,
            )
            assessment = assess_quality(
                QualityInput(
                    outcome_to_validation(outcome),
                    QualitySignals(
                        validation_status=Decimal("1.00")
                        if outcome.result is ValidationResult.VALID
                        else Decimal("0.00"),
                        provider_capability=Decimal("1.00")
                        if envelope.state is AcquisitionState.AVAILABLE
                        else Decimal("0.00"),
                    ),
                    provenance,
                    envelope.event_id,
                    envelope.event_id,
                    capability_state=None,
                )
            )
            evidence = build_quality_evidence(envelope, assessment)
            evidence_result = await quality_repo.persist(evidence)
            if evidence_result.inserted:
                quality_inserted += 1

            if envelope.state is not AcquisitionState.AVAILABLE or not outcome.valid:
                invalid += 1
                continue

            available += 1
            times.append(envelope.event_time)

            canonical_sequence += 1
            record, event = build_canonical_event(
                outcome.value,
                assessment,
                canonical_sequence,
            )
            canonical_result = await canonical_repo.persist(record, event.to_json(), assessment)
            if canonical_result.inserted:
                canonical_inserted += 1
            else:
                canonical_duplicates += 1

        earliest = min(times) if times else None
        latest = max(times) if times else None
        return TradeAcquisitionResult(
            normalized_symbols,
            len(envelopes),
            available,
            raw_inserted,
            raw_duplicates,
            quality_inserted,
            canonical_inserted,
            canonical_duplicates,
            invalid,
            earliest,
            latest,
        )


def outcome_to_validation(outcome: NormalizationOutcome):
    from contracts.canonical.foundation import ValidationOutcome
    return ValidationOutcome(outcome.result, outcome.issues)
