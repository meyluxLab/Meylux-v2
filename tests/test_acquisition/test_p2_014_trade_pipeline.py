from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from contracts.acquisition import (
    AcquisitionEnvelope,
    AcquisitionState,
    EventType,
    InstrumentIdentity,
    ProviderIdentity,
    Provenance,
)
from meylux.acquisition.trade_pipeline import TradeAcquisitionPipeline
from meylux.persistence.canonical import PersistenceResult as CanonicalPersistenceResult
from meylux.persistence.quality_evidence import QualityEvidencePersistenceResult
from meylux.acquisition.persistence import PersistenceResult as RawPersistenceResult


class TradePipelineBoundaryTests(unittest.TestCase):
    def test_authorized_symbols_are_explicit_and_unique(self):
        self.assertEqual(
            TradeAcquisitionPipeline.validate_symbols(["btcusdt", "SOLUSDT"]),
            ("BTCUSDT", "SOLUSDT"),
        )

    def test_duplicate_symbol_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicates"):
            TradeAcquisitionPipeline.validate_symbols(["BTCUSDT", "btcusdt"])

    def test_unauthorized_symbol_is_rejected_without_substitution(self):
        with self.assertRaisesRegex(ValueError, "unauthorized"):
            TradeAcquisitionPipeline.validate_symbols(["ETHUSDT"])

    def test_empty_symbol_is_rejected(self):
        with self.assertRaises(ValueError):
            TradeAcquisitionPipeline.validate_symbols([""])


    def test_pipeline_composes_raw_quality_and_canonical_boundaries(self):
        provider = ProviderIdentity("binance", "binance-acquisition", "1.0.0")
        envelope = AcquisitionEnvelope(
            provider=provider,
            instrument=InstrumentIdentity("BINANCE:BTCUSDT", "BTCUSDT"),
            provenance=Provenance("binance:binance-acquisition", provider, "REST"),
            event_type=EventType.TRADE,
            event_time=datetime(2026, 10, 6, 18, 0, tzinfo=timezone.utc),
            received_at=datetime(2026, 10, 6, 18, 0, 1, tzinfo=timezone.utc),
            state=AcquisitionState.AVAILABLE,
            payload={"id": 123, "price": Decimal("100"), "qty": Decimal("2"), "time": 1791309600000},
            source_sequence="123",
        )
        adapter = type("Adapter", (), {"fetch_trades": lambda self, symbol, limit: (envelope,)})()
        raw = type("Raw", (), {"persist": AsyncMock(return_value=RawPersistenceResult(envelope.event_id, True))})()
        quality = type("Quality", (), {"persist": AsyncMock(return_value=QualityEvidencePersistenceResult("e", True, False))})()
        canonical = type("Canonical", (), {"persist": AsyncMock(return_value=CanonicalPersistenceResult("r", "e", True, 1))})()

        with patch("meylux.acquisition.trade_pipeline.RawStagingRepository", return_value=raw), \
             patch("meylux.acquisition.trade_pipeline.QualityEvidencePersistence", return_value=quality), \
             patch("meylux.acquisition.trade_pipeline.CanonicalPersistence", return_value=canonical):
            result = __import__("asyncio").run(
                TradeAcquisitionPipeline(object(), adapter=adapter, trade_limit=1).acquire_once(["BTCUSDT"])
            )

        self.assertEqual(result.available_trades, 1)
        self.assertEqual(result.raw_inserted, 1)
        self.assertEqual(result.quality_evidence_inserted, 1)
        self.assertEqual(result.canonical_inserted, 1)
        raw.persist.assert_awaited_once_with(envelope)
        quality.persist.assert_awaited_once()
        canonical.persist.assert_awaited_once()

    def test_replay_same_evidence_is_idempotent(self):
        provider = ProviderIdentity("binance", "binance-acquisition", "1.0.0")
        envelope = AcquisitionEnvelope(
            provider=provider,
            instrument=InstrumentIdentity("BINANCE:BTCUSDT", "BTCUSDT"),
            provenance=Provenance("binance:binance-acquisition", provider, "REST"),
            event_type=EventType.TRADE,
            event_time=datetime(2026, 10, 6, 18, 0, tzinfo=timezone.utc),
            received_at=datetime(2026, 10, 6, 18, 0, 1, tzinfo=timezone.utc),
            state=AcquisitionState.AVAILABLE,
            payload={"id": 123, "price": Decimal("100"), "qty": Decimal("2"), "time": 1791309600000},
            source_sequence="123",
        )
        adapter = type("Adapter", (), {"fetch_trades": lambda self, symbol, limit: (envelope,)})()
        raw = type("Raw", (), {"persist": AsyncMock(side_effect=[
            RawPersistenceResult(envelope.event_id, True),
            RawPersistenceResult(envelope.event_id, False),
        ])})()
        quality = type("Quality", (), {"persist": AsyncMock(side_effect=[
            QualityEvidencePersistenceResult("e", True, False),
            QualityEvidencePersistenceResult("e", False, False),
        ])})()
        canonical = type("Canonical", (), {"persist": AsyncMock(side_effect=[
            CanonicalPersistenceResult("r", "e", True, 1),
            CanonicalPersistenceResult("r", "e", False, 1),
        ])})()

        with patch("meylux.acquisition.trade_pipeline.RawStagingRepository", return_value=raw), \
             patch("meylux.acquisition.trade_pipeline.QualityEvidencePersistence", return_value=quality), \
             patch("meylux.acquisition.trade_pipeline.CanonicalPersistence", return_value=canonical):
            result = __import__("asyncio").run(
                TradeAcquisitionPipeline(object(), adapter=adapter, trade_limit=1).acquire_once(
                    ["BTCUSDT"], replay_same_evidence=True
                )
            )

        self.assertTrue(result.replay_executed)
        self.assertEqual(result.raw_inserted, 1)
        self.assertEqual(result.raw_duplicates, 1)
        self.assertEqual(result.quality_evidence_inserted, 1)
        self.assertEqual(result.quality_evidence_duplicates, 1)
        self.assertEqual(result.quality_evidence_contradictory, 0)
        self.assertEqual(result.canonical_inserted, 1)
        self.assertEqual(result.canonical_duplicates, 1)
        self.assertEqual(raw.persist.await_count, 2)
        self.assertEqual(quality.persist.await_count, 2)
        self.assertEqual(canonical.persist.await_count, 2)


    def test_trade_envelope_identity_is_deterministic(self):
        provider = ProviderIdentity("binance", "binance-acquisition", "1.0.0")
        envelope = AcquisitionEnvelope(
            provider=provider,
            instrument=InstrumentIdentity("BINANCE:BTCUSDT", "BTCUSDT"),
            provenance=Provenance("binance:binance-acquisition", provider, "REST"),
            event_type=EventType.TRADE,
            event_time=datetime(2026, 10, 6, 18, 0, tzinfo=timezone.utc),
            received_at=datetime(2026, 10, 6, 18, 0, 1, tzinfo=timezone.utc),
            state=AcquisitionState.AVAILABLE,
            payload={"id": 123, "price": Decimal("100"), "qty": Decimal("2"), "time": 1791309600000},
            source_sequence="123",
        )
        self.assertEqual(envelope.event_id, envelope.deduplication_key)
        self.assertEqual(envelope.event_id, envelope.event_id)


if __name__ == "__main__":
    unittest.main()
