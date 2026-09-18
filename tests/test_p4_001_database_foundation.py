from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/versions/0005_quantitative_foundation.sql"
HARNESS = ROOT / "infrastructure/postgres/migrate.sh"


class P4001DatabaseFoundationTests(unittest.TestCase):
    def test_migration_defines_all_authorized_output_families(self):
        text = MIGRATION.read_text(encoding="utf-8")
        for table in (
            "calculated_indicator_vectors",
            "market_structure_events",
            "market_structure_zones",
            "volume_profile_sessions",
            "market_regime_states",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS meylux.{table}", text)
            self.assertIn(f"identity_hash text NOT NULL UNIQUE", text)
        self.assertIn("session_end > session_start", text)

    def test_migration_preserves_context_and_explicit_result_semantics(self):
        text = MIGRATION.read_text(encoding="utf-8")
        for field in ("symbol text NOT NULL", "timeframe text NOT NULL", "source_ref text",
                      "venue_context text", "version text NOT NULL",
                      "calculation_version text NOT NULL", "status text NOT NULL",
                      "reason text NOT NULL", "payload_json jsonb NOT NULL"):
            self.assertGreaterEqual(text.count(field), 5)

    def test_quantitative_tables_are_append_only_and_least_privilege(self):
        text = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("BEFORE UPDATE OR DELETE", text)
        self.assertIn("REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER", text)
        self.assertIn("GRANT SELECT, INSERT ON", text)
        self.assertNotIn("GRANT DELETE", text)

    def test_migration_is_idempotent_and_registered_in_order(self):
        text = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("ON CONFLICT(version) DO NOTHING", text)
        self.assertIn("VALUES ('0005_quantitative_foundation')", text)
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("0004_canonical_quality_state_alignment.sql", harness)
        self.assertIn("0005_quantitative_foundation.sql", harness)
        self.assertLess(
            harness.index("0004_canonical_quality_state_alignment.sql"),
            harness.index("0005_quantitative_foundation.sql"),
        )


if __name__ == "__main__":
    unittest.main()
