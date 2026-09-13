# MEYLUX V2 — STATE / REGISTRY CORRECTION & RECONCILIATION TASK ORDER

**Task Order ID:** `TO-GOV-007`
**Governance Class:** Governance / State / Registry / Lifecycle Reconciliation
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)
**Status:** `AUTHORIZED TO EXECUTE`
**Predecessor:** `TO-GOV-006`
**Evidence Basis:** `BR-GOV-006` — APPROVED
**Repository:** `meyluxLab/Meylux-v2`

## 1. Sole Objective

Apply the evidence-backed State/Registry corrections identified by `BR-GOV-006`, reconcile the authoritative project state, and produce complete implementation and validation evidence in one execution.

This is a controlled correction task. It is not architecture redesign, Phase activation, VPS work, or historical evidence rewriting.

## 2. Mandatory Target Files

Inspect and, only where evidence requires, correct:

- `docs/state/CURRENT_CHECKPOINT.json`
- `docs/registry/phases.yaml`
- `docs/registry/artifacts.yaml`

Inspect the repository’s established governance, decision, continuity, schema and registry materials before changing any field. Do not invent additional target paths. If a decision or continuity record is required, use only an existing repository convention and document it.

## 3. Required Records

At minimum reconcile:

- `PH-P2`
- `STEP-P2-002`
- `TO-P2-001` through `TO-P2-007`
- `BR-P2-001` through `BR-P2-006`
- `AR-P2-AUDIT-007`
- `TO-GOV-006`
- `BR-GOV-006`

Include directly linked authoritative records discovered during inspection. Do not fabricate missing records.

## 4. Required Field Review

For `CURRENT_CHECKPOINT.json`, inspect and reconcile the fields representing:

- current phase;
- current step;
- status/lifecycle;
- active Task Order;
- last approved Task Order;
- last Build Report;
- last Audit;
- verification state;
- governed revision metadata, if applicable.

For `phases.yaml`, inspect and reconcile:

- phase ID;
- status;
- authorization state;
- active Step;
- active Task Order;
- completion state;
- verification state;
- linked evidence;
- dependencies and successor authorization.

For `artifacts.yaml`, inspect and reconcile all applicable fields:

- Stable ID;
- artifact type;
- phase and step;
- lifecycle status;
- approval state;
- execution state;
- verification state;
- dependencies;
- supersession;
- linked evidence;
- traceability and Source-of-Truth references.

Change only fields proven inconsistent with authoritative evidence or the existing repository schema.

## 5. Required Logical Result

Subject to the repository’s actual schema and authoritative evidence, the resulting state must express:

- Phase 2: evidence-backed `CLOSED / VERIFIED`;
- no active Task Order unless an active authorization is explicitly proven;
- no active Step unless an active authorization is explicitly proven;
- Phase 3: `NOT AUTHORIZED`;
- Phase 4: `NOT AUTHORIZED`;
- `TO-GOV-006`: `APPROVED`;
- `BR-GOV-006`: `APPROVED`.

Do not force these exact strings if the repository schema defines an equivalent representation. Use the existing schema and document the mapping.

## 6. Vocabulary and Authority Rules

Use the lifecycle vocabulary already defined by authoritative repository artifacts. Do not create a parallel vocabulary or silently invent meanings.

Preserve these distinctions wherever the schema supports them:

- `APPROVED` is not `EXECUTED`;
- `EXECUTED` is not `VERIFIED`;
- `VERIFIED` is not automatically `CLOSED`;
- `AUTHORIZED` is not automatically `ACTIVE`;
- `DRAFT` is not `RATIFIED`.

Determine and document which artifact controls:

- Phase status;
- active Step;
- active Task Order;
- approval;
- execution;
- verification;
- registry identity.

If authority, schema or lifecycle meaning is genuinely undefined or contradictory, do not guess. Stop that affected part and record a `Blocking Conflict / Open Question` with exact evidence.

## 7. Strict Non-Scope

The Producer MUST NOT:

- modify VPS or V1 VPS;
- deploy, migrate, restart services or change runtime configuration;
- activate Phase 3 or Phase 4;
- create or activate a new Step or Task Order;
- redesign architecture, contracts or schemas;
- change filenames or Stable IDs;
- create a competing Registry;
- delete or rewrite historical Task Orders, Build Reports, Audits or execution evidence;
- rewrite `TO-GOV-006` or `BR-GOV-006`;
- fabricate validation, execution, verification, hashes or outputs;
- silently resolve an undefined governance conflict.

## 8. Required Execution

1. Inspect the current repository and authoritative inputs.
2. Record the before-state and every inconsistency.
3. Map each proposed correction to evidence.
4. Apply only in-scope corrections.
5. Validate JSON and YAML syntax.
6. Validate cross-references, duplicate Stable IDs, dangling references and active-work indicators.
7. Verify that future phases were not activated.
8. Review the complete diff and changed-file scope.
9. Commit the changes to the repository.
10. Create the complete Build Report in the repository’s established location and format.

## 9. Required Build Report

The Build Report must include:

- Task Order identity, base commit and resulting commit;
- exact changed-file list;
- exact changed-field list;
- complete before/after table;
- evidence supporting every change;
- lifecycle vocabulary and field semantics used;
- authority determination;
- all synchronized Registry records;
- Stable ID preservation statement;
- validation commands and actual outputs;
- diff/scope review;
- unresolved Blocking Conflicts / Open Questions;
- explicit confirmation of no VPS/V1 VPS action and no future-phase activation.

Use `UNVERIFIED` for any validation that was not actually performed. Do not claim completion merely because a report was written.

## 10. Required Final State Declaration

Use exactly one of:

`COMPLETED — ALL IN-SCOPE CHANGES APPLIED AND VALIDATED`

or:

`PARTIALLY COMPLETED — BLOCKING CONFLICTS REMAIN`

The first declaration is forbidden if any required correction, validation or evidence remains incomplete.

## 11. One-Response Completion Requirement

Complete all ordinary in-scope work in this execution and return the implementation summary, repository commit, Build Report path, before/after reconciliation, validation evidence and any blockers in the same response. Do not request another Task Order for work already covered here.

**End of Task Order.**
