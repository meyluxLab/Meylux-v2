# PH-P3 — Validation, Normalization & Data Quality Engine

**Status:** ACTIVE / AUTHORIZED
**Phase SID:** `PH-P3`
**Architectural basis:** `DOC-V2-ARCH-001` RATIFIED / FROZEN; §8.3–8.4 and §13
**Predecessor:** `PH-P2` CLOSED / VERIFIED
**Successor:** `PH-P4` — Deterministic Quantitative & Market Structure Engine
**Reference roadmap:** `DOC-P3-001` — `docs/blueprint/PHASE3_ROADMAP.md` — REGISTERED / REFERENCE ONLY — NOT AUTHORIZED FOR IMPLEMENTATION
**Entry authorization:** Project Owner Final Directive — Phase 3 Establishment + ADR-GOVERNANCE-013 — 2026-09-15
**Phase owner:** `ROL-V2-001` — CONTROL / REVIEWER

## Objective

Phase 3 establishes the Validation, Normalization & Data Quality Engine that converts Phase 2 raw/staging acquisition output into validated, normalized, explicitly quality-classified and traceable canonical data.

Phase 3 owns the trust boundary between provider acquisition and downstream analytical processing.

## Scope

Phase 3 covers schema validation, semantic validation, timestamp and sequence validation, completeness and continuity validation, price and market-data integrity validation, spread integrity validation, tick/lot precision validation, duplicate detection, canonical normalization, provider-to-canonical mapping, cross-venue equivalence and consistency validation, explicit data-quality classification, quarantine / DLQ handling, provenance and lineage, canonical persistence, and normalized event handoff to Phase 4.

## Mandatory Data-Quality Principles

### No Silent Fixing

`Bad Data → Detect → Classify → Route`

The system must not silently guess or repair authoritative market data.

### No Fabrication

Missing, invalid, contradictory, stale, unavailable, or insufficient market values must not be replaced by fabricated values.

### Explicit Degradation

Downstream consumers must be able to distinguish explicit data-quality states including complete/fresh, incomplete, stale, degraded, contradictory, unavailable, and unsupported where applicable.

### Provider Isolation

Provider-specific wire semantics, aliases, event identifiers, sequence details and transport fields remain behind the provider boundary unless an explicit authoritative domain requirement establishes semantic promotion.

### Quarantine, Not Delete, Not Promote

Invalid or untrusted data must not be silently deleted and must not be promoted to canonical truth. It must be isolated according to governed quarantine / DLQ behavior.

### Lineage

Canonical records must remain traceable to upstream evidence and validation history.

## Explicit Non-Scope

The following remain outside Phase 3:

- Technical Indicators including EMA, RSI, MACD, ATR, ADX and Bollinger;
- Market Structure including BOS, CHOCH, MSS, FVG, Order Blocks and Liquidity Pools;
- Volume Profile;
- Order Flow Analytics;
- Regime Classification;
- Specialist Intelligence;
- AI Interpretation;
- Opportunity Score;
- Trade Idea Generation;
- Natural Language Summary;
- Arbitrage / Opportunity Analysis beyond Cross-Venue Validation;
- trading, order execution, capital, custody, leverage, balance, transfer or withdrawal control;
- V1 mutation or V1 runtime activity;
- Phase 4 or later implementation;
- redesign of `DOC-V2-ARCH-001`.

Cross-Venue Validation is within Phase 3. Opportunity Detection is not.

## Phase 3 Step Sequence

### `STEP-P3-001` — Canonical Contracts, Identity & Validation Foundation

**Order:** 1
**Status:** COMPLETE / VERIFIED
**Authorization state:** VERIFIED / COMPLETE
**Active Task Order:** none
**Completed Task Order:** `TO-P3-001`
**Completion Audit:** `AR-P3-001`

Objective: establish the canonical contract, identity, validation semantics and deterministic data-quality foundation required by the remaining Phase 3 Steps.

### `STEP-P3-002` — Structural, Schema & Identity Validation

**Order:** 2
**Status:** ACTIVE / AUTHORIZED
**Authorization state:** AUTHORIZED TO EXECUTE
**Predecessor:** `STEP-P3-001`
**Active Task Order:** `TO-P3-002`

Objective: establish structural, schema and initial identity validation for incoming acquisition data.

### `STEP-P3-003` — Temporal, Sequence & Completeness Validation

**Order:** 3
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-002`

Objective: establish timestamp, ordering, sequence, continuity and completeness validation.

### `STEP-P3-004` — Market Semantic, Price, Spread & Precision Validation

**Order:** 4
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-003`

Objective: establish market-semantic correctness including price, OHLC, quantity, spread and precision validation.

### `STEP-P3-005` — Canonical Normalization & Provider Mapping

**Order:** 5
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-004`

Objective: transform validated provider-normalized evidence into provider-neutral canonical semantics.

### `STEP-P3-006` — Cross-Venue Consistency & Equivalence

**Order:** 6
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-005`

Objective: establish cross-venue equivalence and consistency validation without introducing opportunity detection.

### `STEP-P3-007` — Data Quality, Quarantine, DLQ & Lineage

**Order:** 7
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-006`

Objective: establish explicit quality classification, quarantine/DLQ behavior and lineage.

### `STEP-P3-008` — Authoritative Persistence, Event Handoff & G-3 Verification

**Order:** 8
**Status:** DEFINED / INACTIVE
**Predecessor:** `STEP-P3-007`

Objective: establish authoritative canonical persistence, normalized-event handoff and the evidence boundary required for Phase 3 closure.

## Dependency Rule

The governed dependency is:

`PH-P2 → STEP-P3-001 → STEP-P3-002 → STEP-P3-003 → STEP-P3-004 → STEP-P3-005 → STEP-P3-006 → STEP-P3-007 → STEP-P3-008 → G-3`

A later Step must not rely on unverified behavior from its predecessor. Preparation, fixtures, documentation and bounded tests may proceed in parallel where they do not depend on unverified predecessor behavior.

## Registry Synchronization Rule

Every Phase 3 Step that produces actual evidence in requirements, tests, database, configuration, security, components, contracts, runtime, performance, observability or data-quality domains must register the corresponding record in the applicable specialized registry in the same governed Task Order cycle, with direct evidence traceability. No speculative `CMP-P3-*`, `CTR-P3-*`, `REQ-*` or `TST-*` records are created merely from roadmap intent.

## Standing Role Operating Rules — `ADR-GOVERNANCE-013`

The following rules apply to every governed role and every session:

1. **Continuation Duty:** continue to the highest genuinely authorized boundary. Difficulty, ordinary implementation problems and normal test failures are not blockers. Stop only for (A) actual Owner decision/ratification, (B) an unresolved authoritative conflict requiring a decision rather than a guess, or (C) natural completion requiring independent verification. State A/B/C explicitly when stopping.
2. **Same-Response Communication Duty:** whenever work requires text to be carried to another governed role, produce the complete forward-ready message in the same response. Substantive hand-offs use `FORMAL ENGLISH MESSAGE READY TO SEND` followed by `SIMPLE PERSIAN EXPLANATION`.
3. **Large Artifact Retrieval:** use `Identify artifact → Obtain real Blob SHA → fetch_blob → Retrieve complete artifact → Read / search / verify`; never proceed from truncated content.
4. **SentinelX-Only VPS Execution:** any work genuinely requiring VPS inspection/action must use SentinelX exclusively under `ADR-GOVERNANCE-011`; SentinelX availability does not create new authority.

Every substantive response must end with the `--- STANDING RULES CHECK ---` footer required by `ADR-GOVERNANCE-013`.

## Mandatory Peripheral Synchronization

`ADR-GOVERNANCE-012` applies to every Step/Phase closure. The applicable closure Build Report must individually address: (1) `README.md` synchronization; (2) `docs/registry/artifacts.yaml` lifecycle synchronization; (3) specialized-registry evidence synchronization; (4) standalone status-bearing documents; and (5) supplemental/staging registry absorption or retirement. No closure may be accepted while the checklist is omitted or only partially addressed.

## VPS Boundary

Any VPS inspection or action genuinely required by Phase 3 must be performed exclusively through SentinelX under the existing `ADR-GOVERNANCE-011` privilege model and the specific authorization boundary of the applicable Task Order. No manual or alternative VPS path is permitted. Availability of SentinelX does not itself authorize runtime or VPS changes.

## Completion Boundary

Phase 3 is complete only when all eight Steps are `COMPLETE / VERIFIED`; canonical contracts, validation and normalization behavior, data-quality states, quarantine/DLQ, lineage, authoritative persistence, normalized event handoff, required specialized-registry synchronization, mandatory peripheral synchronization, Phase 3 exit audit and G-3 evidence are all established and verified; and `CURRENT_CHECKPOINT.json` records the closure.

`IMPLEMENTED != EXECUTED != VERIFIED`.

Phase 4 remains `NOT AUTHORIZED` until its own formal establishment and authorization process is completed.
