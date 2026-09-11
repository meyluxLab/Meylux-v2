# CHANGE RECORD — SHARED CONTROL / PRODUCER OPERATING BOUNDARY V2

**Stable ID:** `GOV-CR-001`

**Change Type:** Governed Role / Operational Boundary Formalization

**Decision Authority:** Project Owner

**Affected Roles:** `ROL-V2-001`, `ROL-V2-002`

**Primary Governance Artifact:** `docs/governance/SHARED_CONTROL_PRODUCER_OPERATING_BOUNDARY_V2.md`

**Related Existing Authority:** `ADR-GOVERNANCE-010`, `ADR-GOVERNANCE-011`

**Status:** FORMALLY INCORPORATED / VERIFIED

## 1. Origin

Project Owner directed CONTROL / REVIEWER to formalize the supplied `MEYLUX V2 — SHARED CONTROL / PRODUCER OPERATING BOUNDARY` as a governed common operating rule for `ROL-V2-001` and `ROL-V2-002`.

## 2. Purpose

The change establishes an explicit shared operational interpretation for Repository, development workspace, VPS, runtime, implementation, operational action, correction, and independent verification responsibilities, preserving the Phase 1 working model while preventing silent role transfer and authority ambiguity.

## 3. Scope

The governed boundary permits Producer development access to the authorized Repository/development working tree and, where the authorized Task Order requires it, the development workspace hosted on the project VPS. It does not grant unrestricted operational, production, trading, capital, security-boundary, architectural, or governance authority.

CONTROL retains its already-ratified governance, authorization, audit, bounded VPS execution, recovery, and verification authorities within their existing limits.

Repository state, VPS state, runtime state, and verification evidence remain distinct. Producer implementation ownership and CONTROL independent verification remain distinct.

## 4. Authority Reconciliation

The supplied boundary was reconciled against the current authoritative Role Contracts and existing governance.

The principal pre-existing conflict was the Producer Role Contract language stating that the Producer must not execute VPS commands and that VPS execution belongs to the Reviewer → Operator channel. The Project Owner's explicit formalization instruction authorizes the controlled boundary to supersede that operational restriction specifically for authorized Producer development/development-environment actions, while preserving the prohibition on unrestricted operational authority.

No change to Constitution, architectural invariants, ratified/frozen architecture, read-only/no-trading boundary, or Project Owner reserved authority is authorized by this record.

CONTROL's existing VPS authority remains governed by `ADR-GOVERNANCE-010` and `ADR-GOVERNANCE-011`; this change does not create a second CONTROL authority model.

## 5. Identity

`GOV-CR-001` is the exclusive Stable ID for this change record.

The Shared Operating Boundary itself is separately registered under `GOV-BOUNDARY-001`. Neither identifier is a Role, Phase, Step, Contract, or replacement for an existing governed identity.

## 6. Affected Artifacts

* `docs/governance/SHARED_CONTROL_PRODUCER_OPERATING_BOUNDARY_V2.md`
* `docs/governance/ROLE_CONTRACT_CONTROL_REVIEWER_V2.md`
* `docs/governance/ROLE_DEFINITION_PRODUCER_ARCHITECT_BUILDER_V2.md`
* `docs/governance/ROLE_CONTRACT_V2.md`
* `docs/registry/artifacts.yaml`

## 7. Required Role Interpretation

`ROL-V2-001` and `ROL-V2-002` must interpret the Shared Operating Boundary consistently.

The Producer remains implementation owner and may act directly in the authorized development environment when the active Task Order permits or requires it.

CONTROL remains governance, authorization, audit, bounded operational execution, correction/governance action, and verification authority within existing governed limits.

Neither role may silently assume the other's authority.

## 8. Non-Changes

This record does not:

* authorize V1 modification or integration;
* authorize autonomous trading;
* authorize capital movement or custody;
* authorize unrestricted VPS/root/infrastructure authority;
* authorize unauthorized production activity;
* change Constitution or architectural invariants;
* change ratified/frozen architecture;
* create competing Roles or Stable IDs;
* transfer implementation ownership from Producer to CONTROL;
* eliminate independent verification;
* authorize arbitrary scope expansion.

## 9. Verification Basis

Post-change verification consists of direct inspection of the newly created boundary artifact, the affected Role Contracts, the role summary contract, the Registry record, and the related existing governance authority. The verification confirms that the Producer VPS restriction is reconciled narrowly to authorized development-environment activity and that prohibited unrestricted operational authority remains excluded.

The change is recorded as `FORMALLY INCORPORATED / VERIFIED` because the repository artifacts and cross-artifact consistency were directly inspected after the governed updates were applied.

## 10. Effective Interpretation

From this governed change onward, future Task Orders must not repeat the general Repository/development-workspace/VPS role boundary defined by `GOV-BOUNDARY-001`. A Task Order may impose a narrower boundary or specific exception where required by that Task's scope, security context, environment, or acceptance criteria.
