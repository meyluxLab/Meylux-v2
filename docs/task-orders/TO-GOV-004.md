# MEYLUX V2 — CONTROL VPS EXECUTION & VERIFICATION PILOT TASK ORDER

## TO-GOV-004 — CONTROL Authorized VPS Execution & Verification Pilot

**Task Order ID:** `TO-GOV-004`  
**Governance Class:** Post-Freeze Governance / Authorized Execution Pilot  
**Phase:** `NONE`  
**Step:** `NONE`  
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)  
**Executor:** CONTROL / REVIEWER (`ROL-V2-001`)  
**Status:** `AUTHORIZED TO EXECUTE`  
**Authority:** `ADR-GOVERNANCE-010` + `ADR-GOVERNANCE-011` + `AR-GOV-003` + existing CONTROL standing execution authority

## 1. Objective

Execute the first bounded VPS/environment pilot enabled by the ratified CONTROL authority amendment and verify that the governed execution, evidence, recovery, and security boundaries operate as defined.

This Task Order is the authorized execution boundary following the independent approval of `TO-GOV-003` and the subsequent Project Owner ratification of the SentinelX broad operational privilege model in `ADR-GOVERNANCE-011`.

It does not authorize application feature development, trading activity, capital movement, V1 activity, governance override, or scope expansion.

## 2. Target and Execution Boundary

Target: the authorized Meylux V2 target VPS/environment identified through the authenticated execution context at runtime.

The concrete target identity and connection details are runtime security context, not repository configuration and must not be placed in this Task Order or ordinary evidence when they contain secrets or sensitive credentials.

Execution is permitted only when:

- target identity is authenticated;
- the execution session is authorized;
- the operation is within this Task Order and the applicable security boundary;
- required credentials remain isolated from repository artifacts and logs;
- timeout and controlled-termination boundaries are active;
- all required execution evidence can be captured.

## 3. Allowed Pilot Scope

The pilot shall exercise the minimum governed execution capabilities required by the ratified package and approved SentinelX privilege model:

### T1 — Connection

Establish an authenticated connection to the authorized target and record actual connection evidence without exposing credentials.

### T2 — Authorization Boundary

Confirm that the active session and requested operation are attributable to `ROL-V2-001` and are limited to this Task Order.

### T3 — Allowed Execution

Perform bounded operational administration required to install/configure/validate the SentinelX execution path and exercise the first governed CONTROL operation. Broad operational capability is authorized by `ADR-GOVERNANCE-011`; it must still be used only for the Meylux V2 execution objective and applicable governance boundaries.

### T4 — Execution Evidence

Capture actual commands/actions, outputs, exit codes, timing, target, executor role, and repository/version context required by the EXEC-LOG convention.

### T5 — Execution / Verification Separation

Complete execution evidence before issuing any verification conclusion. Verification must use a separate verification context.

### T6 — R0 Recovery

Where a genuine transient condition occurs, exercise only bounded transient recovery within the same authorized execution context.

### T7 — R1 Recovery

Where an ordinary operational failure occurs, exercise only bounded recovery remaining within this Task Order, scope, and security boundary.

### T8 — R2 Boundary

If a configuration/environment condition is encountered, demonstrate that remediation is permitted only when authorized, non-architectural, and in-scope. Do not force an R2 condition merely to create a test result.

### T9 — R3 Boundary

If an implementation defect is encountered, preserve evidence and route the defect to Producer correction. CONTROL must not silently repair Producer implementation.

### T10 — R4 Boundary

If an architecture, governance, security, authority, or scope conflict is encountered:

```text
STOP THAT PART
→ preserve evidence
→ identify the conflict
→ escalate
```

Do not continue through an R4 condition.

### T11 — Secret Protection

Confirm that credentials/secrets are isolated from Task Orders, EXEC-LOGs, repository artifacts, and ordinary evidence.

### T12 — Privilege Boundary

Confirm that the active SentinelX execution session matches the Project Owner-approved broad operational privilege model and that its use remains attributable to `ROL-V2-001` and bounded by the Task Order and governance constraints. The approved host privilege is `sentinelx ALL=(ALL) NOPASSWD: ALL`; this is intentional and governed by `ADR-GOVERNANCE-011`.

## 4. Execution Context

The runtime execution context shall include at minimum:

```text
Role: ROL-V2-001
Task ID: TO-GOV-004
Step ID: NONE
Objective: bounded CONTROL VPS execution and governance pilot
Target: authenticated authorized target VPS/environment
Allowed Actions: broad operational administration required by the pilot, subject to ADR-GOVERNANCE-011 and this Task Order
Must-Not Actions: trading/capital/V1/governance override/irreversible whole-host destruction as an ordinary autonomous operation
Failure / Recovery Policy: R0–R4 as governed by ADR-GOVERNANCE-010, ADR-GOVERNANCE-011, and CONTROL Role Contract
Retry Boundary: bounded by the active execution context
Timeout Boundary: bounded by the active execution context
Escalation Boundary: Task Order / security / Owner authority boundary
Required Evidence: actual execution evidence and EXEC-LOG
Authorization Reference: TO-GOV-004 / ADR-GOVERNANCE-010 / ADR-GOVERNANCE-011 / AR-GOV-003
```

No credentials or secrets belong in the execution context artifact.

## 5. Verification Context

Verification shall be performed separately from execution and shall include at minimum:

```text
Role: ROL-V2-001
Task ID: TO-GOV-004
Step ID: NONE
Verification Objective: determine whether the pilot satisfied its defined acceptance criteria
Mandatory Verification Baseline: authenticated target, bounded authorization, actual execution evidence, security boundary, recovery-boundary behavior where applicable
Task-Specific Acceptance Criteria: T1–T12 evidence sufficient to establish the exercised pilot behavior; unexercised conditional recovery classes remain explicitly untested rather than fabricated
Required Runtime Observations: actual connection/session, actions, outputs, exit codes, privilege boundary, termination behavior, and recovery observations where applicable
Required Evidence: EXEC-LOG plus supporting runtime evidence
Escalation Conditions: any R4 condition, missing mandatory evidence, unauthorized activity, security-boundary violation, or unexplained contradiction
```

Execution completion does not constitute verification.

## 6. EXEC-LOG Requirement

An actual EXEC-LOG record MUST be created for this pilot execution and must contain the repository-defined minimum fields:

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

`execution_id` is an operational execution/evidence identity and is not a Project Stable ID.

Only actual runtime values may be recorded.

## 7. Recovery and Safety Rules

- Do not manufacture a failure to exercise R0–R4.
- Conditional recovery classes are recorded as `not exercised` when no corresponding real condition occurs.
- R0/R1 recovery may remain within the bounded execution context.
- R2 requires explicit in-scope authorization and must remain non-architectural.
- R3 returns implementation defects to Producer.
- R4 stops the affected operation and escalates.
- Irreversible destruction of the entire host is outside ordinary autonomous recovery; it is not authorized merely because it could be useful for testing.
- No passwords, tokens, private keys, or other secrets may be written to repository artifacts or evidence.

## 8. Pilot Acceptance Criteria

The pilot may be submitted for separate CONTROL verification only when actual evidence demonstrates, as applicable:

1. authenticated target connection;
2. authorized CONTROL executor identity;
3. bounded allowed operation;
4. actual execution evidence captured;
5. execution and verification remain distinct;
6. applicable recovery boundary behavior is respected;
7. R3/R4 stop boundaries are preserved if encountered;
8. credential isolation is preserved;
9. approved privilege model is correctly applied and evidenced;
10. timeout/termination behavior is evidenced;
11. no prohibited trading/capital/V1 activity occurred;
12. EXEC-LOG is complete for the actual execution;
13. no fabricated evidence or unsupported completion claim exists.

Where a conditional R0–R4 class is not naturally encountered, the pilot must record it as not exercised rather than fabricate a failure or recovery event.

## 9. Explicit Non-Authorization

This Task Order does NOT authorize:

- trading or order execution;
- capital movement, custody, withdrawals, deposits, or leverage control;
- V1 access or modification;
- governance or architecture override through runtime actions;
- silent Producer implementation repair;
- deployment outside the authorized pilot scope;
- irreversible whole-host destruction as ordinary autonomous activity;
- secrets in repository artifacts or evidence.

The Project Owner-approved SentinelX broad operational privilege model, including passwordless sudo for the `sentinelx` host user, is expressly authorized by `ADR-GOVERNANCE-011` and is not considered an out-of-scope privilege for this pilot.

## 10. Evidence and Lifecycle Boundary

The governed sequence is:

```text
TO-GOV-004 AUTHORIZED
→ ACTUAL CONTROL EXECUTION
→ EXEC-LOG
→ SEPARATE CONTROL VERIFICATION
→ GOVERNED STATE UPDATE
```

No `EXECUTED`, `VERIFIED`, `ACCEPTED`, or `CLOSED` state may be claimed before its required evidence exists.

`CURRENT_CHECKPOINT.json` remains unchanged until the actual execution and subsequent verification establish a justified state transition.
