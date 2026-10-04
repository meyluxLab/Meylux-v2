# EXEC-LOG-TO-P5-004-CONTROL-RUNTIME-20261004

**Execution ID:** `EXEC-LOG-TO-P5-004-CONTROL-RUNTIME-20261004`  
**Task:** `TO-P5-004`  
**Step:** `STEP-P5-004`  
**Target:** Meylux V2 governed VPS / isolated CONTROL verification runtime  
**Executor:** `ROL-V2-001` — CONTROL / REVIEWER  
**Authorization:** `TO-P5-004` runtime verification boundary  
**Repository/version context:** `45915b9f4ceb4c84349835d4e47d00897ba74eca`; final PR head `be6c9f434272e030e0cb7167ea230485b3929781`

## Actions

1. Verified governed VPS health through SentinelX.
2. Preserved the existing dirty `/srv/meylux-v2` checkout and used isolated detached worktrees/images.
3. Built the authorized TO-P5-004 revision in an isolated Docker image.
4. Executed the independent full repository suite: 633 tests, 7 skipped, OK.
5. Constructed an authoritative P5 Snapshot from persisted P4 PostgreSQL records.
6. Executed S-01, S-06 and S-08 through the Redis → specialist worker → PostgreSQL path.
7. Read back persisted specialist outputs and verified deterministic identities and EvidenceRefs.
8. Replayed identical specialist envelopes and verified no duplicate authoritative outputs.
9. Exercised governed append-only UPDATE and DELETE boundaries.
10. Measured 30 warm S-01 worker-handler samples on the authoritative Snapshot.
11. Removed temporary worktree, image, probe files and CONTROL-created Redis queue state.
12. Restored the pre-existing specialist worker container files after isolated probe injection; the governed worker service was not left running with the audit probe code.

## Observed results

- Authoritative Snapshot ID: `05e5e49b2ef6a33337e4b98df59e05f1b904294d298bd4348e6d73f341d854d5`
- Snapshot `as_of`: `2026-10-01T18:35:00Z`
- Authoritative facts: 60
- S-01 worker: ACKED/read-back; replay output count = 1
- S-06 worker: ACKED/read-back; replay output count = 1
- S-08 worker: ACKED/read-back; replay output count = 1
- Real 4h EMA-20: INSUFFICIENT_DATA
- Real 4h EMA-200: INSUFFICIENT_DATA
- Real 15m S-08: HIGH / EXPANDING / HIGH_VOLATILITY
- UPDATE denial: SQLSTATE 42501
- DELETE denial: SQLSTATE 42501
- Full persisted row unchanged after mutation attempts
- Performance p50: 246.2099335 ms
- Performance p95: 270.70033 ms
- Performance max: 296.435471 ms
- Peak RSS: 35,307,520 bytes
- User CPU delta: 6.857696 s
- System CPU delta: 0.031379 s

## Failures and diagnosis

Several temporary audit-harness failures occurred while constructing the independent probes: an incorrect worker-handler argument type, an isolated import-path issue, an initial EvidenceRef construction using the quality-evidence identity instead of the canonical row identity, and two temporary probe-script syntax/contract mistakes. Each was diagnosed as CONTROL probe construction, not project implementation behavior. The probes were corrected before acceptance evidence was recorded.

No governed database mutation succeeded. No P4 historical artifact was changed. No trading, capital, provider-credential, or acquisition operation occurred.

## Final result

**EXECUTED / SUCCESSFUL FOR CONTROL ACCEPTANCE**

The execution established the runtime evidence required for independent verification of TO-P5-004. It does not itself constitute closure; closure is established by `AR-P5-004` plus CONTROL-owned peripheral synchronization.

--- END EXEC-LOG ---