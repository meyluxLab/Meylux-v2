-- Meylux V2 TO-P4-010 — authoritative P4 knowledge-time persistence correction.
SET TIME ZONE 'UTC';

-- The five P4 quantitative output tables are the existing authoritative
-- persistence boundary. knowledge_time is nullable so historically unevidenced
-- rows remain explicitly unavailable rather than being assigned a substitute.
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

-- Historical Class B reconstruction:
-- the repository's authoritative QuantitativePersistence writer has always
-- persisted these three populated families at QuantOrchestrationResult.as_of.
-- The orchestrator's frozen closed-candle boundary makes knowledge_time equal
-- to that boundary. This is deterministic reconstruction from preserved
-- execution semantics, not persisted_at/logged_at/current-time substitution.
UPDATE meylux.calculated_indicator_vectors
SET knowledge_time = event_time
WHERE knowledge_time IS NULL;

UPDATE meylux.market_regime_states
SET knowledge_time = event_time
WHERE knowledge_time IS NULL;

-- The persisted structure family is currently an ORCHESTRATION summary whose
-- event_time is the orchestration boundary. Only that exact persisted fact
-- shape is reconstructible. Any other legacy structure event remains NULL.
UPDATE meylux.market_structure_events
SET knowledge_time = event_time
WHERE knowledge_time IS NULL
  AND event_type = 'ORCHESTRATION';

-- market_structure_zones and volume_profile_sessions currently have no
-- QuantitativePersistence writer and therefore no authoritative historical
-- reconstruction rule. Leave their knowledge_time NULL. NULL is the
-- machine-readable unavailable/unevidenced disposition and must not be turned
-- into a fabricated timestamp.

INSERT INTO meylux.schema_migrations(version)
VALUES ('0008_p4_knowledge_time_persistence')
ON CONFLICT(version) DO NOTHING;