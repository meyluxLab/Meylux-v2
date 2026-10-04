# EXEC-LOG — TO-P4-012 CONTROL Runtime Acceptance

**execution_id:** `EXEC-LOG-TO-P4-012-CONTROL-RUNTIME-20261004`  
**task_id:** `TO-P4-012`  
**step_id:** `STEP-P5-004` — upstream corrective dependency  
**phase_id:** `PH-P5`  
**target:** `server-l6rf` / governed Meylux VPS  
**executor_role:** `ROL-V2-001 — CONTROL / REVIEWER`  
**mechanism:** SentinelX only  
**execution date:** 2026-10-04  
**authoritative implementation revision:** `0b85a8abe9378c6cc213d3b69249ae66d491bd05`  
**merged repository revision:** `a95f23eabf6d0324fcaacbbed06862881a7e52fa`

## 1. Execution boundary

The existing governed `/srv/meylux-v2` checkout was not overwritten because it contained pre-existing tracked local modifications. CONTROL preserved that state.

An isolated temporary Git worktree was created from the exact Producer implementation commit `0b85a8abe9378c6cc213d3b69249ae66d491bd05` and mounted read-only into a temporary container using the existing governed runtime image. This provided execution of the authorized implementation against the governed PostgreSQL environment without replacing the pre-existing VPS checkout.

No migration, provider credential activation, trading operation, capital operation, or unrelated service mutation was performed.

## 2. Environment observations

- Governed PostgreSQL and Redis services were reachable.
- Repository implementation under test: `0b85a8abe9378c6cc213d3b69249ae66d491bd05`.
- Governed database contained 2,996 raw acquisition events.
- Governed database contained 158 canonical candles.
- 2,995 AVAILABLE Binance CANDLE raw events were present.
- All 158 canonical candles in the governed slice carried provenance `binance:binance-acquisition`.
- Exactly one AVAILABLE Binance CANDLE raw row carried explicit string-valued venue/source context; its venue was `BINANCE`.
- CI/test fixture records were not used as authoritative runtime evidence.

## 3. Actual worker-to-persistence execution

CONTROL executed the actual `QuantWorkerHandler → QuantitativeOrchestrator → QuantitativePersistence → PostgreSQL` path using authoritative persisted BTCUSDT candle inputs.

Primary timeframe population:
- 15m: 117 closed candles.

Higher-timeframe population:
- 1h: 31 closed candles.
- 4h: 10 closed candles.

First execution produced 57 new venue-complete quantitative facts:
- 15m: 19
- 1h: 19
- 4h: 19

The new records carried explicit `venue_context=BINANCE`. Existing historical venue-null records were not updated or deleted.

## 4. EMA runtime result

The five required fact families were observed across the governed execution:

- 15m: EMA-9/20/21/50 VALID; EMA-200 INSUFFICIENT_HISTORY with null numeric value.
- 1h: EMA-9/20/21 VALID; EMA-50/200 INSUFFICIENT_HISTORY with null numeric values.
- 4h: EMA-9 VALID; EMA-20/21/50/200 INSUFFICIENT_HISTORY with null numeric values.

No EMA value was fabricated.

## 5. Replay / idempotency

The identical worker input was replayed immediately.

Result:
- first execution: 57 new venue-complete facts;
- second execution: 0 additional facts.

Existing append-only identity/deduplication semantics therefore held for the governed execution.

## 6. Temporal / EvidenceRef verification

CONTROL independently constructed P5-compatible `EvidenceRef` objects from newly persisted records using the governed quantitative source family `p4_quantitative` and persisted fields.

Nine representative records covering valid and insufficient-history EMA outcomes across 15m/1h/4h were successfully accepted by the current P5 Input Snapshot Builder.

The same records were tested with `as_of` moved one microsecond before their knowledge boundary; the Snapshot Builder rejected every such case with the governed lookahead error.

Runtime read-back showed:
- no null knowledge_time on the inspected BTCUSDT quantitative records;
- no knowledge_time later than event_time;
- no NaN/Infinity numeric leakage.

## 7. Regression evidence

CONTROL independently executed the complete test suite from the exact implementation worktree using the governed runtime image:

`Ran 606 tests in 5.429s — OK (skipped=6)`.

The Producer-reported GitHub Actions evidence associated with implementation commit `0b85a8abe9378c6cc213d3b69249ae66d491bd05` was independently read from repository metadata:
- CI Core Run `37155184431` / #1714 — SUCCESS.
- CI Docker Foundation Run `37155184423` / #599 — SUCCESS.

The forwarded Owner/Producer narrative also mentioned Core #1715 / Docker #600. Those run numbers are not the workflow runs associated with the implementation commit according to the authoritative repository Actions association, and the Build Report at `b5187de950197e5212c897bbc5020cd18e597bb4` itself records #1714/#599. CONTROL therefore does not rely on the #1715/#600 numbers.

## 8. VPS safety / cleanup

The temporary worktree and temporary verification container were isolated from the existing governed checkout. No tracked local modification under `/srv/meylux-v2` was overwritten or reset.

No VPS operation outside the authorized TO-P4-012 runtime acceptance boundary was performed.

## 9. Execution disposition

**EXECUTED — evidence sufficient for independent CONTROL audit.**

Execution evidence establishes the TO-P4-012 runtime acceptance boundary. It does not by itself close the Task Order; closure is established separately by the CONTROL Audit Report and G12 synchronization.
