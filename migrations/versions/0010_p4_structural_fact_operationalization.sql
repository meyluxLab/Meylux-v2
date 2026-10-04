-- Meylux V2 TO-P4-013 — authoritative individual structural event/zone facts.
-- Additive and append-only: no historical row is updated or backfilled.
SET TIME ZONE 'UTC';

-- event_time remains the semantic event location (the relevant candle open_time).
-- confirmation_time and knowledge_time are separate authoritative close-time fields.
-- Existing ORCHESTRATION summaries retain NULL temporal fact fields.
ALTER TABLE meylux.market_structure_events
    ADD COLUMN IF NOT EXISTS confirmation_time timestamptz;
ALTER TABLE meylux.market_structure_events
    ADD COLUMN IF NOT EXISTS source_event_identity text;

ALTER TABLE meylux.market_structure_zones
    ADD COLUMN IF NOT EXISTS confirmation_time timestamptz;
ALTER TABLE meylux.market_structure_zones
    ADD COLUMN IF NOT EXISTS source_event_identity text;

CREATE INDEX IF NOT EXISTS ix_structure_events_knowledge_boundary
    ON meylux.market_structure_events(symbol, timeframe, knowledge_time, event_time)
    WHERE knowledge_time IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_structure_zones_knowledge_boundary
    ON meylux.market_structure_zones(symbol, timeframe, knowledge_time, event_time)
    WHERE knowledge_time IS NOT NULL;

-- Preserve the existing append-only triggers and least-privilege grants from
-- migrations 0005/0006. This migration does not mutate historical facts.
INSERT INTO meylux.schema_migrations(version)
VALUES ('0010_p4_structural_fact_operationalization')
ON CONFLICT(version) DO NOTHING;
