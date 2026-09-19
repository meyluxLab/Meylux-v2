# ADR-QUANTITATIVE-002 — Volume Profile, Order Flow & Derivatives Semantics

Status: RATIFIED / AUTHORIZED
Stable ID: ADR-QUANTITATIVE-002
Decision Authority: ROL-V2-001 — CONTROL / REVIEWER
Delegation Authority: Project Owner Directive — AUTHORIZE STEP-P4-004 / Volume Profile, Order Flow & Derivatives Engine, 2026-09-19
Phase / Step: PH-P4 / STEP-P4-004
Task Order: TO-P4-005
Affected Specification: DOC-P4-003

## 1. Decision
CONTROL establishes DOC-P4-003 as the authoritative deterministic semantic specification for STEP-P4-004.
It freezes exact Decimal profile binning, POC tie-breaking, 70% Value Area expansion/tie-breaking, configuration-driven HVN/LVN, Bar Delta/CVD, configuration-driven imbalance, evidence-bounded absorption, canonical-only derivatives handling, deterministic funding velocity/acceleration and OI delta derivation, explicit unavailable/insufficient semantics, replay and Rule-5 edge requirements.

## 2. Authority and consequences
This decision is subordinate to the Constitution, frozen Master Architecture, superior ratified ADRs, canonical contracts, and P4-001 numeric policy. It does not amend those authorities.
Existing canonical contracts are the input boundary; no new canonical Stable ID is invented. Any genuinely required additive output-contract extension must use governed contract change and remain minimal.
No future Step is activated by this ADR.

## 3. Evidence discipline
Absent canonical evidence must produce explicit unavailable/insufficient status rather than reconstruction or fabrication. Identical governed inputs and explicit configuration must replay deterministically.

## 4. Scope
Only STEP-P4-004 is affected. STEP-P4-005, STEP-P4-006, G-4, Phase 5+, AI interpretation, Venue Intelligence, trading/capital/execution, V1, and VPS/runtime remain outside scope.

## 5. Traceability
Primary specification: docs/quantitative/P4_004_VOLUME_ORDERFLOW_DERIVATIVES_SEMANTICS.md
Task Order: docs/task-orders/TO-P4-005.md
Owner authorization: Project Owner Directive received 2026-09-19.
Closure remains CONTROL-owned under ADR-GOVERNANCE-012.