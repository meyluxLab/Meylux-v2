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

-- Enforce the temporal contract for new facts at the database boundary.
-- NOT VALID preserves historical rows without backfill while still checking new inserts.
DO $p4$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_structure_events_fact_temporal'
          AND conrelid = 'meylux.market_structure_events'::regclass
    ) THEN
        ALTER TABLE meylux.market_structure_events
            ADD CONSTRAINT ck_structure_events_fact_temporal
            CHECK (
                (event_type = 'ORCHESTRATION'
                    AND confirmation_time IS NULL
                    AND knowledge_time IS NULL
                    AND source_event_identity IS NULL)
                OR
                (event_type <> 'ORCHESTRATION'
                    AND confirmation_time IS NOT NULL
                    AND knowledge_time IS NOT NULL
                    AND confirmation_time = knowledge_time
                    AND event_time <= confirmation_time)
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_structure_zones_fact_temporal'
          AND conrelid = 'meylux.market_structure_zones'::regclass
    ) THEN
        ALTER TABLE meylux.market_structure_zones
            ADD CONSTRAINT ck_structure_zones_fact_temporal
            CHECK (
                confirmation_time IS NOT NULL
                AND knowledge_time IS NOT NULL
                AND confirmation_time = knowledge_time
                AND event_time <= confirmation_time
            ) NOT VALID;
    END IF;
END
$p4$;

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
