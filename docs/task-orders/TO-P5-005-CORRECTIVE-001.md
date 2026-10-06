# TO-P5-005-CORRECTIVE-001 — S-12 Liquidity Causal-Resolution Investigation

**Task Order SID:** `TO-P5-005-CORRECTIVE-001`
**Project:** MEYLUX V2
**Phase:** `PH-P5`
**Historical Step Boundary:** `STEP-P5-005` — remains COMPLETE / VERIFIED
**Historical Task Order:** `TO-P5-005` — remains VERIFIED / COMPLETE
**Affected Capability:** `S-12 — Liquidity`
**Issuing Role:** `ROL-V2-001 — CONTROL / REVIEWER`
**Producer Role:** `ROL-V2-002 — PRODUCER / ARCHITECT-BUILDER`
**Status:** VERIFIED / COMPLETE
**Governance Basis:** `ADR-GOVERNANCE-012`, `ADR-GOVERNANCE-013`, `ADR-GOVERNANCE-014`
**Assessment Basis:** `DOC-P5-003`

## 1. Authority and Objective

This Task Order is the concrete governed continuation following the Project Owner directive of 2026-10-06.

Its objective is to establish the actual authoritative causal boundary behind the historical S-12 runtime condition:

`LIQUIDITY_POOL = 0` and `INSUFFICIENT_DATA`.

The investigation must determine whether the historical result represents:

1. no qualifying liquidity pool existed for the authoritative input boundary;
2. a qualifying pool existed but was not produced by the authoritative upstream boundary;
3. it was produced but not persisted;
4. it was persisted but not admitted into the P5 snapshot/input boundary;
5. the acceptance/input semantics are incomplete or incorrect; or
6. the available evidence is insufficient and a further precisely bounded investigation is required.

This Task Order does not presume that zero liquidity records constitute a defect. It also does not permit an unresolved prerequisite of a still-required capability to become a permanent endpoint.

No technical solution is selected in advance.

## 2. Historical Protection

The following remain immutable historical evidence and MUST NOT be reopened or rewritten by this Task Order:

- `STEP-P5-005`;
- `TO-P5-005`;
- `BR-P5-006`;
- `AR-P5-005`;
- `EXEC-LOG-TO-P5-005-CONTROL-RUNTIME-20261005`;
- the historical runtime snapshot and statuses.

The historical S-12 `INSUFFICIENT_DATA` result remains the truthful historical execution result.

This Task Order does not activate `STEP-P5-006`.

## 3. Required Evidence Chain

The causal investigation must trace, using authoritative evidence:

`historical S-12 snapshot`
→ `exact canonical candle boundary`
→ `authoritative P4 swing/liquidity semantics`
→ `P4 liquidity formation/sweep result`
→ `P4 persistence/read-back`
→ `P5 Input Snapshot admission`
→ `S-12 consumed fact surface`
→ `historical INSUFFICIENT_DATA result`.

For each transition, establish exact artifact/revision context, temporal boundary, provenance, identity, presence/absence state, and direct supporting evidence.

A zero count alone is not a causal explanation.

## 4. Causal Decision Tree

### Branch A — No qualifying pool

The authoritative canonical evidence contains no qualifying repeated same-side confirmed swing levels under the ratified P4 liquidity semantics.

Result: the zero-pool state is a truthful no-applicable-zone outcome unless another independent acceptance defect is established.

### Branch B — Pool existed but was not produced

The canonical evidence satisfies the authoritative formation conditions, but the upstream P4 boundary did not produce the expected fact.

Result: identify the exact upstream production/semantic boundary and evidence.

### Branch C — Pool produced but not persisted

The upstream boundary produced the fact, but authoritative persistence/read-back does not contain it.

Result: identify the exact persistence boundary and failure evidence.

### Branch D — Pool persisted but not admitted to P5

The fact exists authoritatively upstream but is absent from the governed P5 snapshot/input boundary.

Result: identify the exact admission/provenance boundary.

### Branch E — Acceptance/input semantics incomplete or incorrect

The authoritative fact is available, but the governing acceptance/input semantics cannot correctly consume or represent it.

Result: identify the exact semantic boundary and applicable governance/change-control consequence.

### Branch F — Evidence insufficient

The authoritative evidence cannot distinguish the branches.

Result: identify the minimum additional bounded evidence required. Do not select a technical fix merely because evidence is incomplete.

## 5. Required Questions

The investigation must establish, in order:

1. Is S-12 within the authoritative required capability boundary?
2. What exact canonical candle population constituted the historical input?
3. Did that population satisfy the authoritative liquidity formation conditions?
4. If yes, did the authoritative P4 boundary produce the corresponding fact?
5. If produced, was it persisted and readable?
6. If persisted, was it admitted into the P5 Input Snapshot?
7. If admitted, could S-12 acceptance semantics consume it correctly?
8. If unresolved, what exact evidence is required next?

The investigation must distinguish:
`RUNTIME STATUS` from `CAPABILITY COMPLETION STATUS`.

## 6. Authorized Scope

Only work necessary to establish the causal boundary is authorized.

This includes, where required:

- repository artifact and source inspection;
- historical evidence inspection;
- deterministic reproduction of existing semantics;
- inspection of existing tests and contracts;
- bounded CI/evidence execution;
- comparison of authoritative upstream/downstream fact boundaries;
- controlled runtime/persistence evidence inspection;
- SentinelX-only VPS inspection or action where genuinely required by the authorized evidence boundary;
- preparation of a complete causal Build Report.

If Producer execution is activated, Producer may use necessary VPS/runtime diagnostics and tests within this exact boundary; Producer is not artificially limited to repository/CI evidence.

## 7. Bounded Expansion Rule

Additional scope is permitted only when newly established evidence demonstrates that it is necessary to distinguish or resolve the causal branches above.

Permitted expansion must remain directly causally connected to the S-12 evidence boundary.

It must not become unrelated improvement.

A discovered requirement for a technical corrective implementation does not automatically authorize that implementation under this Task Order; CONTROL must establish the appropriate subsequent governed implementation boundary.

## 8. Explicit Exclusions

Unless separately authorized through the applicable governance path, this Task Order does not authorize:

- provider expansion or replacement;
- new acquisition mechanisms;
- synthetic or fabricated liquidity data;
- fallback data presented as authoritative;
- P4 mathematical redesign;
- P4 reopening or historical P4 closure modification;
- P5-005 reopening;
- P5 specialist redesign;
- database/schema/migration implementation merely as an investigative shortcut;
- `STEP-P5-006` or later Phase-5 work;
- unrelated refactoring;
- trading, capital, custody, execution, or decision authority.

No provider, calculation, database, schema, contract, migration, or acquisition mechanism may be selected before its causal necessity is established.

## 9. Producer Boundary

If activated for Producer execution, Producer shall:

- perform the authorized causal investigation;
- preserve historical evidence;
- distinguish facts, hypotheses, and unresolved questions;
- continue to the farthest legitimate evidence boundary under ADR-GOVERNANCE-013 R1;
- use VPS/runtime evidence when necessary and only through SentinelX;
- provide a complete Build Report with direct evidence for each causal conclusion;
- state contradictory or insufficient evidence explicitly;
- make no VERIFIED / COMPLETE / CLOSED declaration;
- perform no CONTROL-owned closure synchronization.

Producer retains implementation-level design authority only within the activated investigation boundary.

## 10. Required Build Report Evidence

The Build Report must establish, as applicable:

1. exact repository revision(s) examined;
2. exact historical runtime/snapshot context;
3. exact canonical candle population;
4. authoritative liquidity formation/sweep semantics applied;
5. P4 production result;
6. P4 persistence/read-back result;
7. P5 Input Snapshot admission result;
8. S-12 input/result relationship;
9. provenance and temporal evidence;
10. contradictory evidence, if any;
11. exact causal branch selected, or precise evidence insufficiency;
12. every bounded expansion and why it was necessary;
13. confirmation that no historical evidence was rewritten;
14. confirmation that no technical solution was prematurely selected;
15. exact recommended next governed action.

Unit tests alone are insufficient where authoritative runtime/persistence evidence is required.

## 11. CONTROL Verification Boundary

After Producer delivery, CONTROL shall independently verify the causal evidence against the authoritative repository/runtime evidence.

CONTROL may perform SentinelX-only runtime verification where required.

CONTROL must independently establish whether the claimed causal branch is actually supported.

CONTROL shall not describe its own authorship review of `DOC-P5-003` as independent verification.

CONTROL retains responsibility for all governance disposition and closure synchronization.

## 12. Acceptance Criteria

This Task Order reaches its investigation completion boundary only when CONTROL can determine from authoritative evidence that:

- the historical input boundary is known;
- the authoritative liquidity semantics are correctly applied;
- the zero-pool condition is classified as either:
  - a truthful no-qualifying-pool condition;
  - upstream production failure;
  - persistence failure;
  - P5 admission/input failure;
  - acceptance/semantic deficiency; or
  - demonstrably unresolved evidence requiring a precisely bounded next investigation;
- the conclusion is supported by direct evidence;
- no fabricated/synthetic/unjustified fallback was introduced;
- historical P5-005 evidence remains unchanged;
- no technical implementation solution was assumed prematurely;
- the next governed action is explicit.

A successful investigation does not require a non-empty `LIQUIDITY_POOL` result.

## 13. Stopping Conditions

Under ADR-GOVERNANCE-013 R1, ordinary difficulty, additional bounded analysis, or normal test failure is not a stopping condition.

Stop only when:

**STOP(A):** an actual Owner decision/ratification is required;

**STOP(B):** authoritative sources materially conflict and cannot be reconciled without guessing; or

**STOP(C):** the causal investigation has reached a complete evidence-backed conclusion requiring independent verification by another role.

Any stop must identify the exact decision/conflict/evidence boundary.

## 14. Completion and Follow-On Path

This Task Order does not reopen or reclassify the historical closure.

Possible outcomes:

- truthful no-pool condition → no defect is invented; any remaining capability question is separately governed;
- proven upstream defect → CONTROL defines the minimum bounded corrective implementation Task Order;
- proven persistence defect → CONTROL defines the minimum bounded corrective implementation Task Order;
- proven P5 admission defect → CONTROL defines the minimum bounded corrective implementation Task Order;
- proven acceptance semantic deficiency → CONTROL applies the required governance/change-control path;
- insufficient evidence → next bounded investigation is defined;
- architectural/contract conflict → affected portion stops under the applicable change-control path.

Any implementation arising from the investigation requires an explicit subsequent governed boundary unless the applicable authorized Task Order scope is formally extended through the required authorization mechanism.

## 15. Governance and Closure

`ADR-GOVERNANCE-012` remains the sole authority for CONTROL-owned closure synchronization.

Producer must not update:

- `CURRENT_CHECKPOINT.json`;
- `artifacts.yaml`;
- README status;
- specialized lifecycle registries;
- Change Ledger closure records;
- standalone closure status.

If this Task Order reaches its legitimate completion boundary, CONTROL performs the applicable audit and synchronization cycle.

## 16. Current Governance State

At activation/read-back time:

- `PH-P5 = ACTIVE / AUTHORIZED`;
- `STEP-P5-005 = COMPLETE / VERIFIED`;
- `TO-P5-005 = VERIFIED / COMPLETE`;
- `active_task_order = TO-P5-005-CORRECTIVE-001`;
- `DOC-P5-003 = PRODUCED / UNVERIFIED`;
- causal classification remains unresolved pending authoritative investigation.

This Task Order is **AUTHORIZED TO EXECUTE** and Producer execution is activated under the Owner's explicit full-authority directive.

## 17. Definition of Done

The actual causal state of the historical S-12 `LIQUIDITY_POOL = 0 / INSUFFICIENT_DATA` condition is established from authoritative evidence, or the evidence insufficiency is itself precisely demonstrated with a bounded next evidence requirement.

The required outcome is truthful causal resolution, not manufactured liquidity data and not a predetermined technical patch.

**Producer execution is active under this Task Order.**


## CONTROL Activation Record — 2026-10-06

Project Owner has explicitly granted CONTROL full authority to proceed within the stated project boundary and authorized continuation of this concrete corrective path.

**Activation disposition:** AUTHORIZED TO EXECUTE  
**Active Task Order:** `TO-P5-005-CORRECTIVE-001`  
**Producer execution:** ACTIVATED  
**Historical `STEP-P5-005` / `TO-P5-005` closure:** PRESERVED  
**`STEP-P5-006`:** NOT ACTIVATED

The Producer shall proceed through the complete causal-resolution investigation and evidence-generation boundary defined above. Producer shall deliver the required Build Report and shall not declare VERIFIED / COMPLETE / CLOSED. CONTROL retains independent verification, VPS/SentinelX, scope-control and closure-synchronization authority.
