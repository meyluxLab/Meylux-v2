# ADR-GOVERNANCE-012 — Mandatory Peripheral Synchronization Checklist

**Status:** `RATIFIED / AUTHORIZED FOR IMPLEMENTATION`
**Stable ID:** `ADR-GOVERNANCE-012`
**Decision Authority:** Project Owner
**Affected Artifact:** `docs/governance/ARTIFACT_PROTOCOL_V2.md`
**Affected Roles:** `ROL-V2-001`, `ROL-V2-002`

## Related Decisions / Records

- `ADR-GOVERNANCE-001`
- `TO-GOV-006` / `BR-GOV-006`
- `TO-GOV-007` / `BR-GOV-007`
- `TO-GOV-008`

## 1. Decision

The Project Owner ratifies the addition of a **Mandatory Peripheral Synchronization Checklist** to `docs/governance/ARTIFACT_PROTOCOL_V2.md`.

CONTROL / REVIEWER MUST include this checklist in the Required Output of every future Step/Phase-closing Task Order.

A Step/Phase closure Build Report that omits the checklist or does not individually confirm each checklist item is incomplete and MUST NOT be accepted as a complete closure report.

## 2. Mandatory Peripheral Synchronization Checklist

At every applicable Step/Phase closure, CONTROL must individually confirm:

1. `README.md` matches `docs/state/CURRENT_CHECKPOINT.json` after closure.
2. `docs/registry/artifacts.yaml` records for exercised, created, or verified artifacts do not retain stale pre-activation status.
3. All specialized registries have been checked and evidence-backed records have been transcribed where appropriate.
4. All standalone status-bearing documents have been checked.
5. Supplemental/staging registries have been checked and retired when their contents have been fully absorbed into the canonical registry.

## 3. Authority and Boundary

This checklist is a governance synchronization control. It does not expand authority, create a new artifact class, create a new role, create a new lifecycle state, or authorize a Phase, Step, VPS, or runtime action.

The checklist is not equivalent to independent verification. Synchronization evidence and CONTROL verification remain distinct governance activities.

## 4. Scope and Effective Application

The checklist is prospective. It applies beginning with `TO-GOV-008` and to future Phase/Step-closing Task Orders.

It does not retroactively reopen or re-execute P0, P1, or P2 closure work.

It does not authorize Phase 3 or Phase 4 activation.

It does not authorize VPS/runtime/V1 activity and does not change the Master Architecture.

## 5. Relationship to TO-GOV-008

`TO-GOV-008` is the first corrective action under the diagnostic/reconciliation process associated with this decision and contains the one-time application of the checklist to the identified documentation and registry drift.

The Project Owner directly applied, before formal issuance of `TO-GOV-008`, the following changes:

- `README.md`
- `docs/decisions/ADR_INDEX.md`
- the Mandatory Peripheral Synchronization Checklist addition to `docs/governance/ARTIFACT_PROTOCOL_V2.md`

Those changes are recorded for traceability and evidence accuracy. They are not Producer execution of `TO-GOV-008`, and `F-01 / README.md` is therefore excluded from Producer execution scope.

## 6. Non-Changes

This decision does not:

- silently correct unrelated documentation;
- authorize fabricated registry records or evidence;
- create new lifecycle vocabulary;
- make checklist synchronization equivalent to verification;
- create new roles or Stable IDs;
- alter the architecture hierarchy;
- reopen prior phase closure work;
- authorize Phase 3 or Phase 4;
- authorize VPS, runtime, deployment, migration, restart, or V1 activity.

## 7. Governance Intent

The purpose of this decision is to prevent peripheral documentation and registry status drift from becoming inconsistent with authoritative project state, while preserving the distinction between synchronization, implementation, execution, and independent verification.

**Decision:** RATIFIED / AUTHORIZED FOR IMPLEMENTATION.
