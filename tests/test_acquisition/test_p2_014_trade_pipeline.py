from __future__ import annotations

import unittest
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
