-- Meylux V2 Phase 2 Step 4 — raw/staging acquisition evidence.
-- Raw/staging is evidence only and is not authoritative analytical truth.

SET TIME ZONE 'UTC';

CREATE TABLE IF NOT EXISTS meylux.raw_acquisition_events (
    event_id text PRIMARY KEY,
    provider_id text NOT NULL,
    adapter_id text NOT NULL,
    adapter_version text NOT NULL,
    canonical_instrument_id text NOT NULL,
    provider_instrument_id text NOT NULL,
    event_type text NOT NULL,
    event_time timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    acquisition_state text NOT NULL,
    source_sequence text,
    provenance_id text NOT NULL,
    acquisition_method text NOT NULL,
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL,
    persisted_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_raw_acquisition_identity_hash UNIQUE (identity_hash)
);

CREATE INDEX IF NOT EXISTS ix_raw_acquisition_lookup
    ON meylux.raw_acquisition_events (provider_id, canonical_instrument_id, event_type, event_time);

CREATE INDEX IF NOT EXISTS ix_raw_acquisition_sequence
    ON meylux.raw_acquisition_events (provider_id, canonical_instrument_id, event_type, source_sequence);

COMMENT ON TABLE meylux.raw_acquisition_events IS
    'Phase 2 acquisition evidence/staging only; never authoritative analytical truth.';
COMMENT ON COLUMN meylux.raw_acquisition_events.canonical_bytes IS
    'Deterministic AcquisitionEnvelope canonical serialization captured at acquisition boundary.';
COMMENT ON COLUMN meylux.raw_acquisition_events.identity_hash IS
    'SHA-256 of deterministic AcquisitionEnvelope identity bytes for replay/idempotency.';

INSERT INTO meylux.schema_migrations (version)
VALUES ('0002_raw_acquisition_staging')
ON CONFLICT (version) DO NOTHING;
