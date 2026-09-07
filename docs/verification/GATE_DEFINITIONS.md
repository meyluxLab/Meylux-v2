# Meylux V2 — Gate Definitions

**Status:** RECONCILED / PENDING CONTROL VERIFICATION  
**Scope:** V2 verification, evidence, gate, completion, acceptance, ratification, and freeze semantics

## 1. Purpose

This document defines the governed meaning of a gate and the evidence boundary required before a project state may advance. A gate is a governance boundary, not an implementation artifact and not a substitute for execution evidence.

No gate may grant authority that is absent from the applicable Constitution, ratified ADR/ACR, authorized Task Order, or approved execution path.

## 2. Gate State Model

A gate is evaluated through distinct lifecycle states:

```text
DEFINED
→ ENTRY SATISFIED
→ EVIDENCE ASSEMBLED
→ AUDIT / VERIFICATION
→ ACCEPTED / CLOSED
```

`DEFINED` means the gate exists as an authorized governance concept.  
`ENTRY SATISFIED` means the prerequisites for evaluation are evidenced.  
`EVIDENCE ASSEMBLED` means the required evidence package exists and is traceable.  
`AUDIT / VERIFICATION` means the independent authority is evaluating the evidence.  
`ACCEPTED / CLOSED` means the authorized gate owner has accepted the applicable evidence and the formal closure record exists.

A gate MUST NOT be treated as `CLOSED` merely because its requirements are documented or because a Producer reports that they were satisfied.

## 3. Evidence Classes

Gate evidence is separated into the following classes where applicable:

- **Structural evidence:** repository artifacts, schemas, registries, contracts, configuration structure, and lineage records.
- **Behavioral evidence:** observed behavior from an authorized execution or controlled test.
- **Test evidence:** reproducible static, unit, contract, integration, negative/failure, property, replay, chaos, end-to-end, soak, or other approved test results.
- **Operational evidence:** Operator execution output, EXEC-LOG, deployment/runtime evidence, or other physically executed evidence where explicitly authorized.
- **Governance evidence:** Task Orders, ADR/ACR decisions, audit reports, approvals, ratifications, checkpoints, and controlled status transitions.
- **Data / analytical evidence:** validated market data, deterministic computations, evidence provenance, specialist outputs, and analytical inputs/results. This class must remain distinct from governance evidence.

The required classes depend on the gate. A gate may not claim an evidence class that was not actually produced.

## 4. Evidence Provenance Requirements

Material gate evidence MUST be traceable to:

```text
Evidence ID / source
→ artifact or execution context
→ affected Stable ID(s)
→ parent Task Order / Step / Phase where applicable
→ producer / executor where applicable
→ timestamp or version context where applicable
→ content/version identifier such as commit or hash where applicable
→ verification disposition
```

Where an item has no reliable provenance, it remains `UNVERIFIED` and cannot silently become acceptance evidence.

Repository history, commit identifiers, test outputs, execution logs, and hashes are evidence only for the facts they actually establish. Their existence does not prove unrelated behavior.

## 5. Independence and Authority Separation

The Producer may produce implementation/content and self-check evidence within the authorized Task Order. The Producer MUST NOT independently audit, verify, accept, ratify, freeze, or close its own work.

CONTROL / REVIEWER (`ROL-V2-001`) is the independent audit and verification authority for the governed Producer artifact chain unless a higher-authority approved process explicitly assigns another verifier.

Operator execution evidence is distinct from Producer evidence. An Operator EXEC-LOG records actual physical/environment execution; it does not retroactively validate design claims that were not executed.

Project Owner ratification is a governance act and is not equivalent to technical test evidence. Likewise, technical test evidence does not itself constitute Project Owner ratification.

## 6. Lifecycle Distinctions

The following states MUST remain distinct:

```text
DESIGNED
DRAFT
PROPOSED
APPROVED
IMPLEMENTED
EXECUTED
VERIFIED
ACCEPTED
RATIFIED
FROZEN
CLOSED
```

In particular:

- `IMPLEMENTED` does not mean `EXECUTED`.
- `EXECUTED` does not mean `VERIFIED`.
- `VERIFIED` does not automatically mean `ACCEPTED`.
- `ACCEPTED` does not automatically mean `RATIFIED`.
- `RATIFIED` does not automatically mean `FROZEN`.
- `FROZEN` does not authorize runtime activity unless the applicable governance path explicitly grants that authority.

A Build Report is Producer evidence and remains unverified until the independent audit is completed.

## 7. Gate Closure Requirements

A gate may close only when all requirements applicable to that gate are evidenced and independently evaluated where independence is required. At minimum, the closure record must establish:

1. gate identity and scope;
2. entry criteria and their evidence;
3. required structural evidence;
4. required behavioral/test/operational evidence, where applicable;
5. evidence provenance and traceability;
6. unresolved blockers or explicit confirmation that none remain;
7. independent verification disposition;
8. authority of the party accepting/closing the gate;
9. exact resulting state transition;
10. affected Stable IDs and parent artifact lineage;
11. confirmation that no prohibited or unauthorized activity was used as evidence.

Missing evidence is not equivalent to passing evidence.

## 8. Acceptance vs Verification vs Ratification vs Freeze

**Verification** answers whether the evidence supports the claimed result under the applicable verification method.  
**Acceptance** answers whether the authorized acceptance authority accepts that verified result for the defined boundary.  
**Ratification** is a governance decision by the authority entitled to ratify the relevant artifact or decision.  
**Freeze** establishes that the applicable artifact/boundary is no longer mutable except through its controlled change process.

These actions must have separate records when the governing process requires them.

## 9. Phase 0 Entry Boundary

`G-0R = RATIFIED / VERIFIED` is the verified formation-ratification prerequisite for entry into `PH-P0`. It is necessary for Phase 0 entry but is not itself Phase 0 implementation authorization.

Phase 0 authorization additionally requires the authoritative Phase 0 definition, first Step, entry/authorization criteria, and CONTROL / REVIEWER Entry Review to be present and verified in the repository.

`STEP-P0-001` is the first official Phase 0 Step and remains historically complete and verified. Its completion does not automatically ratify or freeze the Master Architecture.

## 10. Phase 0 Step Boundary

For Phase 0, a Step becomes executable only when its dedicated Task Order is formally authorized through the existing governance process.

Completion of a Step requires, at minimum:

```text
Authorized Task Order
→ Producer execution / Build Report
→ independent CONTROL audit
→ required acceptance / state evidence
→ governed checkpoint transition where applicable
```

The existence of a later Step in the ratified sequence does not activate it.

## 11. Verification / Evidence / Gates Step Boundary

`STEP-P0-008` formalizes this verification/evidence/gate model. Its execution does not:

- ratify or freeze the Master Architecture;
- activate `STEP-P0-009` or `STEP-P0-010`;
- authorize runtime, deployment, V1/VPS, market, trading, capital, or provider-runtime activity;
- create a competing verification, evidence, gate, approval, checkpoint, or registry subsystem.

## 12. Analytical/Data Evidence vs Governance Evidence

Analytical/data evidence establishes facts about market information and derived analysis. Governance evidence establishes authorization, lineage, lifecycle state, audit, acceptance, ratification, and freeze.

Neither class may silently substitute for the other. For example:

- a valid market-data replay does not prove that a Step was authorized;
- an approved Task Order does not prove that market data was valid;
- a passing deterministic test does not prove production deployment;
- a governance approval does not fabricate missing market evidence.

## 13. Failure and Negative Evidence

A failed test, missing execution log, unavailable provider response, stale artifact, or contradictory evidence MUST remain explicitly represented. Failure evidence may establish that a condition was not demonstrated; it does not become a positive verification result.

Contradictory evidence requires controlled reconciliation or an explicit unresolved disposition. It must not be silently discarded.

## 14. Source-of-Truth and Historical Evidence

The GitHub repository is the authoritative project record. Chat statements, memory, or informal summaries do not override repository artifacts.

Historical evidence remains immutable in meaning and lineage. Corrections use the governed artifact process and do not silently rewrite prior evidence.

## 15. Gate Closure Non-Conditions

The following are not sufficient by themselves for gate closure:

- documentation of an intended behavior;
- Producer assertion without supporting evidence;
- existence of a passing test unrelated to the gate's acceptance criteria;
- a commit existing without demonstrating the claimed behavior;
- a design baseline being complete;
- a Task Order being authorized;
- a Build Report being produced;
- Project Owner ratification of a different artifact;
- an environment being defined but not actually executed;
- a runtime observation that was not authorized or properly recorded.

## 16. Safety / Scope Boundary

Verification and gate semantics do not authorize implementation outside the current Task Order. In particular, no gate definition grants permission for V1/VPS mutation, runtime/deployment activity, market-provider execution, trading, capital movement, or fund transfer.

## 17. Current Status

This document is `RECONCILED / PENDING CONTROL VERIFICATION` as part of `TO-P0-009`. Independent CONTROL audit remains required before this artifact or `STEP-P0-008` may be treated as verified/complete.
