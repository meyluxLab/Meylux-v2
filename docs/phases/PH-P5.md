# PH-P5 — Specialist Market Intelligence Layer

**Status:** ACTIVE / AUTHORIZED
**Current Step Lifecycle:** `STEP-P5-004` — COMPLETE / VERIFIED
**Active Task Order:** `null`
**Active Corrective Dependency:** None — `TO-P4-012` VERIFIED / COMPLETE under `AR-P4-019`
**Last Completed Task Order:** `TO-P5-004`  
**Last Completed Corrective Dependency:** `TO-P4-012` — VERIFIED / COMPLETE under `AR-P4-019`
**Completion Audit:** `AR-P5-004`
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
**Status:** COMPLETE / VERIFIED  
**Authorization state:** COMPLETE / VERIFIED  
**Completion Audit:** `AR-P5-002`  
**Predecessor:** `STEP-P5-001` — COMPLETE / VERIFIED  
**Active Task Order:** `null`  
**Activation basis:** Project Owner — PHASE 5 CONTINUATION AUTHORIZATION — 2026-09-23

Purpose: establish the authoritative Stage-1 Input Snapshot boundary and the Fact Requirements Matrix (FRM), using only existing authoritative persisted facts and preserving no-lookahead, provenance, deterministic identity and specialist independence.

This Step does not implement PRQ-1/2/3/4, provider runtime activation, specialist execution, later specialist groups, Futures acquisition, Forex, or cross-specialist synthesis.

VPS boundary: CONTROL-only, SentinelX-only, read-only verification required for Step acceptance; no mutation, restart, migration, deployment or provider-runtime activation.

Required evidence includes the final FRM, deterministic Snapshot identity/replay, no-lookahead boundary tests, explicit missing/unsupported/unavailable/insufficient/invalid/stale semantics, specialist-independence tests, and applicable read-only VPS fact-availability evidence.

### `STEP-P5-003` — Runtime Harness & Reference Specialist (S-10)

**Order:** 3  
**Status:** COMPLETE / VERIFIED  
**Authorization state:** COMPLETE / VERIFIED  
**Predecessor:** `STEP-P5-002` — COMPLETE / VERIFIED  
**Activation basis:** Project Owner authorization — `STEP-P5-003 = AUTHORIZED FOR GOVERNED PROGRESSION` — 2026-09-29  
**Active Task Order:** `null`

Purpose: establish the real bounded end-to-end Stage-1 runtime harness and the reference specialist `S-10`, using the authoritative Input Snapshot / FRM boundary and the independently verified P3 quality/acquisition evidence established by `TO-P3-009`.

This Step is the first runtime walking skeleton for Phase 5. It includes bounded execution, deterministic ordering, timeout/isolation/retry semantics, DLQ, overload handling, idempotent persistence/read-back, replay determinism, and a reproducible runtime/resource baseline.

The Step consumes existing authoritative upstream facts only. It does not implement `PRQ-1`, `PRQ-2`, or `PRQ-3`, does not activate new provider acquisition, does not reopen P2/P3/P4 closure, and does not absorb unavailable upstream fact families.

`PRQ-4` is a resolved prerequisite for this Step: `TO-P3-009 = VERIFIED / COMPLETE`, `AR-P3-009 = APPROVED / VERIFIED`.

The reference specialist `S-10` must emit deterministic, evidence-backed quality/acquisition interpretation, including explicit handling of non-`VALID`, stale, incomplete, contradictory and unavailable inputs. No evidence or timestamp may be fabricated.

VPS/runtime work required by this Step is CONTROL-owned and SentinelX-only under `ADR-GOVERNANCE-011`; Producer implementation remains within the governed development workspace unless CONTROL performs the authorized runtime deployment/verification.

Required evidence includes actual end-to-end runtime execution, failure isolation, bounded retry, DLQ, overload, duplicate/replay behavior, append-only persistence/read-back, security, CI coverage and the Step performance/resource baseline. Passing tests alone does not constitute Step verification.


### `STEP-P5-004` — Group A: Technical, Multi-Timeframe, Volatility

**Order:** 4  
**Status:** ACTIVE / AUTHORIZED  
**Authorization state:** AUTHORIZED TO EXECUTE  
**Predecessor:** `STEP-P5-003` — COMPLETE / VERIFIED  
**Active Task Order:** `TO-P5-004`  
**Activation basis:** Project Owner directive — `STEP-P5-004` normal governed continuation — 2026-10-02  
**Upstream dependency:** `PRQ-1 GROUP-A CAPABILITY = ESTABLISHED / VERIFIED`; corrective root-cause dependency `TO-P4-012 / AR-P4-019` is VERIFIED / COMPLETE

Purpose: establish the real deterministic Group-A specialist capability for `S-01` Technical, `S-06` Multi-Timeframe and `S-08` Volatility using the authoritative Stage-1 Input Snapshot and the independently verified P4 Group-A fact surface.

The Step consumes authoritative P4 facts; it does not create new P4 mathematical truth. It preserves Stage-1 specialist independence, no-lookahead, deterministic evidence identity, provenance, append-only specialist persistence and explicit unavailable/insufficient semantics.

The Group-A boundary includes configured technical facts (EMA, RSI-14, MACD 12/26/9, ADX-14, Bollinger 20/2 and bandwidth), multi-timeframe interpretation across the governed timeframes, and volatility facts/classification (ATR-14, historical volatility, ATR percentile, expansion ratio and Bollinger bandwidth). Indicator divergence is outside this Step.

Required evidence includes deterministic specialist behavior, boundary/golden-vector tests, no-lookahead, real `INSUFFICIENT_DATA` behavior where applicable, EvidenceRef resolution, replay/idempotency, append-only persistence/read-back, specialist independence, applicable runtime/VPS evidence and a reproducible performance/resource baseline.

VPS/runtime work is CONTROL-owned and SentinelX-only. Producer implementation remains within the authorized development workspace. `STEP-P5-005` and later Steps remain unauthorized and out of scope.

## Continuation and Dependency Rule

Phase 5 follows just-in-time dependency completion. A dependency is not treated as a blanket Phase prerequisite merely because the Roadmap mentions it. When an authorized Step demonstrates an actual dependency, CONTROL routes that dependency through the correct ownership and change-control mechanism and continues the Step after the dependency is legitimately resolved or explicitly dispositioned unavailable.

## Exit Boundary

This Phase is not CLOSED by this establishment. Each Step requires its own Build Report, independent Audit Report, evidence review, and ADR-GOVERNANCE-012 closure synchronization. Phase-level closure requires independent verification of the complete Phase boundary and G-5 evidence.


## STEP-P5-004 Closure

`STEP-P5-004` / `TO-P5-004` is COMPLETE / VERIFIED under `AR-P5-004`. CONTROL independently verified the corrected Group-A implementation against CI, authoritative P4 PostgreSQL records, Redis → specialist worker → PostgreSQL persistence/read-back, replay/idempotency, append-only security boundaries and runtime performance/resource evidence. `PH-P5` remains ACTIVE / AUTHORIZED; no later Step is activated.
