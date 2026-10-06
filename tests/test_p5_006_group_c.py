from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from contracts.specialist import EvidenceRef, FactStatus, SpecialistStatus
from meylux.specialists.snapshot import InputSnapshotBuilder, SnapshotRecord
from meylux.specialists.group_c import analyze_s03, analyze_s17, GroupCSemanticError


UTC = timezone.utc
T0 = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


class Config:
    name = "p5-specialists"
    version = "1.3.0"
    environment = "test"
    identity_hash = "a" * 64

    def parameter(self, key):
        return {
            "group_c_symbols": "BTCUSDT",
            "group_c_timeframes": "15m",
            "group_c_venues": "BINANCE",
            "group_c_max_findings": 200,
            "max_evidence_refs": 100,
        }[key]

    def ref(self):
        from contracts.specialist import SpecialistConfigRef
        return SpecialistConfigRef(self.name, self.version, self.identity_hash, self.environment)


CFG = Config()


def ref(record_id: str, event_time: datetime, venue: str = "BINANCE") -> EvidenceRef:
    return EvidenceRef(
        evidence_id="e-" + record_id,
        source_type="P4",
        source_reference=f"p4:{record_id}",
        identity_hash="b" * 64,
        source_family="P4:FACT",
        record_id=record_id,
        event_time=event_time,
        knowledge_time=event_time,
        timeframe="15m",
        venue=venue,
    )


def fact(
    fact_id: str,
    source_table: str,
    record_id: str,
    value,
    event_time: datetime,
    *,
    status=FactStatus.VALID,
    venue="BINANCE",
    knowledge_time=None,
):
    kt = knowledge_time or event_time
    evidence = (ref(record_id, event_time, venue),)
    metadata = {
        "symbol": "BTCUSDT",
        "venue": venue,
        "product": "SPOT",
        "timeframe": "15m",
        "source_table": source_table,
        "record_id": record_id,
        "identity_hash": "b" * 64,
        "version": "1.0.0",
        "event_time": event_time,
        "knowledge_time": kt,
    }
    return SnapshotRecord(
        fact_id=fact_id,
        status=status,
        value=value,
        event_time=event_time,
        knowledge_time=kt,
        evidence_refs=evidence,
        reason=None if status is FactStatus.VALID else "explicit unavailable test state",
        metadata=metadata,
    )


def snapshot(records):
    return InputSnapshotBuilder().build(as_of=T0 + timedelta(hours=2), records=records)


def indicator(name, i, value, *, status=FactStatus.VALID):
    t = T0 + timedelta(minutes=15 * i)
    return fact(
        f"{name}:{i}", "meylux.calculated_indicator_vectors", f"{name}:{i}",
        {"fact_name": name, "value": value, "status": status.value},
        t, status=status,
    )


def candle(i, close, high=None, low=None):
    t = T0 + timedelta(minutes=15 * i)
    close = Decimal(str(close))
    high = Decimal(str(high if high is not None else close + 1))
    low = Decimal(str(low if low is not None else close - 1))
    return fact(
        f"candle:{i}", "meylux.canonical_candles", f"candle:{i}",
        {"open": close, "high": high, "low": low, "close": close, "close_time": t + timedelta(minutes=15)},
        t,
    )


def profile(i, start, end, poc="100", vah="105", val="95", hvn="103", lvn="97"):
    t = end
    return fact(
        f"profile:{i}", "meylux.volume_profile_sessions", f"profile:{i}",
        {
            "profile_interval": {"start": start, "end": end, "boundary": "[start,end)"},
            "facts": {
                "POC": {"value": poc, "status": "VALID", "reason": "volume_profile_analysis"},
                "VAH": {"value": vah, "status": "VALID", "reason": "volume_profile_analysis"},
                "VAL": {"value": val, "status": "VALID", "reason": "volume_profile_analysis"},
                "HVN": {"value": hvn, "status": "VALID", "reason": "volume_profile_analysis"},
                "LVN": {"value": lvn, "status": "VALID", "reason": "volume_profile_analysis"},
            },
            "trade_count": 10,
        },
        t,
    )


class TestP5006GroupC(unittest.TestCase):
    def test_s03_deterministic_volume_classification_and_price_context(self):
        s = snapshot([
            indicator("VOLUME_SMA", 4, "10"),
            indicator("RVOL", 4, "2.5"),
            indicator("VOLUME_SPIKE", 4, "1"),
            indicator("VOLUME_CLIMAX", 4, "0"),
            candle(3, "100"),
            candle(4, "103"),
        ])
        out = analyze_s03(s, CFG)
        self.assertEqual(out.status, SpecialistStatus.SUCCESS)
        condition = next(f for f in out.findings if f.code.endswith(":CONDITION"))
        self.assertEqual(condition.value["state"], "SPIKE")
        price = next(f for f in out.findings if f.code.endswith(":PRICE_CONTEXT"))
        self.assertEqual(price.value["direction"], "UP")
        self.assertEqual(price.value["price_change"], Decimal("3"))

    def test_s03_missing_fact_is_insufficient_without_fallback(self):
        s = snapshot([
            indicator("VOLUME_SMA", 4, "10"),
            indicator("RVOL", 4, "2"),
            indicator("VOLUME_SPIKE", 4, "1"),
            candle(3, "100"),
            candle(4, "103"),
        ])
        out = analyze_s03(s, CFG)
        state = next(f for f in out.findings if f.code.endswith(":STATE"))
        self.assertEqual(state.status, SpecialistStatus.INSUFFICIENT_DATA)
        self.assertIn("VOLUME_CLIMAX", state.value["missing_facts"])

    def test_s03_nonfinite_value_is_rejected(self):
        s = snapshot([
            indicator("VOLUME_SMA", 4, "NaN"),
            indicator("RVOL", 4, "2"),
            indicator("VOLUME_SPIKE", 4, "1"),
            indicator("VOLUME_CLIMAX", 4, "0"),
        ])
        with self.assertRaises(ValueError):
            analyze_s03(s, CFG)

    def test_s03_wrong_venue_is_not_consumed(self):
        rows = [
            indicator("VOLUME_SMA", 4, "10"),
            indicator("RVOL", 4, "2"),
            indicator("VOLUME_SPIKE", 4, "1"),
            indicator("VOLUME_CLIMAX", 4, "0"),
        ]
        rows = [r.__class__(
            fact_id=r.fact_id, status=r.status, value=r.value, event_time=r.event_time,
            knowledge_time=r.knowledge_time, evidence_refs=tuple(
                EvidenceRef(
                    evidence_id=x.evidence_id, source_type=x.source_type, source_reference=x.source_reference,
                    identity_hash=x.identity_hash, source_family=x.source_family, record_id=x.record_id,
                    event_time=x.event_time, knowledge_time=x.knowledge_time, timeframe=x.timeframe, venue="MEXC"
                ) for x in r.evidence_refs
            ), reason=r.reason, metadata={**dict(r.metadata), "venue": "MEXC"}
        ) for r in rows]
        s = snapshot(rows)
        out = analyze_s03(s, CFG)
        self.assertEqual(out.status, SpecialistStatus.INSUFFICIENT_DATA)

    def test_s17_current_position_nearest_levels_and_poc(self):
        start = T0
        end = T0 + timedelta(hours=1)
        s = snapshot([
            profile(1, start, end, poc="100", vah="105", val="95", hvn="103", lvn="97"),
            candle(3, "102", high="103", low="101"),
            candle(4, "104", high="105", low="103"),
        ])
        out = analyze_s17(s, CFG)
        position = next(f for f in out.findings if f.code.endswith(":POSITION"))
        self.assertEqual(position.status, SpecialistStatus.SUCCESS)
        self.assertEqual(position.value["state"], "INSIDE")
        self.assertEqual(position.value["nearest"]["level"], "POC")
        poc = next(f for f in out.findings if f.code.endswith(":POC"))
        self.assertEqual(poc.value["poc"], Decimal("100"))

    def test_s17_prior_session_poc_requires_two_sessions_and_detects_return(self):
        start1, end1 = T0 - timedelta(hours=2), T0 - timedelta(hours=1)
        start2, end2 = T0 - timedelta(hours=1), T0
        s = snapshot([
            profile(1, start1, end1, poc="100"),
            profile(2, start2, end2, poc="110"),
            candle(0, "99", high="101", low="98"),
            candle(1, "104", high="105", low="103"),
            candle(2, "100", high="101", low="99"),
        ])
        out = analyze_s17(s, CFG)
        prior = next(f for f in out.findings if f.code.endswith(":PRIOR_POC_RETURN"))
        self.assertEqual(prior.status, SpecialistStatus.SUCCESS)
        self.assertEqual(prior.value["state"], "RETURNED")

    def test_s17_one_session_is_explicitly_insufficient_for_prior_poc(self):
        start, end = T0 - timedelta(hours=1), T0
        s = snapshot([profile(1, start, end, poc="100"), candle(2, "104")])
        out = analyze_s17(s, CFG)
        prior = next(f for f in out.findings if f.code.endswith(":PRIOR_POC_RETURN"))
        self.assertEqual(prior.status, SpecialistStatus.INSUFFICIENT_DATA)

    def test_s17_missing_profile_is_explicitly_insufficient(self):
        s = snapshot([candle(2, "104")])
        out = analyze_s17(s, CFG)
        state = next(f for f in out.findings if f.code.endswith(":STATE"))
        self.assertEqual(state.status, SpecialistStatus.INSUFFICIENT_DATA)
        self.assertEqual(state.value["state"], "INSUFFICIENT_DATA")

    def test_replay_is_deterministic_without_specialist_dependency(self):
        s = snapshot([
            indicator("VOLUME_SMA", 4, "10"),
            indicator("RVOL", 4, "2"),
            indicator("VOLUME_SPIKE", 4, "1"),
            indicator("VOLUME_CLIMAX", 4, "0"),
            candle(3, "100"),
            candle(4, "101"),
        ])
        first = analyze_s03(s, CFG)
        second = analyze_s03(s, CFG)
        self.assertEqual(first.identity_hash, second.identity_hash)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertNotIn("specialist_output", first.serialize())
        self.assertNotIn("specialist_output", second.serialize())


if __name__ == "__main__":
    unittest.main()
