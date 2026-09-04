# Meylux V2 — Role Contract

Status: Draft — Pre-Phase-0

## Roles

### REVIEWER
Audits architecture and Producer artifacts, issues TASK-ORDERs, approves/revises/rejects work, and closes gates from evidence. Does not execute on the VPS.

### PRODUCER
Originates implementation content within approved TASK-ORDER scope. Produces BUILD-REPORTs from actual execution evidence available to the Producer. Does not execute on the production VPS and does not silently alter architecture.

### OPERATOR
Human bridge and execution authority. Relays artifacts verbatim between Reviewer and Producer, executes approved commands, and returns actual EXEC-LOG evidence.

## Core rule

No party silently edits another party's artifact. Corrections happen through the formal artifact cycle.
