-- Meylux V2 STEP-P5-001 — specialist contract/evidence persistence foundation.
SET TIME ZONE 'UTC';
CREATE TABLE IF NOT EXISTS meylux.specialist_outputs (
 record_id text PRIMARY KEY, specialist_id text NOT NULL, output_version text NOT NULL,
 snapshot_id text NOT NULL, snapshot_version text NOT NULL, config_name text NOT NULL,
 config_version text NOT NULL, config_identity_hash text NOT NULL, environment text NOT NULL,
 status text NOT NULL CHECK(status IN ('SUCCESS','PARTIAL','INSUFFICIENT_DATA','UNAVAILABLE_INPUT','SKIPPED','DISABLED','FAILED','TIMEOUT')),
 reason text NOT NULL, findings_json jsonb NOT NULL CHECK(jsonb_typeof(findings_json)='array'),
 evidence_refs_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_refs_json)='array'),
 payload_json jsonb NOT NULL CHECK(jsonb_typeof(payload_json)='object'),
 identity_hash text NOT NULL UNIQUE, persisted_at timestamptz NOT NULL DEFAULT now(),
 CHECK(status NOT IN ('SUCCESS','PARTIAL') OR jsonb_array_length(evidence_refs_json)>0)
);
CREATE INDEX IF NOT EXISTS ix_specialist_outputs_lookup ON meylux.specialist_outputs(specialist_id,snapshot_id,config_version);
DO $$ BEGIN
 DROP TRIGGER IF EXISTS trg_specialist_outputs_append_only ON meylux.specialist_outputs;
 CREATE TRIGGER trg_specialist_outputs_append_only BEFORE UPDATE OR DELETE ON meylux.specialist_outputs FOR EACH ROW EXECUTE FUNCTION meylux.reject_canonical_mutation();
END $$;
GRANT SELECT,INSERT ON meylux.specialist_outputs TO meylux_app;
REVOKE UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER ON meylux.specialist_outputs FROM meylux_app;
GRANT SELECT ON meylux.specialist_outputs TO meylux_backup;
INSERT INTO meylux.schema_migrations(version) VALUES ('0007_specialist_foundation') ON CONFLICT(version) DO NOTHING;
