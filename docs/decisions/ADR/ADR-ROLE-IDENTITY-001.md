# ADR-ROLE-IDENTITY-001 — V2 Role Stable Identity Basis

**Project:** Meylux V2  
**Status:** APPROVED GOVERNANCE DECISION — LIMITED SCOPE  
**Decision ID:** `ADR-ROLE-IDENTITY-001`  
**Scope:** The seven existing V2 logical Roles only  
**Phase 0:** NOT AUTHORIZED  

## 1. Decision

The existing V2 Stable Identity model is extended by the minimum necessary, narrowly scoped entity prefix:

```text
ROL = Logical Role
```

Role Stable IDs use the form:

```text
ROL-V2-NNN
```

The following seven already-defined logical Roles are assigned these unique Stable IDs:

| Role | Stable ID |
|---|---|
| CONTROL / REVIEWER | `ROL-V2-001` |
| PRODUCER / ARCHITECT-BUILDER | `ROL-V2-002` |
| PRODUCER RELAY | `ROL-V2-003` |
| MARKET INTELLIGENCE | `ROL-V2-004` |
| PHASE CHAT | `ROL-V2-005` |
| TROUBLESHOOTING | `ROL-V2-006` |
| OPERATOR | `ROL-V2-007` |

## 2. Basis

The V2 Master Architecture defines logical identity as independent of path/name and defines the Master Registry as the stable-identity and traceability authority. Its existing entity-prefix table does not define a Role prefix. The Artifact Protocol requires every official artifact to have a Stable ID.

This decision therefore establishes only the missing Role namespace required to identify the seven already-defined Roles. It does not create a new Registry, governance subsystem, Phase, or architecture.

## 3. Identity Rules

1. Each listed Role is one logical entity.
2. A Role SID is independent of the Role file path, filename, chat name, or model occupying the Role.
3. Role SIDs are unique and permanent.
4. A Role SID must not be reused for another Role.
5. Role rename or relocation does not change its SID.
6. The Shared Role Boundary is a governed artifact, not a Role, and receives no `ROL-*` identity under this decision.
7. Existing historical prefixes such as `DOC-*` and `CFG-*` are not promoted into Role identity.
8. No unrelated entity receives a `ROL-*` identity under this decision.

## 4. Registry Target

The seven Role identities shall be registered in the existing `docs/registry/artifacts.yaml` Registry artifact using `entity_type: ROLE`. No competing Role Registry is created.

The registry remains subject to its existing lifecycle and ratification rules. Registering these seven identities does not ratify the Master Architecture and does not authorize Phase 0.

## 5. Traceability

Each Registry record shall reference the corresponding Role Contract / Role Definition artifact. Role documents shall reference their assigned SID only as required for identity traceability; their substantive role definitions are unchanged.

## 6. Continuity

The existing Bootstrap/Continuity system shall discover the seven Role SIDs and their repository artifact locations. This is an integration of Role identity into the existing continuity mechanism, not creation of a competing continuity system.

## 7. Boundaries

This decision does not:

- reopen F003;
- reopen G-0 or G-0R;
- reopen PP-00 through PP-12;
- ratify or modify the Master Architecture;
- authorize Phase 0;
- import V1 identities;
- create unrelated Registry records;
- create a new governance subsystem.

## 8. Required Implementation

The Producer shall implement only the registry/traceability/continuity integration for these seven Roles under the controlled Task Order issued by CONTROL / REVIEWER.

Implementation remains distinct from verification and ratification.
