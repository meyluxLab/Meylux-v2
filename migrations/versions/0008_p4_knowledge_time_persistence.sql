-- Meylux V2 TO-P4-010 — authoritative P4 knowledge-time persistence correction.
SET TIME ZONE 'UTC';

-- The existing P4 tables are append-only. Historical Class-B reconstruction
-- therefore MUST NOT issue UPDATE against existing rows. For families whose
-- governing semantic proves knowledge_time == event_time, a STORED generated
-- column makes the authoritative value materialized for both legacy and new
-- rows without mutating history.
ALTER TABLE meylux.calculated_indicator_vectors
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz
    GENERATED ALWAYS AS (event_time) STORED;

ALTER TABLE meylux.market_regime_states
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz
    GENERATED ALWAYS AS (event_time) STORED;

-- The persisted ORCHESTRATION structure row is a snapshot summary, not one of
-- the structural facts governed by DOC-P4-002. That authority therefore does
-- not establish a fact-level knowledge_time equivalence for this summary.
-- Keep it explicitly nullable until an applicable governed semantic authority
-- establishes the summary's knowledge boundary.
ALTER TABLE meylux.market_structure_events
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;

-- These families currently have no authoritative QuantitativePersistence
-- writer and no governing historical reconstruction rule. Their nullable
-- knowledge_time remains the explicit machine-readable unavailable boundary.
ALTER TABLE meylux.market_structure_zones
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;

ALTER TABLE meylux.volume_profile_sessions
    ADD COLUMN IF NOT EXISTS knowledge_time timestamptz;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0008_p4_knowledge_time_persistence')
ON CONFLICT(version) DO NOTHING;