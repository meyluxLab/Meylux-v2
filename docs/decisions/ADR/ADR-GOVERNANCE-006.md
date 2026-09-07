# ADR-GOVERNANCE-006 — Post-Freeze Governance Build Report Identity Convention

**Status:** PROPOSED — RATIFICATION REQUIRED
**Decision ID:** `ADR-GOVERNANCE-006`
**Decision Authority:** PROJECT OWNER

## Decision Proposal

The Project Owner is requested to ratify the following permanent identity convention for Build Reports produced for formally governed post-freeze Task Orders that do not belong to an active Phase:

```text
BR-GOV-<NNN>
```

where:

- `BR` = Build Report
- `GOV` = Post-Freeze Governance / Governance Activity
- `<NNN>` = permanent three-digit sequential identifier
- identifiers are never reused

The canonical repository path is:

```text
docs/build-reports/BR-GOV-<NNN>.md
```

## Scope

This convention applies only to Build Reports that document Producer work performed under a ratified `TO-GOV-<NNN>` Task Order.

It does not create a new Phase, reopen or reactivate any frozen Phase, modify frozen architecture, or grant any authority to the Producer or the Build Report itself.

Existing Phase-bound Build Reports such as `BR-P0-<NNN>` remain historical and unchanged.

## Allocation Rule

Each `BR-GOV-<NNN>` identity shall be allocated only for the Producer's currently authorized post-freeze Task Order under the applicable governance workflow.

Identifiers are permanent and must not be reused, reassigned, or silently mutated.

The Producer must not self-verify, self-approve, or treat Build Report production as project-level verification.

## First Reserved Use

Following Project Owner ratification of this convention, the first applicable Build Report for:

```text
TO-GOV-001 — PROJECT GUIDE Role Establishment
```

may use:

```text
BR-GOV-001
```

This reservation does not itself establish, ratify, freeze, or verify the PROJECT GUIDE role.

## Boundary

Ratification of this convention:

- does not authorize any new Task Order;
- does not establish or ratify PROJECT GUIDE;
- does not authorize Phase 1 implementation;
- does not modify the Master Architecture;
- does not modify the Constitution;
- does not modify checkpoints or frozen artifacts;
- does not authorize runtime, VPS, provider-runtime, market-data execution, trading, capital, or V1 activity.

## Ratification Statement

> All Build Reports produced for formally governed post-freeze Task Orders that do not belong to an active Phase shall use the permanent identity convention `BR-GOV-<NNN>` with canonical repository path `docs/build-reports/BR-GOV-<NNN>.md`. These Build Reports remain subject to the normal Producer → CONTROL Audit → Project Owner and subsequent verification workflow and do not alter the lifecycle or authority of any frozen Phase.

## Effective State After Ratification

```text
Convention:
BR-GOV-<NNN>

Status:
RATIFIED / FROZEN

Authority:
PROJECT OWNER
```
