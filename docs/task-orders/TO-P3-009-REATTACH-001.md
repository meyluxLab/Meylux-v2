# TO-P3-009-REATTACH-001 — Controlled Reattachment of P3-009 into Current SoT

**Task Order SID:** `TO-P3-009-REATTACH-001`  
**Project:** MEYLUX V2  
**Issuing Role:** `ROL-V2-001` — CONTROL / REVIEWER  
**Producer Role:** `ROL-V2-002` — PRODUCER / ARCHITECT-BUILDER  
**Boundary:** `PH-P5 / STEP-P5-003` prerequisite correction  
**Historical Boundary:** `PH-P3 = CLOSED / VERIFIED` and `STEP-P3-007/008 = COMPLETE / VERIFIED` remain unchanged  
**Governance Class:** Post-closure lineage/integration correction  
**Status:** AUTHORIZED TO EXECUTE  
**Owner Authorization:** Project Owner Ratification — Controlled Reattachment of P3-009 into Current SoT, 2026-10-01  
**Historical predecessor:** `TO-P3-009 / BR-P3-009 / AR-P3-009`

## 1. Required outcome

The Project Owner has ratified **Option A — Controlled Reattachment**.

The required outcome is genuine reattachment of the existing P3-009 quality/acquisition evidence capability to the current authoritative `main` lineage, followed by fresh current-mainline evidence and independent CONTROL verification.

This is a lineage/integration correction, not an architectural redesign and not a reopening of historical PH-P3 closure.

## 2. Authoritative starting evidence

CONTROL established before issuing this Task Order:

- Current `main`: `2b5dc4fc227c157cc00c97cde35287605a8c89c4`.
- Historical functional P3-009 revision: `021030f921b5f7ecc498ebe3e93b7b1bcd849764`.
- PR #51 head: `11e3063d77d817fdb60e0199d5cef4fc1d4d3119`.
- PR #51: `OPEN / UNMERGED / mergeable=false`.
- PR #51 base: `main` at `f8250fadc1cec31cbc2b8bab9afc1ecb1026d331`.
- Current main and historical P3-009 are divergent; the historical implementation is not current-mainline.
- Historical P3-009 contains the required quality-evidence contract, persistence implementation, migration 0009, tests, documentation and P3 vertical-slice integration.
- Current main has evolved since the PR base, including migration 0008, current runtime code and current CI workflows.

Historical evidence is therefore valid historical evidence, but it is not fresh current-mainline verification.

## 3. Critical prohibition

**PR #51 MUST NOT be merged in its current form.**

Do not close, rewrite, force-update, or relabel PR #51 or its historical evidence as though it were the new integration revision.

The current implementation must be established from the current authoritative `main` lineage. Historical P3-009 code may be reused as source material, but every resulting file and behavior must be reconciled with current `main`.

## 4. Controlled integration boundary

The governed path is:

`current main @ 2b5dc4f → P3-009 reattachment → fresh tests/evidence → BR-P3-009-REATTACH-001 → CONTROL independent audit`

Producer retains implementation-level design authority. Producer may choose the exact repository mechanics within this boundary, including a new branch from current `main` and selective reapplication/reconciliation of historical implementation.

The mechanism must:

- preserve historical lineage;
- avoid direct merge of PR #51;
- preserve unrelated current-mainline changes;
- make integration conflicts explicit;
- produce a reproducible current-mainline revision.

## 5. Required current-mainline capability

Re-establish, as applicable and as proven necessary:

- `contracts/quality_evidence.py`;
- `src/meylux/persistence/quality_evidence.py`;
- `migrations/versions/0009_quality_evidence_persistence.sql`;
- P3-009 tests;
- P3-009 semantic documentation;
- required P3 vertical-slice integration;
- migration orchestration integration;
- applicable CI/test integration.

Do not mechanically copy historical files when current contracts or surrounding implementation have changed.

Migration 0008 is **OUT OF SCOPE** for modification, rewrite or reapplication. Migration 0009 must integrate correctly after the current migration head.

## 6. Mandatory semantics

Preserve the ratified P3 quality-evidence semantic:

`knowledge_time = received_at`

Keep event time, receipt/observation time, validation time, persistence/logging time, wall-clock execution time and knowledge_time distinct.

Never substitute `persisted_at`, `logged_at`, current time, synthetic timestamps or fixtures for authoritative knowledge_time.

Preserve quality-state semantics, deterministic identity, provenance, lineage, EvidenceRef compatibility, append-only persistence, duplicate/idempotent behavior and contradiction semantics.

## 7. Required reconciliation

Before declaring implementation complete, inspect and reconcile:

- current acquisition/validation/quality contracts;
- current `src/meylux/runtime/p3_008_vertical_slice.py`;
- current P3 persistence boundaries;
- current migrations, including 0008;
- `infrastructure/postgres/migrate.sh`;
- current CI workflows;
- current tests and relevant registry semantics;
- historical revision `021030f...` and PR #51.

Explicitly document historical changes that cannot be applied verbatim because current main has evolved.

If a frozen architecture/contract or higher-authority semantic conflict is discovered, stop only the affected portion under ADR-GOVERNANCE-013 Rule 1(B) and return the exact conflict to CONTROL. No silent workaround.

## 8. Fresh evidence requirements

Producer must generate fresh evidence against the resulting current-mainline revision for:

1. contract/implementation agreement;
2. migration ordering, creation and idempotency;
3. required database objects and append-only enforcement;
4. quality-evidence persistence and deterministic read-back;
5. quality-state semantics;
6. `knowledge_time = received_at`;
7. event-time / knowledge-time separation;
8. identity, provenance and lineage;
9. EvidenceRef resolution;
10. duplicate/idempotent and concurrent persistence;
11. unavailable/non-VALID evidence persistence without fabrication;
12. P3 vertical-slice integration;
13. applicable regression and CI suites;
14. architecture and scope preservation.

Historical PR #51 CI evidence does not satisfy these fresh requirements.

## 9. Historical evidence boundary

Keep historically identified and unchanged:

- PR #51;
- `feat/to-p3-009-prq4-quality-evidence`;
- `021030f921b5f7ecc498ebe3e93b7b1bcd849764`;
- `11e3063d77d817fdb60e0199d5cef4fc1d4d3119`;
- `BR-P3-009`;
- `AR-P3-009`;
- historical CI and implementation/test/documentation evidence.

The new Build Report must clearly separate historical evidence from fresh evidence.

## 10. P5-003 continuity and stop state

Do not discard, rewrite or restart the existing P5-003 implementation.

Until fresh current-mainline P3-009 verification succeeds:

`P3-009 historical implementation = EXISTS`  
`P3-009 current-mainline implementation = INTEGRATION PENDING`  
`PRQ-4 current reproducible basis = NOT YET RE-ESTABLISHED`  
`STEP-P5-003 = NOT VERIFIED / NOT COMPLETE / NOT CLOSED`

No synthetic Input Snapshot and no fabricated knowledge-time evidence may bypass this prerequisite.

## 11. Explicit non-scope

No authorization is granted for PRQ-1/2/3, implementation of P5-003, TO-P2-013, migration 0008 changes, new provider acquisition, MEXC expansion, trade/depth, derivatives, Futures, Forex, new symbols, P4 mathematical implementation, reopening historical P2/P3/P4 closure, LLM/cross-specialist synthesis, trading/execution/capital/custody, or Phase 6.

No Producer VPS operation is authorized.

## 12. Build Report and lifecycle boundary

Producer must deliver:

`BR-P3-009-REATTACH-001`

It must contain the exact current-mainline revision, integration mechanism, changed-file inventory, historical-to-current reconciliation, architecture/contract impact, migration/database evidence, knowledge-time proof, identity/provenance/lineage/EvidenceRef proof, test/CI results, deviations/open questions, historical-vs-fresh evidence separation and scope compliance.

Producer MUST NOT declare VERIFIED, COMPLETE or CLOSED and MUST NOT perform CONTROL-owned closure synchronization.

Expected lifecycle:

`TO-P3-009-REATTACH-001 → BR-P3-009-REATTACH-001 → CONTROL independent audit → correction cycle(s), if required → AR-P3-009-REATTACH-001 → CONTROL closure/synchronization`

Only CONTROL may determine whether current PRQ-4 is restored after independent verification.

## 13. Continuation and handoff

ADR-GOVERNANCE-013 Rule 1 applies. The Owner decision removes the previous Owner-decision blocker. Producer must continue through implementation, testing and Build Report delivery to the farthest legitimate point.

Normal merge/reconciliation difficulty and ordinary test failures are not blockers.

Stop only for Rule 1(A) Owner decision, Rule 1(B) unresolved authoritative conflict, or Rule 1(C) natural Build Report boundary requiring independent CONTROL verification.

**Task Order conclusion: AUTHORIZED TO EXECUTE.**

---END---
