# AR-P5-CORRECTIVE-001 — CONTROL Independent Audit — Corrective VPS Reconciliation

**Project:** MEYLUX V2  
**Phase:** PH-P5  
**Historical Step boundary:** STEP-P5-002 remains COMPLETE / VERIFIED  
**Audit authority:** ROL-V2-001 — CONTROL / REVIEWER  
**Audit status:** APPROVED / VERIFIED FOR CORRECTIVE RUNTIME BASELINE  
**Execution log:** EXEC-LOG-P5-CORRECTIVE-VPS-RECON-20260924

## 1. Audit basis

Reviewed independently against the Project Owner corrective authorization dated 2026-09-24, the current repository main revision, the P5-002 Fact Requirements Matrix, ADR-GOVERNANCE-012, ADR-GOVERNANCE-013, and real SentinelX evidence from server-l6rf.

This audit does not reopen STEP-P5-002 and does not activate STEP-P5-003.

## 2. Determinations

### A. Repository reconciliation — PASS

Before mutation the VPS was at fb7d9847498323bec067ba98a1e2729f869c0697 while origin/main was independently confirmed at 2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2.

CONTROL synchronized the VPS checkout exactly to main. The final VPS HEAD equals origin/main.

### B. Database migration reconciliation — PASS

The actual DB state was queried before mutation. It contained 0001 through 0006 and did not contain 0007.

Repository 0007_specialist_foundation.sql was verified as the next migration. It was then applied successfully. Final migration state is exactly 0001 through 0007.

No 0001–0006 migration was modified.

### C. Recovery readiness — PASS

A real filesystem archive of the stopped PostgreSQL volume was created before mutation, with recorded SHA-256. A pre-correction logical data dump was also captured.

This satisfies the recovery requirement with an actual recoverable state.

### D. Runtime bring-up — PASS

The existing governed compose stack was brought up without adding services or changing topology.

Final evidence:
- DB running / healthy;
- Redis running / healthy and PONG;
- API, collector, worker-quant and worker-ai running;
- application-role DB connection from api container succeeds.

### E. Schema / privilege integrity — PASS

The 0007 specialist_outputs table, index, append-only trigger and grants are present.

meylux_app has SELECT/INSERT and does not have UPDATE/DELETE/TRUNCATE on specialist_outputs.

No fabricated specialist output was inserted.

### F. Data preservation — PASS

Pre/post row counts match exactly for all measured existing persisted families.

More strongly, normalized pre/post logical dumps of all existing data are byte-for-byte identical after removing pg_dump-generated transient restrict tokens, comments/blank-line formatting, and the newly introduced schema_migrations state.

No destructive DB operation or volume reset occurred.

### G. Re-execution safety — PASS

The exact 0007 migration was safely re-executed. The second execution produced INSERT 0 0 for schema_migrations and left existing data counts unchanged.

The migration's IF NOT EXISTS / ON CONFLICT semantics and observed second-run behavior establish the relevant re-execution property without a destructive repetition.

### H. AVAILABLE_PERSISTED — NOT ESTABLISHED

The runtime availability outage is resolved, but the P5 authoritative fact availability gate is not.

The P5-002 FRM explicitly requires knowledge_time <= snapshot.as_of. The authoritative P4 persistence families inspected on the live DB expose event_time and persistence/logging timestamps, but no dedicated knowledge_time column.

CONTROL therefore correctly refuses to convert physically queryable records into AVAILABLE_PERSISTED facts by substituting event_time or persisted_at/logged_at.

The governed USR-03 disposition remains UNAVAILABLE_DISPOSITIONED for the affected P5 fact families, with the existing P5-002 OQ records preserved.

## 3. Historical integrity

The original P5-001 Roadmap-to-Task-Order VPS discrepancy remains visible as a historical finding.

This corrective execution is new evidence and is not attributed to TO-P5-001 or TO-P5-002.

STEP-P5-002, TO-P5-002, BR-P5-002 and AR-P5-002 lifecycle states remain unchanged.

## 4. Architecture and scope

PASS.

No evidence of:
- STEP-P5-003 activation;
- specialist execution;
- Futures/Forex implementation;
- trading/capital/custody;
- provider credential changes;
- architecture or canonical-contract changes;
- modification of migrations 0001–0006;
- destructive database operations;
- unrelated cleanup.

## 5. Governance conclusion

**Corrective VPS runtime reconciliation: COMPLETE / VERIFIED.**

**Current governed VPS baseline: READY AS A RUNTIME FACTUAL BASELINE FOR A FUTURE AUTHORIZED ACTION.**

**P5 authoritative AVAILABLE_PERSISTED: NOT ESTABLISHED.**

**PH-P5: ACTIVE / AUTHORIZED.**

**STEP-P5-002: COMPLETE / VERIFIED — not reopened.**

**STEP-P5-003: NOT AUTHORIZED.**

The remaining blocker is semantic upstream fact admissibility (knowledge_time), not VPS availability. Any future resolution must follow the owning P4/P3/P2 governance route and must not be implemented opportunistically inside this corrective action.


## 6. Final repository read-back

After the evidence/registry synchronization commits, CONTROL synchronized the VPS checkout to the then-current `origin/main` revision `9cd7ac8d35889f45573ff0e11162112e507bc9a4`.

The runtime implementation baseline remains `2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2`. The intervening and final commits contain governance/evidence synchronization only; no runtime implementation, migration, compose or application-source change occurred after bring-up.

All six governed containers remained running; DB and Redis remained healthy after the final checkout read-back.

This does not alter any Step lifecycle state and does not activate STEP-P5-003.
