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
