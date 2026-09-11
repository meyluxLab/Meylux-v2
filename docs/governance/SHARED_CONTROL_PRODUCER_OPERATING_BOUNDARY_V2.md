# MEYLUX V2 — SHARED CONTROL / PRODUCER OPERATING BOUNDARY

This document establishes the shared operational boundary between:

* **CONTROL / REVIEWER — `ROL-V2-001`**
* **PRODUCER / ARCHITECT-BUILDER — `ROL-V2-002`**

Its purpose is to preserve the proven Phase 1 working model while making the responsibilities and boundaries explicit for all future phases.

---

## 1. Producer / Architect — Repository and Development Environment

`ROL-V2-002` is the implementation owner.

Within an authorized `TASK ORDER`, the Producer may directly:

* read, create, modify, and remove implementation files in the project Repository / development working tree;
* create local commits;
* run tests, builds, validation, and development/integration checks;
* inspect and use the authorized project development environment;
* modify and use the project's development workspace when required to implement and validate the authorized scope.

The development workspace may be hosted on the project VPS.

Therefore:

**Producer Development Workspace Access is permitted and is not, by itself, considered VPS Operational Authority.**

The Producer does not require separate approval for ordinary implementation decisions that are already within the authorized Task Order and existing architecture.

The Producer must remain within the authorized scope and must not silently alter Constitution, Invariants, ratified/frozen Architecture, governed contracts, Stable IDs, security boundaries, or project scope.

---

## 2. Producer — VPS Boundary

The Producer may perform VPS-side actions when they are part of the authorized development/implementation environment required by the active Task Order.

This may include, where applicable:

* editing project files on the development workspace;
* installing or using development dependencies;
* running tests and development processes;
* running authorized integration/runtime validation;
* starting or using development-only components required to validate the implementation.

The Producer must not independently turn development access into unrestricted operational authority.

Production, live trading, capital control, security-boundary changes, architectural changes, or other actions outside the authorized Task Order remain prohibited.

The absence of unrestricted VPS authority must **not** be interpreted as a requirement to stop ordinary development work that can legitimately be performed inside the authorized development environment.

---

## 3. CONTROL — Repository and VPS Responsibilities

`ROL-V2-001` retains Governance, Authorization, Audit, Verification, and bounded operational authority.

CONTROL may directly modify the Repository and/or VPS when required and authorized for:

* governance and project-state artifacts;
* Task Orders and controlled project records;
* Registry and continuity artifacts;
* environment synchronization;
* authorized operational configuration;
* bounded recovery and remediation;
* execution of authorized VPS operations;
* verification and evidence collection;
* other actions explicitly within its existing authority.

CONTROL is not required to remain passive when an operational or governance action must be performed by CONTROL.

However, CONTROL must not silently replace Producer implementation ownership by rewriting implementation merely because it identifies a defect. Implementation defects should normally be returned to the Producer for correction under the established workflow.

---

## 4. CONTROL Response to Producer Changes

Producer changes are not accepted merely because the Producer reports them as complete.

CONTROL must independently determine whether the resulting state is:

* authorized;
* within scope;
* compatible with the governing Architecture and Governance;
* correctly implemented;
* correctly reflected in the Repository;
* correctly reflected on the VPS where applicable;
* and sufficiently evidenced.

Where a Producer change requires VPS-side validation, CONTROL must inspect the actual VPS state rather than assuming that Repository state and VPS state are identical.

CONTROL may then:

* **KEEP** — accept the change as valid;
* **FIX** — require/perform an authorized correction as appropriate;
* **REVERT** — safely remove an unauthorized or invalid change when authorized;
* **INVESTIGATE** — obtain additional evidence;
* **ESCALATE** — when the matter crosses an authority, architecture, governance, security, invariant, or scope boundary.

A normal implementation problem that can be resolved within the existing Task Order should not unnecessarily stop the project or trigger a new authorization cycle.

---

## 5. Repository, VPS, Runtime and Evidence

The following must remain logically distinct:

`Repository State ≠ VPS State ≠ Runtime State ≠ Verification Evidence`

A Repository change does not automatically prove a corresponding VPS change.

A VPS state does not automatically prove that the change was authorized or correctly represented in the Repository.

Producer self-test evidence does not automatically constitute independent CONTROL verification.

Where applicable, CONTROL should verify the relevant state directly.

---

## 6. Shared Operating Model

The normal workflow is:

`CONTROL Authorization → Producer Implementation / Self-Test → Build Report → CONTROL Independent Review / Verification → Correction or Acceptance → Authorized VPS / Operational Action where applicable → Final Verification → CURRENT_CHECKPOINT`

Both roles may work directly with the Repository and the project development environment according to their respective responsibilities.

The purpose of this boundary is **not to create unnecessary access restrictions or approval cycles**.

Its purpose is to ensure that:

* the Producer has enough practical access to perform the implementation job correctly;
* CONTROL has enough practical access to govern, operate, inspect, correct, and verify the project correctly;
* neither role silently assumes the authority of the other;
* every change remains traceable to an authorized scope;
* implementation and independent verification remain distinct;
* and the successful operational model established during Phase 1 can continue without ambiguity.

---

## 7. Governing Boundary

Nothing in this document authorizes:

* V1 modification or integration;
* autonomous trading;
* capital control;
* unauthorized production activity;
* Constitution or Invariant violations;
* unauthorized architectural or governance changes;
* arbitrary scope expansion;
* creation of competing Roles or Stable IDs.

All existing higher-level project constraints remain in force.

This document is intended to serve as the common operational interpretation for both `ROL-V2-001` and `ROL-V2-002` so that Repository, VPS, implementation, operational, correction, and verification responsibilities do not become a source of repeated ambiguity in later phases.
