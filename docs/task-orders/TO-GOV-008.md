# MEYLUX V2 — GOVERNANCE / DOCUMENTATION / REGISTRY / LIFECYCLE RECONCILIATION TASK ORDER

**Task Order ID:** `TO-GOV-008`
**Governance Class:** Governance / Documentation / Registry / Lifecycle Reconciliation
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)
**Status:** `AUTHORIZED TO EXECUTE`
**Predecessor:** `TO-GOV-007` / `BR-GOV-007`
**Repository:** `meyluxLab/Meylux-v2`
**Related ADR:** `ADR-GOVERNANCE-012`
**Required Build Report:** `BR-GOV-008`
**Build Report Path:** `docs/build-reports/BR-GOV-008.md`

## 1. Sole Objective

Reconcile stale, contradictory, or pre-activation lifecycle/status fields in governed documentation and registries, using direct repository evidence and the authoritative governance hierarchy, without introducing new implementation, activating a Phase or Step, changing architecture, or creating new Stable IDs.

This Task Order is a controlled governance/documentation reconciliation action only.

## 2. Formal Traceability Boundary — Project Owner Applied Changes

Before the formal issuance of this Task Order, the Project Owner directly applied the following repository changes:

- `README.md`
- `docs/decisions/ADR_INDEX.md`
- the `Mandatory Peripheral Synchronization Checklist` addition to `docs/governance/ARTIFACT_PROTOCOL_V2.md`, established by `ADR-GOVERNANCE-012`.

These changes were applied directly by the Project Owner **before formal issuance of `TO-GOV-008`**. They are preserved here solely for traceability and evidence accuracy. They do **not** constitute Producer execution of this Task Order and must not be represented as such in `BR-GOV-008`.

Accordingly, `F-01 / README.md` is **OUTSIDE PRODUCER EXECUTION SCOPE**. The Producer MUST NOT repeat, duplicate, or independently re-apply any of the above Project Owner-applied changes.

The remaining Producer execution scope is strictly:

`F-02 → F-03 → F-04 → F-05 → F-06 → F-07 → F-08`

## 3. Authoritative Basis Priority

Use the following authority order when evaluating findings:

1. `docs/constitution/MEYLUX_CONSTITUTION_V2.md`
2. `docs/architecture/MASTER_ARCHITECTURE_V2.md`
3. `docs/state/CHANGE_LEDGER.yaml`
4. `docs/state/CURRENT_CHECKPOINT.json`
5. `docs/registry/phases.yaml`
6. `docs/registry/artifacts.yaml`
7. Existing Task Orders, Build Reports, Audit Reports, and execution/verification evidence for P0/P1/P2 and GOV series
8. `docs/governance/ARTIFACT_PROTOCOL_V2.md`, role contracts/definitions, and relevant ADRs, including `ADR-GOVERNANCE-012`

Do not resolve a conflict by preference, memory, assumption, or convenience.

## 4. Required Findings / Execution Scope

### F-02 — Role Registry Lifecycle Status

Seven role records `ROL-V2-001` through `ROL-V2-007` currently carry `DRAFT_PRE_PHASE_0` in `docs/registry/artifacts.yaml`.

Inspect `ADR-ROLE-IDENTITY-001` and directly related authoritative evidence. Determine the status of each role individually. Do not assume that all seven roles have the same lifecycle state.

If evidence is insufficient for a status correction, do not guess. Preserve the existing record and report the item as an `Open Question / Blocking Conflict` as appropriate.

### F-03 — Specialized Registry Lifecycle Status

Nine specialized registry files require individual inspection:

- components
- contracts
- requirements
- tests
- runtime
- database
- security
- configuration
- performance

The Producer MUST determine, from direct evidence, whether each is:

1. required and evidence-backed;
2. populated in another authoritative location but not transcribed;
3. intentionally deferred / not required at the current lifecycle point; or
4. unresolved and therefore requiring an Open Question / Blocking Conflict.

Do not apply one status uniformly to all nine registries. Do not invent records merely to make a registry appear complete. The contracts registry contains actual records and must be assessed as such.

### F-04 — Deferred Decisions Registry Status

Inspect `DEFERRED_DECISIONS.yaml` and its actual contents.

If the registry is empty, update only its file-level lifecycle/status field when direct evidence and the repository's existing vocabulary support such a correction. Do not invent deferred decisions or records.

If evidence does not establish a safe correction, report the unresolved condition without guessing.

### F-05 — Architecture Hardening Lessons Learned Status

Inspect `MEYLUX_V2_ARCHITECTURE_HARDENING_LESSONS_LEARNED.md` (`DOC-V2-P0-002`) together with `ADR-GOVERNANCE-004` and directly related authoritative evidence.

Determine whether ratification/freeze of the Master Architecture also ratified, superseded, or otherwise resolved the document's self-declared design-baseline/pending-ratification status.

If the evidence does not establish the relationship unambiguously, do not alter the status. Record the matter as a `Blocking Conflict / Open Question` for CONTROL.

### F-06 — Gate Definitions / Evidence Policy Verification Labels

Inspect:

- `docs/verification/GATE_DEFINITIONS.md`
- `docs/verification/EVIDENCE_POLICY.md`

They contain `RECONCILED / PENDING CONTROL VERIFICATION` language.

The Producer MUST only determine whether prior independent CONTROL verification evidence already exists. The Producer MUST NOT perform or claim CONTROL verification.

If no prior CONTROL verification is evidenced, report the condition as unresolved and requiring CONTROL verification. Do not self-verify these artifacts.

### F-07 — Supplemental Phase 2 Registry

Inspect `docs/registry/phase2-artifacts.yaml` and compare it field-by-field with canonical `docs/registry/artifacts.yaml`.

If its contents have been fully absorbed into the canonical registry, mark it as superseded/retired only using an existing repository lifecycle vocabulary and preserve the file; do not delete it.

If any discrepancy remains, do not silently reconcile it. Record the exact discrepancy as a `Blocking Conflict / Open Question` and preserve evidence.

### F-08 — Constitution Stable ID

The Constitution Stable ID remains `IDENTITY UNCONFIRMED`.

**DO NOT CHANGE F-08.** Do not create, infer, replace, or ratify a Constitution Stable ID under this Task Order.

## 5. F-01 Explicit Exclusion

`F-01 / README.md` is not a Producer work item under this Task Order.

The README and the associated `ADR_INDEX.md` / Artifact Protocol checklist changes were applied directly by the Project Owner before formal issuance. Producer must not re-run them, duplicate them, or attribute them to Producer execution.

This traceability record does not mean `TO-GOV-008` was previously executed. It records only the provenance of those specific pre-issuance changes.

## 6. Evidence and Do-Not-Guess Rules

For every finding:

- use direct repository evidence;
- identify the exact file, field, record, or authoritative artifact supporting the conclusion;
- distinguish observed state from proposed correction;
- do not fabricate missing records, statuses, tests, hashes, outputs, verification, or completion;
- do not infer a lifecycle state merely because another artifact has a similar state;
- where evidence is insufficient or contradictory, preserve the evidence and report an `Open Question / Blocking Conflict`;
- do not silently reconcile genuine authority or lifecycle conflicts.

## 7. Strict Non-Scope

The Producer MUST NOT:

- implement application/runtime features or code;
- activate Phase 3 or Phase 4;
- activate any Phase or Step;
- reopen Phase 2 reconciliation;
- modify the VPS or V1 VPS;
- deploy, migrate, restart services, or change runtime configuration;
- redesign or alter architecture, contracts, schemas, interfaces, security boundaries, or approved structures;
- create, delete, replace, or invent Stable IDs;
- create a competing registry or lifecycle vocabulary;
- delete or rewrite historical Task Orders, Build Reports, Audits, execution logs, or evidence;
- repeat the Project Owner's F-01 changes;
- perform CONTROL verification for F-06;
- fabricate evidence or silently resolve blocking conflicts.

## 8. Required Execution Sequence

1. Inspect the current repository and all authoritative inputs relevant to F-02 through F-08.
2. Record the actual before-state for every finding.
3. Map each proposed correction to direct evidence.
4. Apply only corrections supported by authoritative evidence and existing repository vocabulary.
5. Preserve all Stable IDs, filenames, schemas, contracts, architecture, and historical evidence.
6. Validate all changed structured files using appropriate syntax/consistency checks actually performed.
7. Validate relevant cross-references, duplicate Stable IDs, dangling references, and active-work indicators.
8. Confirm that Phase 2 remains closed/verified and that no Phase 3 or Phase 4 activation occurred.
9. Review the complete diff and changed-file scope.
10. Produce `BR-GOV-008` with actual execution evidence and unresolved items.

## 9. Required Build Report

`BR-GOV-008` MUST include:

- Task Order identity;
- base commit and resulting commit;
- exact changed-file list;
- exact changed-field/record list;
- before/after evidence for each in-scope finding;
- evidence supporting every applied change;
- explicit F-01 provenance statement showing Project Owner-applied changes are not Producer execution;
- individual status assessment for all nine specialized registries;
- F-08 unchanged statement;
- validation commands/checks and actual outputs/results;
- blocking conflicts and Open Questions;
- Stable ID preservation statement;
- explicit confirmation that Phase 2 was not reopened;
- explicit confirmation that Phase 3 and Phase 4 were not activated;
- explicit confirmation of no VPS/V1/runtime action;
- explicit non-claims for anything not actually verified.

The Build Report MUST NOT mix Project Owner-applied changes with Producer execution evidence.

## 10. Required Final State Declaration

Use exactly one of:

`COMPLETED — ALL IN-SCOPE CHANGES APPLIED AND VALIDATED`

or:

`PARTIALLY COMPLETED — BLOCKING CONFLICTS REMAIN`

The first declaration is forbidden if any required correction, validation, or evidence remains incomplete, or if any F-02/F-03/F-05/F-07 item requires do-not-guess deferral.

## 11. Responsibility Boundary

**CONTROL / REVIEWER**
→ approval / authorization / repository governance / formal issuance / independent audit and verification after Build Report

**PRODUCER / ARCHITECT-BUILDER**
→ execution of F-02 through F-08 / evidence collection / Build Report production

**CONTROL / REVIEWER**
→ independent audit / verification after Build Report

Registration of this Task Order and the related ADR is a governance/repository issuance action. It does not constitute Phase activation or Producer execution.

## 12. Completion Boundary

Completion of this Task Order does not authorize Phase 3 or Phase 4, does not reopen Phase 2, and does not constitute implementation, VPS execution, architecture work, verification of the overall project, or project-wide reconciliation closure.

After the Producer Build Report is submitted, CONTROL will independently audit and verify the execution evidence.

**End of Task Order.**
