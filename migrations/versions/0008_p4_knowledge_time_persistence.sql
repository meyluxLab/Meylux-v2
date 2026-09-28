-- Meylux V2 TO-P4-010 — authoritative P4 knowledge-time persistence correction.
SET TIME ZONE 'UTC';

-- Existing P4 quantitative rows were produced by QuantitativePersistence from
-- closed-candle QuantOrchestrationResult values. For this owner, result.as_of
-- is the close_time of the last closed input candle and is therefore the
-- earliest deterministic knowledge boundary for the complete derived output.
-- This is reconstruction from preserved authoritative execution semantics,
-- not substitution of persisted_at/logged_at/event receipt time.
ALTER TABLE meylux.calculated_indicator_vectors
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_structure_events
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_structure_zones
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.volume_profile_sessions
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_regime_states
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;

UPDATE meylux.calculated_indicator_vectors SET knowledge_time=event_time WHERE knowledge_time IS NULL;
UPDATE meylux.market_structure_events SET knowledge_time=event_time WHERE knowledge_time IS NULL;
UPDATE meylux.market_structure_zones SET knowledge_time=event_time WHERE knowledge_time IS NULL;
UPDATE meylux.volume_profile_sessions SET knowledge_time=session_end WHERE knowledge_time IS NULL;
UPDATE meylux.market_regime_states SET knowledge_time=event_time WHERE knowledge_time IS NULL;

DO $$
DECLARE
    missing_count bigint;
BEGIN
    SELECT
      (SELECT count(*) FROM meylux.calculated_indicator_vectors WHERE knowledge_time IS NULL) +
      (SELECT count(*) FROM meylux.market_structure_events WHERE knowledge_time IS NULL) +
      (SELECT count(*) FROM meylux.market_structure_zones WHERE knowledge_time IS NULL) +
      (SELECT count(*) FROM meylux.volume_profile_sessions WHERE knowledge_time IS NULL) +
      (SELECT count(*) FROM meylux.market_regime_states WHERE knowledge_time IS NULL)
    INTO missing_count;
    IF missing_count <> 0 THEN
        RAISE EXCEPTION 'TO-P4-010 knowledge_time backfill incomplete: % rows remain unavailable', missing_count;
    END IF;
END $$;

ALTER TABLE meylux.calculated_indicator_vectors ALTER COLUMN knowledge_time SET NOT NULL;
ALTER TABLE meylux.market_structure_events ALTER COLUMN knowledge_time SET NOT NULL;
ALTER TABLE meylux.market_structure_zones ALTER COLUMN knowledge_time SET NOT NULL;
ALTER TABLE meylux.volume_profile_sessions ALTER COLUMN knowledge_time SET NOT NULL;
ALTER TABLE meylux.market_regime_states ALTER COLUMN knowledge_time SET NOT NULL;

ALTER TABLE meylux.calculated_indicator_vectors
    ADD CONSTRAINT ck_indicator_vectors_knowledge_time_utc
    CHECK (knowledge_time = (knowledge_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC');
ALTER TABLE meylux.market_structure_events
    ADD CONSTRAINT ck_structure_events_knowledge_time_utc
    CHECK (knowledge_time = (knowledge_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC');
ALTER TABLE meylux.market_structure_zones
    ADD CONSTRAINT ck_structure_zones_knowledge_time_utc
    CHECK (knowledge_time = (knowledge_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC');
ALTER TABLE meylux.volume_profile_sessions
    ADD CONSTRAINT ck_volume_profile_knowledge_time_utc
    CHECK (knowledge_time = (knowledge_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC');
ALTER TABLE meylux.market_regime_states
    ADD CONSTRAINT ck_regime_states_knowledge_time_utc
    CHECK (knowledge_time = (knowledge_time AT TIME ZONE 'UTC') AT TIME ZONE 'UTC');

INSERT INTO meylux.schema_migrations(version)
VALUES ('0008_p4_knowledge_time_persistence')
ON CONFLICT(version) DO NOTHING;
