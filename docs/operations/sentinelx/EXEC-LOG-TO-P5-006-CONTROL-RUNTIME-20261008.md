# EXEC-LOG-TO-P5-006-CONTROL-RUNTIME-20261008

**Task Order:** `TO-P5-006`  
**Phase / Step:** `PH-P5 / STEP-P5-006`  
**Role:** CONTROL / REVIEWER — `ROL-V2-001`  
**Execution authority:** Project Owner continuation directive 2026-10-08; ADR-GOVERNANCE-013 / ADR-GOVERNANCE-014  
**Runtime host:** SentinelX governed host `server-l6rf`

## 1. Deployment baseline

- Authoritative SoT merge: `1c8a86a02b69abea4b19047c2ac746898fc43c87`
- VPS repository was fast-forwarded from `d7c3fa31cb092543440f2769ffbf9b6022c29a6a` to `1c8a86a02b69abea4b19047c2ac746898fc43c87`.
- Existing local VPS changes in `docs/requirements/P5_002_FACT_REQUIREMENTS_MATRIX.md` and `src/meylux/orchestration/engine.py` were preserved in a named Git stash before deployment; they were not discarded.
- Docker images for `api` and `worker-specialist` were rebuilt from the deployed Source-of-Truth revision.
- `db`, `redis`, `api`, and `worker-specialist` reached running/healthy runtime state.

## 2. Authoritative upstream fact surface

CONTROL independently reused the exact persisted Group-C fact surface already verified under `TO-P4-015 / AR-P4-023`, rather than fabricating or regenerating acceptance facts.

The retained acceptance database `to-p4-015-db-clean` contained:

- 1,040,100 canonical Binance trades;
- 22 closed `BTCUSDT / 15m` canonical candles;
- 23 calculated indicator vectors;
- 2 valid `BTCUSDT / 15m` Volume Profile sessions.

The two accepted Volume Profile sessions were:

- `[2026-10-07T04:30:00Z, 2026-10-07T04:45:00Z)`;
- `[2026-10-07T05:15:00Z, 2026-10-07T05:30:00Z)`.

Both carry explicit `BINANCE` venue context and non-null authoritative `knowledge_time`.

The four required S-03 vectors in the authoritative source surface are:

- `VOLUME_SMA`
- `RVOL`
- `VOLUME_SPIKE`
- `VOLUME_CLIMAX`

with explicit Binance venue and non-null knowledge time.

## 3. Runtime fact transfer

The exact three authoritative fact tables were transferred into the governed runtime database with append-only conflict-safe insertion:

- `meylux.canonical_candles`
- `meylux.calculated_indicator_vectors`
- `meylux.volume_profile_sessions`

No existing row was overwritten or deleted.

The authoritative acceptance Snapshot was bounded to the verified `AR-P4-023` fact surface. Additional bounded diagnostic prerequisite-resolution rows present in the runtime database were not used as acceptance evidence and did not enter the acceptance Snapshot.

## 4. Stage-1 Snapshot

CONTROL constructed Snapshot:

- Snapshot ID: `35e2cebfa0db078433cb5069b37c9e1368270fca44f98476f53ed9a5c47664ae`
- Contract version: `1.2.0`
- `as_of`: the maximum authoritative knowledge boundary of the accepted source surface.
- Facts were reconstructed from persisted PostgreSQL records with structured EvidenceRefs preserving source family, record identity, identity hash, event time, knowledge time, timeframe and venue.
- Closed-candle knowledge boundary used the authoritative persisted candle `close_time` represented by the canonical candle payload; no provider REST finality was synthesized.

## 5. S-03 runtime execution

S-03 was dispatched through an isolated Redis queue and executed by the actual `SpecialistWorkerHandler` against the governed runtime PostgreSQL.

Observed:

- queue dispatch: `ENQUEUED`;
- worker delivery: `DELIVERED`;
- worker completion: `ACKED`;
- PostgreSQL persistence: inserted;
- direct PostgreSQL read-back: present;
- deterministic identity: `7f43c0c61768ad9b59f87dd3d4ad0117f7f984ab50cded4f3037eeb27f6fc9be`;
- output status: `PARTIAL`.

Within the governed primary acceptance slice:

- `BTCUSDT / BINANCE / 15m / CONDITION`: `SUCCESS`;
- `BTCUSDT / BINANCE / 15m / PRICE_CONTEXT`: `SUCCESS`.

Other configured symbol/venue/timeframe combinations with no authoritative facts remain explicit `INSUFFICIENT_DATA`; no fallback or fabricated value was emitted.

Identical replay produced:

- `inserted=false`;
- `readback=true`;
- identical output identity;
- exactly one persisted truth row for S-03.

## 6. S-17 runtime execution

S-17 was dispatched through a separate isolated Redis queue and executed by the actual `SpecialistWorkerHandler` against the governed runtime PostgreSQL.

Observed:

- queue dispatch: `ENQUEUED`;
- worker delivery: `DELIVERED`;
- worker completion: `ACKED`;
- PostgreSQL persistence: inserted;
- direct PostgreSQL read-back: present;
- deterministic identity: `25aa8b15bba6e9ead4f65116fe2db7a15c1b2b8cdd1c8e5e0040023feabb4cf3`;
- output status: `PARTIAL`.

Within the governed primary acceptance slice:

- `BTCUSDT / BINANCE / 15m / POSITION`: `SUCCESS`, state `BELOW`;
- `BTCUSDT / BINANCE / 15m / POC`: `SUCCESS`, state `AVAILABLE`;
- `BTCUSDT / BINANCE / 15m / PRIOR_POC_RETURN`: `SUCCESS`, state `NOT_RETURNED`.

The required prior-session predicate was evaluated from the two authoritative persisted sessions; no synthetic session history was created.

Identical replay produced:

- `inserted=false`;
- `readback=true`;
- identical output identity;
- exactly one persisted truth row for S-17.

## 7. Persistence / append-only boundary

The governed runtime contains:

- `trg_specialist_outputs_append_only`;
- `trg_calculated_indicator_vectors_append_only`;
- `trg_volume_profile_sessions_append_only`.

Final specialist read-back contains exactly one row for each of S-03 and S-17 for Snapshot `35e2cebfa0db078433cb5069b37c9e1368270fca44f98476f53ed9a5c47664ae`, with `record_id = identity_hash`.

## 8. Scope / non-claims

No trading, capital, custody, account, leverage, Futures, Forex, PRQ-3, PRQ-4, new provider abstraction, new P4 mathematics, or later specialist capability was introduced.

A bounded upstream fact-surface restoration was required because the governed deployment did not initially contain the already verified `AR-P4-023` acceptance population. The existing P4 truth and persistence contracts were reused; no second truth source was created.

A bounded attempt to obtain a fresh Binance WebSocket closed 15m candle was also performed but did not observe a final `k.x=true` event within its message bound. This did not become acceptance evidence and no REST close-time fallback was used.

## 9. Execution conclusion

The governed runtime execution path for `TO-P5-006` is established and independently read back.

This log is evidence for CONTROL's independent audit. It is not itself a Step closure declaration.

--- END EXECUTION LOG ---