-- Meylux V2 TO-P4-010 — authoritative P4 knowledge-time persistence correction.
SET TIME ZONE 'UTC';

-- Existing P4 quantitative rows were produced by QuantitativePersistence from
-- closed-candle QuantOrchestrationResult values. For this owner, result.as_of
-- is the close_time of the last closed input candle and is therefore the
-- earliest deterministic knowledge boundary for the complete derived output.
-- This is reconstruction from preserved authoritative execution semantics,
-- not substitution of persisted_at/logged_at/event receipt time.

INSERT INTO meylux.schema_migrations(version)
VALUES ('0008_p4_knowledge_time_persistence')
ON CONFLICT(version) DO NOTHING;
