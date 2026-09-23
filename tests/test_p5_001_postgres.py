from __future__ import annotations

import os
import shutil
import subprocess
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "timescale/timescaledb:2.29.2-pg16"
CONTAINER = f"meylux-to-p5-001-pg-{os.getpid()}"
ADMIN = "meylux_admin"
APP = "meylux_app"
BACKUP = "meylux_backup"
DB = "meylux_p5001"
ADMIN_PASSWORD = "p5-001-admin"
APP_PASSWORD = "p5-001-app"
BACKUP_PASSWORD = "p5-001-backup"


class PostgreSQLSpecialistFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get("GITHUB_WORKFLOW") == "CI Docker Foundation":
            raise unittest.SkipTest(
                "CI Docker Foundation starts its governed database after repository self-checks; "
                "real P5-001 PostgreSQL evidence runs in CI Core."
            )
        cls.docker = shutil.which("docker")
        if cls.docker is None:
            raise unittest.SkipTest("Docker is unavailable; real P5-001 PostgreSQL evidence is skipped cleanly.")
        probe = subprocess.run([cls.docker, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if probe.returncode != 0:
            raise unittest.SkipTest("Docker daemon is unavailable; real P5-001 PostgreSQL evidence is skipped cleanly.")
        cls._start_database()

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "docker", None):
            subprocess.run([cls.docker, "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    @classmethod
    def _run(cls, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(args, text=True, capture_output=True, check=False)
        if check and result.returncode != 0:
            raise AssertionError(
                f"command failed ({result.returncode}): {' '.join(args)}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    @classmethod
    def _start_database(cls) -> None:
        cls._run([
            cls.docker, "run", "--rm", "--detach", "--name", CONTAINER,
            "--env", f"POSTGRES_DB={DB}",
            "--env", f"POSTGRES_USER={ADMIN}",
            "--env", f"POSTGRES_PASSWORD={ADMIN_PASSWORD}",
            "--volume", f"{ROOT}:/workspace:ro",
            IMAGE,
        ])
        for _ in range(60):
            ready = cls._run([
                cls.docker, "exec", "--env", f"PGPASSWORD={ADMIN_PASSWORD}",
                CONTAINER, "psql", "-X", "-At", "-U", ADMIN, "-d", DB, "-c", "SELECT 1;"
            ], check=False)
            if ready.returncode == 0 and ready.stdout.strip() == "1":
                return
            time.sleep(1)
        raise RuntimeError("ephemeral PostgreSQL did not become ready")

    @classmethod
    def _psql(cls, sql: str, *, user: str = ADMIN, password: str = ADMIN_PASSWORD, check: bool = True) -> subprocess.CompletedProcess[str]:
        return cls._run([
            cls.docker, "exec", "--env", f"PGPASSWORD={password}", CONTAINER,
            "psql", "-X", "-v", "ON_ERROR_STOP=1", "-At", "-U", user, "-d", DB, "-c", sql
        ], check=check)

    @classmethod
    def _psql_file(cls, path: str) -> None:
        cls._run([
            cls.docker, "exec", "--env", f"PGPASSWORD={ADMIN_PASSWORD}", CONTAINER,
            "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", ADMIN, "-d", DB, "-f", f"/workspace/{path}"
        ])

    @classmethod
    def _bootstrap(cls) -> None:
        for name in (
            "0001_database_foundation.sql",
            "0002_raw_acquisition_staging.sql",
            "0003_canonical_persistence_event_outbox.sql",
            "0004_canonical_quality_state_alignment.sql",
            "0005_quantitative_foundation.sql",
            "0006_application_role_grant_hardening.sql",
            "0007_specialist_foundation.sql",
        ):
            cls._psql_file(f"migrations/versions/{name}")
        cls._psql(f"ALTER ROLE {APP} LOGIN PASSWORD '{APP_PASSWORD}';")
        cls._psql(f"ALTER ROLE {BACKUP} LOGIN PASSWORD '{BACKUP_PASSWORD}';")

    @staticmethod
    def _insert_sql(record_id: str, status: str, evidence_json: str, identity_digit: str, *, findings_json: str = "[]") -> str:
        payload = "{\"status\":\"" + status + "\"}"
        return (
            "INSERT INTO meylux.specialist_outputs("
            "record_id,specialist_id,output_version,snapshot_id,snapshot_version,"
            "config_name,config_version,config_identity_hash,environment,status,reason,"
            "findings_json,evidence_refs_json,payload_json,identity_hash) VALUES ("
            f"'{record_id}','S-TEST','1.0.0','snap-1','1.0.0','p5','1.0.0',"
            "repeat('b',64),'ci',"
            f"'{status}','explicit-test',{findings_json!r},{evidence_json!r},{payload!r},repeat('{identity_digit}',64)) "
            "ON CONFLICT(identity_hash) DO NOTHING;"
        )

    def test_real_postgresql_persistence_and_privileges(self) -> None:
        self._bootstrap()
        self.assertEqual(
            self._psql("SELECT version FROM meylux.schema_migrations WHERE version='0007_specialist_foundation';").stdout.strip(),
            "0007_specialist_foundation",
        )
        self.assertEqual(
            self._psql(
                "SELECT has_table_privilege('meylux_app','meylux.specialist_outputs','SELECT'),"
                "has_table_privilege('meylux_app','meylux.specialist_outputs','INSERT'),"
                "has_table_privilege('meylux_app','meylux.specialist_outputs','UPDATE'),"
                "has_table_privilege('meylux_app','meylux.specialist_outputs','DELETE'),"
                "has_table_privilege('meylux_app','meylux.specialist_outputs','TRUNCATE');"
            ).stdout.strip(),
            "t|t|f|f|f",
        )
        self.assertEqual(
            self._psql(
                "SELECT has_table_privilege('meylux_backup','meylux.specialist_outputs','SELECT'),"
                "has_table_privilege('meylux_backup','meylux.specialist_outputs','INSERT'),"
                "has_table_privilege('meylux_backup','meylux.specialist_outputs','UPDATE'),"
                "has_table_privilege('meylux_backup','meylux.specialist_outputs','DELETE'),"
                "has_table_privilege('meylux_backup','meylux.specialist_outputs','TRUNCATE');"
            ).stdout.strip(),
            "t|f|f|f|f",
        )

        valid_success = self._insert_sql(
            "p5-success", "SUCCESS", '[{"evidence_id":"ev-1"}]', "1", findings_json='[{"code":"F-1"}]'
        )
        valid_partial = self._insert_sql(
            "p5-partial", "PARTIAL", '[{"evidence_id":"ev-1"}]', "2", findings_json='[{"code":"F-1"}]'
        )
        self.assertEqual(self._psql(valid_success, user=APP, password=APP_PASSWORD).stdout.strip(), "INSERT 0 1")
        self.assertEqual(self._psql(valid_partial, user=APP, password=APP_PASSWORD).stdout.strip(), "INSERT 0 1")
        self.assertEqual(
            self._psql(
                "SELECT status,count(*) FROM meylux.specialist_outputs GROUP BY status ORDER BY status;",
                user=APP, password=APP_PASSWORD
            ).stdout.strip(),
            "PARTIAL|1\nSUCCESS|1",
        )

        denied_success = self._psql(
            self._insert_sql("p5-no-evidence", "SUCCESS", "[]", "3"),
            user=APP, password=APP_PASSWORD, check=False
        )
        denied_partial = self._psql(
            self._insert_sql("p5-partial-no-evidence", "PARTIAL", "[]", "4"),
            user=APP, password=APP_PASSWORD, check=False
        )
        for result in (denied_success, denied_partial):
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("violates check constraint", result.stderr.lower())

        duplicate = self._psql(
            valid_success.replace("'p5-success'", "'p5-success-duplicate'"),
            user=APP, password=APP_PASSWORD
        )
        self.assertEqual(duplicate.stdout.strip(), "INSERT 0 0")

        denied_update = self._psql(
            "UPDATE meylux.specialist_outputs SET reason='tampered' WHERE record_id='p5-success';",
            user=APP, password=APP_PASSWORD, check=False
        )
        denied_delete = self._psql(
            "DELETE FROM meylux.specialist_outputs WHERE record_id='p5-success';",
            user=APP, password=APP_PASSWORD, check=False
        )
        denied_truncate = self._psql(
            "TRUNCATE meylux.specialist_outputs;",
            user=APP, password=APP_PASSWORD, check=False
        )
        for result in (denied_update, denied_delete, denied_truncate):
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("permission denied", result.stderr.lower())

        backup_insert = self._psql(
            self._insert_sql("p5-backup-insert", "FAILED", "[]", "5"),
            user=BACKUP, password=BACKUP_PASSWORD, check=False
        )
        backup_update = self._psql(
            "UPDATE meylux.specialist_outputs SET reason='tampered' WHERE record_id='p5-success';",
            user=BACKUP, password=BACKUP_PASSWORD, check=False
        )
        backup_delete = self._psql(
            "DELETE FROM meylux.specialist_outputs WHERE record_id='p5-success';",
            user=BACKUP, password=BACKUP_PASSWORD, check=False
        )
        backup_truncate = self._psql(
            "TRUNCATE meylux.specialist_outputs;",
            user=BACKUP, password=BACKUP_PASSWORD, check=False
        )
        for result in (backup_insert, backup_update, backup_delete, backup_truncate):
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("permission denied", result.stderr.lower())

        self.assertEqual(
            self._psql(
                "SELECT count(*) FROM meylux.specialist_outputs WHERE record_id='p5-success';",
                user=APP, password=APP_PASSWORD
            ).stdout.strip(),
            "1",
        )

        for status, record_id, digest in (
            ("FAILED", "p5-failed", "6"),
            ("UNAVAILABLE_INPUT", "p5-unavailable", "7"),
            ("INSUFFICIENT_DATA", "p5-insufficient", "8"),
        ):
            result = self._psql(
                self._insert_sql(record_id, status, "[]", digest),
                user=APP, password=APP_PASSWORD
            )
            self.assertEqual(result.stdout.strip(), "INSERT 0 1")

        self.assertEqual(
            self._psql(
                "SELECT count(*) FROM meylux.specialist_outputs "
                "WHERE status IN ('FAILED','UNAVAILABLE_INPUT','INSUFFICIENT_DATA') "
                "AND jsonb_array_length(evidence_refs_json)=0;",
                user=APP, password=APP_PASSWORD
            ).stdout.strip(),
            "3",
        )


if __name__ == "__main__":
    unittest.main()
