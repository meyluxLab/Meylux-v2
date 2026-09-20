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


## 12. Final TO-P4-008 governed real-data execution and G-4 evidence

### V. Corrected provider acquisition and P2 persistence
- CONTROL synchronized and rebuilt the API/quant-worker images from the verified repository revision fb7d9847498323bec067ba98a1e2729f869c0697.
- Using the corrected BinanceAdapter through the API runtime, CONTROL fetched 500 candidates for each required interval and excluded the current open candle.
- New post-correction P2 RawStagingRepository inserts:
  - 15m: 499
  - 1h: 499
  - 4h: 499
  - total: 1497
- The prior 1498 pre-correction raw records were preserved unchanged as historical evidence.

### W. P2 -> P3 -> CanonicalPersistence
- CONTROL processed the corrected real-data records through the existing structural validation, temporal validation, Binance normalization, market-semantic validation and quality boundary.
- G-4 minimum workload:
  - 116 closed 15m primary candles
  - 31 closed 1h candles
  - 9 closed 4h candles
- All 156 records were canonical-eligible and persisted through the existing CanonicalPersistence.
- Final canonical G-4 inventory: 156 records, exactly 116/31/9 by timeframe.
- Canonical event handoff published the inserted canonical events.
- No direct canonical/quantitative table injection and no synthetic/fabricated data were used.

### X. Quantitative orchestration / MTF / replay
- CONTROL executed QuantitativeOrchestrator with 116 primary 15m candles and 31/9 HTF candles.
- Final primary knowledge time: 2026-09-19T23:29:59.999Z.
- 1h selected HTF close: 2026-09-19T22:59:59.999Z.
- 4h selected HTF close: 2026-09-19T19:59:59.999Z.
- Both satisfy HTF.close_time <= primary.close_time.
- Observed regime: RANGE.
- Observed structure event count: 193.
- Observed structure state: UNCONFIRMED.
- Repeated orchestration on identical governed inputs produced replay_equal=true.
- First quantitative persistence inserted 5 records; second identical persistence inserted 0.

### Y. Worker / queue / restart recovery
- CONTROL published real-data MTF payload under CTR-P4-QUANT-CANDLE-CLOSE-1.0.
- Message CONTROL-P4-008-REAL-MTF-001: DELIVERED -> STARTED -> ACKED -> COMPLETED.
- Worker was restarted through SentinelX.
- Message CONTROL-P4-008-REAL-MTF-002 after restart: DELIVERED -> STARTED -> ACKED -> COMPLETED.
- For direct recovery evidence, CONTROL stopped worker-quant, published CONTROL-P4-008-REAL-MTF-003 while the worker was stopped, then started the worker.
- The pending real-data message was delivered, processed and ACKed after restart.
- Quantitative record counts remained idempotently stable: indicator vectors 3, structure events 1, regime states 1.

### Z. Read-only API / security
- Real persisted quantitative API GET returned HTTP 200 with real data.
- POST to the same endpoint returned HTTP 405 with read_only.
- Existing application append-only / denied UPDATE-DELETE security boundary remained intact.
- No account, private market-data, trading, capital, custody or leverage operation occurred.

### AA. Final real-data performance
- Workload: 116 primary 15m + 31 1h + 9 4h.
- Five direct orchestration executions in the synchronized API runtime:
  - average: 22.690451 ms
  - minimum: 16.798383 ms
  - maximum: 31.998459 ms
- Result: below roadmap <50ms full-vector target for the required replay-sized workload.
- Existing separate <5ms/indicator/1000-bars EMA diagnostic remains unsatisfied; no engine or Decimal-policy reopening was performed.

### AB. Final evidence disposition
- P2 raw persistence: VERIFIED.
- P3 structural/temporal validation: VERIFIED.
- P3 normalization: VERIFIED after TO-P4-008.
- Canonical persistence: VERIFIED.
- MTF execution and zero-lookahead boundary: VERIFIED.
- Quantitative persistence/idempotency: VERIFIED.
- Deterministic replay: VERIFIED.
- Worker/event-driven execution: VERIFIED.
- Real-data restart/recovery: VERIFIED.
- Read-only API/security: VERIFIED.
- Real-data replay-sized performance target: PASS.
- G-4: ESTABLISHED / VERIFIED.
- STEP-P4-006: ready for closure synchronization under AR-P4-015.
- Phase 5: NOT AUTHORIZED.


## 13. Final VPS State — Owner Post-Closure Read-Back

### 13.1 Repository / deployment relation
- SentinelX host: server-l6rf / host_3774c70bc3624713
- VPS checkout HEAD/deployed revision: fb7d9847498323bec067ba98a1e2729f869c0697
- Remote main at this read-back: 217a8a10d467a75023fbb7ddbe7ac1c4a915469e
- Divergence: deployed checkout is 52 commits behind remote main; git diff is documentation-only. No runtime source/configuration file differs in the inspected compare.
- VPS worktree: clean; no tracked or untracked runtime artifacts observed.
- Decision: do not synchronize/rebuild solely for documentation-only governance changes. Runtime source hashes inside API and worker-quant images matched the deployed git revision for BinanceAdapter, QuantitativeOrchestrator, QuantWorker, HTTP adapter and quantitative persistence.

### 13.2 Compose / service state
- Services running: api, worker-quant, collector, worker-ai, db, redis.
- DB and Redis report healthy.
- Inspected service restart counts: zero; OOMKilled=false; no crash-loop evidence.
- Last 6-hour error-pattern scan for api, worker-quant, collector and worker-ai: zero matches for error/traceback/fatal/panic/exception/critical.
- Collector remains a foundation service only. The 156 canonical candles are therefore a governed point-in-time slice, not evidence of continuous collector completeness.
- Four historical compose-api-run one-off containers remain running from prior probes. They were not removed because this post-closure read-back was explicitly non-mutating and no cleanup mutation was separately authorized.

### 13.3 Database
- Migrations present/applied: 0001_database_foundation, 0002_raw_acquisition_staging, 0003_canonical_persistence_event_outbox, 0004_canonical_quality_state_alignment, 0005_quantitative_foundation.
- Raw acquisition inventory: 2995 total = 1498 historical pre-correction records + 1497 corrected post-TO-P4-008 records.
- Historical pre-correction records are distinguishable by the original payload shape (k/row markers absent) and are retained unchanged as inert historical evidence; corrected records contain the provider-boundary k/row interval context.
- Canonical inventory: 156 = 116 15m + 31 1h + 9 4h; all quality state VALID.
- Quantitative inventory: 3 indicator vectors + 1 market-structure event + 1 regime state.
- No synthetic rows were observed in the governed inventory.
- Quantitative/canonical truth tables: meylux_app has SELECT/INSERT and no UPDATE/DELETE/TRUNCATE.
- Two application-role grant exceptions were observed and not mutated: raw_acquisition_events has UPDATE inherited from the existing meylux_admin default privilege; canonical_event_outbox has explicit UPDATE required by migration 0003. This is a security-boundary drift relative to the Owner-requested blanket SELECT/INSERT-only statement and requires separate authority before mutation.
- No direct database mutation was performed during this read-back.

### 13.4 Redis / queue / DLQ
- quantitative-candle-close consumer group pending: 0.
- queue lag: 0.
- Idempotency markers for CONTROL-P4-008-REAL-MTF-001, -002, -003 and CONTROL-P4-FAILURE-PROBE-20260919 remain retained.
- Quantitative DLQ retains the historical failure/retry evidence from the controlled failure probe; it was not purged or rewritten.
- Retry keys for the controlled failure probe remain retained.
- No queue/DLQ cleanup mutation was performed.

### 13.5 Host security / hygiene
- Public host listener inspection exposed SSH port 22 only; DB/Redis/application ports were not host-published.
- /srv/meylux-v2/.env permissions: 0600 root:root.
- Secret-pattern scan found no secret assignments in the inspected EXEC-LOG or available history locations.
- Host clock: UTC; system clock synchronized; NTP active.
- Disk: 76G total, approximately 5.0G used (7%); approximately 67G available.
- Memory: approximately 14GiB available.
- Docker log driver: json-file for inspected services.
- Docker system state: 6 images active, no reclaimable images; 2 active volumes; 150.9MB reclaimable build cache.
- No stray benchmark/probe source scripts outside normal repository source/test/migration/documentation locations were identified. Historical one-off runtime containers are recorded above and intentionally retained pending explicit cleanup authority.
- SentinelX state at final inspection: host operational; UTC 2026-09-20T06:08:12Z; load average 0.11/0.14/0.09.

### 13.6 Evidence corrections required by Owner read-back
- The 22.690451 ms result covers only the required replay-sized 116 primary 15m + 31 1h + 9 4h workload. It does not represent the 1000-primary diagnostic.
- The separate 1000-primary diagnostic measured 704.670 ms.
- Component measurements on that diagnostic were EMA 537.506 ms, RSI 34.002 ms, ATR 32.012 ms and Market Structure 440.568 ms; these remain diagnostic evidence only and no engine was reopened.
- The orchestrator currently computes EMA/RSI/ATR and Market Structure on the primary series. Higher-timeframe inputs are used for temporal alignment, not separate HTF indicator-vector calculation.
- Therefore no 1H or 4H HTF indicator vector was claimed as computed. For the configured periods, 31 1H candles are sufficient for EMA-20/RSI-14/ATR-14 input length, while 9 4H candles are insufficient for those configured lookbacks. The implementation intentionally does not compute separate HTF indicator vectors in this orchestration boundary.
- The final 156-candle canonical dataset is a controlled point-in-time real-data slice supplied to the runtime; it is not a claim of continuous collector completeness.

### 13.7 Final VPS disposition
- Runtime health: VERIFIED.
- Runtime source/image correspondence: VERIFIED against deployed revision.
- DB migration state: VERIFIED.
- Canonical and quantitative counts: VERIFIED.
- Redis pending/lag: VERIFIED zero.
- Secret/hygiene scan: VERIFIED within the read-only inspection boundary.
- Deployment synchronization to current main: NOT REQUIRED for runtime correctness because the divergence is documentation-only.
- Security grant blanket SELECT/INSERT-only condition: NOT FULLY SATISFIED; pre-existing raw-staging UPDATE/default-privilege and canonical-event-outbox UPDATE exceptions were observed and deliberately left unchanged pending separate authorization.
- Cleanup of four historical one-off containers: NOT PERFORMED under the non-mutating read-back boundary.
- No VPS mutation occurred during this final read-back.

## 14. Final read-back conclusion
The repository lifecycle/traceability corrections requested by the Project Owner are being synchronized independently of runtime code. The deployed runtime itself remains evidence-consistent with the verified implementation baseline. Two VPS hygiene/security items remain explicitly recorded rather than silently changed: application-role UPDATE exceptions and historical one-off probe containers.

Phase 5 remains NOT AUTHORIZED. No engine, Decimal policy, frozen architecture or Producer implementation was changed.


## 14. Post-Closure Legacy Probe Container Cleanup — Owner-Authorized

**Authority:** Project Owner Decision 1 — legacy probe containers cleanup.

Before removal, the four historical one-off containers were independently inspected through SentinelX. Exact evidence:

1. Container ID: `41acd970c5c7ef714a96e057557b6aef011945797c9b288de1f7e073080c4ae1`
   - Name: `compose-api-run-9d92a105c094`
   - Image ID: `sha256:366dfc4f6f49ba658b23e37ce6d407d162b49f3ef1da7bd6039d47511c159fef`
   - Created: `2026-09-18T17:53:57.541072027Z`
   - Command: `python -m meylux.runtime.p3_008_vertical_slice`
   - Status before removal: `running`
   - `com.docker.compose.oneoff=True`
   - `com.docker.compose.service=api`
   - Last logs: `meylux-v2 foundation service started: api`

2. Container ID: `53bf3301f16f2e5fcd04ba06e63fd9f15c9846b1f42a4dc19831c48e38154878`
   - Name: `compose-api-run-dc97688262e8`
   - Image ID: `sha256:366dfc4f6f49ba658b23e37ce6d407d162b49f3ef1da7bd6039d47511c159fef`
   - Created: `2026-09-18T17:52:57.121746795Z`
   - Command: `python -m meylux.runtime.p3_008_vertical_slice`
   - Status before removal: `running`
   - `com.docker.compose.oneoff=True`
   - `com.docker.compose.service=api`
   - Last logs: `meylux-v2 foundation service started: api`

3. Container ID: `ae3b8a119b51612ba9682989a0fc67cbd94376ad34a1aabd9ad6dac7e2f57a48`
   - Name: `compose-api-run-f0ecf208a940`
   - Image ID: `sha256:366dfc4f6f49ba658b23e37ce6d407d162b49f3ef1da7bd6039d47511c159fef`
   - Created: `2026-09-18T17:52:22.557584373Z`
   - Command: `python -m meylux.runtime.p3_008_vertical_slice`
   - Status before removal: `running`
   - `com.docker.compose.oneoff=True`
   - `com.docker.compose.service=api`
   - Last logs: `meylux-v2 foundation service started: api`

4. Container ID: `fe55bef4dccaf56080a7899906ed40790ec46843af6b3d3312c0e25b378cd14e`
   - Name: `compose-api-run-e88ffee4974a`
   - Image ID: `sha256:366dfc4f6f49ba658b23e37ce6d407d162b49f3ef1da7bd6039d47511c159fef`
   - Created: `2026-09-18T17:51:21.844530055Z`
   - Command: `python -m meylux.runtime.p3_008_vertical_slice`
   - Status before removal: `running`
   - `com.docker.compose.oneoff=True`
   - `com.docker.compose.service=api`
   - Last logs: `meylux-v2 foundation service started: api`

All four matched the historical one-off `compose-api-run-*` pattern and were distinguished from the six live services `api`, `worker-quant`, `collector`, `worker-ai`, `db`, and `redis`. No target container belonged to `worker-quant`, `collector`, `worker-ai`, `db`, or `redis`.

The first removal attempt without force was rejected because the four historical containers were still running. Under the Owner-authorized exact-container removal boundary, the four specified container IDs were then removed with `sudo docker rm -f`. No prune operation was used. No volume, image, network, or service change was requested or performed.

Removed container IDs:
- `41acd970c5c7`
- `53bf3301f16f`
- `ae3b8a119b51`
- `fe55bef4dccaf`

### 14.1 Post-cleanup verification

Current Docker service inventory contains exactly the six expected services:
- `compose-api-1` — Up
- `compose-worker-quant-1` — Up
- `compose-collector-1` — Up
- `compose-worker-ai-1` — Up
- `compose-db-1` — Up / healthy
- `compose-redis-1` — Up / healthy

No `compose-api-run-*` container remains.

Database connection read-back:
- `pg_stat_activity` count for database `meylux`: `4`.

Canonical/quantitative truth inventory read-back:
- canonical candles: `156`
- calculated indicator vectors: `3`
- market structure events: `1`
- market regime states: `1`
- combined quantitative count: `3/1/1`

Error-pattern scan over the last six hours for `api`, `worker-quant`, `collector`, and `worker-ai` returned zero matches for `error|traceback|fatal|panic|exception|critical`.

The first combined verification probe used an incorrect table name (`indicator_vectors`); it failed without mutation. The authoritative table discovery identified `calculated_indicator_vectors`, after which the truth-count query succeeded with `156|3|1|1`.

**Disposition:** Legacy probe-container hygiene item resolved by exact authorized removal. PH-P4 / STEP-P4-006 / G-4 closure status was not changed.
