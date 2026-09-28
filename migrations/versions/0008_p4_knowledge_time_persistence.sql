-- Meylux V2 TO-P4-010 — authoritative P4 knowledge-time persistence correction.
SET TIME ZONE 'UTC';

-- Existing P4 quantitative rows were produced by QuantitativePersistence from
-- closed-candle QuantOrchestrationResult values. For this owner, result.as_of
-- is the close_time of the last closed input candle and is therefore the
-- earliest deterministic knowledge boundary for the complete derived output.
-- This is reconstruction from preserved authoritative execution semantics,
-- not substitution of persisted_at/logged_at/event receipt time.
ALTER TABLE meylux.calculated_indicator_vectors ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_structure_events ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_structure_zones ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.volume_profile_sessions ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;
ALTER TABLE meylux.market_regime_states ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;

UPDATE meylux.calculated_indicator_vectors SET knowledge_time=event_time WHERE knowledge_time IS NULL;
UPDATE meylux.market_structure_events SET knowledge_time=event_time WHERE knowledge_time IS NULL;
-- These two tables have no current QuantitativePersistence writer. Their legacy
-- rows therefore lack a repository-proven reconstruction rule for knowledge_time.
-- Preserve them as explicitly unevidenced and fail rather than laundering event/session
-- boundaries into knowledge_time.
DO $
DECLARE unsupported_legacy bigint;
BEGIN
    SELECT
      (SELECT count(*) FROM meylux.market_structure_zones WHERE knowledge_time IS NULL) +
      (SELECT count(*) FROM meylux.volume_profile_sessions WHERE knowledge_time IS NULL)
    INTO unsupported_legacy;
    IF unsupported_legacy <> 0 THEN
        RAISE EXCEPTION 'TO-P4-010 insufficient historical knowledge_time evidence for % zone/profile rows', unsupported_legacy;
    END IF;
END $;
UPDATE meylux.market_regime_states SET knowledge_time=event_time WHERE knowledge_time IS NULL;

DO $$
DECLARE missing_count bigint;
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

INSERT INTO meylux.schema_migrations(version)
VALUES ('0008_p4_knowledge_time_persistence')
ON CONFLICT(version) DO NOTHING;
