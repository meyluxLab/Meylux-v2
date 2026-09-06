# Meylux V2 — Phase 0 Definition

**Phase ID:** `PH-P0`  
**Status:** `AUTHORIZED / ACTIVE`  
**Entry prerequisite:** `G-0R` (`RATIFIED / VERIFIED`)  
**First official Step:** `STEP-P0-001`  
**Entry Review:** `AR-P0-ENTRY-001`  
**Active Task Order:** `null` — `STEP-P0-001` is complete/verified; no subsequent Step is currently defined.

## 1. Purpose

Phase 0 establishes and ratifies the final V2 architectural baseline before implementation phases begin.

## 2. Entry Boundary

Phase 0 has been formally authorized after the formation boundary was reviewed and verified:

- PP-00 through PP-12 are `APPROVED / CLOSED` as recorded by the formation status artifact.
- `G-0` is `CLOSED / VERIFIED`.
- `G-0R` is `RATIFIED / VERIFIED`.
- The Phase 0 definition and first Step are present in the authoritative registry.
- CONTROL / REVIEWER completed and recorded the formal Phase 0 Entry Review.

`G-0R` is the prerequisite entry gate; it is not itself the authorization decision.

## 3. First Step

### `STEP-P0-001` — Master Architecture Reconciliation

**Status:** `COMPLETE / VERIFIED`

This Step reconciles `DOC-V2-ARCH-001` against the approved V2 formation knowledge, governance artifacts, relevant ADR/ACR decisions, Open Questions/Deferred Decisions state, and relevant post-baseline project evidence.

The Step must identify and govern the disposition of material conflicts, omissions, assumptions, and architectural inconsistencies before final architecture ratification/freeze.

## 4. Architecture Relationship

Entering Phase 0 does not ratify or freeze `MASTER_ARCHITECTURE_V2.md`.

The Master Architecture remains `DESIGN BASELINE — PENDING RATIFICATION` until the reconciliation work is completed and the required governance approval/evidence is recorded.

## 5. Authorization Boundary

Phase 0 authorization permits only the governed Phase 0 work defined by the registry and active Task Order.

It does not authorize runtime implementation, environment/VPS work, or V1 mutation.

## 6. Scope Control

No future-phase implementation may be introduced through Phase 0 reconciliation. Any material architectural change follows the established ADR/ACR/change-control process.

## 7. Continuation Boundary After STEP-P0-001

`STEP-P0-001` is now `COMPLETE / VERIFIED`.

The Draft Master Architecture explicitly contains a ten-Step P0 roadmap, but its first Step is named `Constitution ratification`, whereas the authoritative Phase Registry and this Phase Definition establish `STEP-P0-001` as `Master Architecture Reconciliation` and record it as complete/verified. Because the Master Architecture is still `DESIGN BASELINE — PENDING RATIFICATION`, its draft sequence cannot be promoted to the authoritative execution roadmap by Reviewer assertion.

Accordingly, the current boundary is broader than merely selecting `STEP-P0-002`: the project requires a formal architecture/governance decision that establishes the authoritative complete Phase 0 sequence and reconciles that sequence with the already-completed `STEP-P0-001` without retroactively rewriting its verified history.

CONTROL / REVIEWER may record this boundary, inspect the proposed roadmap, preserve the existing evidence, and prepare the required decision path. CONTROL / REVIEWER must not invent or implicitly activate a new `STEP-P0-*` identity, promote the draft architecture to ratified status, or issue a Task Order for a future Step before the authoritative sequence and current Step are validly established.

Once the formal decision is recorded, the authoritative Phase Registry and this Phase Definition must be updated with the approved sequence and dependencies. Only then may the next valid Step be activated and its Task Order issued if Producer execution is required.

This boundary does not close or suspend `PH-P0`; Phase 0 remains `AUTHORIZED / ACTIVE`. It records only that the complete Phase 0 roadmap is not yet authoritative and therefore no executable subsequent Step may be activated at this time.
