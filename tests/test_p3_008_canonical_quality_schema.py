import unittest
from pathlib import Path

from contracts.data_quality import DataQualityState


class P3008CanonicalQualitySchemaTests(unittest.TestCase):
    def test_authoritative_valid_value_is_preserved_by_migration_contract(self):
        migration = Path("migrations/versions/0004_canonical_quality_state_alignment.sql").read_text()
        self.assertEqual(DataQualityState.VALID.value, "VALID")
        self.assertIn("quality_state = ''VALID''", migration)
        self.assertNotIn("quality_state = ''valid''", migration)

    def test_all_canonical_tables_are_aligned(self):
        migration = Path("migrations/versions/0004_canonical_quality_state_alignment.sql").read_text()
        for table in (
            "canonical_instruments",
            "canonical_candles",
            "canonical_trades",
            "canonical_orderbook_depth",
            "canonical_derivatives",
        ):
            self.assertIn(table, migration)
            self.assertIn("t + '_quality_state_check'", migration)

if __name__ == "__main__":
    unittest.main()
