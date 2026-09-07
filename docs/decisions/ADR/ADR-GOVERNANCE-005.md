# ADR-GOVERNANCE-005 — Post-Freeze Governance Task Order Identity Convention

**Status:** RATIFIED / FROZEN
**Decision ID:** `ADR-GOVERNANCE-005`
**Decision Authority:** PROJECT OWNER
**Ratifying Authority:** PROJECT OWNER

## Decision

The Project Owner formally ratifies the following permanent identity convention for formally governed Task Orders created after Phase/Project Freeze and not belonging to an active Phase:

```text
TO-GOV-<NNN>
```

where:

- `TO` = Task Order
- `GOV` = Post-Freeze Governance / Governance Activity
- `<NNN>` = permanent three-digit sequential identifier
- identifiers are never reused

The canonical repository path is:

```text
docs/task-orders/TO-GOV-<NNN>.md
```

## Scope

This convention applies only to formally governed activities that:

1. occur after a Phase or Project Freeze; and
2. do not belong to an active Phase.

This convention does not reopen, reactivate, or modify any frozen Phase.

In particular:

```text
TO-P0-<NNN>
```

must not be used for new post-freeze governance activities after `PH-P0` has been closed.

## Boundary

Ratification of this convention:

- does not authorize any specific Task Order;
- does not establish or ratify the PROJECT GUIDE role;
- does not authorize Phase 1 implementation;
- does not modify the Master Architecture;
- does not modify any frozen artifact, registry state, or checkpoint;
- does not reopen Phase 0.

A specific `TO-GOV-<NNN>` remains subject to the normal governance and authorization workflow.

## First Reserved Use

Following ratification of this convention, the first applicable Task Order may use:

```text
TO-GOV-001
```

with the intended subject:

```text
PROJECT GUIDE Role Establishment
```

This reservation does not itself constitute authorization or ratification of that Task Order or its target role.

## Ratification Statement

> All formally governed Task Orders created after Phase/Project Freeze and not belonging to an active Phase shall use the permanent identity convention `TO-GOV-<NNN>` with canonical repository path `docs/task-orders/TO-GOV-<NNN>.md`. These Task Orders do not reopen, reactivate, or modify any frozen Phase unless an explicit governance decision separately authorizes such action.

## Effective State After Ratification

```text
Convention:
TO-GOV-<NNN>

Status:
RATIFIED / FROZEN

Authority:
PROJECT OWNER
```
