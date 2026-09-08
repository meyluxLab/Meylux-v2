-- Meylux V2 Database Foundation — initial authoritative persistence boundary.
-- This migration is intentionally limited to foundation objects only.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS meylux AUTHORIZATION meylux_admin;

CREATE TABLE IF NOT EXISTS meylux.schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO meylux.schema_migrations (version)
VALUES ('0001_database_foundation')
ON CONFLICT (version) DO NOTHING;

-- Least-privilege foundation roles. Passwords/login state are configured by the
-- migration harness from environment-provided secrets; no credentials are stored here.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'meylux_app') THEN
        CREATE ROLE meylux_app NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'meylux_backup') THEN
        CREATE ROLE meylux_backup NOLOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE current_database() TO meylux_app, meylux_backup;
GRANT USAGE ON SCHEMA meylux TO meylux_app, meylux_backup;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA meylux TO meylux_app;
GRANT SELECT ON ALL TABLES IN SCHEMA meylux TO meylux_backup;
REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA meylux FROM meylux_app;

ALTER DEFAULT PRIVILEGES FOR ROLE meylux_admin IN SCHEMA meylux
    GRANT SELECT, INSERT, UPDATE ON TABLES TO meylux_app;
ALTER DEFAULT PRIVILEGES FOR ROLE meylux_admin IN SCHEMA meylux
    GRANT SELECT ON TABLES TO meylux_backup;

ALTER DEFAULT PRIVILEGES FOR ROLE meylux_admin IN SCHEMA meylux
    REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES FROM meylux_app;
