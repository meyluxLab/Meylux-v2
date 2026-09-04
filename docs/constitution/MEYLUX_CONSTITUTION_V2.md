# Meylux V2 — Constitution

**Status:** DRAFT — PENDING RATIFICATION  
**Scope:** Meylux V2 only  
**Legacy V1:** FROZEN and outside V2

This document is the repository representation of the V2 constitutional boundary. It is not a ratification record and does not by itself authorize implementation, gate closure, or runtime execution.

## 1. Mission

Meylux V2 is an AI-first, deterministic-baseline, read-only market intelligence and decision-support platform.

## 2. Architectural Invariants

1. **Strict read-only:** Meylux V2 has no authority to place, modify, cancel, or execute trades, manage leverage, move funds, or control trading accounts.
2. **AI-first, not AI-only:** AI reasons over validated evidence; deterministic financial calculations and structural mathematics remain authoritative for mathematical truth.
3. **No data fabrication:** Missing, stale, contradictory, unavailable, or insufficient market information must remain explicitly represented.
4. **Evidence hierarchy:** Verified real market data precedes deterministic computation, validated market structure, derivatives/order-flow evidence, specialist outputs, AI interpretation, and hypothesis.
5. **Source-of-truth separation:** Durable authoritative state belongs in the governed repository/artifact model and, for runtime market data, the approved authoritative database. Redis is not permanent source of truth.
6. **Provider agnosticism:** Provider-specific behavior remains behind provider abstractions.
7. **Stable logical identity:** Renames or relocations must preserve governed logical identity and traceability.
8. **Evidence discipline:** Design, implementation, execution, verification, acceptance, and ratification are distinct states and may not be silently conflated.
9. **V1 isolation:** V1 is historical reference/lesson material and is not a V2 implementation dependency.
10. **No autonomous trading authority:** No component, including AI, may exercise trading authority.

## 3. Architecture Hierarchy

The V2 hierarchy is:

1. Architectural Invariant
2. Required Capability
3. Required Behavior
4. Implementation Choice
5. Configuration / Operational Parameter
6. Performance Target / SLO

Lower tiers must not silently override higher tiers.

## 4. Governance Boundary

The Reviewer audits and governs; the Producer designs/builds within authorized scope and reports actual evidence; the Operator executes approved physical/environment actions.

No party silently edits another party's artifact. Durable project authority resides in governed repository artifacts and evidence, not hidden chat state.

## 5. Ratification Boundary

This constitution is a draft repository artifact pending the formal V2 formation ratification process.

This baseline revision does not:
- close G-0;
- ratify G-0R;
- authorize Phase 0;
- initialize the Registry;
- install the package into GitHub;
- establish runtime implementation or execution evidence.
