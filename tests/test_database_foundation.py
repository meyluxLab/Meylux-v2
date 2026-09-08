from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/versions/0001_database_foundation.sql"
HARNESS = ROOT / "infrastructure/postgres/migrate.sh"


class DatabaseFoundationTests(unittest.TestCase):
    def test_migration_contains_required_foundation_objects(self):
        text = MIGRATION.read_text(encoding="utf-8")
        for required in (
            "CREATE EXTENSION IF NOT EXISTS timescaledb",
            "CREATE SCHEMA IF NOT EXISTS meylux AUTHORIZATION meylux_admin",
            "CREATE TABLE IF NOT EXISTS meylux.schema_migrations",
            "CREATE ROLE meylux_app NOLOGIN",
            "CREATE ROLE meylux_backup NOLOGIN",
            "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA meylux TO meylux_app",
            "GRANT SELECT ON ALL TABLES IN SCHEMA meylux TO meylux_backup",
        ):
            self.assertIn(required, text)

    def test_application_role_has_no_delete_grant(self):
        text = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER", text)
        self.assertNotIn("GRANT DELETE", text)

    def test_database_harness_is_non_secret_and_deterministic(self):
        text = HARNESS.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        self.assertIn("ALTER DATABASE", text)
        self.assertIn("timezone TO 'UTC'", text)
        self.assertNotIn("ci-admin-password", text)
        self.assertNotIn("change-me", text)

    def test_database_config_is_pure_at_import(self):
        import sys

        sys.path.insert(0, str(ROOT))
        from config.database import DatabaseConfig, load_database_config

        cfg = load_database_config()
        self.assertIsInstance(cfg, DatabaseConfig)
        self.assertEqual(cfg.timezone, "UTC")
        self.assertEqual(cfg.user, "meylux_admin")


if __name__ == "__main__":
    unittest.main()
