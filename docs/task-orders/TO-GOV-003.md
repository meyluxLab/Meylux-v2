# MEYLUX V2 — GOVERNANCE / ARCHITECTURE CHANGE TASK ORDER

## TO-GOV-003 — CONTROL Autonomous VPS Execution & Verification Governance Amendment

**Task Order ID:** `TO-GOV-003`  
**Governance Class:** Post-Freeze Governance / Ratified Architecture Change  
**Phase:** `NONE`  
**Step:** `NONE`  
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)  
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)  
**Status:** `AUTHORIZED TO EXECUTE`  
**Authority:** `ADR-GOVERNANCE-010` + Project Owner Ratification of the Formal Governed Change Package  
**Primary Role:** `ROL-V2-001`  
**Affected Role:** `ROL-V2-007`  
**Build Report ID:** `BR-GOV-003`  
**Build Report Path:** `docs/build-reports/BR-GOV-003.md`

## 1. Sole Objective

Implement the Project Owner-ratified governance and frozen-architecture amendment that establishes `ROL-V2-001 — CONTROL / REVIEWER` as an authorized, bounded VPS execution and operational-recovery role while preserving independent verification semantics, the Producer implementation boundary, all unrelated frozen architecture, Stable IDs, historical lineage, and existing project scope.

This Task Order implements only the already-ratified `CONTROL AUTONOMOUS VPS EXECUTION & VERIFICATION — FORMAL GOVERNED CHANGE PACKAGE` recorded by `ADR-GOVERNANCE-010`.

It does not authorize application feature development, unrestricted infrastructure administration, trading activity, capital movement, V1 activity, or any other scope expansion.

## 2. Required Outcome

The repository must consistently represent the following target authority model:

```text
ROL-V2-001 — CONTROL / REVIEWER
=
Governance
+
Review / Audit
+
Authorized VPS Execution
+
Bounded Operational Recovery
+
Verification
```

subject to:

```text
Constitution
→ Ratified/Frozen Architecture
→ Authorized Phase / Step
→ Authorized Task Order
→ Security Boundary
→ Project Owner Reserved Authority
```

The amendment must eliminate the current contradiction in which the Operator is the only VPS execution authority.

Execution and verification remain separate states:

```text
EXECUTED ≠ VERIFIED
```

## 3. Scope In — MUST CHANGE

The Producer SHALL implement the minimum repository changes required by the ratified package:

1. Amend `docs/architecture/MASTER_ARCHITECTURE_V2.md` so §4.1 and any directly contradictory execution-authority wording establish CONTROL as an authorized VPS execution role and remove the Operator-only execution contradiction.
2. Preserve all unrelated frozen architecture, invariants, target repository structure, phase boundaries, and non-goals.
3. Amend `docs/governance/ROLE_CONTRACT_CONTROL_REVIEWER_V2.md` so the CONTROL Role Contract explicitly includes authorized VPS execution, bounded operational recovery, execution-context requirements, security boundary, and the prohibition on unrestricted authority.
4. Preserve all existing CONTROL authorities and limits except for the ratified execution/recovery expansion.
5. Amend `docs/governance/ROLE_CONTRACT_V2.md` only to remove semantic contradictions with the ratified authority model. Do not redesign the shared Role Contract.
6. Preserve `ROL-V2-007 — OPERATOR` as a permanent Stable ID and historical lineage. Remove its normal VPS execution authority from the target model without deleting or silently reusing the identity.
7. Use only an existing repository lifecycle mechanism for the Operator lifecycle disposition. Do not invent a new lifecycle status. The exact disposition remains a deferred governance item unless it can be determined from an existing authoritative mechanism without invention; do not fabricate a status.
8. Preserve the existing Artifact Protocol and Evidence Policy semantics. Make only minimal wording changes if required to eliminate a direct contradiction created by the new authority model; do not create a second artifact/evidence system.
9. Preserve the existing ADR mechanism. Do not create an ACR subsystem.
10. Extend, rather than replace, the existing EXEC-LOG model so CONTROL execution can produce auditable operational evidence while preserving execution/verification separation.
11. Define the VPS Execution Context and VPS Verification Context in the existing appropriate governance/architecture artifact(s), using the ratified package requirements.
12. Define R0–R4 recovery behavior exactly within the ratified package:
    - R0 transient → bounded autonomous recovery;
    - R1 ordinary → bounded autonomous recovery within Task scope;
    - R2 configuration/environment → bounded remediation only when authorized, non-architectural, and in-scope;
    - R3 implementation defect → Producer correction; CONTROL MUST NOT silently implement the defect correction;
    - R4 architecture/governance/security/authority/scope conflict → `STOP THAT PART`, preserve evidence, escalate.
13. Define bounded recovery/session controls without inventing numeric values not established by authoritative project artifacts. Numeric parameters may remain controlled implementation/configuration decisions where appropriate.
14. Preserve technology-neutral security requirements from the ratified package: authenticated target identity, authorized session, bounded operation, credential isolation, privilege boundary, timeout, auditability, controlled termination, and destructive-operation handling.
15. Do not place passwords, private keys, tokens, or secrets in governance artifacts, Task Orders, Build Reports, EXEC-LOGs, registry records, or ordinary evidence.
16. Update relevant registry records only as required to make the ratified change traceable. Preserve all existing IDs and historical records.
17. Record the change in the existing `docs/state/CHANGE_LEDGER.yaml` only when the implementation transition is actually evidenced; do not claim implementation merely because files were edited.
18. Preserve the current Phase 1 historical state. Do not reopen `STEP-P1-001`, `STEP-P1-002`, or `STEP-P1-003`, and do not retroactively attribute their execution to CONTROL.
19. Do not change `docs/state/CURRENT_CHECKPOINT.json` to claim runtime execution or verification. Current VPS status remains `NOT SET UP` until actual governed VPS execution evidence exists.
20. Produce `docs/build-reports/BR-GOV-003.md` with actual implementation changes, exact evidence, tests/self-tests, deviations, Open Questions / Deferred Decisions, and explicit non-claims.
21. Keep `BR-GOV-003` in `PRODUCED / UNVERIFIED` state pending independent CONTROL audit.

## 4. VPS Execution Context — REQUIRED SEMANTICS

The implemented governance model must define an execution context containing, at minimum:

- Role;
- Task ID;
- Step ID where applicable;
- Objective;
- Target;
- Allowed Actions;
- Must-Not Actions;
- Failure / Recovery Policy;
- Retry Boundary;
- Timeout Boundary;
- Escalation Boundary;
- Required Evidence.

The context must not contain credentials or secrets.

## 5. VPS Verification Context — REQUIRED SEMANTICS

The implemented model must define a separate verification context containing, at minimum:

- Role;
- Task ID;
- Step ID where applicable;
- Verification Objective;
- Mandatory Verification Baseline;
- Task-Specific Acceptance Criteria;
- Required Runtime Observations;
- Required Evidence;
- Escalation Conditions.

The verification context must not collapse into the execution result. The existence of execution evidence does not itself constitute verification.

## 6. EXEC-LOG — REQUIRED SEMANTICS

The existing EXEC-LOG mechanism must remain the operational evidence mechanism. Where its schema is extended, support at minimum:

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

Actual runtime values must be produced only from real execution. No fabricated execution evidence is permitted.

## 7. Scope Out — MUST NOT CHANGE

The Producer MUST NOT:

- modify the Constitution;
- weaken or reinterpret `INV-V2-001` or any other constitutional invariant;
- authorize trading, order routing, leverage control, custody, balance management, withdrawals, fund movement, or capital authority;
- grant unrestricted root/shell/infrastructure authority;
- create a new role Stable ID;
- create a replacement for `ROL-V2-007`;
- invent a lifecycle status;
- invent an ACR subsystem;
- redesign the architecture beyond the ratified package;
- alter unrelated frozen architecture;
- alter unrelated Phase/Step scope;
- reopen completed historical work;
- retroactively change execution attribution;
- silently modify Producer implementation boundaries;
- place secrets in repository artifacts or evidence;
- connect to or execute against the Target VPS as part of Producer implementation unless a later controlled execution instruction explicitly authorizes it;
- claim VPS execution, operational recovery, EXEC-LOG evidence, or verification that did not actually occur;
- silently fix an implementation defect that belongs to Producer responsibility under R3;
- resolve an R4 conflict by personal interpretation.

## 8. R3 / R4 Stop Conditions

If implementation encounters a genuine R3 implementation defect, the Producer must report it and correct it within the controlled implementation cycle without expanding scope.

If implementation encounters a genuine R4 Architecture / Governance / Security / Authority / Scope conflict:

```text
STOP THAT PART
→ preserve evidence
→ identify the conflict
→ report it in BR-GOV-003
→ await controlled resolution
```

Do not silently reconcile an R4 conflict.

## 9. Acceptance Criteria

CONTROL may audit `BR-GOV-003` only when actual evidence demonstrates that:

1. CONTROL is represented as an authorized VPS execution role within the ratified boundaries.
2. The Operator-only VPS execution contradiction is removed.
3. `ROL-V2-007` identity and historical lineage remain intact.
4. Execution and verification remain distinct.
5. Producer implementation ownership remains intact.
6. R0–R4 recovery boundaries are represented without scope expansion.
7. Security requirements and credential isolation are represented.
8. Existing Artifact Protocol / Evidence Policy semantics remain coherent.
9. Existing EXEC-LOG mechanism is extended rather than replaced.
10. No new Stable ID or lifecycle state was invented.
11. No unrelated frozen architecture or historical state was changed.
12. Registry/traceability updates are accurate.
13. Tests/self-tests relevant to changed governance semantics pass where available.
14. No claim of actual VPS execution or verification is made unless backed by real evidence.
15. `BR-GOV-003` explicitly reports actual changes and non-claims.

## 10. Verification Boundary

Producer completion means only:

```text
GOVERNANCE / ARCHITECTURE AMENDMENT IMPLEMENTED
+
BR-GOV-003 PRODUCED
+
ACTUAL IMPLEMENTATION EVIDENCE REPORTED
```

It does not mean:

```text
AUDITED
APPROVED
EXECUTED ON VPS
VERIFIED
CLOSED
```

After a passing CONTROL audit, the next governed boundary is the authorized VPS execution pilot and its separate verification, using the existing evidence chain.
