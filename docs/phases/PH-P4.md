# PH-P4 — Deterministic Quantitative & Market Structure Engine

**Status:** ACTIVE / AUTHORIZED
**Phase SID:** `PH-P4`
**Architectural basis:** `DOC-V2-ARCH-001` RATIFIED / FROZEN; §14
**Predecessor:** `PH-P3` CLOSED / VERIFIED
**Successor:** `PH-P5` — Specialist Analytical Layer
**Reference roadmap:** `DOC-P4-001` — `docs/blueprint/PHASE4_ROADMAP.md` — REGISTERED / REFERENCE ONLY; roadmap input only
**Entry authorization:** Project Owner Directive — Establish Phase 4 & Authorize STEP-P4-001 — 2026-09-18
**Phase owner:** `ROL-V2-001` — CONTROL / REVIEWER

## Objective

Phase 4 converts trusted, canonical, quality-aware Phase 3 data into deterministic, reproducible, provenance-aware quantitative and market-structure facts for downstream analytical layers.

The governing separation is:

`P3 = Is this data trustworthy?`
`P4 = What deterministic facts can be computed from trusted data?`
`P5/P6 = What do those facts imply?`

Phase 4 owns mathematical truth and deterministic fact generation. It does not delegate authoritative arithmetic or structure semantics to AI interpretation.

## Scope

Phase 4 covers:
- quantitative contracts and deterministic numeric policy;
- shared mathematical primitives and explicit insufficient-history semantics;
- golden-vector infrastructure and controlled numeric reference freezing;
- technical indicators and statistical/volatility computation;
- deterministic market-structure state and event computation;
- volume profile, order-flow and derivatives evidence;
- deterministic market-regime classification;
- venue-aware quantitative evidence comparison, without absorbing the independent Venue Intelligence Track;
- quantitative orchestration, multi-timeframe execution, authoritative persistence, read-only API, replay and Phase 4 exit/G-4 evidence.

## Non-Negotiable Principles

### Determinism

The same governed input must produce the same authoritative output. Mathematical and structural semantics must not depend on mutable runtime state, network state, wall-clock time or hidden nondeterminism.

### Purity

Authoritative quantitative cores must remain pure computation boundaries: no dependency on network, database, filesystem, wall clock or mutable global state.

### Zero NaN / Inf

Insufficient, invalid or unavailable data must never be silently converted to `NaN`, `Inf`, zero, or another fabricated numeric value. Explicit status/reason semantics are required.

### Golden Vector Freeze

Public mathematical functions require reference input/output vectors and exact regression protection. A numeric reference change is governed change, not a test-fixture convenience.

### Zero Lookahead

Authoritative structure computation must not expose future information as though it were available at an earlier observation point. Any confirmation latency must be explicit in the contract and state model.

### Provenance and Reproducibility

Quantitative facts must retain the available source reference, timestamp, symbol, timeframe, venue/context and version semantics required by the authoritative contract.

## Explicit Non-Scope

Phase 4 does not include:
- AI reasoning, LLM calls or specialist interpretation;
- contradiction analysis or scenario synthesis;
- Opportunity Score or Analytical Confidence synthesis;
- final decision support or intelligence-level trade signals;
- order execution, portfolio management, capital, custody, leverage or account control;
- V1 mutation or V1 runtime activity;
- the complete Venue Intelligence / Opportunity Engine represented by `CMP-V2-VENUE-001`;
- redesign of `DOC-V2-ARCH-001`;
- implementation of any later Phase capability.

Venue-aware quantitative evidence may be produced in P4, but Venue Intelligence remains an independent cross-cutting track and is not merged into PH-P4.

## Phase 4 Step Sequence

### `STEP-P4-001` — Quantitative Foundation, Contracts, Numeric Policy & Golden Vector Freeze

**Order:** 1
**Status:** COMPLETE / VERIFIED
**Completion audit:** `AR-P4-001`
**Completed task order:** `TO-P4-001`
**Authorization state:** AUTHORIZED TO EXECUTE
**Predecessor:** `STEP-P3-008` — COMPLETE / VERIFIED
**Active Task Order:** `TO-P4-001`
**Activation basis:** Project Owner Directive — Establish Phase 4 & Authorize STEP-P4-001 — 2026-09-18

Objective: establish the governed quantitative contracts, numeric policy, shared mathematical primitives, explicit insufficient-history behavior, golden-vector infrastructure/freeze boundary and persistence-model foundation required by later Phase 4 Steps.

The Step must establish the minimum authoritative foundation without prematurely implementing the full indicator, market-structure, orchestration or AI layers.

### `STEP-P4-002` — Technical Indicators, Statistical & Volatility Engine

**Order:** 2
**Status:** COMPLETE / VERIFIED
**Authorization state:** VERIFIED / COMPLETE
**Predecessor:** `STEP-P4-001` — COMPLETE / VERIFIED
**Active Task Order:** `null`
**Completed Task Order:** `TO-P4-003` (targeted correction; `TO-P4-002` retained as historical closure record)
**Completion Audit:** `AR-P4-003` (independent correction re-verification; `AR-P4-002` retained as historical audit)
**Activation basis:** Project Owner Directive — Authorize STEP-P4-002 / Targeted Correction and Reverification
**Canonical Task Order:** `docs/task-orders/TO-P4-003.md`

Objective: implement deterministic price/time/volume technical indicators and statistical/volatility features against the verified P4 quantitative foundation and trusted canonical Phase-3 inputs.

Scope boundary: moving averages, momentum, trend/volatility, statistical/realized-volatility measures supported by authoritative contracts, volume/activity features, VWAP and explicitly anchored VWAP, with deterministic parameter handling, warm-up/insufficient-history semantics, temporal correctness, no-lookahead, golden vectors, regression evidence and documentation. This Step does not authorize Market Structure, Volume Profile/Order Flow/Derivatives, Regime, orchestration/API/runtime/G-4, AI interpretation, Venue Intelligence, trading/capital authority, V1 mutation or unrelated refactoring.

### `STEP-P4-003` — Deterministic Market Structure Engine

**Order:** 3
**Status:** COMPLETE / VERIFIED
**Authorization state:** VERIFIED / COMPLETE
**Predecessor:** `STEP-P4-002` — COMPLETE / VERIFIED
**Active Task Order:** `null`
**Completed Task Order:** `TO-P4-004`
**Completion Audit:** `AR-P4-006`
**Authoritative Market Structure Semantics:** `DOC-P4-002` — `docs/quantitative/P4_003_MARKET_STRUCTURE_SEMANTICS.md`  
**Semantic Decision:** `ADR-QUANTITATIVE-001` — RATIFIED / AUTHORIZED  
**Semantic authority basis:** Project Owner delegation dated 2026-09-19  
**Activation basis:** Project Owner Directive — AUTHORIZE STEP-P4-003 / ADR-GOVERNANCE-012 / ADR-GOVERNANCE-013

Objective: implement deterministic swing, structure, BOS, CHOCH, MSS, FVG, order-block, breaker and liquidity facts with explicit state-machine, UNCONFIRMED, canonical-gap and zero-lookahead semantics. Verified under `AR-P4-006`.

Acceptance boundary: event-location versus confirmation/knowledge time; pinned 60-candle trend/BOS and reversal/CHOCH scenarios; event-by-event and state-transition evidence; deterministic replay; explicit ambiguity handling; canonical-gap behavior; focused failure/boundary coverage; no future-Step scope.

### `STEP-P4-004` — Volume Profile, Order Flow & Derivatives Engine

**Order:** 4
**Status:** COMPLETE / VERIFIED
**Authorization state:** VERIFIED / COMPLETE
**Predecessor:** `STEP-P4-003` — COMPLETE / VERIFIED
**Active Task Order:** `null`
**Completed Task Order:** `TO-P4-005`
**Completion Audit:** `AR-P4-009`
**Semantic Authority:** `DOC-P4-003` — RATIFIED / AUTHORIZED
**Semantic Decision:** `ADR-QUANTITATIVE-002` — RATIFIED / AUTHORIZED
**Activation basis:** Project Owner Directive — AUTHORIZE STEP-P4-004 / Volume Profile, Order Flow & Derivatives Engine — 2026-09-19

Objective: implement deterministic Volume Profile, Order Flow and Derivatives evidence from trusted canonical Phase-3 inputs without fabricating unavailable data or absorbing downstream interpretation.

Acceptance boundary: deterministic POC/VAH/VAL, HVN/LVN, Bar Delta/CVD, Imbalance, evidence-bounded Absorption, Funding/OI/Basis analytics, explicit unavailable/insufficient handling, exact Decimal semantics, deterministic replay, boundary/failure coverage and traceability under DOC-P4-003 / ADR-QUANTITATIVE-002.

### `STEP-P4-005` — Deterministic Market Regime Engine & Venue-Aware Quantitative Evidence

**Order:** 5
**Status:** ACTIVE / AUTHORIZED
**Authorization state:** AUTHORIZED TO EXECUTE
**Predecessor:** `STEP-P4-004` — COMPLETE / VERIFIED
**Active Task Order:** `TO-P4-006`
**Activation basis:** PROJECT OWNER DIRECTIVE — AUTHORIZE PH-P4 / STEP-P4-005 AND DELEGATE WORKFLOW AUTHORITY — 2026-09-19

Objective: implement deterministic regime state with hysteresis and venue-aware quantitative evidence while preserving the independent Venue Intelligence Track boundary.

Acceptance boundary: deterministic multi-factor regime classification, explicit hysteresis and transition semantics, unavailable/insufficient/invalid/contradictory handling, zero-lookahead, deterministic replay, provenance/version preservation, venue-aware quantitative evidence comparison with explicit comparability/rejection semantics, focused boundary/failure coverage and traceability under the existing PH-P4 quantitative contracts and numeric policy.

### `STEP-P4-006` — Quant Orchestration, Multi-Timeframe Runtime, Persistence, API, Replay & G-4 Closure

**Order:** 6
**Status:** COMPLETE / VERIFIED
**Authorization state:** VERIFIED / COMPLETE
**Active Task Order:** `null`
**Activation basis:** Project Owner Directive — AUTHORIZE PH-P4 / STEP-P4-006 AND DELEGATE FULL OPERATIONAL WORKFLOW AUTHORITY — 2026-09-19
**Predecessor:** `STEP-P4-005` — COMPLETE / VERIFIED

**Completion Audit:** `AR-P4-015`
**Completed Task Order:** `TO-P4-008`
**G-4:** ESTABLISHED / VERIFIED

Objective: operationalize the verified quantitative engines through controlled orchestration, candle-close and multi-timeframe execution, authoritative persistence, worker/event processing, read-only API, deterministic replay/recovery, controlled real-data vertical-slice validation and the evidence boundary for G-4 and Phase 4 closure.

## Dependency Rule

The governed dependency is:

`PH-P3 → STEP-P4-001 → STEP-P4-002 → STEP-P4-003 → STEP-P4-004 → STEP-P4-005 → STEP-P4-006 → G-4`

A later Step must not rely on unverified behavior from its predecessor. Preparation and independent fixtures may proceed where they do not depend on unverified predecessor semantics, but no later Step is authorized merely because its roadmap entry exists.

## STEP-P4-001 Foundation Boundary

The first Step shall establish, at minimum and within the actual authoritative repository contracts:

1. quantitative domain contracts for Indicator, Market Structure, Volume Profile, Order Flow and Regime;
2. semantics for value/status/reason/source reference/timestamp/timeframe/symbol/venue-context/version where supported by governing contracts;
3. numeric representation, precision, rounding, quantization, permitted comparison tolerance and serialization policy;
4. shared deterministic rolling, average, weighted, smoothing, standard-deviation, percentile/ranking, accumulation and normalization primitives as actually required;
5. explicit insufficient-history behavior with no numeric fabrication;
6. extensible golden-vector fixture and runner infrastructure with exact comparison semantics;
7. governance boundary for changing frozen mathematical references;
8. persistence-model foundation for the five roadmap-identified quantitative output families, subject to authoritative schema/architecture reconciliation:
   - `DB-P4-001` — `calculated_indicator_vectors`
   - `DB-P4-002` — `market_structure_events`
   - `DB-P4-003` — `market_structure_zones`
   - `DB-P4-004` — `volume_profile_sessions`
   - `DB-P4-005` — `market_regime_states`
9. tests covering nominal, boundary, missing, malformed, contradictory and insufficient-input behavior appropriate to the foundation;
10. traceability sufficient for later independent CONTROL audit.

Roadmap names are planning inputs. The Producer must inspect the actual repository contracts, schemas and existing implementation before fixing implementation-level details. No speculative Stable ID or schema is to be created solely because the roadmap mentions it.

## Quality Standard — ADR-GOVERNANCE-013 Rule 5

Every part of the authorized Step must be built to the maximum achievable standard of correctness, robustness, reproducibility and efficiency, aimed at the highest realistically attainable success rate for the finished product. Minimum-to-pass quality is insufficient.

CONTROL applies this standard in audit and governance decisions and must carry it into the Task Order. Producer must apply it to every implementation detail, including edge cases, deterministic semantics, test depth, numeric integrity, documentation and evidence quality.

This standard does not expand scope, override higher-authority architecture/governance, or bypass Rule 1 stop conditions.

## Governance and Role Boundaries

- `ROL-V2-001` retains governance, architectural-consistency control, Task Order authority, independent verification and closure synchronization.
- `ROL-V2-002` implements only the currently authorized Task Order and supplies a Build Report with real evidence.
- Producer does not self-declare VERIFIED/CLOSED and does not perform CONTROL-owned closure synchronization.
- No VPS action is authorized by this Phase definition itself; any required VPS operation remains subject to the specific Task Order and SentinelX-only boundary.
- No implementation may modify V1, introduce trading/capital authority, or silently change frozen contracts, Stable IDs or architecture.

## Completion Boundary

Phase 4 may be declared CLOSED / VERIFIED only after all six Steps are independently verified, the deterministic quantitative and market-structure outputs are operationally evidenced, replay/reproducibility and required persistence/API behavior are verified, G-4 evidence is established, and ADR-GOVERNANCE-012 peripheral synchronization is completed by CONTROL.

`IMPLEMENTED != EXECUTED != TESTED != VERIFIED != CLOSED`

## Current Step Boundary After P4-004 Closure

STEP-P4-003 is COMPLETE / VERIFIED under AR-P4-006. STEP-P4-004 is COMPLETE / VERIFIED under TO-P4-005 / AR-P4-009. STEP-P4-005 is COMPLETE / VERIFIED under TO-P4-006 / AR-P4-011. STEP-P4-006 is COMPLETE / VERIFIED under AR-P4-015; TO-P4-008 is VERIFIED / COMPLETE; G-4 is ESTABLISHED / VERIFIED. Historical AR-P4-004 and AR-P4-005 remain preserved for traceability.

## Standing Role Operating Rules — ADR-GOVERNANCE-013

1. **Continuation Duty:** continue to the highest genuinely authorized boundary. Difficulty, ordinary implementation problems and normal test failures are not blockers. Stop only for (A) actual Owner decision/ratification, (B) unresolved authoritative conflict, or (C) natural completion requiring independent verification.
2. **Same-Response Communication Duty:** whenever work requires text to be carried to another governed role, produce the complete forward-ready message in the same response.
3. **Large Artifact Retrieval:** use Identify artifact → real Blob SHA → fetch_blob → complete artifact → read/search/verify; never proceed from truncated content.
4. **SentinelX-Only VPS Execution:** any genuinely required VPS action must use SentinelX exclusively under the applicable authorization.
5. **Maximum Quality and Success-Rate Standard:** every part of the system within an authorized boundary must be built to the maximum achievable standard of correctness, robustness, and efficiency, aimed at the highest realistically attainable success rate. Minimum-to-pass quality is not sufficient. This never expands scope or overrides Rule 1 stop conditions. CONTROL must apply and explicitly convey this governing intent; Producer must apply it to every implementation detail. Indefinite hedging, repeated re-verification without new evidence, or failure to reach a definitive, well-supported conclusion is itself a quality failure.

Every substantive response must end with the `--- STANDING RULES CHECK ---` footer required by `ADR-GOVERNANCE-013`.

## Mandatory Peripheral Synchronization

`ADR-GOVERNANCE-012` applies to every Step/Phase closure. At closure CONTROL must synchronize and independently check README, `docs/registry/artifacts.yaml`, applicable specialized registries, standalone status-bearing documents, supplemental/staging registries, Change Ledger and CURRENT_CHECKPOINT as required by the governing protocol.

## Current Phase Boundary

PH-P4 is formally established and ACTIVE / AUTHORIZED. STEP-P4-001 and STEP-P4-002 are COMPLETE / VERIFIED, with STEP-P4-002 re-verified under AR-P4-003. STEP-P4-003 is COMPLETE / VERIFIED under TO-P4-004 / AR-P4-006. STEP-P4-004 is ACTIVE / AUTHORIZED under TO-P4-005. STEP-P4-005 is COMPLETE / VERIFIED under TO-P4-006 / AR-P4-011; STEP-P4-006 is COMPLETE / VERIFIED under AR-P4-015; G-4 is ESTABLISHED / VERIFIED.
