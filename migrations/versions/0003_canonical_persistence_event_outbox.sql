-- Meylux V2 Phase 3 Step 8 — authoritative canonical persistence and event outbox.
SET TIME ZONE 'UTC';

CREATE TABLE IF NOT EXISTS meylux.canonical_instruments (
    record_id text PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    instrument_id text NOT NULL,
    event_time timestamptz NOT NULL,
    provenance_id text NOT NULL,
    source_record_id text NOT NULL,
    lineage_parent_id text NOT NULL,
    quality_state text NOT NULL CHECK (quality_state = 'valid'),
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_canonical_instruments_event_time ON meylux.canonical_instruments(event_time);
CREATE INDEX IF NOT EXISTS ix_canonical_instruments_instrument_time ON meylux.canonical_instruments(instrument_id,event_time);

CREATE TABLE IF NOT EXISTS meylux.canonical_candles (
    record_id text PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    instrument_id text NOT NULL,
    event_time timestamptz NOT NULL,
    provenance_id text NOT NULL,
    source_record_id text NOT NULL,
    lineage_parent_id text NOT NULL,
    quality_state text NOT NULL CHECK (quality_state = 'valid'),
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_canonical_candles_instrument_time ON meylux.canonical_candles(instrument_id,event_time);

CREATE TABLE IF NOT EXISTS meylux.canonical_trades (
    record_id text PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    instrument_id text NOT NULL,
    event_time timestamptz NOT NULL,
    provenance_id text NOT NULL,
    source_record_id text NOT NULL,
    lineage_parent_id text NOT NULL,
    quality_state text NOT NULL CHECK (quality_state = 'valid'),
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_canonical_trades_instrument_time ON meylux.canonical_trades(instrument_id,event_time);

CREATE TABLE IF NOT EXISTS meylux.canonical_orderbook_depth (
    record_id text PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    instrument_id text NOT NULL,
    event_time timestamptz NOT NULL,
    provenance_id text NOT NULL,
    source_record_id text NOT NULL,
    lineage_parent_id text NOT NULL,
    quality_state text NOT NULL CHECK (quality_state = 'valid'),
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_canonical_orderbook_instrument_time ON meylux.canonical_orderbook_depth(instrument_id,event_time);

CREATE TABLE IF NOT EXISTS meylux.canonical_derivatives (
    record_id text PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    instrument_id text NOT NULL,
    event_time timestamptz NOT NULL,
    provenance_id text NOT NULL,
    source_record_id text NOT NULL,
    lineage_parent_id text NOT NULL,
    quality_state text NOT NULL CHECK (quality_state = 'valid'),
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    payload_json jsonb NOT NULL,
    canonical_bytes bytea NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_canonical_derivatives_instrument_time ON meylux.canonical_derivatives(instrument_id,event_time);

CREATE TABLE IF NOT EXISTS meylux.data_quality_logs (
    log_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    record_id text,
    quality_state text NOT NULL,
    lifecycle_state text NOT NULL,
    quality_score numeric(3,2) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    reason_codes jsonb NOT NULL,
    validation_result text,
    provenance_id text,
    source_record_id text,
    lineage_parent_id text,
    payload_fingerprint text,
    logged_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_quality_logs_record ON meylux.data_quality_logs(record_id,logged_at);
CREATE INDEX IF NOT EXISTS ix_quality_logs_state ON meylux.data_quality_logs(quality_state,logged_at);

CREATE TABLE IF NOT EXISTS meylux.canonical_event_outbox (
    sequence_no bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    record_id text NOT NULL,
    event_type text NOT NULL,
    event_time timestamptz NOT NULL,
    payload_json jsonb NOT NULL,
    published_at timestamptz,
    published_stream_id text
);
CREATE INDEX IF NOT EXISTS ix_canonical_outbox_pending ON meylux.canonical_event_outbox(sequence_no) WHERE published_at IS NULL;

CREATE OR REPLACE FUNCTION meylux.reject_canonical_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'authoritative canonical history is append-only: % is not permitted on %', TG_OP, TG_TABLE_NAME;
END;
$$;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'canonical_instruments',
        'canonical_candles',
        'canonical_trades',
        'canonical_orderbook_depth',
        'canonical_derivatives',
        'data_quality_logs'
    ] LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_append_only ON meylux.%I', t, t);
        EXECUTE format('CREATE TRIGGER trg_%I_append_only BEFORE UPDATE OR DELETE ON meylux.%I FOR EACH ROW EXECUTE FUNCTION meylux.reject_canonical_mutation()', t, t);
    END LOOP;
END $$;

GRANT USAGE ON SCHEMA meylux TO meylux_app;
GRANT SELECT, INSERT ON meylux.canonical_instruments, meylux.canonical_candles, meylux.canonical_trades, meylux.canonical_orderbook_depth, meylux.canonical_derivatives TO meylux_app;
GRANT SELECT, INSERT ON meylux.data_quality_logs TO meylux_app;
GRANT SELECT, INSERT, UPDATE ON meylux.canonical_event_outbox TO meylux_app;
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON meylux.canonical_instruments, meylux.canonical_candles, meylux.canonical_trades, meylux.canonical_orderbook_depth, meylux.canonical_derivatives, meylux.data_quality_logs FROM meylux_app;

GRANT SELECT ON meylux.canonical_instruments, meylux.canonical_candles, meylux.canonical_trades, meylux.canonical_orderbook_depth, meylux.canonical_derivatives, meylux.data_quality_logs, meylux.canonical_event_outbox TO meylux_backup;
DO $MEYLUX$
DECLARE
    seq_name text;
BEGIN
    seq_name := pg_get_serial_sequence('meylux.canonical_event_outbox', 'sequence_no');
    IF seq_name IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO meylux_app', seq_name);
    END IF;
    seq_name := pg_get_serial_sequence('meylux.data_quality_logs', 'log_id');
    IF seq_name IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO meylux_app', seq_name);
    END IF;
END $MEYLUX$;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0003_canonical_persistence_event_outbox')
ON CONFLICT(version) DO NOTHING;
