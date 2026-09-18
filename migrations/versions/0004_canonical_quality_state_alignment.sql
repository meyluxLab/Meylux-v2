-- Meylux V2 Phase 3 Step 8 — align canonical quality-state storage with DataQualityState.
SET TIME ZONE 'UTC';

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'canonical_instruments',
        'canonical_candles',
        'canonical_trades',
        'canonical_orderbook_depth',
        'canonical_derivatives'
    ] LOOP
        EXECUTE format(
            'ALTER TABLE meylux.%I DROP CONSTRAINT IF EXISTS %I',
            t,
            t || '_quality_state_check'
        );
        EXECUTE format(
            'ALTER TABLE meylux.%I ADD CONSTRAINT %I CHECK (quality_state = ''VALID'')',
            t,
            t || '_quality_state_check'
        );
    END LOOP;
END $$;

INSERT INTO meylux.schema_migrations(version)
VALUES ('0004_canonical_quality_state_alignment')
ON CONFLICT(version) DO NOTHING;
