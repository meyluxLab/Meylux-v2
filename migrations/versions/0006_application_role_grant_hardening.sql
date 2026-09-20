-- Meylux V2 TO-P4-009 — post-closure application-role grant hardening.
-- Forward-only, idempotent correction of the pre-existing meylux_app UPDATE boundary.

SET TIME ZONE 'UTC';

-- Remove the inherited UPDATE privilege from future tables created by meylux_admin.
ALTER DEFAULT PRIVILEGES FOR ROLE meylux_admin IN SCHEMA meylux
    REVOKE UPDATE ON TABLES FROM meylux_app;

-- raw_acquisition_events is append-only application evidence: SELECT/INSERT remain,
-- but application-role UPDATE is not a legitimate production capability.
REVOKE UPDATE ON meylux.raw_acquisition_events FROM meylux_app;

-- The relay only mutates these two publication-state columns. Remove the
-- table-level UPDATE privilege first, then grant the minimum column-level
-- UPDATE privilege required by the existing relay SQL.
REVOKE UPDATE ON meylux.canonical_event_outbox FROM meylux_app;
GRANT UPDATE (published_at, published_stream_id)
    ON meylux.canonical_event_outbox TO meylux_app;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0006_application_role_grant_hardening')
ON CONFLICT(version) DO NOTHING;
