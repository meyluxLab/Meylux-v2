# MEYLUX MASTER TARGET ARCHITECTURE V2

**Document ID:** DOC-V2-ARCH-001  
**Project:** Meylux AI Market Intelligence Platform  
**Version:** 2.0.0  
**Status:** RATIFIED / FROZEN  
**Classification:** Authoritative Target Architecture / Frozen V2 Baseline  
**Scope:** Meylux V2 only  
**Legacy V1:** FROZEN; this document grants no permission to mutate or resume V1  
**Supersedes for V2:** `MEYLUX MASTER TARGET ARCHITECTURE v5.1.1` as the target architecture after formal ratification  

> Meylux protects its intelligence first, while protecting the host through safe resource management.

---

# 0. DOCUMENT CONTROL AND AUTHORITY

## 0.1 Purpose

This document is the comprehensive target architecture for Meylux V2. It consolidates the valid architectural intent accumulated through the original Meylux specification, MASTER TARGET ARCHITECTURE v5.1.1, Market Intelligence specification, Reviewer/Producer governance contract, Master Handoff material, the V2 Architecture Hardening document, and lessons observed during the real V1 construction and verification process.

This document is not an implementation report and does not claim that any component exists. Every implementation and verification status is maintained separately in the project registry, current checkpoint, and evidence chain.

## 0.2 Authority hierarchy

The V2 document hierarchy is:

1. **Constitution / Architectural Invariants** — absolute system boundaries.
2. **Master Target Architecture V2** — complete target architecture and dependency model.
3. **ADR records** — approved decisions within architectural discretion.
4. **Master Registry** — stable identity and traceability authority.
5. **Phase / Step specifications** — milestone-level execution boundaries.
6. **TASK-ORDERs** — concrete commissioned implementation scope.
7. **Implementation artifacts** — producer-generated code/configuration.
8. **Verification evidence** — tests, CI, replay, live/operator evidence.
9. **CURRENT_CHECKPOINT** — current verified project state, never a replacement for architecture.

A lower layer cannot silently override a higher layer.

## 0.3 V2 source material reconciliation

The following are incorporated as source material:

- Meylux original project understanding and Base Structure.
- MASTER TARGET ARCHITECTURE v5.1.1.
- Reviewer / Producer / Operator governance contract.
- Market Intelligence v4 doctrine.
- Master Project Handoff knowledge.
- MEYLUX V2 ARCHITECTURE HARDENING & LESSONS LEARNED.
- Operational lessons from V1: persistence growth, duplicate identity, queue backlog, provider stream liveness, order-book sequence semantics, repeated resync/rate-limit pressure, hidden worker coupling, host resource pressure, and evidence/state drift.

No source document is treated as automatically correct merely because it is old or authoritative. Conflicts are resolved through explicit ADR/ACR governance before implementation.

## 0.4 Design status vocabulary

Every major entity uses two orthogonal dimensions:

### Architectural tier

- `ARCH-INVARIANT`
- `REQ-CAPABILITY`
- `REQ-BEHAVIOR`
- `IMPL-CHOICE`
- `CONFIG-PARAM`
- `PERF-TARGET`

### Evidence lifecycle

- `UNPLANNED`
- `PLANNED`
- `SPECIFIED`
- `IMPLEMENTED`
- `TESTED`
- `VERIFIED`
- `ACCEPTED`
- `DEPRECATED`
- `RETIRED`

`IMPLEMENTED` never means `VERIFIED`, and `VERIFIED` never means `ACCEPTED` without the required gate evidence.

---

# 1. SYSTEM IDENTITY, MISSION, SCOPE, AND NON-GOALS

## 1.1 What Meylux is

Meylux is an AI-first, deterministic-baseline, read-only market intelligence and decision-support platform. It ingests real market data, validates and normalizes it, computes deterministic quantitative and structural facts, assembles independent evidence, performs specialist analysis and contradiction testing, and produces explainable scenarios and monitoring outputs.

## 1.2 What Meylux is not

Meylux V2 is not:

- a trading execution bot;
- an order-routing engine;
- a portfolio manager;
- a balance or custody manager;
- a leverage controller;
- a fund-transfer or withdrawal system;
- an AI that invents market values when data is missing;
- an architecture in which the LLM performs authoritative financial arithmetic;
- a system in which Redis is the permanent source of truth.

## 1.3 Core intelligence pipeline

```text
External Market Sources
        |
        v
Provider Adapters
        |
        v
Raw / Staging Representation
        |
        v
Validation + Normalization
        |
        v
Canonical Market Data + Data Quality
        |
        +-----------------------+
        |                       |
        v                       v
Deterministic Quant        Cross-Venue Track
        |                       |
        +-----------+-----------+
                    |
                    v
            Structured Evidence
                    |
                    v
             Specialist Layer
                    |
                    v
          Contradiction Analysis
                    |
                    v
          Lead Intelligence Agent
                    |
                    v
        Scenario / Decision Support
                    |
            +-------+--------+
            |       |        |
            v       v        v
           API      UI     Telegram
                    |
                    v
            Historical Evaluation
```

## 1.4 Mission invariants

`INV-V2-001` **STRICT READ-ONLY**: zero trade execution authority.  
`INV-V2-002` **DETERMINISTIC BASELINE**: authoritative arithmetic/structure is deterministic.  
`INV-V2-003` **NO FABRICATION**: missing or unreliable data is explicit.  
`INV-V2-004` **EVIDENCE PROVENANCE**: every material intelligence output can be traced.  
`INV-V2-005` **INDEPENDENT EVIDENCE**: correlated signals are not treated as independent votes.  
`INV-V2-006` **LOGICAL IDENTITY**: logical identity is independent of path/name.  
`INV-V2-007` **SINGLE AUTHORITATIVE PERSISTENCE**: durable truth is in the designated database layer.  
`INV-V2-008` **PROVIDER ISOLATION**: one provider failure must not corrupt unrelated providers.  
`INV-V2-009` **ZERO LOOKAHEAD**: historical evaluation never consumes future information.  
`INV-V2-010` **EVIDENCE-BACKED STATE**: completion claims require evidence.

---

# 2. ARCHITECTURAL SPECIFICATION HIERARCHY

## 2.1 Six tiers

| Tier | Meaning | Change authority |
|---|---|---|
| T1 | Architectural Invariant | ACR + ratification |
| T2 | Required Capability | Formal architectural review |
| T3 | Required Behavior | Formal behavioral change |
| T4 | Implementation Choice | Within constraints; record if material |
| T5 | Configuration / Operational Parameter | Controlled configuration |
| T6 | Performance Target / SLO | Evidence-based tuning |

## 2.2 Precedence rules

- T4 cannot invalidate T1-T3.
- T5 cannot weaken T1 or T3.
- T6 is a target unless explicitly marked a guarantee.
- An assumption cannot be represented as a verified fact.
- A runtime observation cannot silently become an architecture rule.

## 2.3 Statement-type tags

Normative statements use one of:

`[MUST]` ` [MUST-NOT]` ` [SHOULD]` ` [MAY]` ` [DEFERRED]` ` [ASSUMPTION]` ` [OBSERVED]` ` [VERIFIED]` ` [TARGET]` ` [GUARANTEE]`

The tag is part of the semantic meaning.

---

# 3. STABLE IDENTITY AND MASTER REGISTRY

## 3.1 Stable ID rule

Logical identity is permanent across rename, relocation, refactor, technology replacement, and other non-semantic physical changes.

## 3.2 Entity prefixes

```text
REQ  Requirement
PH   Phase
STEP Phase Step
CMP  Component
SUB  Subcomponent
ART  Implementation Artifact
CTR  Contract
DB   Database Object
SRV  Runtime Service
WRK  Worker
QUE  Queue / Stream
API  Interface
CFG  Configuration
TST  Test Domain
OBS  Observability
SEC  Security Control
DOC  Formal Document
SCR  Script
DEP  Deployment Artifact
PERF Performance Target
TO   Task Order
BR   Build Report
AR   Audit Report
EL   Execution Log
ADR  Architecture Decision Record
CHK  Checkpoint
OQ   Open Question
CHG  Change Ledger Entry
```

## 3.3 Registry is more than a file list

For every material entity the registry records, as applicable:

```text
SID
logical_name
entity_type
phase
step
tier
purpose
responsibility
owner
parent
children
requirements
inputs
outputs
contracts
producers
consumers
dependencies
forbidden_dependencies
database_objects
workers
queues
apis
configuration
security_controls
observability
failure_modes
recovery
verification_method
verification_status
lifecycle_status
current_location
location_history
change_policy
DoD
```

## 3.4 Lifecycle rules

`RETIRED` SIDs are permanently tombstoned and never reused. A split creates child identities and records the predecessor. A merge creates a successor identity and preserves predecessor lineage.

---

# 4. GOVERNANCE, ROLES, AND ARTIFACT PROTOCOL

## 4.1 Logical roles

### Reviewer

The Reviewer is the quality gate. The Reviewer interprets the ratified architecture, identifies required work, creates TASK-ORDERs, audits BUILD-REPORTs, issues APPROVE / REVISE / REJECT, and provides execution command packs to the Operator.

The Reviewer does not claim execution evidence that only the Operator can provide.

### Producer

The Producer originates implementation content in the exact scope of the TASK-ORDER, self-tests what it is able to run, reports actual results, and surfaces deviations/questions without silently changing scope.

The Producer does not change architecture, SIDs, contracts, or infrastructure scope without an explicit approved directive.

### Operator

The Operator is the human bridge. The Operator relays artifacts verbatim and is the only role authorized to execute approved VPS or environment commands in this workflow.

## 4.2 Artifact chain

```text
TASK-ORDER
     |
     v
BUILD-REPORT
     |
     v
AUDIT-REPORT
     |
     v
EXEC-LOG
     |
     v
CURRENT_CHECKPOINT
```

Every material transition references its parent artifact IDs and affected SIDs.

## 4.3 No silent mutation

No party silently edits another party's artifact. Corrections happen through the formal artifact cycle. If an emergency correction to a governance/status artifact is necessary, the change is explicitly disclosed and recorded.

---

# 5. SOURCE-OF-TRUTH MODEL

| Concern | Authoritative source |
|---|---|
| Immutable system rules | Constitution |
| Target architecture | Master Architecture V2 |
| Stable identity | Master Registry |
| Decisions | ADR / ACR ledger |
| Current state | CURRENT_CHECKPOINT.json |
| Open issues | OPEN_QUESTIONS.yaml |
| Deferred choices | DEFERRED_DECISIONS.yaml |
| Change history | CHANGE_LEDGER.yaml |
| Environment | ENVIRONMENT_MANIFEST.yaml |
| Source code | Git repository |
| CI results | CI artifacts |
| Runtime execution evidence | Operator EXEC-LOG |
| Durable market/intelligence data | Authoritative database |
| Transport/cache | Redis / ephemeral infrastructure |

Chat sessions are collaboration surfaces, not the ultimate source of truth.

---

# 6. PROJECT STATE, CONTINUITY, AND CROSS-AI RESUMABILITY

## 6.1 CURRENT_CHECKPOINT

`docs/state/CURRENT_CHECKPOINT.json` is the machine-readable bootstrap state.

Minimum fields:

```json
{
  "schema_version": "2.0",
  "project_version": "V2",
  "phase": "PH-P0",
  "step": "STEP-P0-001",
  "gate": "G-0",
  "status": "IN_PROGRESS",
  "last_approved_task_order": null,
  "last_build_report": null,
  "last_audit_report": null,
  "last_execution_log": null,
  "verified_artifacts": [],
  "unverified_artifacts": [],
  "open_questions": [],
  "active_assumptions": [],
  "deferred_decisions": [],
  "last_verified_commit": null,
  "updated_at_utc": null
}
```

## 6.2 AI continuation bootstrap sequence

Any new AI must read in this order:

1. Constitution.
2. Master Architecture V2.
3. Governance / Role Contract.
4. Artifact Protocol.
5. Current Checkpoint.
6. Open Questions.
7. Deferred Decisions.
8. Relevant ADRs/ACRs.
9. Relevant registry records.
10. Latest approved artifact chain.
11. Repository state.
12. Evidence referenced by the current gate.

The AI must not infer current completion from chat memory alone.

---

# 7. TARGET REPOSITORY ARCHITECTURE

The following is the V2 target layout. `LOC-MANDATED` means the location convention itself is part of the repository contract; `LOC-RECOMMENDED` means the logical artifact and SID are mandatory while physical relocation is allowed under registry lineage rules.

```text
meylux-v2/
├── .github/
│   ├── workflows/
│   │   ├── ci-core.yml
│   │   ├── ci-contracts.yml
│   │   ├── ci-integration.yml
│   │   ├── ci-security.yml
│   │   └── ci-governance.yml
│   └── CODEOWNERS
├── config/
│   ├── base.py
│   ├── environments/
│   │   ├── dev.py
│   │   ├── staging.py
│   │   └── prod.py
│   ├── providers.yaml
│   ├── normalization.yaml
│   ├── quantitative.yaml
│   ├── specialists.yaml
│   ├── ai_endpoints.yaml
│   ├── ai_orchestration.yaml
│   ├── scanner.yaml
│   ├── venue.yaml
│   ├── notifications.yaml
│   └── logging.yaml
├── contracts/
│   ├── canonical/
│   │   ├── instrument.py
│   │   ├── candle.py
│   │   ├── trade.py
│   │   ├── orderbook.py
│   │   └── derivatives.py
│   ├── quantitative/
│   │   ├── indicators.py
│   │   ├── structure.py
│   │   ├── volume_profile.py
│   │   ├── order_flow.py
│   │   └── regime.py
│   ├── specialist/
│   │   ├── base.py
│   │   └── payloads.py
│   ├── intelligence/
│   │   ├── evidence.py
│   │   ├── scenario.py
│   │   └── score.py
│   ├── venue/
│   │   ├── mapping.py
│   │   ├── spread.py
│   │   ├── opportunity.py
│   │   └── outcome.py
│   └── events/
│       ├── ingestion.py
│       └── system.py
├── docs/
│   ├── constitution/
│   │   └── MEYLUX_CONSTITUTION_V2.md
│   ├── architecture/
│   │   └── MASTER_ARCHITECTURE_V2.md
│   ├── governance/
│   │   ├── ROLE_CONTRACT_V2.md
│   │   ├── ARTIFACT_PROTOCOL_V2.md
│   │   └── AI_CONTINUATION_PROTOCOL_V2.md
│   ├── registry/
│   │   ├── requirements.yaml
│   │   ├── phases.yaml
│   │   ├── components.yaml
│   │   ├── artifacts.yaml
│   │   ├── contracts.yaml
│   │   ├── database.yaml
│   │   ├── runtime.yaml
│   │   ├── configuration.yaml
│   │   ├── tests.yaml
│   │   ├── observability.yaml
│   │   ├── security.yaml
│   │   └── performance.yaml
│   ├── decisions/
│   │   ├── ADR_INDEX.md
│   │   └── ADR/
│   ├── state/
│   │   ├── CURRENT_CHECKPOINT.json
│   │   ├── OPEN_QUESTIONS.yaml
│   │   ├── DEFERRED_DECISIONS.yaml
│   │   └── CHANGE_LEDGER.yaml
│   ├── environment/
│   │   └── ENVIRONMENT_MANIFEST.yaml
│   ├── verification/
│   │   ├── GATE_DEFINITIONS.md
│   │   └── EVIDENCE_POLICY.md
│   ├── testing/
│   │   └── TEST_STRATEGY_V2.md
│   └── runbooks/
├── infrastructure/
│   ├── docker/
│   ├── compose/
│   ├── postgres/
│   ├── redis/
│   └── scripts/
├── migrations/
│   ├── env.py
│   └── versions/
├── src/
│   ├── app/
│   ├── providers/
│   ├── collectors/
│   ├── normalization/
│   ├── quantitative/
│   ├── specialists/
│   ├── orchestration/
│   ├── venue/
│   ├── scanner/
│   ├── notifications/
│   ├── memory/
│   ├── database/
│   ├── workers/
│   └── host_protection/
├── ui/
├── prompts/
│   └── registry/
├── scripts/
└── tests/
    ├── unit/
    ├── contract/
    ├── integration/
    ├── failure/
    ├── replay/
    ├── property/
    ├── chaos/
    ├── e2e/
    └── soak/
```

No runtime directory is considered complete solely because the tree exists. Registry evidence must link each required node to implementation and verification state.

---

# 8. DOMAIN AND DATA-FLOW ARCHITECTURE

## 8.1 Provider boundary

All external APIs terminate at provider adapters. The domain layer never consumes provider-specific payloads directly.

```text
Provider Protocol
      ↓
Provider Adapter
      ↓
Provider-Normalized Event
      ↓
Canonical Contract
      ↓
Validation
      ↓
Authoritative Data
```

## 8.2 Data states

A data item can be:

```text
RAW
STAGED
VALIDATING
NORMALIZED
CANONICAL
QUALITY_DEGRADED
REJECTED
QUARANTINED
EXPIRED
ARCHIVED
```

A rejected or unavailable data item is never silently promoted to canonical truth.

## 8.3 Canonical data rule

Canonical contracts contain only validated semantic data. Provider-specific aliases, event IDs, sequence details, and wire-format fields remain in provider adapters unless a domain requirement explicitly promotes a semantic field.

## 8.4 Data-quality rule

Every downstream intelligence consumer receives sufficient data-quality context to distinguish:

- complete and fresh;
- incomplete;
- stale;
- degraded;
- contradictory;
- unavailable;
- unsupported.

---

# 9. PHASE MODEL — GLOBAL LIFECYCLE

Meylux V2 retains the valid global phase structure, with stronger entry/exit evidence requirements.

| Phase | Scope | Gate dependency |
|---|---|---|
| PH-P0 | Constitution, architecture, specification | G-0 |
| PH-P1 | Runtime foundation, persistence, messaging, reproducibility | G-1 |
| PH-P2 | Market acquisition and provider abstraction | G-2 |
| PH-P3 | Validation, normalization, canonical data quality | G-3 |
| PH-P4 | Deterministic quantitative and structure engine | G-4 |
| PH-P5 | Specialist analytical layer | G-5 |
| PH-P6 | AI orchestration and lead intelligence | G-6 |
| PH-P7 | Scanner and monitoring | G-7 |
| PH-P8 | APIs, UI, notifications | G-8 |
| PH-P9 | Memory, evaluation, replay | G-9 |
| PH-P10 | Security, reliability, DR, productionization | G-10 |

Every phase contains an explicit dependency declaration, artifact registry, tests, failure model, observability model, security controls, and handoff package.

---

# 10. PHASE P0 — CONSTITUTION, ARCHITECTURE, SPECIFICATION FOUNDATION

**SID:** `PH-P0`

## Objective

Freeze the rules and complete architecture necessary to build V2 without architectural guessing.

## Required outputs

- Constitution V2.
- Master Architecture V2.
- Registry schemas and initial records.
- Governance and Artifact Protocol.
- AI Continuation Protocol.
- Gate definitions.
- Evidence policy.
- Test strategy.
- Environment Manifest schema.
- Initial ADR/ACR ledger.
- V2 Vertical Slice specification.
- Open Questions and Deferred Decision registries.

## P0 steps

```text
STEP-P0-001  Master Architecture Reconciliation
STEP-P0-002  Constitution Ratification
STEP-P0-003  V1 Lessons Integration
STEP-P0-004  Stable Identity / Registry
STEP-P0-005  Governance / Artifact Protocol
STEP-P0-006  AI Continuation Protocol
STEP-P0-007  Environment Contract
STEP-P0-008  Verification / Evidence / Gates
STEP-P0-009  Dependency and Boundary Graph
STEP-P0-010  Master Architecture Freeze
```

This ordering is the ratified Phase 0 sequence established by `ADR-ARCHITECTURE-001`. The historical execution of `STEP-P0-001` as Master Architecture Reconciliation is preserved exactly.

## Non-goals

No runtime service, provider connection, production database, or trading capability is implemented in P0.

## P0 exit

All critical architecture questions closed or explicitly recorded as non-blocking/deferred; no unresolved blocking contradiction remains.

---

# 11. PHASE P1 — INFRASTRUCTURE, REPRODUCIBILITY, PERSISTENCE, MESSAGING

**SID:** `PH-P1`

## Objective

Create the smallest reproducible runtime foundation capable of safely hosting later phases.

## Components

`CMP-P1-001` Persistence Layer  
`CMP-P1-002` Worker / Messaging Infrastructure  
`CMP-P1-003` Host / Resource Protection  
`CMP-P1-004` Configuration Runtime  
`CMP-P1-005` Observability Foundation

## Technology constraints

Python 3.12 compatibility is a V2 baseline target. PostgreSQL + TimescaleDB is the authoritative persistence direction. Redis is transport/cache/ephemeral infrastructure only. Exact versions are frozen in the P0 environment manifest before implementation.

## Persistence requirements

Every persistent object must declare:

- logical identity;
- key and uniqueness policy;
- insert path;
- update/delete policy;
- retention;
- expected event rate;
- expected daily growth;
- test-data disposal policy;
- replay/backfill semantics;
- alarms;
- recovery behavior.

## Worker requirements

Workers have one primary responsibility. They may call explicitly allowed dependencies but cannot silently own another subsystem.

## Host protection

V2 preserves the principle that intelligence quality is not silently degraded simply to hide resource pressure. Resource protection uses bounded concurrency, backpressure, workload shedding at permitted boundaries, disk alarms, memory budgets, and restart/recovery controls.

## Security

Database services are not publicly exposed. Least-privilege database roles are mandatory. Secrets are never hardcoded or written to logs.

## P1 exit

Reproducible runtime, migrations harness, queue foundation, logs, resource controls, and critical failure behavior verified.

---

# 12. PHASE P2 — MARKET DATA AND PROVIDER ABSTRACTION

**SID:** `PH-P2`

## Objective

Acquire real and historical market data without leaking provider-specific protocol assumptions into the domain.

## Initial providers

- Binance
- MEXC

Additional providers are allowed only through the same abstraction and change process.

## Feed classes

- instruments / metadata;
- ticker / quote;
- candles;
- trades / aggTrades / deals;
- order-book snapshot;
- order-book incremental depth;
- funding;
- open interest;
- liquidations where supported;
- market status;
- provider health.

Actual availability of any feed must be verified; architecture does not assume undocumented provider behavior.

## Provider protocol contract

Before implementation, each provider feed declares:

- endpoint/interface class;
- authentication;
- permission scope;
- request limits;
- heartbeat;
- timestamps;
- event IDs;
- sequence semantics;
- connection lifecycle;
- reconnect;
- backoff;
- circuit breaker;
- stale classification;
- snapshot/bootstrap rule;
- gap rule;
- resync rule;
- isolation behavior.

## Order-book specific rule

A provider order-book reconstructor is not accepted merely because it parses JSON. It requires replay fixtures demonstrating bootstrap bridge, contiguous updates, duplicate handling, out-of-order handling, gap detection, snapshot recovery, and bounded resync.

The generic contract must not be expanded merely to accommodate a provider-specific wire field unless that field has domain meaning.

## Connectivity state model

```text
DISCONNECTED
CONNECTING
CONNECTED
LIVE
SEMANTICALLY_VALID
FRESH
STABLE
DEGRADED
RECOVERING
FAILED
```

A successful TCP/WebSocket connection is not equivalent to a healthy market feed.

## Rate-limit protection

Recovery loops are bounded. Every provider has rate-budget telemetry and a recovery circuit breaker. Repeated resync cannot become an outage amplifier.

## P2 exit

Provider adapters, controlled feed ingestion, liveness/semantic health, gap recovery, rate-limit behavior, and provider isolation are verified for required feeds.

---

# 13. PHASE P3 — VALIDATION, NORMALIZATION, DATA QUALITY

**SID:** `PH-P3`

## Objective

Convert provider data into trustworthy canonical data.

## Responsibilities

- schema validation;
- semantic validation;
- timestamp validation;
- monotonicity / sequence checks;
- price and spread integrity;
- tick/lot precision rules;
- duplicate detection;
- cross-venue equivalence checks;
- data-quality scoring;
- quarantine / DLQ behavior.

## Data-quality outcomes

```text
VALID
DEGRADED
STALE
INCOMPLETE
CONTRADICTORY
REJECTED
UNAVAILABLE
```

## Cross-Venue rider

Venue comparisons require a dedicated consistency gate covering instrument identity, quote/base assets, market type, contract type, unit semantics, timestamp alignment, freshness, bid/ask sanity, and impossible values.

Uncertain mappings never become silently active.

## P3 exit

Canonical data integrity, explicit degradation, duplicate protection, and cross-venue validation are verified.

---

# 14. PHASE P4 — DETERMINISTIC QUANTITATIVE AND MARKET STRUCTURE ENGINE

**SID:** `PH-P4`

## Objective

Provide reproducible mathematical facts and market-structure state without LLM calculation.

## Deterministic modules

### Technical

- EMA 9/21/50/200
- SMA/WMA/HMA where specified
- RSI 14
- MACD 12/26/9
- ATR 14
- ADX 14
- Bollinger Bands 20/2
- Supertrend where ratified
- VWAP
- volatility metrics
- volume / RVOL / climax

### Structure

- HH / HL / LH / LL;
- swing points;
- BOS;
- CHOCH;
- MSS;
- FVG lifecycle;
- order blocks;
- breakers;
- liquidity zones.

### Volume profile

- POC;
- VAH;
- VAL;
- HVN;
- LVN.

### Derivatives

- funding;
- funding change/velocity;
- OI;
- OI delta/divergence;
- basis where canonical inputs permit.

### Order flow

- delta;
- CVD;
- imbalance;
- absorption.

### Regime

A multi-factor market regime classifier with explicitly defined states and transitions.

## Determinism requirements

- No network, I/O, or clock access inside pure math modules.
- No NaN/Inf in output contracts.
- Missing history returns explicit typed missing state.
- Zero-divide and invalid-domain cases are explicit.
- Precision policy is explicit and stable.
- Replays are deterministic.

## Golden Vector Freeze

Every critical formula family owns pinned input/output vectors. Golden vectors are generated from actual implementation execution, then frozen. A change that alters an accepted vector requires formal change approval.

## V1 lesson carried forward

Math correctness alone is not enough. Persistence, event identity, candle-close semantics, and worker scheduling must not cause duplicate or explosive persistence around otherwise correct calculations.

## P4 exit

Math suite green, golden vectors zero-deviation, structural tests green, numerical error tests green, and required persistence/replay integration evidence complete.

---

# 15. VENUE INTELLIGENCE TRACK — CROSS-CUTTING, NOT A GLOBAL PHASE

**Logical Component:** `CMP-V2-VENUE-001`  
**Placement:** P2/P3/P4/P5/P6/P9 riders

## 15.1 Principle

Cross-venue price dislocation is a market-intelligence capability. A raw difference is never automatically a profit or an executable opportunity.

## 15.2 Core flow

```text
Venue data
 -> equivalence
 -> alignment/freshness
 -> headline spread
 -> executable spread
 -> depth/friction
 -> persistence
 -> historical context
 -> classification
 -> evidence package
 -> specialist analysis
 -> contradiction analysis
 -> scenario
 -> historical outcome evaluation
```

## 15.3 State model

V2 retains the conceptual progression:

```text
S0 OBSERVED_SPREAD
S1 VALIDATED_SPREAD
S2 EXECUTABLE_SPREAD
S3 PERSISTENT_SPREAD
S4 STATISTICALLY_SIGNIFICANT
S5 OPPORTUNITY_CANDIDATE
S6 HIGH_QUALITY_CANDIDATE
S7 INVALID_DISLOCATION
S8 NO_OPPORTUNITY
```

S7/S8 are terminal dispositions, not ladder rungs. Degradation states are orthogonal.

## 15.4 Equivalence

Comparison requires semantic instrument mapping, not ticker equality alone. Mapping fields include base/quote, market type, contract type, multiplier/unit semantics, precision compatibility, aliases, lifecycle state, confidence, provenance, approval status.

Auto-discovery may suggest mappings but cannot activate them without the defined approval process.

## 15.5 Deterministic mathematics

### Headline / directional spread

Directional spread is represented for both directions using the approved sign convention.

### Executable analysis

Executable analysis models ask-side acquisition and bid-side liquidation, order-book walking, explicit taker fees, requested versus executable size, and resulting net edge.

Fees come from configuration, never hardcoded code paths.

### Quantity

Executable size is constrained by deterministic depth availability and operator-defined **modeled analytical** caps. No live account inventory is accessed.

### Persistence

Persistence records start, end, duration, observation count, trajectory, and the configured consecutive-sample rule.

### Historical statistics

At minimum: percentile statistics and z-score. Additional measures may be activated by later approved phases.

### Convergence

Historical outcome evaluation includes partial/full/failed convergence, time-to-convergence, overshoot, and reversal.

## 15.6 Headline versus executable

The displayed spread and executable spread are separate facts. Internal venue spread, slippage, fee drag, depth, and availability must be surfaced where relevant.

## 15.7 Cause classification

A cause can be labeled `FACT` only when directly derivable. Otherwise it is `INTERPRETATION` or `HYPOTHESIS`.

## 15.8 Venue evidence

The evidence package includes pair identity, both venue books, measured spreads, executable sizes, friction, persistence, statistics, convergence history, data quality, venue health, state/tier, scores, TTL, timestamps, and provenance.

## 15.9 Venue failure behavior

- Provider down -> venue-scoped degradation.
- Feed stale -> comparison skipped.
- Book unavailable -> no upward classification.
- Mapping uncertain -> blocks classification above defined validation state.
- Extreme spread -> investigation/anomaly path before opportunity classification.
- Recovery loop -> rate-limited and circuit-broken.

## 15.10 Venue track in global gates

Venue requirements are riders on existing gates rather than a new global Phase.

---

# 16. PHASE P5 — SPECIALIST MARKET INTELLIGENCE LAYER

**SID:** `PH-P5`

## 16.1 Principle

The specialist layer decomposes analysis into independent domains. Not every specialist is an LLM. Deterministic specialists remain deterministic.

## 16.2 Specialist domains

At minimum:

1. Technical Analyst
2. Market Structure Analyst
3. Volume Analyst
4. Derivatives Analyst
5. Order Flow Analyst
6. Multi-Timeframe Analyst
7. Cross-Exchange Analyst
8. Volatility Analyst
9. Risk Analyst
10. Data Quality Analyst
11. Price Action Reasoner
12. Liquidity Reasoner
13. Contrarian / Devil's Advocate
14. Historical Pattern Reasoner
15. News / Event Reasoner
16. Setup Validation
17. Volume Profile Reasoner
18. Market Regime Reasoner

The exact implementation form of a specialist is decided within the architecture boundary and recorded in the registry.

## 16.3 Independence rule

Evidence must be clustered by informational independence. EMA, MACD, RSI, and similar correlated signals cannot create artificial majority consensus.

## 16.4 Failure rule

One failed or timed-out specialist must not crash the whole intelligence pipeline. Failures become explicit status with reason and confidence impact.

## 16.5 Specialist contract

Every specialist consumes a versioned payload and returns a versioned output including:

- domain;
- findings;
- evidence refs;
- confidence;
- data-quality status;
- uncertainty;
- risk flags;
- invalidation evidence;
- version metadata.

---

# 17. PHASE P6 — AI ORCHESTRATION, CONTRADICTION, LEAD INTELLIGENCE

**SID:** `PH-P6`

## Objective

Use AI for reasoning and synthesis over validated evidence.

## Required capabilities

- AI provider abstraction;
- context/evidence builder;
- schema guard;
- contradiction detector;
- evidence hierarchy resolver;
- lead intelligence synthesizer;
- scenario builder;
- budget/cost controller;
- model health/fallback.

## Provider abstraction

Model vendor and model identity are configuration-level implementation choices unless explicitly elevated by ADR. Provider strings must not leak into generic business logic.

## Prompt isolation

User input and external text are untrusted. Prompt injection must not override system policy, tool boundaries, or schema rules.

## Fallback

If AI is unavailable, the platform returns the approved deterministic fallback representation or explicit degraded result. It does not fabricate a narrative.

## Scenario model

Where applicable:

- primary scenario;
- alternative scenario;
- invalidation conditions;
- evidence supporting each;
- evidence contradicting each;
- data-quality condition;
- analytical confidence;
- opportunity score;
- NO TRADE when the evidence does not justify an actionable interpretation.

## Three scores remain separate

```text
Opportunity Score
Analytical Confidence
Data Quality
```

Venue Opportunity Score, where present, is an internal venue-domain score and does not replace the global scores.

## P6 exit

Structured evidence, contradiction behavior, fallback behavior, prompt isolation, and scenario schema are verified.

---

# 18. PHASE P7 — AUTONOMOUS SCANNER AND MONITORING

**SID:** `PH-P7`

## Objective

Continuously identify candidates efficiently without forcing every asset through the expensive intelligence path.

## Pipeline

```text
Universe discovery
 -> liquidity filter
 -> volatility filter
 -> structure filter
 -> derivatives/venue filter
 -> candidate rank
 -> intelligence trigger
```

## Scanner principles

- fast filters before expensive AI;
- bounded concurrency;
- backpressure;
- no duplicate candidate storms;
- explicit cooldown/hysteresis;
- provider outage isolation;
- alert TTL;
- replayable deterministic scheduling semantics.

## Resource control

Scanner load is constrained by a declared resource budget and cannot bypass host protection controls.

---

# 19. PHASE P8 — API, UI, TELEGRAM, USER INTERFACES

**SID:** `PH-P8`

## API principles

APIs expose read-only intelligence and operational state. No order-management capability exists in this architecture.

Representative API domains:

- health;
- market data;
- data quality;
- quantitative features;
- structure;
- intelligence scenarios;
- specialists;
- scanner candidates;
- venue intelligence;
- evaluation/replay views.

Exact endpoints are frozen through the registry before implementation.

## UI principles

The UI must display uncertainty, freshness, data quality, evidence provenance, timestamps, and scenario/invalidation context. It must not visually imply trade execution authority.

## Telegram

Telegram is a notification/read-only interaction channel. It may deliver summaries, alerts, and controlled read-only queries. Credentials remain secret and isolated.

---

# 20. PHASE P9 — MEMORY, EVALUATION, HISTORICAL REPLAY

**SID:** `PH-P9`

## Objective

Measure whether intelligence and opportunity classifications were historically useful without lookahead.

## Memory

Store analytical artifacts and evidence snapshots with immutable references and version metadata.

## Evaluation

Evaluate:

- scenario outcomes;
- convergence;
- time-to-convergence;
- false positives;
- specialist reliability;
- calibration;
- regime dependence;
- venue dependence;
- data-quality dependence.

## Replay invariant

Historical replay consumes only information available at the historical decision timestamp. Future data may be used only after the simulated decision point for outcome measurement, never for the original decision.

## No future leakage

Replay engine, baseline snapshots, features, and evaluation windows must have explicit temporal boundaries.

---

# 21. PHASE P10 — SECURITY, RELIABILITY, DISASTER RECOVERY, PRODUCTIONIZATION

**SID:** `PH-P10`

## Objective

Demonstrate that V2 remains safe, recoverable, observable, and consistent under realistic failure.

## Security controls

- strict read-only enforcement;
- least privilege;
- secret isolation;
- secret scrubbing;
- network segmentation;
- no public database exposure;
- no trade endpoints;
- AST/static checks for forbidden execution functionality;
- prompt isolation;
- dependency security scanning;
- audit logging.

## Reliability controls

- restart behavior;
- bounded queues;
- retry/backoff;
- circuit breakers;
- provider isolation;
- database transaction safety;
- recovery checkpoints;
- deterministic replay;
- disk and memory alarms;
- controlled workload shedding.

## Disaster recovery

The authoritative database is backed up and restore-tested. Recovery procedures are documented and executed in controlled drills.

## P10 exit

Security, DR, resource pressure, provider outage, queue overload, and recovery evidence support production readiness.

---

# 22. DATABASE MASTER ARCHITECTURE

## 22.1 Logical domains

1. System metadata
2. Provider/staging data
3. Canonical market data
4. Data-quality ledger
5. Quantitative facts
6. Structural events/zones
7. Specialist executions
8. Intelligence scenarios/evidence
9. Venue intelligence
10. Scanner candidates
11. Evaluation/replay
12. Operational telemetry

## 22.2 Database rules

- Authoritative data ownership is explicit.
- Every high-volume object has a growth model.
- Every logical event has a stable identity.
- Every retry-sensitive ingestion path has an idempotency strategy.
- Retention is specified before implementation.
- Test data is distinguishable from production-like evidence and can be safely disposed of.
- Disposable test truncation is never used as a production recovery strategy.

## 22.3 Permissions

Application runtime roles must not receive broad DDL privileges. Migration authority is isolated from application DML authority. Deletion of authoritative data is forbidden or tightly governed according to the specific table contract.

---

# 23. CONTRACT MASTER ARCHITECTURE

## 23.1 Contract doctrine

Contracts are immutable/frozen at runtime where applicable, timezone-aware, explicit about units and precision, and free from provider-specific accidental semantics.

## 23.2 Contract requirements

Every contract defines:

- SID;
- version;
- producer;
- consumer(s);
- fields;
- types;
- nullable rules;
- units;
- precision;
- timestamp semantics;
- validation;
- error/degradation representation;
- compatibility policy.

## 23.3 Numeric policy

`Decimal` is the authoritative boundary representation where monetary/financial exactness requires it. Any internal optimization using binary numeric representations must be explicitly approved, bounded, and converted under a deterministic output policy.

The V2 architecture does not allow hidden float-to-money semantics.

---

# 24. SERVICE, COMPONENT, WORKER, AND QUEUE ARCHITECTURE

## 24.1 Component ownership

Every component has one clear responsibility and a bounded public interface.

## 24.2 Worker ownership

A worker record declares:

```text
primary responsibility
inputs
outputs
queues
allowed dependencies
forbidden responsibilities
side effects
resource budget
retry policy
timeout
concurrency
failure isolation
```

## 24.3 Queue ownership

A queue record declares:

```text
owner
producer
consumer
purpose
payload contract
ordering requirement
retry policy
timeout
concurrency/backlog limits
DLQ policy
idempotency
retention
drain/recovery method
```

## 24.4 Queue overload behavior

Backlog growth is observable. A queue cannot be allowed to grow without bound merely because downstream work is expensive. Every queue has an explicit overload response.

---

# 25. API MASTER ARCHITECTURE

The API layer is a read-oriented boundary over canonical and intelligence data.

Representative domains:

```text
GET /health/live
GET /health/ready
GET /market/...
GET /quality/...
GET /quant/...
GET /structure/...
GET /intelligence/...
GET /specialists/...
GET /scanner/...
GET /venue/...
GET /evaluation/...
```

No API under this architecture can create or mutate trading orders or account state.

Any operational control endpoint must be explicitly classified and must not cross the trading-execution boundary.

---

# 26. CONFIGURATION ARCHITECTURE

Configuration is divided into:

- immutable architectural constants;
- environment values;
- provider configuration;
- operational thresholds;
- model binding;
- feature flags;
- resource limits;
- retention settings.

Configuration cannot disable an invariant. A configuration change that materially changes required behavior is an architectural change, not a routine tuning action.

Every configuration family has:

```text
SID
owner
source
default
allowed range
unit
environment scope
safety constraints
change procedure
```

---

# 27. SECURITY AND READ-ONLY ENFORCEMENT

Read-only is enforced in layers:

```text
Architecture rule
     ↓
Contract / interface design
     ↓
Credential permissions
     ↓
Network policy
     ↓
Database RBAC
     ↓
Application guards
     ↓
Static / AST checks
     ↓
Runtime verification
```

The goal is defense in depth, not dependence on one environment variable.

Secrets:

- never hardcoded;
- never committed;
- never returned in API payloads;
- never logged in plaintext;
- scrubbed from structured logs;
- rotated through the environment/secret mechanism.

---

# 28. OBSERVABILITY ARCHITECTURE

## 28.1 Health dimensions

```text
PROCESS
CONNECTION
DATA FLOW
SEMANTIC VALIDITY
FRESHNESS
SUSTAINED STABILITY
```

## 28.2 Required telemetry classes

- ingestion latency;
- provider connection state;
- stale feed count;
- sequence gap count;
- resync count;
- rate-limit utilization;
- normalization rejection count;
- data-quality scores;
- queue backlog;
- worker duration/failure;
- quant calculation duration/errors;
- AI tokens/cost/latency;
- scenario count;
- venue spread/opportunity/rejection metrics;
- database growth;
- disk usage;
- host CPU/RAM;
- recovery events.

## 28.3 Evidence correlation

Structured logs carry correlation identifiers sufficient to follow one ingestion/recovery/intelligence chain across boundaries without logging secrets.

---

# 29. TEST AND VERIFICATION ARCHITECTURE

## 29.1 Test pyramid

```text
Static
  ↓
Unit
  ↓
Contract
  ↓
Integration
  ↓
Failure
  ↓
Property
  ↓
Replay
  ↓
Chaos
  ↓
E2E
  ↓
Soak
  ↓
Production Verification
```

## 29.2 Golden vectors

Golden vectors are mandatory for critical deterministic algorithms. They are generated by actual implementation execution and pinned only after verification.

## 29.3 Failure tests

Critical failure domains include:

- provider outage;
- silent feed;
- stale timestamp;
- malformed payload;
- duplicate event;
- out-of-order event;
- sequence gap;
- snapshot mismatch;
- resync storm;
- rate limit;
- Redis loss;
- DB disconnect;
- queue overload;
- worker crash;
- AI outage;
- schema violation;
- disk pressure;
- insufficient historical context.

## 29.4 Verification language

`PASS` means the required assertion passed.  
`VERIFIED` means sufficient evidence exists for the entity and scope.  
`ACCEPTED` means the responsible gate was formally closed.  
`COMPLETE` is reserved for milestone state supported by all mandatory evidence.

---

# 30. CONTROLLED VERTICAL SLICE STRATEGY

V2 introduces a vertical slice early, before the full architecture is populated.

## Slice A — Market-data-to-canonical proof

```text
Provider sample
 -> adapter
 -> canonical contract
 -> validation
 -> persistence
 -> retrieval
```

## Slice B — Canonical-to-quant proof

```text
Canonical candle/order book
 -> deterministic calculation
 -> contract
 -> test
 -> persisted fact
```

## Slice C — Evidence-to-intelligence proof

```text
Validated evidence
 -> specialist
 -> contradiction
 -> lead synthesis
 -> scenario contract
```

## Slice D — Venue proof

```text
Two venue inputs
 -> equivalence
 -> alignment/freshness
 -> executable math
 -> evidence package
 -> classification
```

Each slice is replayable and must expose failures rather than bypass them.

---

# 31. GATE ARCHITECTURE

## G-0 — Architecture Freeze

Requires Constitution, Master Architecture, registry, governance, continuation, evidence model, gate definitions, environment model, and no unresolved blocking contradictions.

## G-1 — Infrastructure

Requires reproducible runtime, persistence, queues, observability, security, and critical failure verification.

## G-2 — Market Data

Requires required provider feeds, semantic health, reconnection/recovery, rate-budget protection, and provider isolation.

## G-3 — Canonical Data

Requires normalization, quality gates, duplicate protection, canonical contracts, and rejection/DLQ behavior.

## G-4 — Deterministic Quant

Requires math tests, golden vectors, replay determinism, no NaN/Inf, and structural correctness.

## G-5 — Specialists

Requires specialist contracts, independence rules, failure isolation, and evidence provenance.

## G-6 — Lead Intelligence

Requires schema validation, contradiction handling, NO TRADE conditions, prompt isolation, and fallback behavior.

## G-7 — Scanner

Requires bounded scan load, duplicate prevention, candidate TTL/cooldown, and recovery behavior.

## G-8 — Interfaces

Requires API/UI/Telegram read-only behavior, security, and output clarity around uncertainty.

## G-9 — Evaluation

Requires zero-lookahead replay, outcome ledger, calibration, and historical evidence.

## G-10 — Production

Requires security, DR, resource stress, provider failure isolation, operational runbooks, and production verification.

No gate may close solely because a code path exists.

---

# 32. EVIDENCE POLICY

Every verification claim must have an evidence reference.

Evidence classes:

```text
E-STRUCT      structural evidence
E-UNIT        unit test evidence
E-CONTRACT    contract evidence
E-INTEGRATION integration evidence
E-FAILURE     negative/failure evidence
E-REPLAY      historical replay evidence
E-LIVE        live market/runtime evidence
E-CI          CI evidence
E-OPS         operator execution evidence
E-SOAK        sustained runtime evidence
```

Evidence is immutable by reference. If the implementation changes materially, old verification evidence does not automatically transfer.

---

# 33. DEPENDENCY GRAPH AND IMPLEMENTATION SEQUENCE

Canonical dependency direction:

```text
P0
 ↓
P1
 ↓
P2
 ↓
P3
 ↓
P4
 ↓
P5
 ↓
P6
 ↓
P7/P8
 ↓
P9
 ↓
P10
```

Cross-cutting tracks, including Venue, attach to these phases through explicit dependencies.

Dependency rules:

- no hidden reverse dependency;
- no circular dependency unless explicitly required and approved;
- no runtime layer consumes a lower-confidence evidence tier as if it were higher-confidence truth;
- infrastructure concerns cannot leak into pure math modules;
- provider details cannot leak into canonical contracts without approved semantic promotion.

---

# 34. PERFORMANCE ARCHITECTURE

Performance values are typed as `TARGET` until verified.

Each target must specify:

- workload;
- hardware/environment;
- sample size;
- percentile;
- measurement method;
- warm/cold condition;
- concurrency;
- pass/fail threshold.

The old V1 habit of quoting a number without explaining workload or evidence is prohibited.

Resource performance is treated as a bounded system property across CPU, RAM, disk, database, queues, providers, and AI cost.

---

# 35. HOST AND ENVIRONMENT ARCHITECTURE

## 35.1 Environment classes

```text
DEV
STAGING
PRODUCTION
```

## 35.2 Environment contract

The final environment baseline must identify:

- operating system;
- CPU;
- RAM;
- disk;
- container runtime;
- Python runtime;
- database version;
- Redis version;
- network boundaries;
- filesystem paths;
- resource limits;
- dependency versions;
- backup destination;
- observability endpoints.

The architecture does not prematurely freeze exact production hardware if the V2 target environment is not yet selected. Once selected, the manifest becomes normative for the production deployment target.

## 35.3 Local-first reality

The V2 architecture supports single-machine development first while preserving production deployment readiness. Host protection is treated as a first-class boundary rather than as an afterthought.

---

# 36. FAILURE AND RECOVERY MASTER MODEL

Every critical capability must answer:

```text
How does it fail?
How is failure detected?
How is it represented?
What is isolated?
What is retried?
What is not retried?
What is the backoff?
What is the circuit breaker?
What is the degraded output?
How is recovery verified?
What data must remain authoritative?
```

## 36.1 Generic recovery pattern

```text
DETECT
  ↓
CLASSIFY
  ↓
ISOLATE
  ↓
BOUND
  ↓
RECOVER
  ↓
VERIFY
  ↓
RESUME
```

## 36.2 Recovery must not amplify failure

Retries are not free. Recovery itself is a load source and therefore subject to resource and rate budgets.

This rule directly incorporates V1's order-book resync/rate-limit lesson.

---

# 37. PERSISTENCE AND DATA-GROWTH GOVERNANCE

Before any high-volume persistence is approved, the task must identify:

```text
Logical event identity
Deduplication key
Unique constraint
Expected rate
Peak rate
Daily growth
Retention
Compression/archive
Maximum acceptable cardinality
Alert threshold
Recovery path
Backfill semantics
Replay semantics
```

A functionally correct writer can still be operationally incorrect if it duplicates records. V2 treats data-growth safety as part of correctness.

---

# 38. CHANGE MANAGEMENT — ADR / ACR / LEDGER

## ADR

Records an architectural choice where multiple valid implementations exist.

## ACR

Changes an already ratified invariant, capability boundary, architecture relationship, or other protected rule.

## Change Ledger

Each approved change records:

```text
CHG ID
reason
requestor
reviewer
operator
affected SIDs
old state
new state
ADR/ACR reference
required re-tests
verification invalidations
commit reference
```

## Change impact rule

Any change to a contract, persistent identity, event semantics, deterministic algorithm, security boundary, or worker/queue ownership triggers an explicit impact assessment.

---

# 39. OPEN QUESTIONS AND DEFERRED DECISIONS

## 39.1 Open Question record

```yaml
id: OQ-V2-xxxx
severity: HIGH|MEDIUM|LOW
blocking: true|false
description: ...
affected_sids: []
evidence_required: []
owner: ...
status: OPEN|RESOLVED
resolution_ref: ...
```

## 39.2 Deferred Decision record

```yaml
id: DD-V2-xxxx
domain: ...
reason_deferred: ...
trigger: ...
affected_phases: []
owner: ...
status: DEFERRED|RESOLVED
resolution_ref: ...
```

Examples of appropriate deferred decisions include future provider additions, future market classes, embedding technology, optional advanced scanner optimizations, or final production hardware where not yet selected.

Deferred does not mean forgotten.

---

# 40. MARKET INTELLIGENCE MASTER DOCTRINE

The MI Brain remains:

- evidence-driven;
- explicit about uncertainty;
- multi-timeframe;
- contradiction-aware;
- specialist-based;
- regime-aware;
- risk-aware;
- capable of NO TRADE / NO OPPORTUNITY;
- incapable of claiming execution or guaranteed profit.

## Evidence hierarchy

```text
1. Verified real market data
2. Deterministic quantitative computation
3. Validated market structure
4. Derivatives / order flow evidence
5. Specialist outputs
6. AI interpretation / synthesis
7. Hypothesis
```

## Multi-timeframe doctrine

Primary timeframes remain 1D, 4H, 1H, 15M, with optional lower frames where supported. Lower-timeframe analysis cannot silently ignore higher-timeframe context.

## Contradiction doctrine

The system actively searches for evidence that could make its leading interpretation wrong. Contradictions are recorded, not hidden.

## NO TRADE / NO OPPORTUNITY doctrine

A valid output may be:

```text
NO TRADE
NO OPPORTUNITY
LIMITED DATA
INSUFFICIENT DATA
```

The system must not create an idea because a user requested an idea.

---

# 41. SCORING ARCHITECTURE

The following remain independent:

### Opportunity Score

How attractive and structurally complete the setup appears.

### Analytical Confidence

How confident the system is that its interpretation is correct.

### Data Quality

How reliable and complete the underlying evidence is.

### Venue Opportunity Score

Optional internal venue-domain score. It never replaces or overrides the three global scores.

Every score must disclose its inputs and version/config basis sufficiently for audit.

---

# 42. AI COST, MODEL, AND PROVIDER GOVERNANCE

AI provider identity is an implementation/configuration concern unless explicitly elevated by ADR.

Required controls:

- model registry;
- fallback chain;
- health checks;
- timeout;
- retry policy;
- token/cost budget;
- output schema;
- prompt version;
- prompt hash where required;
- cache rules;
- provider outage state.

Vendor/model strings should not be copied throughout business logic. Provider changes must be isolated behind adapter/config boundaries.

---

# 43. REPLAY, BACKFILL, AND LOOKAHEAD CONTROL

Backfill is an ingestion operation, not a free license to alter historical decisions.

Historical replay must specify:

- time range;
- input dataset snapshot/version;
- event ordering;
- clock semantics;
- feature availability;
- model/prompt version;
- configuration version;
- output capture;
- outcome horizon.

A replay that cannot prove temporal isolation is not accepted as evaluation evidence.

---

# 44. OPERATIONAL RUNBOOK REQUIREMENTS

Each critical production path has a runbook containing:

1. symptom;
2. detection;
3. likely causes;
4. immediate safe action;
5. forbidden actions;
6. diagnostic evidence;
7. recovery steps;
8. verification steps;
9. rollback if applicable;
10. post-incident recording.

Runbooks are version-controlled and linked to the relevant SIDs.

---

# 45. V1 ISOLATION AND V2 BOUNDARY

V1 remains a separate frozen project.

V2 may reuse lessons and conceptual knowledge from V1, but:

- V2 is not a V1 fork;
- V1 code is not a V2 dependency;
- V1 runtime is not a V2 environment;
- V1 verification evidence does not automatically prove V2;
- V1 SIDs do not automatically become V2 SIDs unless explicitly mapped;
- V1 operational incidents are lessons, not implementation inheritance.

A formal V1-to-V2 lesson mapping record is maintained so useful knowledge is retained without importing undocumented coupling.

---

# 46. PHASE HANDOFF CONTRACT

Every phase handoff contains:

```text
Source phase
Destination phase
Closed gate
Approved commit
Verified artifacts
Open questions
Known limitations
Required assumptions
Required registry sync
Evidence bundle
Next permitted task
```

The receiving phase is not permitted to reinterpret closed requirements.

---

# 47. DEFINITION OF DONE — GLOBAL V2

Meylux V2 is not considered production-ready until all mandatory phases are accepted and:

- every required component has a SID;
- every required contract is registered and versioned;
- every persistence object has identity/growth/retention policy;
- every worker and queue has ownership and safety rules;
- every provider path has failure semantics;
- every critical deterministic calculation has verification evidence;
- every intelligence output has provenance and uncertainty context;
- every gate has evidence;
- the system has a controlled vertical slice;
- replay is zero-lookahead;
- security controls are verified;
- disaster recovery is tested;
- production resource limits are verified in the target environment;
- there are no unresolved blocking architectural questions;
- the final checkpoint points to the accepted commit and evidence bundle.

---

# 48. PHASE-BY-PHASE IMPLEMENTATION CONTRACT MATRIX

| Phase | Must exist | Must be verified | Forbidden until later |
|---|---|---|---|
| P0 | architecture/governance/spec | architecture consistency | runtime build |
| P1 | runtime/DB/queue/obs base | recovery/security/limits | market providers |
| P2 | provider + collector | live/controlled feed semantics | canonical assumptions |
| P3 | validators/normalizers/contracts | canonical integrity | AI scenario synthesis |
| P4 | quant/structure | golden vectors/replay | LLM math |
| P5 | specialists | contracts/independence/failure | final lead synthesis |
| P6 | orchestration/lead | contradiction/fallback/security | execution |
| P7 | scanner | bounded load/dup controls | uncontrolled AI fan-out |
| P8 | APIs/UI/Telegram | read-only + clarity | trading endpoints |
| P9 | memory/evaluation/replay | zero lookahead/calibration | forward leakage |
| P10 | security/DR/ops | production readiness | none beyond approved scope |

---

# 49. V2 ARCHITECTURAL CHECKLIST FOR EVERY NEW ARTIFACT

Before a material artifact is approved, it must answer:

```text
1. What is it?
2. Why does it exist?
3. Who owns it?
4. What SID identifies it?
5. What requirement does it satisfy?
6. What phase/step owns it?
7. What tier governs it?
8. What does it consume?
9. What does it produce?
10. Who consumes its output?
11. What does it depend on?
12. What may it NOT depend on?
13. What happens when it fails?
14. How is degraded behavior represented?
15. How is duplicate/retry behavior controlled?
16. What is its resource envelope?
17. What security boundary applies?
18. What telemetry proves it is healthy?
19. How is it tested?
20. What evidence proves it?
21. How does another AI discover it?
22. What state record tracks it?
23. How can it change?
24. What old evidence becomes invalid after the change?
```

A critical artifact missing material answers is `NOT READY FOR IMPLEMENTATION APPROVAL`.

---

# 50. V2 DESIGN PRINCIPLES TO REMEMBER

1. **Architecture is a contract, not a suggestion.**
2. **State is not architecture.**
3. **Evidence is not a narrative.**
4. **A connection is not a healthy feed.**
5. **A green unit test is not production correctness.**
6. **A functioning writer can still be an unsafe writer.**
7. **A retry can create an outage.**
8. **A queue can become a failure domain.**
9. **A provider-specific wire field does not automatically belong in a generic contract.**
10. **A detailed repository tree does not prove that the dependency graph is correct.**
11. **A model-generated conclusion is not a deterministic fact.**
12. **NO TRADE and NO OPPORTUNITY are valid outcomes.**
13. **Deferred decisions must remain visible.**
14. **Every completion claim requires evidence.**
15. **Every important capability must be resumable by another AI.**
16. **No V2 implementation starts before the architectural freeze gate is closed.**

---

# 51. REQUIRED V2 GOVERNANCE ARTIFACT SET

At minimum, the repository must eventually contain:

```text
MEYLUX_CONSTITUTION_V2.md
MASTER_ARCHITECTURE_V2.md
ROLE_CONTRACT_V2.md
ARTIFACT_PROTOCOL_V2.md
AI_CONTINUATION_PROTOCOL_V2.md
TEST_STRATEGY_V2.md
EVIDENCE_POLICY.md
GATE_DEFINITIONS.md
ENVIRONMENT_MANIFEST.yaml
CURRENT_CHECKPOINT.json
OPEN_QUESTIONS.yaml
DEFERRED_DECISIONS.yaml
CHANGE_LEDGER.yaml
ADR_INDEX.md
Master Registry YAML files
Operational runbooks
```

The list is a governance capability requirement. Individual filenames can only be changed through the registry/change process after ratification.

---

# 52. CHATGPT PROJECT ARCHITECTURE

Meylux V2 should use one ChatGPT Project for the whole project:

```text
MEYLUX V2
├── CONTROL / REVIEWER
├── PRODUCER RELAY
├── MARKET INTELLIGENCE
└── TROUBLESHOOTING
```

The Project-level instruction set contains durable governance rules. Large architecture and state files remain in the version-controlled project repository and are loaded into the Project as needed.

The chat topology is a collaboration convenience, not an alternative source of truth.

---

# 53. INITIAL V2 IMPLEMENTATION SEQUENCE

After ratification:

```text
1. Create GitHub repository.
2. Install governance / architecture documents.
3. Create registry foundation.
4. Create initial checkpoint.
5. Run static governance validation.
6. Build the smallest P1 runtime foundation.
7. Close G-1.
8. Build provider foundation.
9. Close G-2.
10. Build canonical validation.
11. Close G-3.
12. Build quantitative baseline.
13. Close G-4.
14. Continue phase-by-phase.
```

No skipped gate. No “parallel build” that creates an unverified dependency on a closed-looking but unverified phase.

---

# 54. RATIFICATION RULE

This document became the **Master Target Architecture V2** through formal Reviewer audit, resolution of blocking Open Questions at the ratification boundary, registry/state synchronization, and the Project Owner ratification/freeze decision recorded in `ADR-GOVERNANCE-004`.

The architecture is now a frozen V2 governance baseline. Changes to protected architectural content require the established ADR/ACR/change-control process and may invalidate dependent verification evidence as defined by that process.

---

# APPENDIX A — PRIMARY V2 CONTROL MAPPINGS FROM V1 LESSONS

| V1 lesson | V2 architectural control |
|---|---|
| Context drift | Source-of-truth separation + checkpoint + continuation protocol |
| Premature completion claims | Orthogonal lifecycle + evidence policy + gate evidence |
| Duplicate/data explosion | Logical identity + uniqueness + growth budget + retention |
| Queue backlog | Queue budget + concurrency + backlog alarms + drain runbook |
| Worker coupling | Explicit ownership + forbidden responsibilities |
| Provider sequence defect | Protocol contract + replay fixtures + bridge proof |
| Silent feed | Layered health model |
| Resync/rate-limit loop | Rate budgets + bounded recovery + circuit breaker |
| Policy mistaken as guarantee | Statement-type tags |
| Large tree / hidden dependency | Registry graph + dependency contract |
| Late integration | Early vertical slices |
| Host pressure | Resource budgets + backpressure + intelligence-preservation rule |
| AI hallucination | Structured evidence + schema guard + explicit uncertainty |
| Vendor lock-in | Provider/model abstraction |

---

# APPENDIX B — MINIMUM REGISTRY RECORD EXAMPLES

## Component

```yaml
component_id: CMP-V2-P4-001
logical_name: DeterministicQuantitativeEngine
phase: PH-P4
tier: REQ-CAPABILITY
responsibility: Deterministic calculation of validated quantitative facts
inputs:
  - CTR-V2-CANONICAL-CANDLE
outputs:
  - CTR-V2-QUANT-VECTOR
dependencies:
  - CMP-V2-P3-001
forbidden_dependencies:
  - AI provider runtime
  - external network
verification:
  suites:
    - TST-V2-P4-001
    - TST-V2-P4-002
lifecycle_status: PLANNED
verification_status: UNVERIFIED
```

## Queue

```yaml
queue_id: QUE-V2-P4-001
purpose: asynchronous quantitative work
producer: WRK-V2-P3-001
consumer: WRK-V2-P4-001
payload_contract: CTR-V2-EVENT-QUANT-REQUEST
retry_policy: bounded
concurrency_limit: CONFIGURED
backlog_alarm: CONFIGURED
dlq: QUE-V2-DLQ-001
recovery: documented_runbook
```

---

# APPENDIX C — MINIMUM TASK-ORDER CONTENT

```text
TASK ID
Objective
Context / governing sources
In scope
Out of scope
Affected SIDs
Allowed files
Forbidden files
Inputs
Expected outputs
Contracts
Dependencies
Behavioral requirements
Failure requirements
Tests
Evidence requirements
Definition of Done
Open-question escalation rule
```

---

# APPENDIX D — MINIMUM BUILD-REPORT CONTENT

```text
status
context
changes
tests
golden_vectors
evidence
open_questions
deviations
unexecuted_items
```

No simulated results. No invented hashes. No invented counts.

---

# APPENDIX E — MASTER ARCHITECTURE V2 NON-GOALS

This document does not authorize:

- trading execution;
- account management;
- production credential handling during design phase;
- implementation of every future market class;
- premature dependency selection where the architecture intentionally defers a choice;
- claiming that an architectural requirement is already implemented;
- automatic continuation of V1.

---

# FINAL ARCHITECTURAL DECLARATION

Meylux V2 is designed as a system in which **truth, identity, state, evidence, and change are all explicit**.

The architecture is intentionally detailed enough that an implementation agent should not need to invent the system's boundaries, ownership, persistence semantics, security model, failure behavior, or verification obligations while coding.

Where implementation detail is intentionally left open, it is identified as an implementation choice or deferred decision rather than silently guessed.

The ultimate V2 design objective is therefore:

```text
NO HIDDEN STATE
NO HIDDEN DEPENDENCY
NO HIDDEN MUTATION
NO HIDDEN ASSUMPTION
NO HIDDEN DATA FABRICATION
NO UNVERIFIED COMPLETION
NO UNDOCUMENTED ARCHITECTURAL DRIFT
```

**Document Status:** `RATIFIED / FROZEN`  
**Ratification Authority:** `PROJECT OWNER`  
**Ratification Record:** `ADR-GOVERNANCE-004`  
**Freeze State:** `FROZEN`  
**V1 Mutation Permission:** `NO`
