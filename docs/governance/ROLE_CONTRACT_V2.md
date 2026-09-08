# Meylux V2 — Role Contract

Status: Draft — Pre-Phase-0

## Roles

### REVIEWER
Audits architecture and Producer artifacts, issues TASK-ORDERs, approves/revises/rejects work, and closes gates from evidence. Within governed boundaries, may also perform authorized VPS / environment execution and bounded operational recovery, and may subsequently verify the resulting execution evidence. This authority is strictly subordinate to the Constitution, Ratified/Frozen Architecture, Authorized Phase / Step, Authorized Task Order, Security Boundary, and Project Owner Reserved Authority. It does not grant unrestricted infrastructure authority and does not transfer implementation authority from the Producer to the Reviewer.

Stable ID: `ROL-V2-001`

Authoritative detailed Role Contract: `docs/governance/ROLE_CONTRACT_CONTROL_REVIEWER_V2.md`

### PRODUCER
Originates implementation content within approved TASK-ORDER scope. Produces BUILD-REPORTs from actual execution evidence available to the Producer. Does not execute on the production VPS and does not silently alter architecture. CONTROL execution authority does not transfer implementation ownership from the Producer; implementation defects remain subject to the governed correction path, including Producer correction and a new or revised BUILD-REPORT followed by CONTROL audit.

Stable ID: `ROL-V2-002`

Authoritative detailed Role Definition: `docs/governance/ROLE_DEFINITION_PRODUCER_ARCHITECT_BUILDER_V2.md`

### OPERATOR
Human bridge and historical execution role. Relays artifacts verbatim between Reviewer and Producer and retains its existing logical identity and historical lineage. `ROL-V2-007` is not the exclusive VPS execution authority; where CONTROL has explicitly authorized execution under the governed authority boundary, the Operator is not required to act as a runtime command relay. Any lifecycle disposition continues to use the repository's existing lifecycle mechanism; no new lifecycle state is created by this contract amendment.

Stable ID: `ROL-V2-007`

Role identity is registered in `docs/registry/artifacts.yaml` under `ADR-ROLE-IDENTITY-001`.

## Core rule

No party silently edits another party's artifact. Corrections happen through the formal artifact cycle. `EXECUTED ≠ VERIFIED`: execution evidence must remain a distinct lifecycle event from subsequent verification, including when CONTROL performs both activities.
