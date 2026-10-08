from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from contracts.acquisition import AcquisitionEnvelope, AcquisitionState, EventType, InstrumentIdentity, ProviderIdentity, Provenance, ProviderError
from meylux.acquisition.mexc_orderbook import MEXCOrderBookReconstructor, ReconstructionStatus

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


def env(payload, *, state=AcquisitionState.AVAILABLE, event_type=EventType.ORDER_BOOK, symbol="BTCUSDT", provider="mexc", sequence=None, when=NOW):
    p = ProviderIdentity(provider, f"{provider}-acquisition", "1.1.0")
    return AcquisitionEnvelope(
        p, InstrumentIdentity(symbol, symbol), Provenance(f"{provider}:orderbook:test", p, "TEST"),
        event_type, when, NOW, state, payload, sequence,
        ProviderError("TEST_FAILURE", "TEST", "failure") if state is not AcquisitionState.AVAILABLE else None,
    )


def snapshot(version=100, bids=(("100", "2"),), asks=(("101", "1"),), symbol=None):
    p = {"lastUpdateId": str(version), "bids": [list(x) for x in bids], "asks": [list(x) for x in asks]}
    if symbol is not None:
        p["symbol"] = symbol
    return env(p)


def depth(start, end, bids=(), asks=(), symbol="BTCUSDT"):
    return env({"symbol": symbol, "channel": "spot@public.aggre.depth.v3.api.pb@100ms@BTCUSDT",
                "data": {"fromVersion": str(start), "toVersion": str(end),
                         "bidsList": [{"price": p, "quantity": q} for p, q in bids],
                         "asksList": [{"price": p, "quantity": q} for p, q in asks]}})


class MEXCOrderBookTests(unittest.TestCase):
    def test_snapshot_bootstrap_and_canonicalization(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        out = r.apply_snapshot(snapshot())
        self.assertEqual(out.status, ReconstructionStatus.READY)
        self.assertEqual(out.version, 100)
        self.assertEqual(out.canonical.bids, ((Decimal("100"), Decimal("2")),))
        self.assertEqual(out.canonical.asks, ((Decimal("101"), Decimal("1")),))
        self.assertEqual(out.canonical.provenance_id, "mexc:orderbook:test")

    def test_missing_snapshot_version_is_invalid_and_not_canonicalized(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        out = r.apply_snapshot(env({"bids": [["100", "2"]], "asks": [["101", "1"]]}))
        self.assertEqual(out.status, ReconstructionStatus.INVALID)
        self.assertIsNone(r.canonical())

    def test_malformed_snapshot_and_invalid_levels_are_rejected(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        for payload in (
            {"lastUpdateId": "x", "bids": [["100", "2"]], "asks": [["101", "1"]]},
            {"lastUpdateId": "1", "bids": [["0", "2"]], "asks": [["101", "1"]]},
            {"lastUpdateId": "1", "bids": [["100", "NaN"]], "asks": [["101", "1"]]},
            {"lastUpdateId": "1", "bids": [["100", "2"]], "asks": [["101", "1"], ["101", "2"]]},
            {"lastUpdateId": "1", "bids": [], "asks": []},
            {"lastUpdateId": "1", "bids": [["102", "2"]], "asks": [["101", "1"]]},
        ):
            out = r.apply_snapshot(env(payload))
            self.assertEqual(out.status, ReconstructionStatus.INVALID)
            self.assertIsNone(r.canonical())

    def test_contiguous_update_applies_absolute_quantities_and_removal(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot())
        out = r.apply_depth(depth(101, 102, bids=(("100", "3"), ("99", "1")), asks=(("101", "0"), ("102", "2"))))
        self.assertEqual(out.status, ReconstructionStatus.READY)
        self.assertEqual(out.version, 102)
        self.assertEqual(out.canonical.bids, ((Decimal("100"), Decimal("3")), (Decimal("99"), Decimal("1"))))
        self.assertEqual(out.canonical.asks, ((Decimal("102"), Decimal("2")),))

    def test_snapshot_update_overlap_boundary_is_accepted_only_at_bootstrap(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        out = r.apply_depth(depth(99, 101, bids=(("100", "3"),)))
        self.assertEqual(out.status, ReconstructionStatus.READY)
        self.assertEqual(out.version, 101)
        second = r.apply_depth(depth(101, 102, bids=(("100", "4"),)))
        self.assertEqual(second.status, ReconstructionStatus.READY)
        self.assertEqual(second.version, 102)

    def test_gap_requires_recovery_and_hides_stale_state(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        out = r.apply_depth(depth(103, 104, bids=(("100", "3"),)))
        self.assertEqual(out.status, ReconstructionStatus.RECOVERY_REQUIRED)
        self.assertIsNone(out.canonical)
        self.assertIsNone(r.canonical())

    def test_recovery_snapshot_is_deterministic(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        out = r.apply_depth_with_recovery(depth(103, 104), lambda: snapshot(200, bids=(("100", "5"),), asks=(("101", "2"),)))
        self.assertEqual(out.status, ReconstructionStatus.RECOVERED)
        self.assertEqual(out.version, 200)
        self.assertEqual(r.recovery_attempts, 1)
        self.assertEqual(out.canonical.bids, ((Decimal("100"), Decimal("5")),))

    def test_recovery_failure_leaves_state_unavailable(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        out = r.apply_depth_with_recovery(depth(103, 104), lambda: env({}, state=AcquisitionState.UNAVAILABLE))
        self.assertEqual(out.status, ReconstructionStatus.UNAVAILABLE)
        self.assertIsNone(r.canonical())
        self.assertEqual(r.recovery_attempts, 1)

    def test_repeated_recovery_failure_is_not_fabricated(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        for _ in range(2):
            out = r.apply_depth_with_recovery(depth(103, 104), lambda: (_ for _ in ()).throw(ConnectionError("offline")))
            self.assertEqual(out.status, ReconstructionStatus.UNAVAILABLE)
            self.assertIsNone(r.canonical())
        self.assertEqual(r.recovery_attempts, 2)

    def test_stale_and_equal_version_replays_do_not_regress(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot(100))
        r.apply_depth(depth(101, 102, bids=(("100", "3"),)))
        stale = r.apply_depth(depth(100, 100, bids=(("100", "99"),)))
        duplicate = r.apply_depth(depth(101, 102, bids=(("100", "99"),)))
        self.assertEqual(stale.status, ReconstructionStatus.STALE_IGNORED)
        self.assertEqual(duplicate.status, ReconstructionStatus.DUPLICATE_IGNORED)
        self.assertEqual(r.version, 102)
        self.assertEqual(r.canonical().bids[0][1], Decimal("3"))

    def test_version_regression_and_malformed_versions_are_rejected(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot())
        for start, end in (("bad", "102"), ("103", "102"), ("-1", "1")):
            out = r.apply_depth(depth(start, end))
            self.assertEqual(out.status, ReconstructionStatus.INVALID)
            self.assertIsNone(r.canonical())

    def test_provider_instrument_mismatch_is_rejected(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        self.assertEqual(r.apply_snapshot(snapshot(symbol="ETHUSDT")).status, ReconstructionStatus.INVALID)
        r.apply_snapshot(snapshot())
        self.assertEqual(r.apply_depth(depth(101, 101, symbol="ETHUSDT")).status, ReconstructionStatus.INVALID)

    def test_non_mexc_and_non_orderbook_inputs_are_rejected(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        self.assertEqual(r.apply_snapshot(env(snapshot().payload, provider="binance")).status, ReconstructionStatus.INVALID)
        self.assertEqual(r.apply_snapshot(env({}, event_type=EventType.TRADE)).status, ReconstructionStatus.INVALID)

    def test_disconnect_requires_recovery_without_canonical_state(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot())
        disconnected = env({}, state=AcquisitionState.DISCONNECTED)
        out = r.apply_depth(disconnected)
        self.assertEqual(out.status, ReconstructionStatus.DISCONNECTED)
        self.assertIsNone(r.canonical())

    def test_invalid_update_does_not_create_crossed_or_empty_book(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        r.apply_snapshot(snapshot())
        crossed = r.apply_depth(depth(101, 102, bids=(("101", "2"),)))
        self.assertEqual(crossed.status, ReconstructionStatus.RECOVERY_REQUIRED)
        self.assertIsNone(r.canonical())

    def test_replay_identity_is_deterministic(self):
        first = snapshot(100)
        second = snapshot(100)
        self.assertEqual(first.event_id, second.event_id)
        r1, r2 = MEXCOrderBookReconstructor("BTCUSDT"), MEXCOrderBookReconstructor("BTCUSDT")
        self.assertEqual(r1.apply_snapshot(first).canonical, r2.apply_snapshot(second).canonical)

    def test_provider_version_is_not_present_in_canonical_contract(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        canonical = r.apply_snapshot(snapshot(100)).canonical
        self.assertFalse(hasattr(canonical, "version"))
        self.assertFalse(hasattr(canonical, "fromVersion"))
        self.assertFalse(hasattr(canonical, "toVersion"))

    def test_restart_without_state_is_not_authoritative(self):
        r = MEXCOrderBookReconstructor("BTCUSDT")
        out = r.apply_depth(depth(101, 102))
        self.assertEqual(out.status, ReconstructionStatus.RECOVERY_REQUIRED)
        self.assertIsNone(out.canonical)

    def test_evidence_chain_is_bounded_and_replayable(self):
        r = MEXCOrderBookReconstructor("BTCUSDT", max_evidence_ids=3)
        r.apply_snapshot(snapshot(100))
        r.apply_depth(depth(101, 101, bids=(("100", "3"),)))
        r.apply_depth(depth(102, 102, bids=(("100", "4"),)))
        r.apply_depth(depth(103, 103, bids=(("100", "5"),)))
        self.assertEqual(len(r.evidence_event_ids()), 3)


if __name__ == "__main__":
    unittest.main()
