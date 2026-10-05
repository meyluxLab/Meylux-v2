# ADR-GOVERNANCE-014 — Required Capability Continuation & No-Drop Prerequisite Resolution

**Project:** Meylux V2  
**Status:** RATIFIED / AUTHORIZED  
**Stable ID:** `ADR-GOVERNANCE-014`  
**Decision Authority:** Project Owner  
**Decision Type:** Governance / Workflow / Completion Semantics  
**Scope:** Project-wide  
**Applies To:** All project Phases, Steps, Capabilities, Task Orders, runtime executions, verification cycles, and closure decisions where a required capability depends on a prerequisite.

## 1. Purpose

This ADR establishes a project-wide governance rule for situations in which a capability that is required by the current authoritative project scope cannot be fully established because one or more required prerequisites are missing, unavailable, unresolved, or not yet authoritative.

The governing principle is:

> **An unresolved prerequisite of a currently required capability is a problem to be resolved, not a permanent endpoint for that capability.**

This rule does not require fabricated evidence, synthetic data, unjustified fallback behavior, premature architectural changes, or silent reinterpretation of truthful runtime limitations.

The purpose of this ADR is to ensure that:

1. truthful incomplete runtime results remain truthful;
2. incomplete runtime results are not incorrectly treated as completed required capabilities;
3. required capabilities are not silently abandoned because a prerequisite is missing;
4. corrective work remains bounded to the identified problem;
5. historical evidence remains immutable;
6. retrospective review can distinguish legitimate outcomes from unresolved required capability gaps; and
7. governance, implementation, verification, and closure remain clearly separated.

## 2. Decision

The project adopts the following mandatory rule:

### 2.1 Required capability continuation

When a capability remains within the authoritative required boundary and a prerequisite necessary to establish that capability is unresolved, the unresolved prerequisite creates an explicit **resolution obligation**.

The capability shall not be treated as permanently abandoned merely because the prerequisite is currently unavailable.

The existence of an incomplete runtime result does not itself authorize closure of the required capability.

The resolution obligation shall remain explicit until one of the following occurs:

1. the prerequisite is genuinely resolved and the capability is subsequently verified;
2. the capability is formally removed from the required boundary through the applicable governance authority; or
3. an authoritative governance decision determines that the capability was never actually required within the relevant boundary.

No silent abandonment is permitted.

## 3. Runtime Status Is Not Capability Completion Status

The project formally distinguishes:

> **RUNTIME STATUS ≠ CAPABILITY COMPLETION STATUS**

### 3.1 Runtime status

Runtime status describes what an execution actually established, given the evidence, inputs, prerequisites, and environment available at that execution.

Examples include, where truthful:

- `COMPLETE`
- `PARTIAL`
- `INSUFFICIENT_DATA`
- `UNAVAILABLE`
- `UNAVAILABLE_INPUT`
- `SKIPPED`
- other formally defined truthful execution states.

These statuses must describe actual runtime truth.

### 3.2 Capability completion status

Capability completion status describes whether the intended capability has satisfied its authoritative:

- requirements;
- prerequisites;
- required behaviors;
- acceptance conditions;
- architectural constraints;
- evidence requirements; and
- independent verification requirements.

Therefore, a truthful runtime state such as `PARTIAL` or `INSUFFICIENT_DATA` may be the correct result of an execution while simultaneously meaning that a required capability remains unresolved.

A runtime status must never be silently promoted into capability completion merely because the execution itself completed.

Conversely, a runtime limitation must not be rewritten merely to make capability completion appear successful.

## 4. Missing Prerequisite Creates an Explicit Resolution Obligation

When a required prerequisite is missing or unresolved, the governing record for the affected capability shall make the following explicit, to the extent applicable:

1. **Affected capability**
2. **Computable / verifiable portion**
3. **Uncomputable / unverifiable portion**
4. **Exact reason for the limitation**
5. **Missing or unresolved prerequisite**
6. **Required resolution path or resolution question**
7. **Responsible governance or implementation boundary**
8. **Evidence required to establish resolution**
9. **Acceptance consequence**
10. **Relationship to the capability's completion condition**

The record must distinguish what is known from what is not known.

It must not replace the missing prerequisite with an invented value, synthetic evidence, unjustified assumption, or unapproved fallback.

## 5. Preservation of Truthful Incomplete States

This ADR does **not** prohibit incomplete runtime states.

Truthful incomplete states remain mandatory where the evidence warrants them.

The project shall preserve the distinction between:

- successfully established facts;
- partially established behavior;
- unavailable evidence;
- unresolved prerequisites;
- uncomputable portions;
- failed verification; and
- genuinely completed capability.

A limitation is not a defect merely because it prevents completion.

The governance defect occurs when a known limitation is treated as if it permanently satisfies, closes, or removes a still-required capability without the required authority and evidence.

## 6. No Fabrication or Synthetic Completion

Nothing in this ADR authorizes:

- fabricated market data;
- fabricated provider responses;
- synthetic production evidence represented as authoritative external evidence;
- invented prerequisite satisfaction;
- hard-coded values solely to satisfy acceptance;
- unjustified fallback values;
- silent data repair;
- silent provider substitution;
- silent contract/schema alteration;
- or any other mechanism whose primary effect is to make an unresolved capability appear complete without establishing its real prerequisite.

Where authoritative evidence does not exist, the project shall record that fact truthfully and resolve the underlying problem through governed work.

## 7. Bounded Corrective Expansion

Resolving an identified missing prerequisite may require work outside the immediate implementation boundary of the affected capability.

Such expansion is permitted only where it is necessary to resolve the identified prerequisite.

The expansion shall be:

- explicitly bounded;
- traceable to the unresolved prerequisite;
- outcome-driven rather than implementation-prescriptive;
- consistent with the architecture hierarchy;
- subject to the applicable authorization;
- independently verifiable; and
- limited to what is necessary to establish the required capability.

This rule does **not** authorize unrelated scope expansion.

Potentially useful but unrelated improvements shall remain outside the corrective boundary and follow the normal governance process.

## 8. Formal Removal from the Required Boundary

A required capability may cease to create a resolution obligation only when its removal from the applicable required boundary is formally authorized.

Such removal must not be inferred from:

- implementation difficulty;
- missing data;
- provider limitations;
- failed runtime execution;
- `PARTIAL`;
- `INSUFFICIENT_DATA`;
- `UNAVAILABLE`;
- or any other runtime status.

Where removal requires an Owner decision, architectural decision, requirement change, or other formal governance action, the workflow shall stop at that decision boundary rather than silently treating the capability as optional.

## 9. Historical Evidence Preservation

Historical evidence is immutable unless a separately governed correction mechanism explicitly permits a correction to the historical record.

This ADR does not authorize rewriting:

- Build Reports;
- Audit Reports;
- Task Orders;
- runtime evidence;
- test evidence;
- execution logs;
- historical status records;
- closure records;
- registry history;
- or other evidence-bearing artifacts.

A later discovery that a capability remained unresolved does not make the original truthful runtime evidence false.

Instead:

> **New evidence establishes the later state; it does not retroactively manufacture a different historical execution.**

Where a historical completion or closure decision requires retrospective reassessment, the reassessment shall be recorded as a distinct governed artifact and shall preserve the original evidence unchanged.

## 10. Retrospective Review Rules

When this ADR is applied retrospectively, each potentially affected historical capability shall be individually classified.

### A — No Impact

The capability was not required within the authoritative boundary applicable to that work.

No corrective capability work is required.

### B — Legitimate Investigation / Disposition

The Task Order's actual objective was investigation, discovery, availability assessment, or disposition rather than delivery of the capability itself.

A truthful `UNAVAILABLE` or equivalent disposition may therefore be a legitimate completion of that investigation objective.

This does not establish delivery of a separate capability that remains required elsewhere.

### C — Resolved Upstream Dependency

The prerequisite was subsequently resolved through authoritative work and evidence.

The historical record remains unchanged.

The later evidence is linked to the affected capability so that the resolution chain is traceable.

### D — Unresolved Required Prerequisite

The capability was required, the prerequisite remained unresolved, and the historical completion semantics did not adequately preserve that unresolved capability obligation.

A bounded corrective assessment and, where required, corrective implementation shall be initiated.

### E — Boundary Ambiguity

The evidence does not establish whether the capability was actually required.

No assumption shall be made.

The matter shall be escalated to the authority required to determine the applicable boundary.

### F — Architectural / Contract Conflict

Resolution would require changing a frozen architectural invariant, authoritative contract, schema, or other protected project constraint.

The affected work shall stop at that conflict boundary and proceed through the applicable change-control / ADR process.

No silent architectural resolution is permitted.

## 11. Corrective Work Governance

Retrospective classification does not itself authorize implementation.

Where corrective work is required:

1. the affected capability and unresolved prerequisite shall be identified;
2. the required outcome shall be defined;
3. the technical cause shall be assessed using authoritative evidence;
4. the minimum necessary corrective boundary shall be determined;
5. architectural, contract, schema, security, data, infrastructure, and provider implications shall be assessed as applicable;
6. a governed Task Order shall define the authorized work;
7. the Producer shall implement only that authorized scope;
8. the Producer shall provide its Build Report and evidence;
9. CONTROL shall independently verify the result;
10. only CONTROL shall perform the applicable closure synchronization.

The corrective mechanism must not prescribe a technical solution before evidence establishes what the actual prerequisite problem is.

## 12. Outcome-Driven Corrective Scope

A corrective Task Order created under this ADR shall define the required outcome and acceptance conditions without prematurely prescribing an implementation mechanism unless the mechanism is already authoritative.

The assessment must determine, rather than assume, whether resolution requires any particular combination of:

- data availability;
- upstream acquisition;
- provider capability;
- transformation or derivation;
- persistence;
- schema or contract behavior;
- infrastructure;
- configuration;
- verification;
- or another project component.

No specific provider, data source, calculation, database modification, schema modification, or architectural change shall be treated as mandatory merely because it appears technically convenient.

## 13. Relationship to ADR-GOVERNANCE-012

ADR-GOVERNANCE-012 remains authoritative for closure synchronization and closure ownership.

Application of this ADR does not transfer closure authority away from CONTROL.

Where a corrective cycle reaches a legitimate Step or Phase closure boundary, CONTROL remains responsible for the complete closure synchronization cycle, including the applicable:

- checkpoint;
- README;
- artifact registry;
- specialized registries;
- status-bearing documents;
- change ledger;
- and related governance records.

No Producer action under this ADR may partially perform or pre-empt that CONTROL-owned closure synchronization.

## 14. Relationship to ADR-GOVERNANCE-013

This ADR operates consistently with ADR-GOVERNANCE-013.

In particular:

### R1 — Continuation

Where authority, information, and evidence are sufficient, an unresolved required prerequisite is not by itself a reason to halt the workflow permanently.

Authorized corrective work shall continue to the farthest legitimate point reachable within the current governance boundary.

The workflow stops only at an applicable legitimate boundary, including:

- Owner decision or ratification;
- unresolved authoritative conflict;
- or a natural completion boundary requiring independent verification.

### R2 — Communication

Where a continuation, corrective action, escalation, or governance decision is required, the applicable formal communication shall be produced in the same workflow cycle.

### R3 — Large Artifacts

Large evidence-bearing artifacts shall be retrieved completely through the governed large-artifact procedure before decisions are made from them.

### R4 — VPS Operations

Any real VPS operation remains subject to the SentinelX-only rule and existing authorization boundaries.

### R5 — Evidence and Correctness

No capability may be declared complete merely because a minimal or superficial test passes.

Independent verification remains required.

## 15. Governance Lifecycle

The normative lifecycle established by this ADR is:

**Required Capability**  
→ **Prerequisite Assessment**  
→

**Prerequisites Available and Authoritative**  
→ compute / execute / verify capability  
→ independent verification  
→ capability completion when all conditions are satisfied

OR

**Prerequisite Missing / Unresolved**  
→ preserve truthful runtime result  
→ explicitly record resolution obligation  
→ determine bounded corrective path  
→ authorize corrective Task Order  
→ resolve prerequisite  
→ obtain new evidence  
→ independently verify capability  
→ complete capability when acceptance conditions are satisfied

OR

**Capability Formally Removed from Required Boundary**  
→ preserve historical evidence  
→ record authoritative boundary decision  
→ no further capability-resolution obligation under that boundary.

## 16. Non-Goals

This ADR does not:

- redesign the project architecture;
- define a particular data provider;
- mandate a particular acquisition mechanism;
- mandate a particular database schema;
- mandate a particular calculation or derivation;
- redefine truthful runtime statuses;
- invalidate historical evidence;
- automatically reopen previously closed work;
- authorize implementation by itself;
- or replace existing architecture, contract, security, or change-control governance.

## 17. Consequences

### Positive Consequences

This ADR:

- prevents unresolved required capabilities from disappearing behind runtime status labels;
- preserves truthful incomplete execution results;
- prevents fabricated completion;
- provides a reusable project-wide corrective mechanism;
- makes retrospective assessment deterministic and classifiable;
- permits bounded dependency resolution without uncontrolled scope expansion;
- preserves historical evidence;
- and maintains the separation between Governance, implementation, verification, and closure.

### Governance Cost

Applying this rule may create additional retrospective assessment and corrective work where historical completion was accepted despite an unresolved required prerequisite.

That cost is intentional.

The project accepts the cost of resolving genuine capability gaps rather than treating missing prerequisites as permanent endpoints.

## 18. Ratification

The Project Owner reviewed and accepted the revised project-wide structure and explicitly authorized formal ratification of this ADR as the normative governance rule.

**Decision:** RATIFIED / AUTHORIZED.

This ratification does not reopen previously closed work, modify historical evidence, authorize corrective implementation, or authorize unrelated project-state mutation.

## 19. Authoritative Principle

> **A truthful incomplete runtime result must remain truthful, but a missing prerequisite of a capability that the project still requires must remain an explicit problem to resolve until the capability is genuinely established or its required boundary is formally changed.**
