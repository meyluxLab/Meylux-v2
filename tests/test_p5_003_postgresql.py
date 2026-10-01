from __future__ import annotations

import asyncio
import os
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from contracts.specialist import EvidenceRef, FactStatus, InputSnapshot, SnapshotFact, SpecialistConfigRef, SpecialistFinding, SpecialistOutput, SpecialistStatus
from meylux.specialists.persistence import SpecialistPersistence

DATABASE_URL = os.environ.get("MEYLUX_TEST_DATABASE_URL")
UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
REF = EvidenceRef("p5-concurrency", "p3-quality", "quality/concurrency", "a" * 64, T0, "1.0.0", "quality", "p5-concurrency", T0, T0, "15m", "BINANCE")
CFG = SpecialistConfigRef("p5-specialists", "1.1.0", "b" * 64, "development")


def _output() -> SpecialistOutput:
    snapshot = InputSnapshot.build(
        as_of=T0,
        version="1.0.0",
        facts=(SnapshotFact("price", FactStatus.VALID, Decimal("100"), T0, (REF,)),),
        provenance_refs=(REF,),
    )
    return SpecialistOutput(
        "S-10",
        "1.0.0",
        snapshot.snapshot_id,
        snapshot.version,
        CFG,
        SpecialistStatus.SUCCESS,
        "concurrency probe",
        (SpecialistFinding("OVERALL_QUALITY", SpecialistStatus.SUCCESS, {"worst_status": "VALID"}, "probe", evidence_refs=(REF,)),),
        (REF,),
    )


@unittest.skipUnless(DATABASE_URL, "requires MEYLUX_TEST_DATABASE_URL for real PostgreSQL evidence")
class TestP5003PostgreSQL(unittest.TestCase):
    def test_concurrent_duplicate_persistence_has_one_winner(self):
        async def run():
            import asyncpg

            first = await asyncpg.connect(DATABASE_URL)
            second = await asyncpg.connect(DATABASE_URL)
            try:
                output = _output()
                results = await asyncio.gather(
                    SpecialistPersistence(first).persist(output),
                    SpecialistPersistence(second).persist(output),
                )
                self.assertEqual(sorted(results), [False, True])
                count = await first.fetchval(
                    "SELECT count(*) FROM meylux.specialist_outputs WHERE identity_hash=$1",
                    output.identity_hash,
                )
                self.assertEqual(count, 1)
            finally:
                await first.close()
                await second.close()


if __name__ == "__main__":
    unittest.main()
