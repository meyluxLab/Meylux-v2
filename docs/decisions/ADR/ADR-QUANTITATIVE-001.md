# ADR-QUANTITATIVE-001 — Authoritative Market Structure Semantics for STEP-P4-003

**Status:** RATIFIED / AUTHORIZED
**Stable ID:** `ADR-QUANTITATIVE-001`
**Decision Authority:** `ROL-V2-001 — CONTROL / REVIEWER`
**Delegation Authority:** Project Owner Directive — `STEP-P4-003 / TO-P4-004 — Full Authority Delegated to CONTROL for Market-Structure Semantics`, 2026-09-19
**Phase:** `PH-P4`
**Step:** `STEP-P4-003`
**Task Order:** `TO-P4-004`
**Affected Specification:** `DOC-P4-002` — `docs/quantitative/P4_003_MARKET_STRUCTURE_SEMANTICS.md`
**Related Open Question:** `OQ-P4-003-STRUCTURE-SEMANTICS`

## 1. Decision

Under explicit Project Owner delegation, CONTROL establishes and ratifies `DOC-P4-002` as the authoritative Market Structure semantic specification for STEP-P4-003.

The specification resolves the semantic authority gap identified during Producer reconstruction of TO-P4-004.

The selected semantics cover:

- exact 5/5 swing confirmation and equality;
- HH/HL/LH/LL classification;
- deterministic structure states;
- close-confirmed BOS;
- CHOCH as counter-trend break;
- MSS as confirmed new-trend transition after CHOCH;
- FVG creation and lifecycle;
- deterministic Order Block detection/invalidation;
- Breaker transitions;
- exact-equality liquidity pools;
- structural event identity and duplicate prevention;
- append-only invalidation;
- canonical-gap behavior;
- event location versus confirmation/knowledge time;
- deterministic per-bar state evolution and replay.

## 2. Higher-Order Authority

This decision does not amend or override:

- the Constitution;
- DOC-V2-ARCH-001;
- INV-V2-002;
- INV-V2-009;
- INV-V2-010;
- existing authoritative canonical contracts;
- ADR-GOVERNANCE-012;
- ADR-GOVERNANCE-013;
- P4-001 numeric policy;
- any other superior ratified governance authority.

If a higher-order conflict is discovered, the affected semantic decision is stopped and escalated.

## 3. Principal Decisions

1. 5/5 swings use strict inequalities; equality disqualifies the pivot.
2. Swing confirmation occurs only after the fifth future valid closed candle.
3. BOS is close-confirmed, not wick-confirmed.
4. CHOCH moves the structure to UNCONFIRMED rather than immediately declaring a new trend.
5. MSS is the subsequent qualifying confirmation of the opposite trend.
6. FVG mitigation is wick-based and follows the exact three-state lifecycle.
7. Order Blocks use the nearest preceding opposite-body candle tied to a confirmed structural displacement.
8. Breakers result from close-based Order Block invalidation and polarity flip.
9. Liquidity pools require exact Decimal equality; no epsilon/tolerance is introduced.
10. Canonical gaps break continuity and prevent inferred cross-gap structural transitions.
11. Structural facts are immutable; invalidation is additive.
12. All timing semantics distinguish event location from confirmation/knowledge time.

## 4. Rationale

The selected rules maximize deterministic reproducibility while minimizing new configuration and interpretation surfaces. They preserve zero-lookahead, use the existing exact Decimal policy, avoid undocumented tolerance, and create an auditable state machine rather than relying on informal labels.

The full alternatives and consequences considered are recorded in DOC-P4-002.

## 5. Consequences

TO-P4-004 can proceed without Producer inventing semantic behavior.

The Market Structure implementation must treat DOC-P4-002 as authoritative.

The existing generic MarketStructureResult contract is insufficient to express the complete required semantic output directly. A minimal additive contract extension is therefore authorized under the governed contract-change process; the extension must remain limited to the fields required by DOC-P4-002 and must not redesign the quantitative contract family.

No future Phase-4 Step is activated by this decision.

## 6. Evidence / Traceability

This ADR resolves:
`OQ-P4-003-STRUCTURE-SEMANTICS`.

Primary specification:
`docs/quantitative/P4_003_MARKET_STRUCTURE_SEMANTICS.md`

Governed implementation boundary:
`docs/task-orders/TO-P4-004.md`

Owner delegation:
Project Owner Directive received 2026-09-19.

Closure remains CONTROL-owned under ADR-GOVERNANCE-012.
