# Meylux V2 — Artifact Protocol

Status: Ratified Operational Protocol

## Official artifact chain

`TASK-ORDER (TO) → BUILD-REPORT (BR) → AUDIT-REPORT (AR) → EXEC-LOG (EL) → CHECKPOINT (CHK)`

## Rules

1. Every official artifact has a stable ID.
2. Artifact content is not authoritative merely because it appears in chat.
3. Approved artifacts and verified evidence are recorded in the repository.
4. No silent edits.
5. Anything not actually executed is explicitly marked unverified or not executed.
6. Stable IDs and artifact sequence records are governance-controlled; previously registered identities and historical records are immutable.

## Phase 0 Operational Artifact Convention

For Producer Build Reports, the governed identity/path convention is:

- Stable ID form: `BR-P<phase>-<sequence>`.
- The sequence is monotonically increasing within the applicable Phase and must not collide with an existing registered BR identity.
- The Build Report is produced by the Producer and remains `ALLOCATED / NOT YET PRODUCED` until allocation is recorded and the actual report is created. Production does not imply verification.
- The repository artifact registry is the authoritative source for BR identity, path, and traceability.

## Producer Build Report Allocation Delegation

Under `ADR-GOVERNANCE-003`, `ROL-V2-002 — PRODUCER / ARCHITECT-BUILDER` has limited authority to allocate the next Build Report identity required for its own currently authorized Task Order.

The Producer allocation procedure is:

1. Confirm the current Task Order is `AUTHORIZED TO EXECUTE` and is the sole active Task Order for the Producer's Step.
2. Read the current `docs/registry/artifacts.yaml` from the repository Source of Truth immediately before allocation.
3. Determine the next unused integer sequence for the current Phase using only registered BR identities.
4. Confirm that the proposed BR identity and canonical path do not already exist.
5. Add exactly one BR registry record containing the stable ID, canonical name, `entity_type: BR`, artifact path, and traceability to the current Task Order / Step / Phase.
6. Preserve every existing registry record and use repository content-version protection; do not force-overwrite concurrent registry changes.
7. Create the Build Report at the registered path and keep its state distinguishable from `VERIFIED`.
8. If the registry write is rejected because its source content is stale, re-read the authoritative registry, recompute the next unused sequence, and retry without overwriting concurrent changes.
9. If any ambiguity exists about authorization, sequence ownership, or collision, stop the allocation and report the exact blocker to CONTROL.

## Delegation Boundaries

The Producer MAY allocate only a BR for the Producer's own currently authorized Task Order. The Producer MUST NOT:

- allocate BR identities for unauthorized, future, inactive, or completed work;
- allocate artifact types other than BR under this delegation;
- modify or renumber previously registered BR identities;
- modify historical artifact records;
- alter the BR naming convention or Stable ID rules;
- modify Architecture, ADRs, Governance rules, Phase/Step authorization, or unrelated registry records as part of allocation;
- approve, audit, verify, close, ratify, or freeze its own work;
- activate future Steps or issue future Task Orders;
- perform runtime, V1/VPS, market-data, trading, capital, fund-transfer, or provider-runtime actions.

## EXEC-LOG Operational Convention

The existing `EXEC-LOG (EL)` element of the official artifact chain is operationalized by this repository convention. This section clarifies the concrete record convention without creating a new artifact class, governance subsystem, Stable ID, lifecycle state, or parallel execution/evidence framework.

An actual EXEC-LOG record is created only when an authorized execution occurs. Its operational record identity is `execution_id`; this is execution/evidence identity and is not a Project Stable ID.

The repository-backed EXEC-LOG record MUST be capable of representing, at minimum:

```text
execution_id
task_id
step_id
target
executor_role
start_time_utc
end_time_utc
actions
commands
outputs
exit_codes
failures
diagnosis
remediation
retries
final_result
evidence_references
escalation_status
authorization_reference
verification_reference
repository/version_context
```

The record MUST contain actual observed execution evidence only. No field may be populated with fabricated runtime values. Where a field is not applicable or not available from the actual execution, that fact remains explicit rather than being replaced by invented data.

EXEC-LOG records MUST remain traceable to the applicable Task Order and repository/version context. They represent execution evidence and do not by themselves establish verification, approval, closure, ratification, or freeze.

For the current TO-GOV-003 implementation activity, no EXEC-LOG runtime record is created because no VPS execution is performed. `CURRENT_CHECKPOINT` is not changed by establishing this convention.

## Independent Verification

CONTROL / REVIEWER (`ROL-V2-001`) remains the independent audit and verification authority. A Producer allocation or Build Report production is never a `VERIFIED` state. Step completion requires the existing independent audit and verification process.

## Governance Basis

The delegation is established by `ADR-GOVERNANCE-003`, ratified by the Project Owner under `ADR-GOVERNANCE-001`. It is an operational clarification of this existing Artifact Protocol and does not create a new governance subsystem, role, artifact class, or approval mechanism.

This protocol does not ratify/freeze the Master Architecture, alter the Phase 0 sequence, reopen G-0/G-0R, or authorize runtime or V1 activity.

## Mandatory Peripheral Synchronization Checklist

Established by `ADR-GOVERNANCE-012`, in direct response to the root-cause
finding of `TO-GOV-008` (README and Registry status drift discovered
after Phase 2 closure).

Every Task Order that closes a Step or Phase MUST include the following
checklist in its Required Output section, and the corresponding Build
Report MUST report against each item individually before the Step/Phase
may be declared `CLOSED / VERIFIED`:

1. `README.md` — does its repository-status summary still match
   `CURRENT_CHECKPOINT.json` after this closure? If not, correct it as
   part of THIS Task Order, not a deferred cleanup task.

2. `docs/registry/artifacts.yaml` — does the record for any Role,
   Component, Contract, or other artifact that was exercised, created,
   or verified in this Step still carry a stale pre-activation status
   (e.g. `DRAFT_PRE_PHASE_0`)? If so, correct it now, using only
   already-established repository vocabulary.

3. Specialized registries (`components.yaml`, `contracts.yaml`,
   `requirements.yaml`, `tests.yaml`, `runtime.yaml`, `database.yaml`,
   `security.yaml`, `configuration.yaml`, `performance.yaml`,
   `observability.yaml`) — did this Step produce evidence (test counts,
   CI runs, schema changes, security controls, configuration records)
   that belongs in one of these files but was only reported in the
   Build Report? If so, transcribe it now with a direct evidence
   reference. Do not defer to a future cleanup task, and do not
   populate any record without a direct evidence reference.

4. Any standalone status-bearing document referenced by this Step's
   architecture basis (for example, a design/lessons-learned document
   later absorbed into a ratified document) — does its own Status line
   still reflect a pre-absorption state? If so, correct it when
   evidence supports the correction, or raise it explicitly as an Open
   Question when it does not. Do not leave it silently stale.

5. Any supplemental/staging registry created earlier in the current
   Phase (for example, a `SUPPLEMENTAL / ACTIVE` index) — has its
   content now been fully absorbed into the canonical registry? If so,
   mark it superseded/retired using existing vocabulary rather than
   leaving it indefinitely active.

A Step/Phase-closure Build Report that omits this checklist, or that
addresses it without individually confirming each of the five items,
is INCOMPLETE regardless of how correct its primary implementation
evidence is, and must not be accepted as `CLOSED / VERIFIED` by CONTROL.

This checklist does not expand CONTROL or Producer authority, does not
create a new artifact class, role, or lifecycle state, and does not by
itself authorize any Phase, Step, VPS, or runtime action. It is a
reporting and consistency obligation attached to existing Step/Phase
closure authority only.

## Governance Basis — Checklist Amendment

This checklist is established by `ADR-GOVERNANCE-012`, ratified by the Project Owner. It is an operational clarification of this existing Artifact Protocol and does not create a new governance subsystem, role, artifact class, or approval mechanism, consistent with the precedent already set by the "Governance Basis" section above for `ADR-GOVERNANCE-003`.

## Standing Role Operating Rules

Established by `ADR-GOVERNANCE-013`, ratified and amended by the Project Owner.  
`ADR-GOVERNANCE-014` remains the authoritative normative decision for required-capability No-Drop semantics.

### Canonical R1–R7 Operating Set

The following seven Rules are the single canonical operational interpretation for governed CONTROL, PRODUCER, and PROJECT GUIDE work. This section is an operational rendering of `ADR-GOVERNANCE-013`; it does not create a competing rule system.

**R1 — Continuation & Genuine Resolution**  
Continue authorized work to the farthest legitimate point supported by sufficient authority, information, and evidence. Ordinary difficulty, additional analysis, normal test failure, or discovery of additional authorized corrective work is not by itself a stop. Stop only at the applicable ADR-013 A/B/C boundary. The objective is genuine resolution, not superficial patching, fixture-passing, reclassification, documentation substitution, or happy-path completion.

**R2 — Same-Response Communication & Governed Handoff**  
When continuation requires a hand-off, clarification, escalation, correction, Task Order, or other inter-role communication, the complete forward-ready communication must be produced in the same response. CONTROL→Producer hand-offs preserve outcome, requirements, evidence expectations, constraints, and authorized boundary. Producer→CONTROL reporting preserves the evidence required for independent governance and verification.

**R3 — Complete Artifact & Evidence Integrity**  
Large artifacts must use the identify → Blob SHA → fetch_blob → complete read/verify process. No substantive claim may rely on truncated content. Preserve the lifecycle distinction `DESIGNED ≠ IMPLEMENTED ≠ EXECUTED ≠ TESTED ≠ VERIFIED ≠ FROZEN ≠ CLOSED`. Evidence must be appropriate to the exact claim; synthetic, inferred, fabricated, or unjustified evidence may not substitute for authoritative evidence. Repository/CI evidence is not sufficient where authoritative runtime/VPS evidence is materially required.

**R4 — No-Drop & Prerequisite Resolution**  
A missing, unavailable, or unresolved prerequisite of a still-required capability is a resolution obligation, not a permanent endpoint. Preserve truthful incomplete state, determine the bounded corrective path, continue authorized resolution, and do not silently drop or optionalize the capability. No fabricated, synthetic, unjustified, or silently repaired fallback is permitted. `ADR-GOVERNANCE-014` is the normative source for this rule.

**R5 — VPS / Runtime / SentinelX**  
Where runtime evidence or implementation activity genuinely requires VPS access, use SentinelX only and only within existing authorization. Producer may perform necessary authorized runtime diagnostics/activity within the Task Order boundary; CONTROL must not artificially substitute repository/CI evidence where governed runtime evidence is materially required. SentinelX availability is never authorization by itself.

**R6 — Architecture, Contract, Scope & Role Authority**  
Preserve the architecture hierarchy, contracts, schemas, Stable IDs, governance boundaries, and ratified decisions. CONTROL retains project-level governance, Task Order, audit, verification, and closure authority. Producer retains implementation-level design authority within the authorized boundary. Neither role may silently convert implementation discretion into project-level authority or expand scope. Genuine higher-authority conflict follows the applicable change-control path.

**R7 — Quality, Edge Cases, Regression & Closure Integrity**  
Apply the maximum-quality standard within the authorized boundary. Cover applicable missing, malformed, boundary, contradictory, failure/recovery, persistence, replay, regression, and evidence cases. Passing a happy path is not sufficient. Before Step/Phase verification or closure, CONTROL must complete the full `ADR-GOVERNANCE-012` synchronization, including applicable Checkpoint, README, artifacts registry, specialized registries, status-bearing documents, and staging/supplemental disposition.

### Mandatory R1–R7 Finalization Cycle

For every applicable response or governed work product, the responsible role must execute:

**DRAFT → R1–R7 REVIEW → CORRECTIVE REVISION → FINALIZE**

1. **Draft** the complete required response/work product.
2. **Review** the complete draft against all seven Rules, not only the obviously relevant ones.
3. **Correct** every applicable omission, contradiction, premature stop, unsupported claim, evidence deficiency, scope/authority problem, edge-case gap, governance inconsistency, or closure deficiency identified by the review.
4. **Finalize** only the corrected version.

Appending the Rules or merely stating that they were considered does not satisfy this cycle. The cycle applies independently to CONTROL and Producer within their existing authorities and creates no new authority or scope.

### Mandatory Standing Rules Footer

Every substantive response from a governed role must terminate with a current, regenerated footer. The footer is a reporting/check mechanism only and never grants authority:

```text
--- STANDING RULES CHECK ---
R1 Continuation: <CONTINUING | STOPPED(A) | STOPPED(B) | STOPPED(C)> — <one line>
R2 Hand-off: <NONE REQUIRED | INCLUDED ABOVE> — <recipient role + type>
R3 Artifact/Evidence integrity: <APPLIED | N/A> — <large-artifact method / evidence boundary>
R4 No-Drop/Prerequisite resolution: <APPLIED | N/A> — <resolution obligation state>
R5 VPS/SentinelX: <N/A | used for: ...>
R6 Architecture/Scope/Role authority: <APPLIED | N/A> — <one line>
R7 Quality/Edge/Regression/Closure: <APPLIED | N/A> — <one line>
G12 Peripheral sync: <N/A | CHECKED | PENDING AT STEP CLOSURE>
Phase/Step: <current> | Active TO: <id or null>
```

`R2 INCLUDED ABOVE` is valid only when the required message actually appears above. G12 remains an explicit closure-sync check even though its underlying requirement is incorporated into R7.

## Required Capability Continuation & No-Drop Prerequisite Resolution

Established by `ADR-GOVERNANCE-014`, ratified by the Project Owner.

### Normative rule

Where a capability remains within the authoritative required boundary and a prerequisite necessary to establish that capability is missing, unavailable, unresolved, or not yet authoritative, that prerequisite creates an explicit **resolution obligation**. It is not a permanent completion endpoint and the required capability may not be silently abandoned.

### Runtime status versus capability completion

**RUNTIME STATUS ≠ CAPABILITY COMPLETION STATUS.** Runtime status records what an actual execution established under the evidence and prerequisites available at that execution. Capability completion records whether the intended capability satisfied its authoritative requirements, prerequisites, acceptance conditions, evidence requirements, and independent verification requirements.

Truthful states such as `PARTIAL`, `INSUFFICIENT_DATA`, `UNAVAILABLE`, `UNAVAILABLE_INPUT`, or `SKIPPED` remain valid where they accurately describe execution. They do not, by themselves, establish completion of a currently required capability.

### Resolution obligation

For an unresolved required prerequisite, the affected record must preserve, as applicable: the affected capability; computable/verifiable portion; uncomputable/unverifiable portion; exact limitation; missing prerequisite; resolution question/path; responsible boundary; evidence required for resolution; and acceptance consequence.

No fabricated value, synthetic evidence presented as authoritative, unjustified fallback, silent data repair, or silent provider/contract/schema substitution may be used to manufacture capability completion.

### Bounded corrective work

Corrective expansion is permitted only to the extent necessary to resolve the identified prerequisite and establish the required capability. It must remain bounded, outcome-driven, authorized, traceable, and independently verifiable. Unrelated improvements remain outside the corrective boundary.

A capability may cease to create a resolution obligation only when it is formally removed from the applicable required boundary through the proper governance authority. Runtime difficulty or an incomplete runtime status does not constitute such removal.

### Historical evidence and retrospective review

Historical Build Reports, Audit Reports, Task Orders, runtime evidence, execution evidence, statuses, closure records, and other evidence-bearing artifacts remain unchanged unless a separate governed correction mechanism explicitly authorizes otherwise. Later evidence establishes later state; it does not rewrite a historical execution.

Retrospective application of this rule must classify each affected case individually and distinguish: no impact; legitimate investigation/disposition; resolved upstream dependency; unresolved required prerequisite; boundary ambiguity; and architectural/contract conflict. Corrective classification does not itself authorize implementation.

### Governance relationships

`ADR-GOVERNANCE-012` remains authoritative for CONTROL-owned closure synchronization. `ADR-GOVERNANCE-013` remains authoritative for continuation, same-response communication, large-artifact retrieval, SentinelX-only VPS execution, and maximum-quality requirements. `ADR-GOVERNANCE-014` adds the required-capability continuation/no-drop semantic and does not replace or weaken those decisions.

This section does not authorize any Phase, Step, Task Order, VPS/runtime action, architectural change, or implementation by itself.
