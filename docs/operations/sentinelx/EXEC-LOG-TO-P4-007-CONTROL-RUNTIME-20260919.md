# EXEC-LOG — TO-P4-007 CONTROL Operational Verification Cycle

execution_id: EXEC-LOG-TO-P4-007-CONTROL-RUNTIME-20260919
task_id: TO-P4-007
step_id: STEP-P4-006
target: server-l6rf / /srv/meylux-v2
executor_role: ROL-V2-001 — CONTROL / REVIEWER
authorization_reference: Project Owner Directive — AUTHORIZE PH-P4 / STEP-P4-006 AND DELEGATE FULL OPERATIONAL WORKFLOW AUTHORITY — 2026-09-19
repository_version_context: 48bae89931c3ab003223a867ab9f9bf75fe3117a

## 1. Execution disposition

EXECUTED / PARTIALLY VERIFIED — Step closure NOT reached.

## 2. Actions and observed results

### A. VPS repository synchronization
- SentinelX privileged CONTROL execution.
- Previous checkout: 6bb95c9cb046d45854daa511a6c18cf7cc82bbe6.
- Target checkout: 48bae89931c3ab003223a867ab9f9bf75fe3117a.
- Fetch, checkout, hard reset and clean completed successfully.

### B. Compose build and runtime start
- Compose configuration validation: PASS.
- API and worker-quant image builds: PASS.
- db, redis, api and worker-quant started successfully; db and redis healthy.

### C. Database migration / authoritative schema
- Host migration wrapper initially failed because host-level psql is absent.
- CONTROL continued using the repository migration SQL through the authorized DB container, preserving migration order 0001 through 0005.
- All five migration scripts executed successfully and the quantitative tables were created.
- Quantitative table counts immediately after migration were zero.
- This is runtime-foundation evidence, not real-data evidence.

### D. API operational wire probe
- TCP probe from the API container to 127.0.0.1:8080 returned HTTP/1.1 200 OK with real CRLF framing and an empty JSON array.
- Result: PASS.
- No authoritative data was fabricated or inserted.

### E. Worker failure/recovery boundary probe
- Published one controlled invalid worker envelope using contract CTR-P4-QUANT-CANDLE-CLOSE-1.0 with an empty candle list.
- Message ID: CONTROL-P4-FAILURE-PROBE-20260919.
- Observed attempt 1 failure/retry, attempt 2 retry, attempt 3 delivery, one DLQ entry, and zero pending entries afterward.
- Result: failure isolation/retry/DLQ boundary PASS.

### F. Security privilege probe
- meylux_app privileges on calculated_indicator_vectors: SELECT=true, INSERT=true, UPDATE=false, DELETE=false.
- Direct UPDATE probe was rejected with permission denied.
- Result: append-only application privilege boundary PASS.

### G. Deterministic runtime performance measurement
- Workload: 1000 closed synthetic BTCUSDT 15M canonical candles.
- Repetitions: 5.
- Orchestrator average: 1036.023 ms per 1000-candle run.
- Component measurements: EMA 537.506 ms; RSI 34.002 ms; ATR 32.012 ms; Market Structure 440.568 ms; Regime 1.677 ms; Orchestrator 1029.511 ms.
- These are measured implementation/runtime observations only, not production performance claims.
- The measured orchestrator result does not satisfy the roadmap aspirational target of <50ms per full multi-timeframe vector.

### H. Controlled real-data vertical slice
- VPS canonical-candle inventory contained no rows.
- No governed BTCUSDT 15M/1H/4H canonical dataset was available.
- Required real-data vertical slice remains UNEXECUTED / UNVERIFIED.
- No live/synthetic substitution was used to manufacture G-4 evidence.

## 3. Failures / diagnosis / remediation

1. Host migration wrapper failed because psql is absent; remediation used the same repository SQL through the DB container.
2. Quantitative tables were initially absent on the deployed DB; remediation applied migrations 0001–0005.
3. HTTP framing defect found by CONTROL audit; remediation corrected response framing and added live CRLF evidence.
4. Worker MTF propagation defect found by CONTROL audit; remediation carries higher_timeframes into the orchestrator and adds direct CI coverage.
5. MTF timeframe-key validation gap found by CONTROL audit; remediation rejects key/candle-timeframe mismatches and adds direct coverage.
6. Missing registry record for CTR-P4-QUANT-CANDLE-CLOSE-1.0; CONTROL registered the runtime handoff contract with lifecycle TESTED / UNVERIFIED.

## 4. Unexecuted / unresolved evidence

- Controlled BTCUSDT 15M + 1H + 4H real-data vertical slice: UNEXECUTED / UNVERIFIED.
- Full persistence write/read-back on real governed data: UNEXECUTED.
- Real-data replay equivalence: UNEXECUTED.
- Restart/recovery of a real-data processing sequence: NOT YET VERIFIED.
- Production/runtime performance target satisfaction: NOT ESTABLISHED.
- G-4 evidence: NOT ESTABLISHED.
- Phase-4 closure: NOT ESTABLISHED.

## 5. Evidence references

- CI Core Run #1016 / Run ID 35468822047 / Job 105965939193 / SUCCESS / 445 tests / 1.189s.
- CI Core Run #1014 / Run ID 35468789235 / FAILURE; preserved correction evidence.
- Docker Foundation Run #218 / Run ID 35467898682 / SUCCESS.
- Runtime deployment checkout: 48bae89931c3ab003223a867ab9f9bf75fe3117a.
- Audit: AR-P4-012.
- Re-audit: AR-P4-013.
- Producer Build Report: BR-P4-007.

## 6. Final execution result

CONTROL operational execution succeeded for the reachable runtime-foundation, API, worker-failure, security-boundary and measurement surfaces.

The Step is NOT CLOSED / VERIFIED because the governed real-data vertical slice and G-4 evidence are unavailable, and measured performance exposes a material efficiency gap.

No Phase-5 authorization or implementation was introduced.