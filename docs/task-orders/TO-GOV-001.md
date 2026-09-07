# MEYLUX V2 — GOVERNANCE TASK ORDER

## TO-GOV-001 — PROJECT GUIDE Role Establishment

**Task Order ID:** `TO-GOV-001`
**Governance Class:** Post-Freeze Governance / Governance Activity
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)
**Status:** `AUTHORIZED TO EXECUTE`
**Authority:** `ADR-GOVERNANCE-001`; `ADR-GOVERNANCE-003`; `ADR-GOVERNANCE-005`
**Target Role:** `PROJECT GUIDE`
**Canonical Role Contract Path:** `docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md`

## 1. Sole Objective

Establish the formal `PROJECT GUIDE` role contract as a governed repository artifact, within the approved Project Guide role-establishment scope, and prepare that role contract for the required independent CONTROL audit and subsequent Project Owner ratification.

This Task Order establishes only the work required to produce and evidence the proposed role contract. It does not itself establish, ratify, freeze, register, or activate the PROJECT GUIDE role.

## 2. Authoritative Basis

This Task Order is issued under the ratified post-freeze Task Order identity convention established by `ADR-GOVERNANCE-005`.

The applicable Project Guide role contract requirements have been reviewed as the authorized design input for this Task Order. The role contract must preserve the previously approved role boundary, including:

- informational, knowledge, navigation, continuity, and assistance responsibility;
- broad repository-grounded project knowledge and navigation;
- evidence-grounded current-state explanation;
- external technical research capability where appropriate;
- no governance, ratification, implementation, execution, trading, or capital authority;
- no silent project mutation;
- no self-authorization;
- no substitution for Project Owner, CONTROL, Producer, Operator, Market Intelligence, or Troubleshooting authority;
- repository Source of Truth supremacy over chat memory;
- explicit uncertainty and evidence discipline;
- V1/V2 isolation;
- scope and continuity discipline.

The role lifecycle and establishment process must preserve the required distinction between role-contract drafting/review, ratification, registry entry, freeze, and verification.

## 3. Scope In

The Producer shall, within this Task Order only:

1. Produce the complete `PROJECT GUIDE` Role Contract at:
   `docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md`.
2. Incorporate the approved Project Guide role-contract content and the three previously identified hardening requirements:
   - formal establishment requires authoritative registry entry in addition to lifecycle progression;
   - Evidence-Assessment Capability is informational/analytical only, with Verification Authority = NONE and Formal Verification Approval = NONE;
   - the role has no assumed background execution capability; continuous monitoring means invocation-time revalidation or an explicitly authorized read-only monitoring mechanism.
3. Preserve the role's authority boundary exactly: the Project Guide may inform, explain, navigate, assess evidence, research, cross-reference, and recommend, but may not ratify, approve, modify, implement, execute, deploy, trade, control capital, or self-authorize.
4. Define the role lifecycle so that `DRAFT → REVIEWED → RATIFIED → FROZEN` is distinct from formal establishment, with authoritative registry entry required for formal establishment.
5. Include explicit Source-of-Truth, freshness, uncertainty, evidence, continuity, role-routing, conflict-handling, scope-control, and V1/V2 boundary requirements appropriate to the approved Project Guide contract.
6. Preserve the distinction between FACT and ASSESSMENT and between evidence assessment and formal verification authority.
7. Produce a complete Build Report containing actual work performed, changed artifacts, self-test/evidence results, deviations, open questions, and explicit non-claims.
8. Keep the Build Report unverified until independent CONTROL audit.

## 4. Scope Out / Explicit Prohibitions

The Producer MUST NOT:

- reopen, reactivate, or modify `PH-P0`;
- modify `STEP-P0-001` through `STEP-P0-010`;
- create or modify any Phase 0 Task Order;
- authorize, define, or begin Phase 1 implementation;
- modify `DOC-V2-ARCH-001` or any other frozen architecture artifact;
- alter the ratified Constitution;
- create or modify governance authority beyond the explicitly authorized PROJECT GUIDE role-contract work;
- grant PROJECT GUIDE governance, ratification, approval, implementation, execution, deployment, trading, or capital authority;
- make PROJECT GUIDE the Source of Truth or superior to the repository;
- register the PROJECT GUIDE role as established unless the required Project Owner Ratification → Registry → Freeze → Verification cycle has actually occurred;
- modify `docs/state/CURRENT_CHECKPOINT.json` as part of this Task Order;
- modify frozen historical artifacts or retrospectively alter prior evidence;
- create speculative Stable IDs;
- alter existing Stable IDs;
- invent a new Task Order, ADR, ACR, Phase, Step, gate, approval mechanism, or governance subsystem;
- perform runtime, VPS, deployment, provider-runtime, market-data execution, trading, capital, or V1/VPS activity;
- fabricate evidence, tests, repository state, hashes, verification, approval, ratification, registry state, or completion;
- silently expand the role contract beyond the approved Project Guide scope.

## 5. Registry and Freeze Boundary

The role contract may be prepared and reviewed by this Task Order, but the PROJECT GUIDE role is NOT established by Producer completion, Build Report production, or CONTROL approval alone.

The required establishment sequence is:

```text
TO-GOV-001
    ↓
PRODUCER ROLE CONTRACT
    ↓
BUILD REPORT
    ↓
CONTROL AUDIT
    ↓
PROJECT OWNER RATIFICATION
    ↓
AUTHORITATIVE REGISTRY ENTRY
    ↓
ROLE CONTRACT FREEZE
    ↓
INDEPENDENT VERIFICATION
```

No step in this Task Order may be represented as completing a later stage without the actual evidence and authority for that stage.

## 6. Build Report Identity Boundary

A Build Report is required for the Producer's work under this Task Order.

The existing ratified Build Report allocation delegation in `ADR-GOVERNANCE-003` is scoped to the Producer's own currently authorized Task Order and does not itself establish a post-freeze `BR-GOV-<NNN>` naming convention.

Therefore the Producer MUST NOT invent a new Build Report identity convention. If no applicable ratified Build Report identity/path can be established under the existing governance mechanism, the Producer MUST stop at that allocation boundary and report the exact blocker to CONTROL rather than fabricate or repurpose an identity.

## 7. Acceptance Criteria

CONTROL may consider the resulting Build Report for audit only if actual evidence demonstrates that:

- the role contract exists at the exact canonical path;
- the contract is complete and internally consistent;
- the role's informational/navigation/continuity mission is explicit;
- the role has no governance, ratification, implementation, execution, deployment, trading, or capital authority;
- Evidence-Assessment Capability is explicitly informational/analytical only;
- Verification Authority is explicitly `NONE`;
- Formal Verification Approval is explicitly `NONE`;
- continuous monitoring has no assumed background execution capability;
- repository Source of Truth remains authoritative over memory/chat;
- lifecycle and formal establishment/registry requirements are distinct;
- V1/V2 isolation is preserved;
- no Phase 0, Master Architecture, Constitution, checkpoint, or frozen artifact has been reopened or modified;
- no Phase 1 implementation is authorized;
- no runtime/VPS/provider/trading/capital activity occurred;
- no unauthorized Stable ID or governance mechanism was created;
- all deviations and open questions are explicitly reported;
- the Build Report remains unverified pending independent CONTROL audit.

## 8. Producer Completion Boundary

Producer completion under this Task Order means only:

```text
ROLE CONTRACT PRODUCED
+
BUILD REPORT PRODUCED
+
ACTUAL EVIDENCE REPORTED
```

It does NOT mean:

```text
ROLE RATIFIED
ROLE REGISTERED
ROLE FROZEN
ROLE VERIFIED
```

Those states require the separate authorities and evidence defined above.

## 9. Control and Project Owner Boundary

CONTROL / REVIEWER retains independent audit, revision, rejection, and progression-review authority.

PROJECT OWNER retains final ratification authority under `ADR-GOVERNANCE-001`.

Only the Project Owner may formally ratify the PROJECT GUIDE role contract.

Following Project Owner ratification, the registry update, freeze, and verification must be performed and evidenced through the applicable controlled workflow. No chat statement may substitute for the authoritative repository state.

## 10. Completion / Stop Conditions

The Producer MUST stop the affected portion and report to CONTROL if:

- the approved Project Guide contract cannot be implemented without changing frozen architecture or ratified governance;
- a required identity cannot be established without invention;
- a required Build Report identity has no applicable ratified allocation mechanism;
- an authority conflict is discovered;
- a requested change would exceed this Task Order's scope;
- required evidence is unavailable;
- any action would require runtime/VPS/V1/provider/trading/capital execution.

Use:

```text
STOP THAT PART
```

for genuine architecture, governance, identity, scope, or authority conflicts.

## 11. Final Non-Claims

This Task Order does not claim:

- PROJECT GUIDE role establishment;
- PROJECT GUIDE ratification;
- PROJECT GUIDE registry registration;
- PROJECT GUIDE freeze;
- PROJECT GUIDE verification;
- Phase 1 authorization;
- Phase 0 reopening;
- Master Architecture modification;
- runtime/VPS execution;
- V1 modification or resumption;
- trading or capital authority.

All such states remain pending until their respective authorized workflow stages produce actual repository evidence.
