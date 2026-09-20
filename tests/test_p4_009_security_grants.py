from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations" / "versions"
IMAGE = "timescale/timescaledb:2.29.2-pg16"
CONTAINER = f"meylux-to-p4-009-pg-{os.getpid()}"

LEGACY_MIGRATION_BLOB_SHAS = {
    "0001_database_foundation.sql": "4cb44b7eb2cb37170793ee03605fb1cbcb587c0e",
    "0002_raw_acquisition_staging.sql": "27c1c05f9a8e9739d71521c326326501d29cfbed",
    "0003_canonical_persistence_event_outbox.sql": "15749baff0a2848f419ab1fc80181a2941db9949",
    "0004_canonical_quality_state_alignment.sql": "2ba2cdf69f548b7df7f8386f567228cedbeaf99f",
    "0005_quantitative_foundation.sql": "fd0afb2187625d29c527d35ca856b2e7d3caaf9e",
}

ADMIN = "meylux_admin"
APP = "meylux_app"
DB = "meylux_p4009"
ADMIN_PASSWORD = "p4-009-admin"
APP_PASSWORD = "p4-009-app"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    material = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(material).hexdigest()


class PostClosureSecurityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docker = shutil.which("docker")
        if cls.docker is None:
            raise unittest.SkipTest("Docker is unavailable; PostgreSQL-backed TO-P4-009 evidence is skipped cleanly.")

        probe = subprocess.run(
            [cls.docker, "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode != 0:
            raise unittest.SkipTest("Docker daemon is unavailable; PostgreSQL-backed TO-P4-009 evidence is skipped cleanly.")

        cls._start_database()

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "docker", None):
            subprocess.run([cls.docker, "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    @classmethod
    def _run(cls, args: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(args, text=True, capture_output=True, check=False, env=env)
        if check and result.returncode != 0:
            raise AssertionError(
                f"command failed ({result.returncode}): {' '.join(args)}\\n"
                f"stdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}"
            )
        return result

    @classmethod
    def _start_database(cls) -> None:
        cls._run(
            [
                cls.docker,
                "run",
                "--rm",
                "--detach",
                "--name",
                CONTAINER,
                "--env",
                f"POSTGRES_DB={DB}",
                "--env",
                f"POSTGRES_USER={ADMIN}",
                "--env",
                f"POSTGRES_PASSWORD={ADMIN_PASSWORD}",
                "--volume",
                f"{ROOT}:/workspace:ro",
                IMAGE,
            ]
        )
        for _ in range(60):
            ready = cls._run(
                [cls.docker, "exec", CONTAINER, "pg_isready", "-U", ADMIN, "-d", DB],
                check=False,
            )
            if ready.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError("ephemeral PostgreSQL did not become ready")

    @classmethod
    def _psql(
        cls,
        sql: str,
        *,
        user: str = ADMIN,
        password: str | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        args = [
            cls.docker,
            "exec",
            "--env",
            f"PGPASSWORD={password}" if password is not None else f"PGPASSWORD={ADMIN_PASSWORD}",
            CONTAINER,
            "psql",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-At",
            "-U",
            user,
            "-d",
            DB,
            "-c",
            sql,
        ]
        return cls._run(args, check=check)

    @classmethod
    def _psql_file(cls, path: str) -> None:
        cls._run(
            [
                cls.docker,
                "exec",
                "--env",
                f"PGPASSWORD={ADMIN_PASSWORD}",
                CONTAINER,
                "psql",
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                ADMIN,
                "-d",
                DB,
                "-f",
                f"/workspace/{path}",
            ],
        )

    @classmethod
    def _bootstrap_0001_to_0005(cls) -> None:
        for name in (
            "0001_database_foundation.sql",
            "0002_raw_acquisition_staging.sql",
            "0003_canonical_persistence_event_outbox.sql",
            "0004_canonical_quality_state_alignment.sql",
            "0005_quantitative_foundation.sql",
        ):
            cls._psql_file(f"migrations/versions/{name}")
        cls._psql(
            f"ALTER ROLE {APP} LOGIN PASSWORD '{APP_PASSWORD}';"
        )

    def test_governed_grant_hardening_on_real_postgresql(self) -> None:
        self._bootstrap_0001_to_0005()

        # Migration ordering and legacy-file integrity are checked before applying 0006.
        harness = (ROOT / "infrastructure/postgres/migrate.sh").read_text()
        self.assertLess(harness.index("0005_quantitative_foundation.sql"), harness.index("0006_application_role_grant_hardening.sql"))
        self.assertEqual(
            sorted(p.name for p in MIGRATIONS if p.name.startswith("000")),
            [
                "0001_database_foundation.sql",
                "0002_raw_acquisition_staging.sql",
                "0003_canonical_persistence_event_outbox.sql",
                "0004_canonical_quality_state_alignment.sql",
                "0005_quantitative_foundation.sql",
                "0006_application_role_grant_hardening.sql",
            ],
        )
        for name, expected_sha in LEGACY_MIGRATION_BLOB_SHAS.items():
            self.assertEqual(git_blob_sha(MIGRATIONS / name), expected_sha, name)

        # Complete implementation/test search: no legitimate production UPDATE path exists.
        update_pattern = re.compile(r"UPDATE\s+(?:meylux\.)?raw_acquisition_events\b", re.IGNORECASE)
        source_hits = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "src").rglob("*.py")
            if update_pattern.search(path.read_text())
        ]
        test_hits = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "tests").rglob("*.py")
            if path.name != Path(__file__).name and update_pattern.search(path.read_text())
        ]
        self.assertEqual(source_hits, [])
        self.assertEqual(test_hits, [])

        pre_default_acl = self._psql(
            """SELECT privilege_type
                 FROM aclexplode(
                    (SELECT defaclacl
                       FROM pg_default_acl
                      WHERE defaclrole='meylux_admin'::regrole
                        AND defaclnamespace='meylux'::regnamespace
                        AND defaclobjtype='r')
                 ) AS x
                 JOIN pg_roles r ON r.oid=x.grantee
                WHERE r.rolname='meylux_app'
                ORDER BY privilege_type;"""
        ).stdout.splitlines()
        self.assertEqual(pre_default_acl, ["INSERT", "SELECT", "UPDATE"])

        pre_table_privs = self._psql(
            """SELECT
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','SELECT'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','INSERT'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','UPDATE'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','DELETE'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','TRUNCATE'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','UPDATE');"""
        ).stdout.strip()
        self.assertEqual(pre_table_privs, "t|t|t|f|f|t")

        # Prove the pre-0006 default privilege inheritance on a future table.
        self._psql("CREATE TABLE meylux.to_p4_009_pre_future(id integer);")
        self.assertEqual(
            self._psql(
                "SELECT has_table_privilege('meylux_app','meylux.to_p4_009_pre_future','UPDATE');"
            ).stdout.strip(),
            "t",
        )
        self._psql("DROP TABLE meylux.to_p4_009_pre_future;")

        pre_outbox_columns = self._psql(
            """SELECT
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','published_at','UPDATE'),
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','published_stream_id','UPDATE'),
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','event_id','UPDATE');"""
        ).stdout.strip()
        self.assertEqual(pre_outbox_columns, "t|t|t")

        # The repository migration harness is the authorized forward path; running it
        # from a 0001-0005 database applies 0006 after the established five migrations.
        self._run(
            [
                self.docker,
                "exec",
                "--env", f"MEYLUX_DB_NAME={DB}",
                "--env", f"MEYLUX_DB_USER={ADMIN}",
                "--env", f"MEYLUX_DB_PASSWORD={ADMIN_PASSWORD}",
                "--env", f"MEYLUX_APP_PASSWORD={APP_PASSWORD}",
                CONTAINER,
                "bash",
                "/workspace/infrastructure/postgres/migrate.sh",
            ]
        )

        post_default_acl = self._psql(
            """SELECT privilege_type
                 FROM aclexplode(
                    (SELECT defaclacl
                       FROM pg_default_acl
                      WHERE defaclrole='meylux_admin'::regrole
                        AND defaclnamespace='meylux'::regnamespace
                        AND defaclobjtype='r')
                 ) AS x
                 JOIN pg_roles r ON r.oid=x.grantee
                WHERE r.rolname='meylux_app'
                ORDER BY privilege_type;"""
        ).stdout.splitlines()
        self.assertEqual(post_default_acl, ["INSERT", "SELECT"])

        post_table_privs = self._psql(
            """SELECT
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','SELECT'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','INSERT'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','UPDATE'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','DELETE'),
                has_table_privilege('meylux_app','meylux.raw_acquisition_events','TRUNCATE'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','SELECT'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','INSERT'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','UPDATE'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','DELETE'),
                has_table_privilege('meylux_app','meylux.canonical_event_outbox','TRUNCATE');"""
        ).stdout.strip()
        self.assertEqual(post_table_privs, "t|t|f|f|f|t|t|f|f|f")

        post_outbox_columns = self._psql(
            """SELECT
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','published_at','UPDATE'),
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','published_stream_id','UPDATE'),
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','event_id','UPDATE'),
                has_column_privilege('meylux_app','meylux.canonical_event_outbox','event_type','UPDATE');"""
        ).stdout.strip()
        self.assertEqual(post_outbox_columns, "t|t|f|f")

        # Future tables must no longer inherit UPDATE.
        self._psql("CREATE TABLE meylux.to_p4_009_post_future(id integer);")
        self.assertEqual(
            self._psql(
                """SELECT
                    has_table_privilege('meylux_app','meylux.to_p4_009_post_future','SELECT'),
                    has_table_privilege('meylux_app','meylux.to_p4_009_post_future','INSERT'),
                    has_table_privilege('meylux_app','meylux.to_p4_009_post_future','UPDATE'),
                    has_table_privilege('meylux_app','meylux.to_p4_009_post_future','DELETE'),
                    has_table_privilege('meylux_app','meylux.to_p4_009_post_future','TRUNCATE');"""
            ).stdout.strip(),
            "t|t|f|f|f",
        )

        # Required raw SELECT/INSERT still work under the resulting privilege model.
        self._psql(
            """INSERT INTO meylux.raw_acquisition_events(
                event_id,provider_id,adapter_id,adapter_version,
                canonical_instrument_id,provider_instrument_id,event_type,
                event_time,received_at,acquisition_state,source_sequence,
                provenance_id,acquisition_method,payload_json,canonical_bytes,identity_hash
            ) VALUES (
                'to-p4-009-raw','test','test-adapter','1.0',
                'BTCUSDT','BTCUSDT','TRADE',
                '2026-09-20T00:00:00Z','2026-09-20T00:00:01Z','AVAILABLE','1',
                'p4-009','TEST','{}'::jsonb,decode('00','hex'),'to-p4-009-raw-hash'
            );""",
            user=APP,
            password=APP_PASSWORD,
        )
        self.assertEqual(
            self._psql(
                "SELECT count(*) FROM meylux.raw_acquisition_events WHERE event_id='to-p4-009-raw';",
                user=APP,
                password=APP_PASSWORD,
            ).stdout.strip(),
            "1",
        )

        denied_raw_update = self._psql(
            "UPDATE meylux.raw_acquisition_events SET acquisition_state='AVAILABLE' WHERE event_id='to-p4-009-raw';",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_raw_update.returncode, 0)
        self.assertIn("permission denied", denied_raw_update.stderr.lower())

        denied_raw_delete = self._psql(
            "DELETE FROM meylux.raw_acquisition_events WHERE event_id='to-p4-009-raw';",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_raw_delete.returncode, 0)

        denied_raw_truncate = self._psql(
            "TRUNCATE meylux.raw_acquisition_events;",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_raw_truncate.returncode, 0)

        # Execute the exact relay publication UPDATE as meylux_app.
        self._psql(
            """INSERT INTO meylux.canonical_event_outbox(
                event_id,record_id,event_type,event_time,payload_json
            ) VALUES(
                'to-p4-009-event','to-p4-009-record','trade',
                '2026-09-20T00:00:00Z','{"x":1}'::jsonb
            );""",
            user=APP,
            password=APP_PASSWORD,
        )
        relay_update = self._psql(
            """UPDATE meylux.canonical_event_outbox
                  SET published_at=now(),published_stream_id='stream:test'
                WHERE event_id='to-p4-009-event' AND published_at IS NULL;""",
            user=APP,
            password=APP_PASSWORD,
        )
        self.assertEqual(relay_update.returncode, 0)
        self.assertEqual(
            self._psql(
                """SELECT published_stream_id IS NOT NULL
                     FROM meylux.canonical_event_outbox
                    WHERE event_id='to-p4-009-event';""",
                user=APP,
                password=APP_PASSWORD,
            ).stdout.strip(),
            "t",
        )

        denied_outbox_unrelated = self._psql(
            "UPDATE meylux.canonical_event_outbox SET event_type='not-allowed' WHERE event_id='to-p4-009-event';",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_outbox_unrelated.returncode, 0)

        denied_outbox_delete = self._psql(
            "DELETE FROM meylux.canonical_event_outbox WHERE event_id='to-p4-009-event';",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_outbox_delete.returncode, 0)

        denied_outbox_truncate = self._psql(
            "TRUNCATE meylux.canonical_event_outbox;",
            user=APP,
            password=APP_PASSWORD,
            check=False,
        )
        self.assertNotEqual(denied_outbox_truncate.returncode, 0)

        # Re-applying only the new migration is explicitly idempotent.
        self._psql_file("migrations/versions/0006_application_role_grant_hardening.sql")
        self.assertEqual(
            self._psql(
                "SELECT count(*) FROM meylux.schema_migrations WHERE version='0006_application_role_grant_hardening';"
            ).stdout.strip(),
            "1",
        )
        self.assertEqual(
            self._psql(
                "SELECT has_table_privilege('meylux_app','meylux.raw_acquisition_events','UPDATE');"
            ).stdout.strip(),
            "f",
        )
        self.assertEqual(
            self._psql(
                "SELECT has_table_privilege('meylux_app','meylux.canonical_event_outbox','UPDATE');"
            ).stdout.strip(),
            "f",
        )

        self._psql("DROP TABLE meylux.to_p4_009_post_future;")

        self.assertEqual(
            self._psql(
                "SELECT version FROM meylux.schema_migrations ORDER BY version;"
            ).stdout.splitlines(),
            [
                "0001_database_foundation",
                "0002_raw_acquisition_staging",
                "0003_canonical_persistence_event_outbox",
                "0004_canonical_quality_state_alignment",
                "0005_quantitative_foundation",
                "0006_application_role_grant_hardening",
            ],
        )


if __name__ == "__main__":
    unittest.main()
