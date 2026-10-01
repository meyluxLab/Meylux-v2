# AR-P3-009-REATTACH-001 — CONTROL Independent Audit — Controlled Reattachment of P3-009

**Audit Report ID:** `AR-P3-009-REATTACH-001`  
**Project:** MEYLUX V2  
**Role:** `ROL-V2-001` — CONTROL / REVIEWER  
**Phase / Step:** `PH-P5 / STEP-P5-003` prerequisite correction  
**Task Order:** `TO-P3-009-REATTACH-001`  
**Build Report:** `BR-P3-009-REATTACH-001`  
**Authoritative integration commit:** `c0518c99f84c1a74ead21704355d1cb585498fd3`  
**Producer implementation revision:** `008f7f3bfc554077ea9ca87bc39ee00b337a59c4`  
**CONTROL merge:** PR #54 → `c0518c99f84c1a74ead21704355d1cb585498fd3`  
**Historical predecessor:** `TO-P3-009 / BR-P3-009 / AR-P3-009`  
**Audit authority:** ADR-GOVERNANCE-012 / ADR-GOVERNANCE-013

## 1. Independent audit disposition

CONTROL independently audited the controlled reattachment against the authorized Task Order, Producer Build Report, current authoritative `main`, implementation diff, current contracts and runtime boundaries, migration ordering, P3-009 tests, fresh Core and Docker evidence, and the preserved historical lineage.

**Final disposition: APPROVED / VERIFIED.**

The authorized P3-009 reattachment outcome is independently established on current `main`. The historical PR #51 remains historical evidence and was not used as the authoritative integration path.

## 2. Authoritative current-mainline evidence

The resulting `main` revision is:

`c0518c99f84c1a74ead21704355d1cb585498fd3`

GitHub Actions explicitly checked out this exact SHA in the fresh Core run.

Fresh resulting-main CI:

- CI Core Run ID `36825603601` — **SUCCESS**.
- CI Docker Foundation Run ID `36825603711` — **SUCCESS**.
- Core repository-foundation job `110250487177` — **SUCCESS**.
- Docker Foundation job `110250487469` — **SUCCESS**.

The Core job executed the full foundation suite and the dedicated real-PostgreSQL P3-009 suite. The Docker job completed foundation self-checks, migration harness, knowledge-time migration verification and database-boundary checks.

## 3. Fresh P3-009 behavioral evidence

The resulting-main Core log records:

- foundation suite: **573 tests / OK**;
- dedicated PostgreSQL P3-009 suite: **6 tests / OK** in approximately 5.696 seconds;
- all six dedicated PostgreSQL cases completed with `ok` and terminal `OK`.

The six real-PostgreSQL cases independently establish:

1. an actual unavailable provider outcome reaches persisted quality evidence;
2. persisted evidence resolves to the P5 Snapshot boundary and enforces the temporal boundary;
3. append-only privileges and migration rerun behavior;
4. transaction rollback after a failed evidence insert;
5. deterministic concurrent duplicate persistence behavior;
6. duplicate/idempotent persistence and contradictory logical-fact behavior.

This is direct PostgreSQL evidence, not an in-memory substitute.

Docker Foundation independently completed:

- P3-009 semantic test execution;
- migration harness;
- migration 0009 execution;
- current database foundation checks;
- legacy 0008 knowledge-time/idempotency verification;
- UTC database verification.

The Docker foundation test population differs from Core because the Docker job does not execute the dedicated real-PostgreSQL P3-009 suite. This is an execution-boundary difference, not an evidence contradiction.

## 4. Contract and knowledge-time audit

CONTROL independently inspected the resulting implementation and current-main diff.

The reattached `QualityEvidenceRecord` contract explicitly enforces:

`knowledge_time = received_at`

and rejects mismatch.

Migration 0009 independently enforces the same semantic at database level.

The implementation keeps `event_time`, `received_at`, `knowledge_time` and operational `persisted_at` distinct. No `persisted_at`, `logged_at`, migration time, wall-clock time or synthetic fixture timestamp is substituted for authoritative knowledge time.

The current-main Docker database evidence shows `meylux.quality_evidence.knowledge_time` is non-null, while legacy P4 families remain governed separately.

The P5 temporal-boundary tests explicitly reject future knowledge time and accept the authoritative boundary. No synthetic market fact is introduced.

## 5. Persistence, migration and security audit

The resulting implementation establishes:

- `meylux.quality_evidence`;
- migration `0009_quality_evidence_persistence`;
- migration ordering after 0008;
- idempotent migration registration;
- append-only database enforcement;
- application SELECT/INSERT only;
- application UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER denied;
- deterministic `INSERT ... ON CONFLICT ... RETURNING` behavior.

The resulting-main Docker evidence confirms the migration/database foundation and privilege matrix. The Core PostgreSQL suite independently verifies append-only behavior, privilege boundaries and rerun behavior.

Migration 0008 was not modified by the reattachment.

## 6. Identity, provenance, lineage and EvidenceRef audit

The implementation preserves the existing P2 acquisition identity and derives deterministic quality-evidence identity from the governed semantic inputs.

CONTROL accepts the independently evidenced behavior that:

- identical replay is idempotent;
- contradictory logical facts are retained/detected rather than silently overwritten;
- provenance and lineage remain explicit;
- missing timeframe/venue is not fabricated;
- persisted evidence resolves to the structured P5 EvidenceRef boundary only from authoritative context;
- temporal lookahead is rejected.

No P5-002 implementation was altered to manufacture unavailable evidence.

## 7. Unavailable / non-VALID evidence audit

The reattached P3 path persists authoritative non-VALID acquisition outcomes without manufacturing market payloads or replacement timestamps.

For unavailable acquisition, the runtime uses the authoritative P2 acquisition state and preserved ProviderError/canonical bytes where present.

The fresh PostgreSQL test `test_actual_unavailable_provider_outcome_reaches_persisted_quality_evidence` passed on the resulting current-mainline execution.

This establishes the required evidence route without converting unavailable input into fabricated analytical truth.

## 8. Current-mainline scope and architecture audit

The merge diff is bounded to the authorized P3-009 reattachment surface: P3 quality-evidence contract/persistence/migration/runtime integration, dedicated tests, CI integration and the required semantic/legacy documentation.

No evidence was found of:

- PRQ-1/2/3 implementation;
- P5-003 implementation;
- TO-P2-013 implementation;
- migration 0008 modification;
- new provider acquisition;
- MEXC expansion;
- trade/depth or derivatives implementation;
- Futures or Forex implementation;
- new-symbol expansion;
- P4 mathematical redesign;
- Phase 6/LLM/synthesis;
- trading, execution, capital or custody authority;
- reopening PH-P3 historical closure.

Frozen architecture and existing contract ownership were preserved.

## 9. Historical lineage boundary

Historical evidence remains explicitly preserved:

- PR #51 remains OPEN / UNMERGED;
- historical functional revision `021030f921b5f7ecc498ebe3e93b7b1bcd849764`;
- historical PR head `11e3063d77d817fdb60e0199d5cef4fc1d4d3119`;
- historical `BR-P3-009`;
- historical `AR-P3-009`;
- historical CI evidence.

The authoritative current-mainline implementation is instead the controlled PR #54 integration resulting in `c0518c99f84c1a74ead21704355d1cb585498fd3`.

No historical evidence was relabeled as fresh current-mainline evidence.

## 10. PRQ-4 disposition

The original PRQ-4 basis was not considered restored merely because migration 0009 existed.

The current audit now establishes the complete underlying capability required by the reattachment Task Order on authoritative `main`, with fresh evidence for contract semantics, persistence, migration, append-only/security boundaries, deterministic identity, contradiction/idempotency, unavailable evidence, EvidenceRef resolution and P5 temporal compatibility.

Therefore:

**PRQ-4 = RESOLVED / VERIFIED**

This does not assert population-wide historical backfill or availability of legacy rows whose authoritative source bytes are absent. The existing legacy evidence inventory remains authoritative for that boundary.

## 11. Lifecycle consequence

This reattachment is a post-closure prerequisite correction and does not reopen PH-P3.

After CONTROL-owned closure synchronization:

- `TO-P3-009-REATTACH-001 = VERIFIED / COMPLETE`;
- `BR-P3-009-REATTACH-001 = VERIFIED`;
- `AR-P3-009-REATTACH-001 = APPROVED / VERIFIED`;
- historical `TO-P3-009 / STEP-P3-007 / STEP-P3-008 / PH-P3` closure remains unchanged;
- `STEP-P5-003 = ACTIVE / AUTHORIZED`;
- `TO-P5-003 = AUTHORIZED TO EXECUTE` and resumes as the active audit/implementation boundary;
- no P5-003 verification or closure is implied by this audit.

## 12. ADR-GOVERNANCE-012 closure synchronization

CONTROL is responsible for and completes the G12 synchronization for this correction cycle.

The synchronized surfaces are:

- artifact registry;
- phase/step registry;
- current checkpoint;
- README;
- requirements registry;
- tests registry;
- database registry;
- runtime registry;
- contract registry;
- security registry;
- Build Report lifecycle;
- this Audit Report registration;
- Change Ledger;
- applicable standalone status records.

Historical P3-009 records remain traceable; no supplemental/staging registry is promoted as a competing Source of Truth.

A machine-readable read-back is required after the synchronization mutations and is part of this closure record.

## 13. Final CONTROL conclusion

The genuine P3-009 current-mainline reattachment requirement has been reached and independently verified.

**CONTROL conclusion: TO-P3-009-REATTACH-001 = VERIFIED / COMPLETE; PRQ-4 = RESOLVED / VERIFIED.**

The natural next boundary is the already-authorized continuation of `TO-P5-003`. Its existing implementation remains preserved. CONTROL must resume its independent P5-003 verification from the previously established boundary; no reimplementation is authorized or required.

--- END AUDIT REPORT ---
