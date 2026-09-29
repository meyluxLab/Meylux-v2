-- Meylux V2 P3-009 — authoritative persisted quality/acquisition evidence.
-- Additive, idempotent, non-destructive and append-only.

SET TIME ZONE 'UTC';

CREATE TABLE IF NOT EXISTS meylux.quality_evidence (
    evidence_id text PRIMARY KEY,
    logical_fact_key text NOT NULL,
    source_record_id text NOT NULL,
    source_identity_hash text NOT NULL,
    provider_id text NOT NULL,
    adapter_id text NOT NULL,
    adapter_version text NOT NULL,
    canonical_instrument_id text NOT NULL,
    provider_instrument_id text NOT NULL,
    event_type text NOT NULL,
    event_time timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    knowledge_time timestamptz NOT NULL,
    acquisition_state text NOT NULL,
    quality_state text NOT NULL,
    lifecycle_state text NOT NULL,
    quality_score numeric(3,2),
    reason_codes jsonb NOT NULL,
    validation_result text,
    provenance_id text NOT NULL,
    lineage_parent_id text,
    payload_fingerprint text NOT NULL,
    timeframe text,
    venue text,
    persisted_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_quality_evidence_identity UNIQUE (evidence_id),
    CONSTRAINT ck_quality_evidence_knowledge_boundary CHECK (knowledge_time = received_at),
    CONSTRAINT ck_quality_evidence_quality_state CHECK (
        quality_state IN ('VALID','DEGRADED','STALE','INCOMPLETE','CONTRADICTORY','REJECTED','UNAVAILABLE')
    ),
    CONSTRAINT ck_quality_evidence_quality_score CHECK (
        quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_evidence_logical_fact
    ON meylux.quality_evidence(logical_fact_key, evidence_id);
CREATE INDEX IF NOT EXISTS ix_quality_evidence_source
    ON meylux.quality_evidence(source_record_id, knowledge_time);
CREATE INDEX IF NOT EXISTS ix_quality_evidence_p5
    ON meylux.quality_evidence(knowledge_time, canonical_instrument_id, event_time);

CREATE OR REPLACE FUNCTION meylux.reject_quality_evidence_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'authoritative quality evidence is append-only: % is not permitted on %', TG_OP, TG_TABLE_NAME;
END;
$$;

DROP TRIGGER IF EXISTS trg_quality_evidence_append_only ON meylux.quality_evidence;
CREATE TRIGGER trg_quality_evidence_append_only
BEFORE UPDATE OR DELETE ON meylux.quality_evidence
FOR EACH ROW EXECUTE FUNCTION meylux.reject_quality_evidence_mutation();

GRANT SELECT, INSERT ON meylux.quality_evidence TO meylux_app;
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON meylux.quality_evidence FROM meylux_app;
GRANT SELECT ON meylux.quality_evidence TO meylux_backup;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0009_quality_evidence_persistence')
ON CONFLICT(version) DO NOTHING;
