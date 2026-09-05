# Meylux V2 — Role Contract

Status: Draft — Pre-Phase-0

## Roles

### REVIEWER
Audits architecture and Producer artifacts, issues TASK-ORDERs, approves/revises/rejects work, and closes gates from evidence. Does not execute on the VPS.

Stable ID: `ROL-V2-001`

Authoritative detailed Role Contract: `docs/governance/ROLE_CONTRACT_CONTROL_REVIEWER_V2.md`

### PRODUCER
Originates implementation content within approved TASK-ORDER scope. Produces BUILD-REPORTs from actual execution evidence available to the Producer. Does not execute on the production VPS and does not silently alter architecture.

Stable ID: `ROL-V2-002`

Authoritative detailed Role Definition: `docs/governance/ROLE_DEFINITION_PRODUCER_ARCHITECT_BUILDER_V2.md`

### OPERATOR
Human bridge and execution authority. Relays artifacts verbatim between Reviewer and Producer, executes approved commands, and returns actual EXEC-LOG evidence.

Stable ID: `ROL-V2-007`

Role identity is registered in `docs/registry/artifacts.yaml` under `ADR-ROLE-IDENTITY-001`.

## Core rule

No party silently edits another party's artifact. Corrections happen through the formal artifact cycle.
