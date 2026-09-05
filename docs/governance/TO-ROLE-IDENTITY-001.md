# MEYLUX V2 — TASK ORDER

## TO-ROLE-IDENTITY-001 — ROLE IDENTITY / REGISTRY / CONTINUITY INTEGRATION

**Project:** Meylux V2  
**Task Order ID:** `TO-ROLE-IDENTITY-001`  
**Issuer:** CONTROL / REVIEWER  
**Recipient:** PRODUCER  
**Status:** AUTHORIZED TO START  
**Scope:** Seven existing logical Roles only  
**Governing Decision:** `ADR-ROLE-IDENTITY-001`  
**Phase 0:** NOT AUTHORIZED

---

## 1. Objective

Complete the repository-backed Stable Identity integration for exactly these seven existing Roles:

```text
CONTROL / REVIEWER
PRODUCER / ARCHITECT-BUILDER
PRODUCER RELAY
MARKET INTELLIGENCE
PHASE CHAT
TROUBLESHOOTING
OPERATOR
```

The Shared Role Boundary is a governed artifact, not a Role, and is excluded.

## 2. Assigned Stable IDs

Use the following controlled assignments exactly; do not invent alternatives:

| Role | Stable ID |
|---|---|
| CONTROL / REVIEWER | `ROL-V2-001` |
| PRODUCER / ARCHITECT-BUILDER | `ROL-V2-002` |
| PRODUCER RELAY | `ROL-V2-003` |
| MARKET INTELLIGENCE | `ROL-V2-004` |
| PHASE CHAT | `ROL-V2-005` |
| TROUBLESHOOTING | `ROL-V2-006` |
| OPERATOR | `ROL-V2-007` |

The `ROL` namespace and assignments are governed by `ADR-ROLE-IDENTITY-001`.

## 3. Required Changes

### 3.1 Registry

Update the existing:

```text
docs/registry/artifacts.yaml
```

Add exactly seven Role records with:

- Stable ID;
- canonical Role name;
- `entity_type: ROLE`;
- current Role artifact path;
- traceability to `ADR-ROLE-IDENTITY-001`;
- lifecycle/status values supported by the existing Registry schema;
- no speculative metadata.

Do not create `roles.yaml` or another Registry.

Do not populate unrelated Registry entities.

### 3.2 Role Artifacts

Update only the identity/traceability portion of these existing artifacts where necessary:

```text
docs/governance/ROLE_CONTRACT_CONTROL_REVIEWER_V2.md
docs/governance/ROLE_DEFINITION_PRODUCER_ARCHITECT_BUILDER_V2.md
docs/governance/ROLE_CONTRACT_PRODUCER_RELAY_V2.md
docs/governance/ROLE_CONTRACT_MARKET_INTELLIGENCE_V2.md
docs/governance/ROLE_DEFINITION_PHASE_CHAT_V2.md
docs/governance/ROLE_CONTRACT_TROUBLESHOOTING_V2.md
docs/governance/ROLE_CONTRACT_V2.md  (only if a role-identity reference is genuinely required)
```

For OPERATOR, update the existing authoritative Role artifact if present in the repository; do not create a duplicate Role Definition merely to attach the SID.

Do not redesign any Role definition or substantive contract.

### 3.3 Continuity

Integrate Role discovery into:

```text
docs/continuity/MEYLUX_V2_BOOTSTRAP.md
```

The Bootstrap must allow a successor AI/operator to discover the seven Role SIDs and their authoritative repository artifacts using the existing continuity mechanism.

Do not create a second continuity mechanism.

## 4. Constraints

Do not:

- reopen F003;
- reopen G-0 or G-0R;
- reopen PP-00 through PP-12;
- modify the Master Architecture;
- authorize or start Phase 0;
- import V1 identities;
- create competing SIDs;
- create a competing Registry;
- create speculative Role entities;
- assign a Role SID to Shared Role Boundary;
- modify unrelated Registry records;
- change CURRENT_CHECKPOINT unless separately required by an existing authoritative protocol and explicitly authorized.

## 5. Evidence Requirements

The BUILD-REPORT must provide actual repository evidence for:

1. the exact seven SID assignments;
2. the Registry records created/updated;
3. each Role artifact identity reference changed;
4. Bootstrap/Continuity changes;
5. validation performed against duplicate/conflicting SIDs;
6. final repository state relevant to the task;
7. any files intentionally not changed and why.

Do not claim execution, verification, or completion without actual evidence.

## 6. Stop Condition

If any requested change would require a new architecture decision, a new governance subsystem, a competing identity model, an unrelated Registry mutation, or an unauthorized phase transition:

```text
STOP THAT PART
```

Report the exact conflict. Do not improvise.

## 7. Acceptance Criteria

The Producer work is acceptable only when:

- all seven Roles have exactly one unique assigned SID from the approved list;
- Registry contains exactly those seven new Role records and no unrelated additions from this task;
- Role artifact references are traceable;
- Bootstrap discovers all seven Role identities through the existing continuity mechanism;
- Shared Role Boundary has no Role SID;
- no F003/G-0/G-0R/PP-stage reopening occurred;
- Phase 0 remains NOT AUTHORIZED;
- Master Architecture remains unchanged;
- no fabricated evidence is reported;
- actual changed-file evidence is supplied;
- any deviation is explicitly reported.

## 8. Reporting

Return:

```text
BUILD-REPORT
Task Order: TO-ROLE-IDENTITY-001
Status: DONE / BLOCKED / REVISE
```

with actual changed paths, operations, Stable IDs, evidence, self-test/validation, deviations, and unperformed work.

A DONE report does not itself constitute CONTROL verification. CONTROL will audit the submitted evidence before this work is closed.
