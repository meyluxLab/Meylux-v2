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

Established by `ADR-GOVERNANCE-013`, ratified by the Project Owner.

### Rule 1 — Continuation Duty

A role must continue governed work to the highest genuinely authorized boundary available to it, without unnecessary re-authorization round-trips.

Difficulty, additional required analysis, an ordinary implementation problem, or a normal test failure requiring diagnosis are not blockers.

Stopping is justified only when one of exactly three conditions is met:

- **(A)** an actual Project Owner decision or ratification is required;
- **(B)** an actual conflict between authoritative sources exists that cannot be resolved without guessing;
- **(C)** the governed unit of work has naturally ended and requires independent verification by another role.

When stopping, the role must state explicitly which of A, B or C applies, and precisely what decision or evidence is required to resume. A role must never end a response with "Should I continue?" or an equivalent while authorized work remains within its own boundary.

### Rule 2 — Same-Response Communication Duty

This rule applies to every governed role without exception, including `ROL-V2-001`, `ROL-V2-002`, and `ROL-V2-008`. Whenever the outcome of a role's work requires any text to be carried to another governed role, the role must produce the complete, forward-ready text inside the same response. This includes formal artifacts, intermediate or informal messages, clarifications, escalations, conflict reports, scope questions, blocker notifications, partial-progress hand-offs, prompts, bootstrap texts, directives, and answers to role-to-role questions.

The formality of the structure scales with the formality of the message, but the same-response obligation does not. For substantive hand-offs the required structure is:

```text
FORMAL ENGLISH MESSAGE READY TO SEND
↓
SIMPLE PERSIAN EXPLANATION
```

For brief intermediate messages, the English message may be correspondingly short but must remain self-contained and must not invent Architecture, Scope, Stable IDs, Contracts, or Requirements lacking repository basis. Formal governed artifacts must follow the applicable existing repository conventions.

### Rule 3 — Large Artifact Retrieval Method

For any repository artifact too large to be retrieved completely in a single ordinary read, the role must use:

```text
Identify artifact
        ↓
Obtain real Blob SHA
        ↓
fetch_blob
        ↓
Retrieve complete artifact
        ↓
Read / search / verify
```

This workflow has been empirically verified across `ROL-V2-001`, `ROL-V2-002`, and `ROL-V2-008` against `MASTER_ARCHITECTURE_V2.md`, `artifacts.yaml`, and `CURRENT_CHECKPOINT.json`.

Proceeding on truncated content, or claiming an artifact was reviewed when only partial retrieval occurred, constitutes Fabrication under the existing Evidence Policy. Rule 3 provides the governed means to retrieve full content before an otherwise authorized complete write.

This rule establishes a method, not new authority. It does not itself authorize any Phase, Step, Task Order, repository mutation, or VPS action.

### Rule 4 — SentinelX-Only VPS Execution

Any work that genuinely requires inspection or action on the VPS must be performed exclusively through the SentinelX tool under the existing privilege model established by `ADR-GOVERNANCE-011`. No alternative or manual VPS access path is permitted as a substitute.

Availability of SentinelX does not by itself create new authority to change VPS or runtime state. It is the governed method for exercising VPS-related authority already existing within an authorized Task Order boundary.

### Rule 5 — Maximum Quality and Success-Rate Standard

Every part of the system — architecture choices made within an authorized boundary, implementation design, validation depth, test coverage, edge-case handling, documentation, and closure evidence — must be built to the maximum achievable standard of correctness, robustness, and efficiency, aimed at the highest realistically attainable success rate for the finished product. Satisfying only the minimum requirement to pass is not sufficient.

This rule governs quality *within* an authorized boundary; it never expands scope beyond what is authorized, and it never justifies skipping the Continuation Duty stop conditions of Rule 1.

CONTROL must hold itself to this standard in every audit, Task Order, and closure decision, and must explicitly convey it to Producer in every Task Order — not as one line among many, but as the governing intent behind the engagement. Producer is expected to apply this standard to every detail of implementation, not selectively.

Indefinite hedging, repeated re-verification without new evidence, or declining to reach a definitive, well-supported conclusion is itself a form of falling short of this standard — it is not caution.

### Mandatory Standing Rules Footer

Every substantive response from a governed role must terminate with this footer, regenerated from the role's current state rather than copied mechanically:

```text
--- STANDING RULES CHECK ---
R1 Continuation: <CONTINUING | STOPPED(A) | STOPPED(B) | STOPPED(C)> — <one line>
R2 Hand-off message: <NONE REQUIRED | INCLUDED ABOVE> — <recipient role + type>
R3 Large artifacts: <N/A | fetch_blob used for: ...>
R4 VPS/SentinelX: <N/A | used for: ...>
R5 Quality standard: <APPLIED | N/A>
G12 Peripheral sync: <N/A | CHECKED | PENDING AT STEP CLOSURE>
Phase/Step: <current> | Active TO: <id or null>
```

The footer is a reporting device only. It does not grant authority, and `R2 INCLUDED ABOVE` is valid only when the required message was actually produced.
