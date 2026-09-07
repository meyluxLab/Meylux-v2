# ADR-GOVERNANCE-007 — PROJECT GUIDE Stable Identity Extension

**Project:** Meylux V2  
**Status:** RATIFIED / FROZEN  
**Decision ID:** `ADR-GOVERNANCE-007`  
**Decision Authority:** PROJECT OWNER  
**Ratifying Authority:** PROJECT OWNER  

## 1. Decision Purpose

This ADR establishes the minimum necessary extension of the existing V2 Role Stable Identity basis so that the formally governed `PROJECT GUIDE` role has a unique permanent Stable ID and can proceed through the already-authorized `TO-GOV-001 — PROJECT GUIDE Role Establishment` workflow.

## 2. Ratified Identity

The PROJECT GUIDE logical Role is assigned the next unused Role Stable ID under the existing `ROL-V2-NNN` namespace:

```text
ROL-V2-008
```

This decision extends the identity scope of `ADR-ROLE-IDENTITY-001` only by adding the PROJECT GUIDE logical Role. It does not alter any of the seven existing Role identities.

## 3. Identity Rules

1. `PROJECT GUIDE` is one logical V2 Role.
2. `ROL-V2-008` is its unique permanent Stable ID.
3. The Stable ID is independent of filename, repository path, chat name, or model occupying the Role.
4. The Stable ID must not be reused for another Role.
5. The substantive PROJECT GUIDE Role Contract is unchanged by this identity decision.
6. No other new Role or unrelated entity receives an identity under this ADR.
7. The existing seven Role SIDs remain unchanged.

## 4. Registry Integration

`ROL-V2-008` shall be entered into the existing authoritative `docs/registry/artifacts.yaml` Registry as:

```text
stable_id: ROL-V2-008
canonical_name: PROJECT GUIDE
entity_type: ROLE
artifact_path: docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md
traceability: ADR-GOVERNANCE-007 / TO-GOV-001
```

Registry registration is a controlled implementation action and is not performed by this ADR merely by being ratified.

## 5. Relationship to TO-GOV-001

Ratification of this ADR removes the Stable Identity blocker for `TO-GOV-001` and permits the authorized governance workflow to continue without reopening Phase 0:

```text
TO-GOV-001
→ PROJECT GUIDE ROLE CONTRACT
→ BR-GOV-001 BUILD REPORT
→ CONTROL AUDIT
→ PROJECT OWNER RATIFICATION
→ AUTHORITATIVE REGISTRY ENTRY
→ ROLE CONTRACT FREEZE
→ INDEPENDENT VERIFICATION
```

The existing `BR-GOV-001` identity remains unchanged.

## 6. Boundaries

This ADR does not:

- reopen Phase 0;
- reopen Pre-Project;
- modify the frozen Master Architecture;
- modify the Constitution;
- modify the substantive PROJECT GUIDE Role Contract;
- authorize Phase 1;
- authorize runtime, VPS, provider-runtime, market-data execution, trading, capital, or V1 activity;
- grant PROJECT GUIDE governance, ratification, implementation, execution, trading, or capital authority.

## 7. Ratification

The Project Owner explicitly ratified this ADR with the following statement:

> I ratify ADR-GOVERNANCE-007 — PROJECT GUIDE Stable Identity Extension.

Accordingly, `ADR-GOVERNANCE-007` is authoritative and frozen as the identity basis for `PROJECT GUIDE`.

## 8. Ratification Effect

This decision authorizes CONTROL to perform the remaining controlled establishment steps under `TO-GOV-001`, including authoritative Registry registration and the subsequent governed Role Contract ratification/freeze and independent verification steps, subject to their respective authorities and evidence requirements.
