# BR-P5-004-GROUP-A — Producer Build Report

**Task Order:** TO-P5-004  
**Step:** STEP-P5-004 — Group A: Technical, Multi-Timeframe, Volatility  
**Producer role:** ROL-V2-002  
**Implementation revision tested:** 21204c8bc77d3f8b0770cb95458eff3994f01c81  
**Pull Request:** [#59 — TO-P5-004 Group-A specialists](https://github.com/meyluxLab/Meylux-v2/pull/59)  
**Report disposition:** Implementation and CI evidence delivered for independent audit. This report does not declare the Task Order VERIFIED, COMPLETE or CLOSED. Several acceptance boundaries require CONTROL resolution/evidence, as detailed in §10.

## 1. Executive summary

The authorized Stage-1 specialist execution path has been implemented for:

- **S-01 Technical:** MA_ALIGNMENT, PRICE_VS_MA, MACD_STATE, RSI_ZONE, ADX_STRENGTH, BOLLINGER_POSITION, and configured Bollinger squeeze interpretation.
- **S-06 Multi-Timeframe:** independent timeframe findings and CONFLUENCE / CONFLICT / PARTIAL, with explicit insufficient and post-boundary states.
- **S-08 Volatility:** LOW / NORMAL / HIGH, EXPANDING / CONTRACTING / STABLE, and HIGH_VOLATILITY risk flag.

The specialists consume an existing InputSnapshot; they do not recompute P4 indicators. They use the existing SpecialistOutput, deterministic identity, queue contract, worker handler, append-only specialist_outputs persistence and read-back boundary. S-10's analyzer was not changed.

CI demonstrates deterministic semantics and the real Redis → worker handler → PostgreSQL output-persistence path using a controlled, explicitly synthetic test Snapshot. It does **not** establish that the deployed authoritative P4 rows can always be transformed into a venue-complete Input Snapshot or that every EvidenceRef resolves to a real upstream row. Those are not represented as passed acceptance criteria.

## 2. Complete changed-file inventory

1. src/meylux/specialists/group_a.py — S-01/S-06/S-08 deterministic interpretation, metric-state handling, event-time alignment, no-lookahead checks and output identity.
2. src/meylux/specialists/runtime.py — dispatch and worker-handler routing for the three authorized Stable IDs; S-10 remains the default analyzer path.
3. config/specialists.yaml — configuration version advanced to 1.2.0; Group-A symbols, timeframes, EMA periods and interpretation thresholds.
4. tests/test_p5_004_group_a.py — deterministic semantic and boundary tests using the canonical InputSnapshotBuilder.
5. tests/test_p5_004_redis_postgresql.py — real Redis/worker/PostgreSQL persistence/read-back, replay, concurrent duplicate, append-only and CI resource-baseline test.
6. .github/workflows/ci-docker.yml — Docker path filters and dedicated Group-A PostgreSQL acceptance step; passes the exact CI revision into the test.
7. tests/test_p5_001_foundation.py — updates the expected shared configuration version to 1.2.0.
8. docs/build-reports/BR-P5-004-GROUP-A.md — this report.

No database migration was added. No P4 indicator mathematics, migration 0008, frozen architecture document, canonical specialist contract, closure registry, CURRENT_CHECKPOINT.json, README closure state or Change Ledger was changed. No VPS operation was performed.

The existing path docs/build-reports/BR-P5-004.md was not overwritten because it is already an existing report for a different corrective task. This report therefore uses the explicit BR-P5-004-GROUP-A.md path; CONTROL may assign/register its canonical artifact identifier through the normal governance process.

## 3. S-01 — Technical semantics

### 3.1 Authoritative input and findings

The specialist reads only authoritative SnapshotFact values from meylux.calculated_indicator_vectors and closed-candle close values from the canonical candle Snapshot facts. It does not call P4 indicator functions or infer missing EMA values.

- MA_ALIGNMENT: compares available, configured EMA periods in period order. At least two valid EMA periods are required to assert alignment. Missing periods are reported individually; facts from different event times produce CONTRADICTORY_CONTEXT.
- PRICE_VS_MA: compares the closed-candle close with the configured primary EMA. Price and EMA must be valid and refer to the same event time.
- MACD_STATE: consumes persisted MACD, signal and histogram values. Components must be valid and event-time aligned.
- RSI_ZONE: OVERSOLD at or below the configured oversold boundary; OVERBOUGHT at or above the configured overbought boundary; otherwise NEUTRAL. Out-of-domain RSI is not silently accepted.
- ADX_STRENGTH: STRONG at or above the configured threshold; otherwise WEAK.
- BOLLINGER_POSITION: compares the closed-candle close with the persisted upper, middle and lower bands. Missing or contradictory band ordering is explicit.
- BOLLINGER_SQUEEZE: uses the configured bandwidth threshold; equality is classified as SQUEEZE.

Missing, unavailable, stale, invalid, contradictory and post-boundary metric states are not replaced with a fallback numeric value. Numeric parsing rejects booleans, binary floats and non-finite decimal values.

### 3.2 Current fact-surface limitation

The shared configuration lists EMA periods 9,20,21,50,200, with 20 as the primary EMA period. An unqualified persisted P4 EMA fact is associated only with that configured primary period; it is never relabelled as EMA-9/21/50/200.

Consequently, if the authoritative Snapshot contains only the current unqualified EMA fact, MA_ALIGNMENT remains INSUFFICIENT_DATA and identifies the missing configured periods, including EMA-200. This is deliberate; the specialist does not create a competing P4 calculation. Unit fixtures cover a fully populated period set and the missing-EMA-200 case.

## 4. S-06 — Multi-Timeframe semantics

For each configured symbol and timeframe, S-06 independently requires the timeframe's closed price, configured primary EMA, MACD, MACD signal and RSI. It does not import or consume S-01 output.

Directional interpretation:
- BULLISH: close above EMA, MACD above signal, and RSI at/above the configured RSI midline.
- BEARISH: close below EMA, MACD below signal, and RSI below the configured RSI midline.
- NEUTRAL: valid, event-time-aligned facts do not satisfy either directional conjunction.

Overall interpretation:
- CONFLUENCE: all required timeframes establish the same bullish or bearish direction.
- CONFLICT: required timeframes establish opposing bullish/bearish directions.
- PARTIAL: a required timeframe is missing/insufficient, neutral, contradictory, or contains post-boundary evidence.
- A missing required timeframe is explicitly emitted as INSUFFICIENT_DATA.

The primary closed-candle event boundary and knowledge boundary are carried separately. An HTF fact is rejected from directional interpretation if its event_time exceeds the primary event boundary or its knowledge_time exceeds the primary knowledge boundary. Fact components within a timeframe must also agree on event time. A fact that is known by the primary knowledge boundary but refers to a later event time is explicitly classified as POST_BOUNDARY_EVIDENCE; equality at the applicable boundary is eligible.

## 5. S-08 — Volatility semantics

S-08 consumes persisted ATR, ATR percentile, historical volatility, volatility expansion ratio and Bollinger bandwidth. It adds no estimator or indicator.

The versioned configuration currently proposes these defaults:

| Parameter | Configured value | Boundary behavior |
|---|---:|---|
| ATR percentile low / high | 25 / 75 | LOW uses <=25; HIGH uses >=75 |
| Historical volatility low / high | 0.15 / 0.50 | inclusive at each boundary |
| Bollinger bandwidth low / high | 0.05 / 0.10 | inclusive at each boundary |
| Expansion ratio threshold | 1.20 | EXPANDING at >=1.20 |
| Contraction ratio threshold | 0.80 | CONTRACTING at <=0.80 |
| Bollinger squeeze bandwidth | 0.05 | SQUEEZE at <=0.05 |

Classification:
- HIGH if ATR percentile, historical volatility or bandwidth reaches its configured high boundary.
- LOW only when percentile and historical volatility are at/below their low boundaries and bandwidth is at/below its low boundary.
- NORMAL otherwise, provided all required inputs are valid and event-time aligned.
- Expansion ratio between the configured contraction and expansion thresholds is explicitly STABLE.
- HIGH_VOLATILITY is emitted when classification is HIGH or the valid expansion state is EXPANDING.

Missing, insufficient, invalid, non-finite, contradictory or post-boundary inputs remain explicit. These values are versioned configuration defaults introduced by this implementation, not claimed as pre-existing ratified market-domain thresholds. CONTROL must independently review/ratify them before treating the defaults as final domain policy.

## 6. Configuration and versioning impact

config/specialists.yaml is now version 1.2.0. In addition to existing runtime limits, it contains configurable symbols (BTCUSDT,SOLUSDT), timeframes (15m,1h,4h), primary timeframe/EMA period, the EMA-period set, RSI oversold/overbought/midline, ADX threshold, MACD histogram neutral threshold, Bollinger squeeze/low/high bandwidth thresholds, volatility percentile/HV boundaries, and expansion/contraction ratio boundaries.

This is an extension of the existing configuration shape, not a new file format or persistence contract. However, the shared configuration identity is used by existing specialists too: advancing its version changes the config identity attached to future S-10 outputs even though S-10 analysis code is unchanged. Existing append-only output rows are not rewritten. CONTROL should explicitly accept this shared-configuration identity impact as part of its audit.

## 7. Temporal, evidence and independence controls

- The canonical InputSnapshotBuilder is used by tests to construct immutable snapshots from SnapshotRecord fixtures. The specialist validates required source family, record ID, identity hash, timeframe and venue fields on consumed EvidenceRefs.
- knowledge_time is checked against snapshot.as_of; S-06 separately checks both HTF event and knowledge boundaries against the primary timeframe boundaries.
- Price/indicator comparisons and multi-fact classifications reject event-time mismatches as CONTRADICTORY_CONTEXT.
- The output carries the shared snapshot identity, versioned configuration reference, deterministic identity and de-duplicated EvidenceRefs.
- Static independence test confirms group_a.py imports neither S-10 nor the runtime module. S-06/S-08 do not consume another specialist's output.
- No NaN/Inf value is emitted, and no missing P4 fact is mathematically reconstructed.

**Evidence limitation:** the real Redis/PostgreSQL integration uses a controlled synthetic Snapshot with complete test-only provenance fields. It proves the specialist worker/persistence boundary, but does not query or resolve the fixture's EvidenceRefs back to the authoritative P4 source tables. The canonical InputSnapshotBuilder validates record metadata; it is not itself a database resolver.

## 8. Persistence, replay, append-only and failure evidence

The Docker integration exercises QueueEnvelope → SpecialistDispatcher → Redis Streams → AsyncWorker → SpecialistWorkerHandler → SpecialistPersistence → PostgreSQL → read-back for S-01, S-06 and S-08.

It verifies:
- one persisted row per specialist/snapshot identity;
- read-back payload Stable ID and output identity;
- EvidenceRef serialization and temporal fields;
- deterministic replay and concurrent duplicate handler calls converge on one output row;
- UPDATE and DELETE against meylux.specialist_outputs are denied for the application role, with the persisted row remaining present;
- an unauthorized specialist Stable ID is rejected by the handler;
- the existing worker/queue foundation continues to execute its retry/DLQ tests.

The integration input is explicitly labeled a controlled synthetic test Snapshot. No live market data, provider acquisition, trading or capital action is represented by this test.

**Restart/pending-work limitation:** the shared AsyncWorker.run() path does not invoke the available RedisQueue.recover_stale() method. The policy advertises stale-claim recovery, but this Task Order did not change the shared queue loop because doing so would alter a generic runtime used by excluded specialist S-10 as well. Producer therefore does not claim that Group-A worker restart/pending-work recovery has been established. CONTROL must either provide evidence of an existing external recovery path or authorize a bounded shared-queue recovery change under the applicable boundary.

## 9. Exact CI and performance evidence

### 9.1 CI results

All results below are real CI observations; no test result is inferred from source inspection.

- **CI Core, run 37051899822** — [workflow](https://github.com/meyluxLab/Meylux-v2/actions/runs/37051899822), SUCCESS on implementation/unit-test head 01e67af6dff02eaa41fe0248b5ffe9e0b3fd977b. Foundation suite: 614 tests in 30.221s; dedicated P3-009 PostgreSQL suite: 7 tests in 5.749s, OK.
- **CI Docker Foundation, run 37052524169** — [workflow](https://github.com/meyluxLab/Meylux-v2/actions/runs/37052524169), SUCCESS on exact final code/test head 21204c8bc77d3f8b0770cb95458eff3994f01c81. Foundation self-check: 612 tests in 1.402s; TO-P4-011 PostgreSQL check: 2 tests in 0.201s; P3-009 PostgreSQL evidence: 7 tests in 5.832s; Group-A Redis/worker/PostgreSQL integration: 1 test, OK. The full Docker Foundation workflow completed successfully.
- **CI Core, run 37052524164** — [workflow](https://github.com/meyluxLab/Meylux-v2/actions/runs/37052524164), FAILURE in two unrelated foundation PostgreSQL harness tests: test_governed_grant_hardening_on_real_postgresql (P4-009) and test_real_postgresql_persistence_and_privileges (P5-001). Both failed because psql could not connect to the ephemeral container socket (No such file or directory) while applying the first migration. The Group-A tests themselves did not fail in that run. Core had passed on the immediately preceding head with the same specialist and unit-test implementation; this latest failure is retained, not rewritten as a pass.
- Earlier correction cycles also included failed Group-A unit assertions, which were corrected before the successful runs above. The failed histories are preserved in GitHub Actions.

### 9.2 Reproducible CI resource baseline

Observed from Docker Foundation run 37052518932 (push run on the same exact implementation revision 21204c8bc77d3f8b0770cb95458eff3994f01c81): [workflow](https://github.com/meyluxLab/Meylux-v2/actions/runs/37052518932).

- **Environment:** Docker Foundation CI, real Redis 7.4.6 and TimescaleDB/PostgreSQL; controlled synthetic Snapshot fixture.
- **Workload:** one snapshot; sequential first queue/worker execution for S-01/S-06/S-08; two concurrent duplicate replays; 30 warm persistence/read-back replays.
- **Cold first path, enqueue through worker execution:** S-01 28.810 ms; S-06 11.919 ms; S-08 12.782 ms.
- **Warm replay:** p50 9.817 ms; p95 16.241 ms (30 samples).
- **Process resource delta:** user CPU 0.437678 s; system CPU 0.012523 s; peak RSS 45,588 platform units.
- **Disk observation:** total 154,894,188,544 bytes; used 64,600,678,400 bytes; free 90,276,732,928 bytes.
- **Queue observation at test end:** active backlog 0; pending entries 0; retained stream entries 3.
- **Measurement method:** time.perf_counter_ns, median and deterministic index-based p95 from sorted replay samples, resource.getrusage, shutil.disk_usage, Redis backlog/pending/stream observations. Exact revision is printed by the test via GITHUB_SHA.

This is a reproducible CI baseline, not a production target or deployed-VPS measurement. CONTROL remains responsible for the authorized runtime deployment/restart, actual source-row resolution, runtime health/resource observations, and independent acceptance.

## 10. Blocking evidence gaps and formal escalation to CONTROL

The following are specific, bounded gaps; they are not silently treated as passed acceptance.

### A. Authoritative P4 venue context vs. frozen P5 EvidenceRef requirements

The P4 calculation context builder in src/meylux/quantitative/indicators.py creates QuantitativeContext with source reference, timestamp, timeframe, symbol and version, but does not populate venue_context. src/meylux/orchestration/engine.py likewise fills missing context without adding a venue. src/meylux/persistence/quantitative.py writes venue_context from that context and allows it to be null.

By contrast, InputSnapshotBuilder.REQUIRED_METADATA_FIELDS and the Stage-1 EvidenceRef contract require venue context. Producer will not infer a venue from a symbol, source-reference string or assumed exchange. Therefore this repository evidence does not establish that every authoritative P4 Group-A row can be transformed into a contract-valid, source-resolvable P5 Snapshot. If CONTROL's independently verified runtime path supplies venue from a separate authoritative source, please identify that exact resolver/evidence and confirm the mapping. Otherwise, the affected P4 provenance portion requires a separately authorized corrective Task Order; P4 changes are outside TO-P5-004.

### B. Authoritative source resolution

The integration proves actual Redis delivery, specialist execution, PostgreSQL output persistence/read-back, duplicate idempotency and output-table append-only denial. Its input is a controlled test Snapshot, not a Snapshot built from and independently resolved against the actual persisted P4 Group-A source rows. The required authoritative EvidenceRef resolution acceptance therefore remains open for CONTROL's runtime/source-row verification.

### C. EMA fact population

The current P4 orchestration configuration has a single ema_period (default 20), while the Group-A interpretation configuration includes multiple EMA periods. The specialist correctly maps an unqualified EMA fact only to the configured primary period and does not synthesize other EMAs. With only that source fact, MA_ALIGNMENT is explicitly insufficient for the remaining configured periods. CONTROL must verify whether the active authoritative input population includes period-specific EMA facts; if not, the additional fact population requires a separately authorized P4 change, which this Task Order excludes.

### D. Threshold ratification and shared config identity

The exact threshold defaults and the 1.2.0 shared config identity are listed in §§5–6. Please independently review the semantic values and the fact that future S-10 outputs use the new shared config identity despite no S-10 analyzer change. No prior threshold authority is claimed.

### E. Pending-work recovery and deployed runtime

The generic worker's startup loop does not call the available stale-claim recovery method. Because the queue is shared with excluded S-10, Producer has not changed that generic runtime as an incidental side effect. CONTROL should either evidence the existing external recovery mechanism or authorize a bounded correction. No VPS/SentinelX operation was performed by Producer.

## 11. Requirement-to-evidence matrix

| Requirement | Evidence | Producer disposition |
|---|---|---|
| S-01 deterministic semantics | tests/test_p5_004_group_a.py; CI Core and Docker foundation suites | Implemented and unit-tested |
| S-06 confluence/conflict/partial | Unit tests for confluence, conflict, missing timeframe | Implemented and unit-tested |
| Event-time and knowledge-time no-lookahead | Unit tests for HTF event and knowledge boundaries; post-boundary state | Implemented and unit-tested |
| S-08 LOW/NORMAL/HIGH, expansion/contraction, risk | Unit tests for threshold equality, low/high and expansion/contraction | Implemented and unit-tested |
| Configured thresholds and EMA periods | config/specialists.yaml v1.2.0; equality tests | Implemented; defaults require CONTROL ratification |
| Missing EMA-200 / insufficient history | Explicit missing-period states and tests | Implemented; real authoritative population must be checked by CONTROL |
| Invalid/non-finite/contradictory facts | Unit tests for non-finite input and mismatched event times | Implemented and unit-tested |
| EvidenceRef shape/provenance | SnapshotRecord + InputSnapshotBuilder tests; persisted output refs read-back | Shape covered; actual P4 source-row resolution remains open |
| Deterministic output identity/replay | repeated serialization/hash tests and worker persistence replay | Tested |
| Append-only persistence/read-back | real PostgreSQL integration, UPDATE/DELETE denial and read-back | Tested in CI fixture path |
| Concurrent duplicate persistence | concurrent handler calls and one-row read-back assertion | Tested in CI fixture path |
| Failure isolation | unsupported Stable ID rejected; existing queue foundation retry/DLQ tests | Partial; deployed worker failure/restart boundary remains CONTROL evidence |
| Restart/pending-work | generic recover_stale exists but worker startup does not invoke it | Open; escalated in §10E |
| Real Redis → worker → PostgreSQL path | Docker Foundation Group-A integration test | Tested with controlled Snapshot fixture; not proof of live P4 source resolution |
| CI/regression | Core success run 37051899822; Docker full success 37052524169; latest Core failure 37052524164 retained | Core latest-run flake remains visible |
| Performance/resource baseline | run 37052518932, metrics in §9.2 | CI baseline measured; deployed runtime baseline remains CONTROL-owned |
| P4 ownership/G-4/frozen architecture | no P4 math/migration or architecture/closure files changed | Scope preserved; source provenance dependency escalated |

## 12. Scope statement and hand-off

Producer changed only the files listed in §2. No P4 mathematical definition or implementation, P4 migration, P5 later Step, other specialist analyzer, PRQ-2/3/4, provider acquisition, trading/execution/capital/custody, public API/UI, governance registry, checkpoint, README closure state or Change Ledger was changed. No VPS operation was performed.

**Formal hand-off to CONTROL / REVIEWER (ROL-V2-001):**

The implementation and CI evidence for the authorized S-01/S-06/S-08 specialist boundary are delivered in PR #59. Please independently verify the semantics, config defaults and shared config identity impact; establish actual authoritative P4-to-InputSnapshot EvidenceRef resolution and venue mapping; confirm whether the configured EMA-period population exists in the active fact surface; and decide the required disposition for the shared worker's pending-work recovery gap. Please do not treat the synthetic Snapshot integration as live-market or source-row acceptance evidence. The Producer does not declare VERIFIED, COMPLETE or CLOSED; no closure synchronization has been performed.

**Current stopping boundary:** unresolved authoritative provenance/configuration/runtime dependencies have been isolated and escalated. Further work on those portions requires CONTROL's evidence or authorization; the remaining implemented code and tests are available for independent review.
