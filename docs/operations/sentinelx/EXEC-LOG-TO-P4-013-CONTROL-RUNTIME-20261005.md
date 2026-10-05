# EXEC-LOG — TO-P4-013 CONTROL Runtime Acceptance

**execution_id:** `EXEC-LOG-TO-P4-013-CONTROL-RUNTIME-20261005`  
**task_id:** `TO-P4-013`  
**phase_id:** `PH-P5`  
**step_boundary:** `STEP-P5-004 — COMPLETE / VERIFIED`; downstream `STEP-P5-005` remains NOT ACTIVATED  
**target:** `server-l6rf` / governed Meylux VPS  
**executor_role:** `ROL-V2-001 — CONTROL / REVIEWER`  
**mechanism:** SentinelX only  
**execution date:** 2026-10-05  
**implementation revision:** `7c809edc38cb08451f605383af568febb9ef6827`  
**merged repository revision:** `0be8406454ad933a23ac1d33609553731ab23000`

## 1. Execution Boundary

The existing governed `/srv/meylux-v2` checkout was not overwritten because it contained pre-existing tracked local modifications.

CONTROL created an isolated temporary worktree at the exact implementation revision and built a temporary Docker image from that exact source.

No migration, provider credential activation, trading operation, capital operation, or unrelated service mutation was performed.

The existing governed quantitative worker was not replaced or restarted.

## 2. Authoritative Runtime Input

CONTROL read authoritative persisted canonical candles from PostgreSQL:

- BTCUSDT canonical rows: 158;
- 15m primary: 117 closed candles;
- 1h: 31 closed candles;
- 4h: 10 closed candles;
- canonical provenance: `binance:binance-acquisition`.

CI fixtures were not used as authoritative runtime input.

## 3. Worker-to-Persistence Execution

CONTROL constructed the governed `CTR-P4-QUANT-CANDLE-CLOSE-1.0` QueueEnvelope from persisted canonical input and invoked the exact:

`QueueEnvelope → QuantWorkerHandler → QuantitativeOrchestrator → QuantitativePersistence → PostgreSQL`

path.

First execution:

- new individual structural events: **248**;
- new structural zones: **64**.

Immediate identical replay:

- additional structural events: **0**;
- additional structural zones: **0**.

## 4. Runtime Read-Back

Structural events were persisted for the 15m, 1h and 4h fact boundaries.

Zone rows were persisted for the applicable zone-bearing event families.

All newly inspected event and zone rows had non-null `knowledge_time`.

All 248 newly persisted structural-event rows had `venue_context=BINANCE`.

No venue inference was performed.

Classification read-back found zero missing, unresolved, or member-mismatch source identities.

## 5. Temporal Boundary

Primary 15m authoritative close boundary:

`2026-10-01T18:33:59.999Z`

Persisted structural event count with `knowledge_time` after that boundary:

**0**

The check was performed against canonical candle `close_time`, the authoritative knowledge boundary.

## 6. 4h History Boundary

The governed 4h input contained only 10 closed candles.

The resulting structural state remained `UNCONFIRMED`; no guessed directional state or fabricated structural fact was persisted.

CI separately covers explicit `insufficient_history` persistence for short neutral structural histories.

## 7. Append-Only Acceptance

Using the application role:

### `meylux.market_structure_events`
- UPDATE rejected with SQLSTATE `42501`.
- DELETE rejected with SQLSTATE `42501`.
- Row remained present and unchanged.

### `meylux.market_structure_zones`
- UPDATE rejected with SQLSTATE `42501`.
- DELETE rejected with SQLSTATE `42501`.
- Row remained present and unchanged.

## 8. Historical Protection

Canonical row count remained **158**.

No historical P4/G-4 source data was rewritten, deleted, or backfilled.

## 9. Cleanup

The temporary worktree and temporary Docker image were removed after verification.

## 10. Execution Disposition

**EXECUTED — SUFFICIENT FOR INDEPENDENT CONTROL VERIFICATION.**

This execution establishes the governed runtime acceptance boundary for `TO-P4-013`. Task Order closure is established by `AR-P4-020` and the associated peripheral synchronization.
