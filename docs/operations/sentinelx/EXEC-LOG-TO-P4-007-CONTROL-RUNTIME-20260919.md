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

 
## 7. Post-probe addendum

### I. Worker restart/recovery probe
- CONTROL restarted worker-quant through SentinelX.
- After restart the quantitative worker returned to running state; db and redis remained healthy and API remained running.
- Result: service restart/liveness PASS.
- This does not constitute real-data replay/recovery evidence.

### J. Data-source diagnosis
- The repository's collector service was inspected through its current container logs.
- It reports only foundation-service startup/shutdown messages and does not provide a live acquisition stream in this deployed runtime.
- The canonical_candles table is empty.
- CONTROL therefore did not bypass the governed acquisition/normalization boundary by injecting public-provider data directly into the quantitative runtime.
- The real-data vertical slice remains UNEXECUTED / UNVERIFIED.

## 8. Owner-authorized governed historical acquisition and normalization boundary probe

### K. Public Binance Spot historical acquisition
- CONTROL used the existing repository BinanceAdapter.fetch_klines() through the API container.
- No authentication, account credential, private endpoint, trading/order/capital/custody endpoint, V1 path or direct quantitative-table insertion was used.
- Acquired 500 requested closed-candle candidates per interval; the currently open last candle was excluded.
- Persisted through the existing P2 RawStagingRepository into meylux.raw_acquisition_events.
- Result:
  - 15M: 499 closed envelopes inserted; open-time window 2026-09-14T17:30:00Z through 2026-09-19T22:00:00Z.
  - 1H: 499 closed envelopes inserted; open-time window 2026-08-30T03:00:00Z through 2026-09-19T21:00:00Z.
  - 4H: 499 closed envelopes inserted; open-time window 2026-06-28T16:00:00Z through 2026-09-19T16:00:00Z.
- Total raw acquisition records after the operation: 1498.

### L. P2 -> P3 normalization boundary result
- CONTROL executed the existing validate_acquisition_envelope, validate_temporal_evidence, and normalize functions against an actual acquired Binance Spot candle.
- Structural validation: PASS.
- Temporal validation: PASS.
- Normalization: REJECTED because the provider candle payload does not carry explicit timeframe context required by the existing P3 normalization contract.
- This is a genuine implementation-boundary finding.
- CONTROL did NOT inject timeframe into the envelope, bypass normalization, or write directly to canonical/quantitative tables.
- TO-P4-008 authorizes Producer to make the minimal provider-boundary context-preservation correction.

## 9. Performance profiling under Owner Decision B

### M. Roadmap target basis
- Authoritative roadmap records: <5ms / indicator / 1000 bars; <50ms / full multi-timeframe vector; TARGET != GUARANTEE.
- The roadmap does not define the full-vector target as a 1000-bar end-to-end calculation. CONTROL therefore tested both the required one-day replay-sized workload and the prior 1000-primary-bar diagnostic workload.

### N. Orchestrator workload measurements
- 21 primary 15M + 25 1H + 7 4H: average 3.766 ms.
- 116 primary 15M + 31 1H + 9 4H: average 26.078 ms.
- 1000 primary 15M + 252 1H + 64 4H: average 704.670 ms.
- The 116-primary workload represents 20 EMA warm-up bars plus the roadmap-required one-day 96-bar 15M replay; 25 1H and 7 4H cover the same evaluation span plus one preceding closed HTF boundary.
- Therefore the current orchestration implementation is below the <50ms full-vector target on the one-day replay-sized workload, while the 1000-primary-bar diagnostic workload is not.

### O. Profiler evidence
- cProfile on the 1000-primary workload identified the dominant cumulative costs as EMA/Decimal processing and Market Structure, not the orchestration wrapper itself.
- EMA cumulative: approximately 0.633s.
- Market Structure cumulative: approximately 0.180s.
- The orchestration wrapper direct function frame contributed approximately 0.004s before callees.
- Decimal as_tuple/precision/context operations were prominent in the EMA path.

### P. Decimal policy diagnostic
- Authoritative Decimal EMA over 1000 values: average 464.081 ms.
- Separate diagnostic float-only recurrence: average 0.757 ms.
- Diagnostic ratio: approximately 613x.
- This float comparison is NOT an alternative quantitative truth, not a candidate implementation, and not output-equivalence evidence. It is diagnostic evidence that the authoritative Decimal policy is a material performance factor.
- No Decimal policy or verified engine implementation was changed.

## 10. Current evidence disposition

- Governed raw historical acquisition: EXECUTED / OBSERVED.
- P2 raw persistence: PASS.
- P3 structural/temporal validation: PASS.
- P3 normalization for historical candles: BLOCKED by missing timeframe context; TO-P4-008 correction required.
- Canonical persistence of this historical candle set: NOT YET EXECUTED.
- 1-day real-data P4 replay: NOT YET EXECUTED.
- Performance full-vector target on 116-primary one-day workload: MEASURED PASS (26.078 ms).
- Indicator <5ms / 1000 bars target: NOT SATISFIED for current EMA implementation; engine reopening is outside current authorization.
- G-4: NOT ESTABLISHED.

## 11. TO-P4-008 correction verification and live normalization continuation

### Q. Repository synchronization
- CONTROL fetched the authorized final main revision through SentinelX and synchronized /srv/meylux-v2 to fb7d9847498323bec067ba98a1e2729f869c0697.
- No producer-side runtime mutation was performed before this CONTROL verification.

### R. Independent implementation/test verification
- Binance acquisition suite: 19 tests — PASS.
- P3-005 normalization suite: 16 tests — PASS.
- Full repository unittest discovery: 448 tests in 2.609s — PASS.
- A ResourceWarning for an existing MEXC test file was observed during the full suite; it did not produce a test failure and did not concern the TO-P4-008 correction.

### S. Real Binance Spot provider -> P3 normalization probe
- CONTROL executed the existing public Binance Spot BinanceAdapter.fetch_klines() directly from the synchronized repository.
- No authentication/private endpoint/trading/order/capital/custody/V1 path was used.
- Real BTCUSDT candles were requested at the minimum G-4 workload basis:
  - 15m: 116 envelopes
  - 1h: 31 envelopes
  - 4h: 9 envelopes
- All returned envelopes normalized successfully through the unchanged P3 normalize() implementation.
- Resulting canonical timeframe values were exactly 15m, 1h, and 4h.
- Close-boundary behavior was observed:
  - 15m: 115/116 closed
  - 1h: 30/31 closed
  - 4h: 8/9 closed
- The currently open candle at the receipt boundary was not promoted to closed state.

### T. Persistence/runtime boundary after correction
- Full P2 RawStagingRepository -> CanonicalPersistence -> P4 runtime continuation was not executed after correction.
- Current host execution context does not expose MEYLUX_DB_NAME, MEYLUX_DB_PASSWORD, or MEYLUX_APP_PASSWORD.
- Host-level PostgreSQL and Redis services report inactive.
- Docker socket access remains denied to the current SentinelX command context.
- CONTROL therefore did not inject data directly into canonical/quantitative tables or fabricate G-4 evidence.

### U. Verification disposition
- TO-P4-008 provider-boundary correction: VERIFIED under AR-P4-014.
- Previous timeframe-normalization finding: CLOSED / VERIFIED.
- Governed full real-data persistence/runtime/replay/recovery: OPEN / UNEXECUTED.
- G-4: NOT ESTABLISHED.
- STEP-P4-006: ACTIVE / AUTHORIZED.
- Phase 5: NOT AUTHORIZED.
