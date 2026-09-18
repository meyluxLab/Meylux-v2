-- Meylux V2 Phase 4 Step 1 — quantitative persistence-model foundation only.
SET TIME ZONE 'UTC';

CREATE TABLE IF NOT EXISTS meylux.calculated_indicator_vectors (
    record_id text PRIMARY KEY,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    event_time timestamptz NOT NULL,
    source_ref text,
    venue_context text,
    version text NOT NULL,
    calculation_version text NOT NULL,
    status text NOT NULL,
    reason text NOT NULL,
    value_numeric numeric,
    payload_json jsonb NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_indicator_vectors_symbol_time
    ON meylux.calculated_indicator_vectors(symbol, timeframe, event_time);

CREATE TABLE IF NOT EXISTS meylux.market_structure_events (
    record_id text PRIMARY KEY,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    event_time timestamptz NOT NULL,
    event_type text NOT NULL,
    source_ref text,
    venue_context text,
    version text NOT NULL,
    calculation_version text NOT NULL,
    status text NOT NULL,
    reason text NOT NULL,
    value_numeric numeric,
    payload_json jsonb NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_structure_events_symbol_time
    ON meylux.market_structure_events(symbol, timeframe, event_time);

CREATE TABLE IF NOT EXISTS meylux.market_structure_zones (
    record_id text PRIMARY KEY,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    event_time timestamptz NOT NULL,
    zone_type text NOT NULL,
    source_ref text,
    venue_context text,
    version text NOT NULL,
    calculation_version text NOT NULL,
    status text NOT NULL,
    reason text NOT NULL,
    value_numeric numeric,
    payload_json jsonb NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_structure_zones_symbol_time
    ON meylux.market_structure_zones(symbol, timeframe, event_time);

CREATE TABLE IF NOT EXISTS meylux.volume_profile_sessions (
    record_id text PRIMARY KEY,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    session_start timestamptz NOT NULL,
    session_end timestamptz NOT NULL,
    source_ref text,
    venue_context text,
    version text NOT NULL,
    calculation_version text NOT NULL,
    status text NOT NULL,
    reason text NOT NULL,
    value_numeric numeric,
    payload_json jsonb NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now(),
    CHECK (session_end > session_start)
);
CREATE INDEX IF NOT EXISTS ix_volume_profile_sessions_symbol_time
    ON meylux.volume_profile_sessions(symbol, timeframe, session_start);

CREATE TABLE IF NOT EXISTS meylux.market_regime_states (
    record_id text PRIMARY KEY,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    event_time timestamptz NOT NULL,
    regime_state text NOT NULL,
    source_ref text,
    venue_context text,
    version text NOT NULL,
    calculation_version text NOT NULL,
    status text NOT NULL,
    reason text NOT NULL,
    value_numeric numeric,
    payload_json jsonb NOT NULL,
    identity_hash text NOT NULL UNIQUE,
    persisted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_market_regime_states_symbol_time
    ON meylux.market_regime_states(symbol, timeframe, event_time);

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'calculated_indicator_vectors',
        'market_structure_events',
        'market_structure_zones',
        'volume_profile_sessions',
        'market_regime_states'
    ] LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_append_only ON meylux.%I', t, t);
        EXECUTE format(
            'CREATE TRIGGER trg_%I_append_only BEFORE UPDATE OR DELETE ON meylux.%I FOR EACH ROW EXECUTE FUNCTION meylux.reject_canonical_mutation()',
            t, t
        );
    END LOOP;
END $$;

GRANT SELECT, INSERT ON
    meylux.calculated_indicator_vectors,
    meylux.market_structure_events,
    meylux.market_structure_zones,
    meylux.volume_profile_sessions,
    meylux.market_regime_states
TO meylux_app;

REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON
    meylux.calculated_indicator_vectors,
    meylux.market_structure_events,
    meylux.market_structure_zones,
    meylux.volume_profile_sessions,
    meylux.market_regime_states
FROM meylux_app;

GRANT SELECT ON
    meylux.calculated_indicator_vectors,
    meylux.market_structure_events,
    meylux.market_structure_zones,
    meylux.volume_profile_sessions,
    meylux.market_regime_states
TO meylux_backup;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0005_quantitative_foundation')
ON CONFLICT(version) DO NOTHING;
