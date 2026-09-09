# ADR-GOVERNANCE-011 — SentinelX Broad Operational Privilege Model

**Status:** RATIFIED / AUTHORIZED FOR IMPLEMENTATION  
**Stable ID:** `ADR-GOVERNANCE-011`  
**Decision Authority:** Project Owner  
**Related Decision:** `ADR-GOVERNANCE-010`  
**Affected Role:** `ROL-V2-001`  
**Affected Execution Mechanism:** SentinelX host agent / CONTROL VPS execution pilot

## 1. Decision

The Project Owner has explicitly approved the SentinelX execution model in which CONTROL (`ROL-V2-001`) receives broad operational capability on the authorized Meylux V2 VPS rather than a narrow command allowlist.

The approved model is:

```text
Broad Operational Access
+
Autonomous command selection/execution
+
Broad filesystem read/write capability
+
Service / Docker / package / Git / build / test administration
+
Passwordless sudo for the SentinelX host user
+
Autonomous R0/R1/R2 recovery within governed scope
```

The SentinelX host user is `sentinelx`. The approved privilege model permits passwordless sudo for all commands on the authorized host:

```text
sentinelx ALL=(ALL) NOPASSWD: ALL
```

This is an intentional Project Owner decision for this private Meylux V2 environment and is not the default SentinelX security posture.

## 2. Relationship to ADR-GOVERNANCE-010

This ADR supersedes only the privilege-model restriction in `ADR-GOVERNANCE-010` that stated that unrestricted root/shell authority was not authorized.

All other provisions of `ADR-GOVERNANCE-010` remain in force, including:

- CONTROL authority remains subordinate to Constitution, Ratified/Frozen Architecture, authorized Task Order, Security Boundary, and Owner Reserved Authority;
- `EXECUTED != VERIFIED`;
- R0-R4 recovery semantics;
- Producer implementation boundary;
- R4 `STOP THAT PART -> preserve evidence -> escalate`;
- V1 isolation;
- evidence and secret-handling requirements;
- no new role identity or lifecycle state.

This ADR does not create a new execution framework or SentinelX subsystem.

## 3. SentinelX Configuration Boundary

The repository stores the approved deployment configuration template. The actual runtime policy remains `/etc/sentinelx/config.yaml` on the target host.

The approved configuration intentionally uses broad command execution, including shell execution, because the Project Owner explicitly requires CONTROL to be able to diagnose and remediate unforeseen operational problems without repeatedly requesting manual command approval.

Filesystem primitives use the SentinelX `file_ops.paths` model with `/` granted `rw` access. This does not replace Linux privilege semantics; root-level operations use the approved sudo policy.

## 4. Hard Governance Exclusions

The SentinelX configuration is not the mechanism used to create a second Meylux governance layer. The following remain CONTROL governance boundaries:

1. CONTROL must not manipulate SentinelX's execution authority in order to escape its own governed role or bypass Meylux governance.
2. CONTROL must not intentionally perform irreversible destruction of the entire host as an ordinary autonomous operation.
3. Architecture / governance / authority / scope conflicts remain R4 and require `STOP THAT PART -> preserve evidence -> escalate`.

These exclusions are governance constraints. They are not represented as an artificial narrow command allowlist when doing so would defeat the approved broad-operational model.

## 5. Recovery

R0 and R1 remain autonomous within the authorized execution context. R2 may be remediated autonomously when the change is in-scope, non-architectural, and otherwise authorized. R3 remains a Producer correction boundary. R4 remains a stop/escalation boundary.

## 6. Evidence and Audit

SentinelX's own operational/audit information is supporting runtime evidence. It is not the Meylux EXEC-LOG and does not replace the official artifact protocol.

Actual execution remains subject to `TO-GOV-004`, EXEC-LOG creation, separate CONTROL verification, and governed repository state updates.

No runtime execution, installation, connection, or verification is claimed by this ADR.

## 7. Non-Changes

This decision does not authorize:

- trading, order execution, capital movement, custody, withdrawals, deposits, leverage control, or fund transfer;
- V1 access or modification;
- silent Producer implementation repair;
- architecture or governance changes through runtime command execution;
- fabricated execution evidence;
- automatic project-state transition merely because this decision exists.

## 8. Ratification Record

**Owner Decision:** RATIFIED. Proceed with the approved broad SentinelX operational privilege model and continue the governed execution pilot.
