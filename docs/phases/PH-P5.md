# PH-P5 — Specialist Market Intelligence Layer

**Status:** ACTIVE / AUTHORIZED
**Current Step Lifecycle:** `STEP-P5-002` — COMPLETE / VERIFIED
**Last Completed Task Order:** `TO-P5-002`
**Completion Audit:** `AR-P5-002`
**Phase SID:** `PH-P5`
**Architectural basis:** `DOC-V2-ARCH-001` RATIFIED / FROZEN; §16–§17
**Predecessor:** `PH-P4` CLOSED / VERIFIED; `G-4` ESTABLISHED / VERIFIED
**Successor:** `PH-P6` — not established by this document
**Reference roadmap:** `DOC-P5-001` — `docs/blueprint/PHASE5_ROADMAP.md` — REGISTERED / REFERENCE ONLY
**Entry authorization:** Project Owner — PHASE 5 RE-DIRECTION AND SIMPLIFIED ESTABLISHMENT DIRECTIVE — 2026-09-23
**Phase owner:** `ROL-V2-001` — CONTROL / REVIEWER

## Objective

Phase 5 interprets authoritative upstream facts through independent specialist domains and produces deterministic, structured, traceable specialist evidence. It does not create new upstream mathematical truth, perform cross-specialist synthesis, produce final scoring or trading decisions, or perform trading/capital/custody activity.

## Current Product Scope

- Spot + Futures simultaneously.
- Initial instruments: `BTCUSDT` and `SOLUSDT`.
- Venues: Binance and MEXC.
- Only public market data and provider capabilities actually required by an authorized Step.
- Forex is future intent only and is not implementation scope for PH-P5.

## Owner Decisions Governing Phase 5

- **PD-1:** Real public market-data acquisition from Binance and MEXC is authorized within the Phase 5 scope; no private credentials/account access.
- **PD-2:** Spot + Futures are simultaneous current scope; Forex is future extension.
- **PD-3:** `BTCUSDT` and `SOLUSDT`; no silent substitution.
- **PD-4:** Stage-1 specialist independence: each specialist receives only the authoritative shared Input Snapshot.
- **PD-5:** Mathematical boundary remains deterministic comparison, classification, ranking, set membership, and simple difference/ratio operations on existing facts.
- **BND-1 / PROC-1:** applied as Blueprint-defined governance/procedural entries, not Owner decisions.

## Non-Negotiable Boundaries

- No trading, execution, capital management, custody or account control.
- No LLM calls in P5 unless separately governed; the current specialist model is deterministic/rule-based.
- No fabrication or synthetic market data presented as real.
- No silent instrument substitution.
- No speculative dependency construction.
- No silent reopening or absorption of P2/P3/P4 ownership.
- Existing `PH-P0` through `PH-P4`, their Stable IDs and verified evidence remain closed and are not reopened by Phase 5.
- Genuine upstream gaps are handled just-in-time through the owning phase/change-control route.

## Step Sequence

### `STEP-P5-001` — Contract, Evidence Model, Config & Persistence Foundation

**Order:** 1
**Status:** COMPLETE / VERIFIED
**Completion Audit:** `AR-P5-002`
**Authorization state:** COMPLETE / VERIFIED
**Predecessor:** `STEP-P4-006` — COMPLETE / VERIFIED
**Active Task Order:** `null`
**Activation basis:** Project Owner — PHASE 5 RE-DIRECTION AND SIMPLIFIED ESTABLISHMENT DIRECTIVE — 2026-09-23

Purpose: establish the specialist contract/evidence model, configuration and append-only persistence foundation required by later Phase 5 execution, while preserving Stage-1 independence and the frozen architecture.

This Step does not implement later specialist groups, cross-specialist synthesis, Forex, or Futures acquisition. It may identify concrete upstream/provider gaps and route them through the correct governed owner when actual evidence demonstrates they are required.

Required evidence includes deterministic contract semantics, explicit status/reason handling, no NaN/Inf, versioned configuration, append-only persistence semantics, tests, and the applicable VPS evidence required by the Task Order.

### `STEP-P5-002` — Input Snapshot Builder & Fact Availability Verification

**Order:** 2  
**Status:** ACTIVE / AUTHORIZED  
**Authorization state:** ACTIVE / AUTHORIZED  
**Predecessor:** `STEP-P5-001` — COMPLETE / VERIFIED  
**Active Task Order:** `null`  
**Activation basis:** Project Owner — PHASE 5 CONTINUATION AUTHORIZATION — 2026-09-23

Purpose: establish the authoritative Stage-1 Input Snapshot boundary and the Fact Requirements Matrix (FRM), using only existing authoritative persisted facts and preserving no-lookahead, provenance, deterministic identity and specialist independence.

This Step does not implement PRQ-1/2/3/4, provider runtime activation, specialist execution, later specialist groups, Futures acquisition, Forex, or cross-specialist synthesis.

VPS boundary: CONTROL-only, SentinelX-only, read-only verification required for Step acceptance; no mutation, restart, migration, deployment or provider-runtime activation.

Required evidence includes the final FRM, deterministic Snapshot identity/replay, no-lookahead boundary tests, explicit missing/unsupported/unavailable/insufficient/invalid/stale semantics, specialist-independence tests, and applicable read-only VPS fact-availability evidence.

## Continuation and Dependency Rule

Phase 5 follows just-in-time dependency completion. A dependency is not treated as a blanket Phase prerequisite merely because the Roadmap mentions it. When an authorized Step demonstrates an actual dependency, CONTROL routes that dependency through the correct ownership and change-control mechanism and continues the Step after the dependency is legitimately resolved or explicitly dispositioned unavailable.

## Exit Boundary

This Phase is not CLOSED by this establishment. Each Step requires its own Build Report, independent Audit Report, evidence review, and ADR-GOVERNANCE-012 closure synchronization. Phase-level closure requires independent verification of the complete Phase boundary and G-5 evidence.
