# ADR-GOVERNANCE-010 — CONTROL Autonomous VPS Execution & Verification

**Status:** RATIFIED / AUTHORIZED FOR IMPLEMENTATION  
**Stable ID:** `ADR-GOVERNANCE-010`  
**Decision Authority:** Project Owner  
**Related Change Package:** `CONTROL AUTONOMOUS VPS EXECUTION & VERIFICATION — FORMAL GOVERNED CHANGE PACKAGE`  
**Affected Roles:** `ROL-V2-001`, `ROL-V2-007`  
**Affected Architecture:** `DOC-V2-ARCH-001`

## 1. Decision

The Project Owner formally ratified the governed change that expands `ROL-V2-001 — CONTROL / REVIEWER` to include:

```text
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

The authority is strictly subordinate to:

```text
Constitution
→ Ratified/Frozen Architecture
→ Authorized Phase / Step
→ Authorized Task Order
→ Security Boundary
→ Project Owner Reserved Authority
```

Implementation is authorized only within the ratified Formal Governed Change Package.

## 2. Required Architectural/Governance Amendment

The frozen Master Architecture and affected Role Contract semantics must be minimally amended to:

1. remove the contradiction that currently makes `ROL-V2-007 — OPERATOR` the only VPS execution authority;
2. establish authorized CONTROL VPS execution and bounded operational recovery;
3. preserve execution/verification separation;
4. preserve the Producer implementation boundary;
5. preserve all unrelated frozen architecture;
6. preserve all Stable IDs and historical lineage;
7. introduce no additional authority, scope, or functionality beyond the ratified package.

## 3. Operator Identity

`ROL-V2-007 — OPERATOR` remains a permanent logical identity with historical lineage.

Its final lifecycle disposition must use an existing repository lifecycle mechanism. No new lifecycle state may be invented. The exact disposition remains an explicit deferred governance item until determined through the existing lifecycle mechanism.

Regardless of lifecycle label, the transferred VPS execution authority must not remain simultaneously assigned to the Operator in the target authority model.

## 4. Execution / Verification Separation

CONTROL may execute an authorized VPS operation and subsequently verify its result, but the states remain distinct:

```text
EXECUTED ≠ VERIFIED
```

Execution evidence must be captured before independent verification is concluded.

## 5. Recovery Boundary

The governed recovery model is:

- `R0`: transient bounded autonomous recovery;
- `R1`: ordinary bounded recovery within Task scope;
- `R2`: bounded configuration/environment remediation only when authorized, non-architectural, and in-scope;
- `R3`: implementation defect → Producer correction; CONTROL must not silently implement the correction;
- `R4`: architecture/governance/security/authority/scope conflict → `STOP THAT PART`, preserve evidence, escalate.

Numeric retry/time/session parameters remain implementation-level controlled parameters and must not be invented outside the Task Order/implementation process.

## 6. Security Boundary

The implementation must use a controlled, authenticated and auditable execution boundary. Credentials/secrets must not appear in Task Orders, execution logs, repository artifacts, or ordinary evidence. Privilege must be bounded to the authorized operation and controlled termination must be supported.

Implementation technology is not prescribed by this ADR; selection remains subject to the ratified package, security requirements, and implementation review.

## 7. Governance Path

Implementation proceeds through the existing governed workflow:

```text
Ratified Change
→ Controlled Repository Amendment
→ Required Task Order
→ Producer Implementation
→ Build Report
→ CONTROL Audit
→ Authorized VPS Execution
→ EXEC-LOG
→ Separate CONTROL Verification
→ Governance State Update
```

No additional Project Owner approval loop is required for matters already covered by this ratification.

## 8. Non-Changes

This decision does not:

- authorize trading, capital movement, leverage control, custody, or fund transfer;
- authorize unrestricted root/shell authority;
- change the Producer's implementation ownership;
- alter unrelated Phase/Step scope;
- retroactively change historical execution attribution;
- reopen completed Phase 0 or completed Phase 1 steps;
- create a new role Stable ID;
- create a new lifecycle state;
- create a new ACR subsystem.

## 9. Evidence Requirement

Implementation claims remain subject to the existing Artifact Protocol and Evidence Policy. In particular:

```text
IMPLEMENTED ≠ EXECUTED ≠ VERIFIED
```

Operational evidence must come from actual execution, and verification must remain evidence-based.

## 10. Ratification Record

The Project Owner directive explicitly states:

`Owner Decision: RATIFIED. Proceed to governed implementation.`

This ADR records that ratified decision in the repository's existing ADR mechanism. It does not itself claim that implementation or verification has occurred.
