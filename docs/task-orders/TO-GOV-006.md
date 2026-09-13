# MEYLUX V2 — STATE / REGISTRY CLEANUP & RECONCILIATION TASK ORDER

**Task Order ID:** `TO-GOV-006`
**Governance Class:** Governance / State / Registry Reconciliation
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)
**Status:** `AUTHORIZED TO EXECUTE`
**Build Report ID:** `BR-GOV-006`
**Build Report Path:** `docs/build-reports/BR-GOV-006.md`
**GitHub Issue:** `#18`

## 1. Sole Objective

Reconcile contradictory authoritative State and Registry records before any new implementation or Step activation.

## 2. Known Conflict

- `docs/state/CURRENT_CHECKPOINT.json` reports Phase 2 `CLOSED / VERIFIED`, with no active Task Order.
- `docs/registry/phases.yaml` reports Phase 2 `ACTIVE / AUTHORIZED`, with `STEP-P2-002` and `TO-P2-002` active.

These records cannot remain simultaneously authoritative.

## 3. Required Work

1. Inspect authoritative Phase 2 Task Orders, Build Reports, Audit Reports, Execution Reports, verification evidence, ADR/ACR records, Change Ledger, State, Registry, and Continuity artifacts.
2. Determine the evidence-backed Phase 2 state.
3. Produce a complete conflict matrix.
4. Identify exact file-by-file corrections.
5. Preserve all Stable IDs, filenames, schemas, contracts, architecture, and historical evidence.
6. Review stale lifecycle labels and unresolved Constitution Stable ID / architecture-status contradictions.
7. Produce a self-contained Reconciliation Report with evidence references, Open Questions, blockers, and the required CONTROL decision.

## 4. Strict Non-Scope

The Producer MUST NOT:

- perform new implementation;
- activate any Step or Task Order;
- begin Phase 3 or Phase 4;
- modify the VPS or V1 VPS;
- deploy, migrate, restart services, or change configuration;
- redesign architecture, contracts, schemas, filenames, or Stable IDs;
- delete or rewrite historical evidence;
- fabricate tests, execution evidence, or verification evidence;
- resolve genuine conflicts silently.

## 5. Required Output

Return `BR-GOV-006 — State / Registry Reconciliation Report` containing:

- inspected files and evidence;
- current State findings;
- Registry findings;
- complete Conflict Matrix;
- evidence-backed Phase 2 status;
- exact proposed corrections;
- files requiring no change;
- Open Questions and Deferred Decisions;
- Stable ID impact statement;
- schema/contract preservation statement;
- actual validation checks performed;
- evidence references;
- blockers;
- required CONTROL decision;
- explicit non-claims.

## 6. Acceptance Criteria

The report is acceptable only if:

1. Every identified conflict is explicitly documented.
2. Phase 2 status is determined from actual authoritative evidence.
3. No status is changed by assumption or memory.
4. Proposed changes are exact and file-specific.
5. No Stable ID is invented or replaced.
6. No architecture, contract, schema, filename, or structure is silently changed.
7. No implementation or VPS action is performed.
8. Empty registries are not populated with fabricated data.
9. Open Questions and Deferred Decisions are preserved.
10. All claims of testing, execution, verification, closure, or completion have actual evidence.

## 7. Conflict Handling

If a conflict cannot be resolved from authoritative evidence:

`STOP THAT PART → preserve evidence → record the conflict → report to CONTROL`

Do not invent a resolution.

## 8. Completion Boundary

The permitted completion state is:

`RECONCILIATION REPORT PREPARED — AWAITING CONTROL AUDIT`

Do not claim the repository is cleaned, reconciled, verified, frozen, closed, or complete.

Do not proceed to any next Phase or Step.
