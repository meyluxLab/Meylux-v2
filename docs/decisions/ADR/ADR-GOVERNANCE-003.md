# ADR-GOVERNANCE-003 — Producer Build Report Allocation Delegation

**Status:** RATIFIED
**Decision Authority:** Project Owner
**Scope:** Build Report identity allocation for Producer execution only
**Phase:** PH-P0 operational governance

## Decision

The Project Owner delegates to `ROL-V2-002 — PRODUCER / ARCHITECT-BUILDER` the limited authority to allocate and register the legitimate next Producer Build Report identity required for the Producer's own currently authorized Task Order execution, without a separate CONTROL allocation cycle.

This delegation is an operational governance clarification under the existing Artifact Protocol and does not create a new role, approval mechanism, registry subsystem, or artifact class.

## Allocation Rule

For a currently authorized Producer Task Order:

1. The Producer may allocate exactly one next Build Report identity using the existing convention `BR-P<phase>-<sequence>`.
2. The sequence is the next unused integer for that Phase in the authoritative artifact registry at the time of allocation.
3. Allocation MUST be recorded in `docs/registry/artifacts.yaml` before or atomically with creation of the Build Report artifact, using the repository's normal Git history and collision-visible update behavior.
4. The allocation record MUST link the BR to the Producer's currently authorized Task Order, Step, and Phase.
5. The allocated state MUST remain distinguishable from `VERIFIED`; Producer allocation/production is not approval, audit, or verification.
6. The Producer MUST inspect the authoritative registry immediately before allocation and MUST NOT reuse an existing BR identity.
7. If the authoritative registry changes concurrently and the intended update is rejected by repository content-version protection, the Producer MUST re-read the registry and recompute the next unused sequence. It MUST NOT force-overwrite the registry.
8. The Producer may not allocate BR identities for future, unauthorized, inactive, or already-completed Task Orders.

## Strict Boundaries

The delegated authority does NOT permit the Producer to:

- modify previously registered BR identities or historical BR records;
- alter Stable IDs or the BR naming convention;
- alter Architecture, ADRs, Governance rules, Phase definitions, Step authorization, or unrelated registry records;
- allocate any artifact type other than a Build Report for the Producer's own currently authorized Task Order;
- approve, audit, verify, close, ratify, freeze, or otherwise self-authorize the resulting Build Report or Step;
- activate future Steps or issue future Task Orders;
- modify runtime, V1/VPS, market-data, trading, capital, fund-transfer, or provider-runtime state.

## Collision and Traceability Requirement

The authoritative registry remains the collision and traceability authority. A successful allocation is valid only when the repository records the new BR entry with a unique stable ID, canonical path, and Task Order / Step / Phase traceability. The Producer must preserve all pre-existing registry records and must not use destructive replacement to manufacture a sequence.

## Independent Verification

CONTROL / REVIEWER (`ROL-V2-001`) remains the independent audit and verification authority. Producer-created BR allocation and production MUST enter an unverified/produced state until independently audited. No Producer allocation is evidence of approval or verification.

## Immediate Application

This delegation applies immediately to `TO-P0-004 / STEP-P0-003 / PH-P0`. The currently legitimate immediate Build Report destination is `BR-P0-005` at `docs/build-reports/BR-P0-005.md`, subject to the allocation record in the authoritative registry.

## Governance Boundary

This ADR does not redesign the Artifact Protocol, alter the Phase 0 sequence, ratify/freeze the Master Architecture, reopen G-0/G-0R, or authorize any runtime or V1 activity. It only removes the recurring manual allocation dependency for the narrowly bounded Producer Build Report allocation operation.
