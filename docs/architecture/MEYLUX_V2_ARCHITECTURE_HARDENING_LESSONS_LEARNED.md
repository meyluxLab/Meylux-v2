# MEYLUX V2 ARCHITECTURE HARDENING & LESSONS LEARNED

**Document ID:** DOC-V2-P0-002  
**Project:** Meylux AI Market Intelligence Platform  
**Version:** 1.0.0  
**Status:** DESIGN BASELINE — PENDING RATIFICATION  
**Classification:** Architectural Hardening / Pre-Implementation  
**Scope:** New Meylux V2 only  
**Legacy V1:** Frozen; no implementation mutation authorized by this document  

---

## 1. Purpose

این سند پلی رسمی بین تجربه‌ی Meylux V1 و طراحی Meylux V2 است. هدف آن کپی‌کردن V1 نیست؛ هدف استخراج دانش معتبر، خطاهای واقعی، اصول اثبات‌شده و ضعف‌های ساختاری V1 و تبدیل آن‌ها به الزامات قابل‌ردیابی برای V2 است.

این سند قبل از هرگونه implementation در V2 باید بررسی و ratify شود. پس از ratification، مواردی که در آن با برچسب **V2-MANDATORY** مشخص شده‌اند، بخشی از مبنای طراحی V2 خواهند بود.

V1 در این سند فقط به‌عنوان evidence و منبع lessons learned استفاده می‌شود. هیچ موردی از این سند مجوز تغییر، تعمیر یا ادامه‌ی کدنویسی V1 نیست.

---

## 2. Executive Decision

تصمیم طراحی پایه‌ی V2:

1. Meylux V2 از **codebase V1 fork نمی‌شود**.
2. Architecture v5.1.1 و اسناد فعلی به‌عنوان material ورودی بررسی می‌شوند، نه به‌عنوان متن مقدسی که بدون بازبینی کپی شود.
3. هسته‌ی مأموریت Meylux، Read-Only، AI-FIRST/NOT AI-ONLY، deterministic baseline، no-data-fabrication، evidence hierarchy، provider abstraction و separation of intelligence از execution حفظ می‌شوند.
4. مدل 6-Tier معماری حفظ می‌شود.
5. Stable Identity / SID حفظ و برای workflow artifactها و continuation بین AIها تکمیل می‌شود.
6. Venue Intelligence به‌عنوان **Cross-Cutting Track** حفظ می‌شود، نه Phase مستقل.
7. Project State از Architecture جدا می‌شود و به‌صورت machine-readable نگهداری خواهد شد.
8. Registry از یک فهرست ساده به یک traceability graph رسمی تبدیل خواهد شد.
9. Vertical Slice و failure verification باید از ابتدای lifecycle وارد طراحی شوند، نه در انتهای پروژه.
10. هر ادعای "implemented"، "verified" و "complete" باید از هم جدا باشد و evidence مستقل داشته باشد.

---

## 3. Relationship to Existing V1 Documents

اسناد موجود V1 هنوز ارزش معماری دارند، اما برای V2 نقش آن‌ها این است:

| Existing Document | V2 Treatment |
|---|---|
| Meylux Project Understanding / Base Structure | Preserve mission and conceptual model; rewrite for V2 terminology and governance |
| MASTER TARGET ARCHITECTURE v5.1.1 | Primary architectural input; harden, reconcile, and reorganize before freeze |
| Reviewer / Producer Role Contract | Preserve governance core; split/expand artifact and continuation protocols |
| Market Intelligence v4 | Preserve intelligence doctrine; convert into formal intelligence specification |
| Master Project Handoff | Do not carry forward as a monolithic state document; replace with structured state/checkpoint model |

اصل اصلی: **V2 is derived from validated intent, not copied from V1 implementation.**

---

## 4. Architectural Principles Retained from V1

### 4.1 Strict Read-Only
Meylux V2 is a decision-support and intelligence system. The core platform has no authority to place, modify, cancel, or execute trades, manage leverage, move funds, or control trading accounts.

### 4.2 AI-First, Not AI-Only
AI performs reasoning, synthesis, contradiction analysis, and explanation over validated evidence. Deterministic financial calculations and structural mathematics remain outside the LLM reasoning layer.

### 4.3 No Data Fabrication
Missing, stale, contradictory, unavailable, or insufficient information remains explicitly represented. The system must be allowed to return LIMITED_DATA, INSUFFICIENT_DATA, STALE, DATA_GAP, UNAVAILABLE, or equivalent typed states rather than inventing values.

### 4.4 Evidence Hierarchy
Evidence precedence remains:

1. Verified real market data
2. Deterministic quantitative computation
3. Validated market structure
4. Derivatives and order-flow evidence
5. Specialist outputs
6. AI interpretation/synthesis
7. Hypothesis

Lower-level interpretation may not be represented as a higher-level fact.

### 4.5 Source of Truth Separation
PostgreSQL/TimescaleDB may serve as authoritative persistent truth. Redis is infrastructure for transport, queues, ephemeral coordination, caching, and rate limiting; it is not the authoritative permanent store.

### 4.6 Provider Agnosticism
Provider-specific details stay behind adapters. Binance and MEXC are initial providers, not architectural identities of the core domain.

### 4.7 Stable Logical Identity
Logical identity is independent from physical paths, filenames, class names, or runtime labels. Rename and relocation must not silently create a new architectural entity.

---

## 5. V1 Lessons Learned — Findings

### L1 — Context became distributed
**Finding:** Architecture, handoff, repository state, execution evidence, and chat context could diverge.

**Risk:** A new AI or a later session may infer an incorrect project state.

**V2 Rule — V2-MANDATORY:** Separate Architecture, Decisions, Registry, State, and Evidence. They must have explicit source-of-truth ownership.

### L2 — "Completed" and "Verified" were too easy to conflate
**Finding:** Phase labels could imply a stronger level of assurance than the evidence justified.

**Risk:** Downstream work assumes a capability is real because a document says it is complete.

**V2 Rule:** Lifecycle states must distinguish at minimum PLANNED, SPECIFIED, IMPLEMENTED, TESTED, VERIFIED, ACCEPTED, DEPRECATED.

### L3 — Data-growth failure was possible despite functional correctness
**Finding:** Incorrect close detection and unstable logical identity caused excessive persistence growth and duplicate records in V1.

**Risk:** Functional correctness at unit level did not prevent operational data explosion.

**V2 Rule — V2-MANDATORY:** Every persistent stream/table must define logical identity, uniqueness/idempotency protection, retention, expected growth envelope, and growth alarms before implementation approval.

### L4 — Queue backlog can become an operational failure domain
**Finding:** A heavy stale worker backlog accumulated in V1.

**Risk:** Recovery and operator visibility become difficult; queues may amplify rather than isolate load.

**V2 Rule:** Every queue must define ownership, purpose, retry policy, timeout, concurrency bound, dead-letter behavior, backlog alarm, and drain/recovery procedure.

### L5 — Hidden responsibility coupling between workers
**Finding:** Normalization work became coupled to another worker domain during V1.

**Risk:** A failure or load increase in one responsibility affects another.

**V2 Rule — V2-MANDATORY:** Worker ownership must be explicit. A worker cannot silently become the owner of another subsystem's responsibility.

### L6 — Exchange protocol semantics must not leak into generic contracts
**Finding:** Binance order-book sequence semantics created a bootstrap/resynchronization defect when the local reconstructor assumptions did not match the real update bridge rules.

**Risk:** A parser/reconstructor can appear syntactically correct while being behaviorally wrong.

**V2 Rule — V2-MANDATORY:** Provider protocol semantics must be specified before adapter implementation, including snapshot/update sequence semantics, bootstrap bridge condition, gap detection, replay ordering, duplicate handling, and resync behavior.

### L7 — Live endpoint correctness must be proven with real payloads
**Finding:** A WebSocket endpoint could connect successfully while not producing the expected stream, while another endpoint produced live updates.

**Risk:** "Connected" is incorrectly treated as "working".

**V2 Rule:** Connectivity, liveness, semantic validity, and sustained correctness are separate verification states.

### L8 — Rate-limit safety is a first-class reliability requirement
**Finding:** Repeated order-book resync attempts increased rate-limit consumption rapidly.

**Risk:** A recovery loop can become the source of a provider outage.

**V2 Rule — V2-MANDATORY:** Backoff, rate-budget monitoring, resync caps, escalation, and circuit-breaking must be specified for external-provider recovery paths.

### L9 — Policy, Target, Guarantee, Assumption and Observation were not always sufficiently separated
**Finding:** Configuration values and performance values can be mistaken for hard guarantees.

**Risk:** Architecture promises behavior the implementation or environment cannot prove.

**V2 Rule:** Every nonfunctional statement is typed as POLICY, TARGET, GUARANTEE, ASSUMPTION, OBSERVED, or VERIFIED.

### L10 — A large architecture tree can create false confidence
**Finding:** A detailed tree may look comprehensive while exact dependencies, failure behavior, identity, and evidence paths remain underspecified.

**Risk:** Missing contracts and hidden coupling appear late.

**V2 Rule:** Registry records must include dependencies, inputs, outputs, consumers, verification, failure behavior, security, observability, and lifecycle state, not just paths.

### L11 — Vertical integration was needed earlier
**Finding:** Layer-by-layer development can postpone discovery of integration defects until many artifacts already exist.

**Risk:** Late integration creates expensive redesign or exception handling.

**V2 Rule — V2-MANDATORY:** A controlled vertical slice must be defined early and maintained as a living integration proof.

### L12 — Real execution evidence belongs to Operator, not Producer
**Finding:** The governance workflow correctly separates implementation generation from actual execution.

**V2 Rule:** Producer reports only what it actually ran in its allowed environment; Operator supplies infrastructure/VPS EXEC-LOG; Reviewer closes gates only from evidence.

---

## 6. V1 Failure Classes Converted into V2 Design Controls

| Failure Class | V2 Control |
|---|---|
| Duplicate persistence | Logical identity + unique constraints + idempotency contract |
| Unbounded time-series growth | Retention + cardinality budget + growth alarms |
| Queue explosion | Bounded concurrency + backlog budget + alerting + recovery runbook |
| Wrong event-close semantics | Explicit provider event semantics + golden replay fixtures |
| Order-book resync loop | Sequence contract + bridge proof + bounded resync + rate budget |
| Silent feed failure | Liveness + semantic health + freshness checks |
| Hidden worker coupling | Responsibility ownership matrix |
| Architecture/state divergence | Machine-readable checkpoint + registry + change ledger |
| Premature completion claim | Lifecycle state machine + gate evidence |
| Host/resource pressure | Resource budget + backpressure + safe degradation policy |
| AI hallucination risk | Structured evidence input + schema guard + explicit uncertainty |
| Model/vendor lock-in | Provider/model abstraction and configuration binding |

---

## 7. New V2 Architectural Hardening Rules

### HR-01 — State is not Architecture
A project-state statement must never be embedded as an architectural rule. Current status belongs in `docs/state/` and evidence belongs in verification records.

### HR-02 — Registry is authoritative for identity
Every architectural entity that matters to traceability receives a stable identity before implementation, or is explicitly marked DISCOVERY/DEFERRED if intentionally unknown.

### HR-03 — Every dependency is directional
Dependencies must form a reviewable graph. Cycles are forbidden unless explicitly approved as an architectural requirement.

### HR-04 — Every persistent data path is bounded
No new persistent flow may be approved without a defined data-growth model and duplicate/idempotency model.

### HR-05 — Every external provider path has failure semantics
For each external source define timeout, retry, backoff, rate budget, outage state, stale state, recovery, and isolation behavior.

### HR-06 — Health has layers
At minimum distinguish process health, connection health, data-flow health, semantic correctness, freshness, and sustained stability.

### HR-07 — Verification is evidence-based
Words such as PASS, VERIFIED, COMPLETE, GREEN, DONE, or CLOSED require evidence references.

### HR-08 — Configuration cannot silently override architecture
Configuration may tune a permitted behavior but cannot weaken an invariant or change subsystem ownership without formal architectural change approval.

### HR-09 — Failure behavior is part of the contract
Happy-path success is not sufficient for acceptance. Every critical capability defines explicit negative and degraded states.

### HR-10 — AI continuation is a formal capability
The project must be resumable by another capable AI using repository state, registry, decisions, checkpoint, and the current artifact chain without relying on hidden chat memory.

---

## 8. V2 Architecture Classification Model

The existing 6-Tier hierarchy is retained:

- Tier 1 — Architectural Invariant
- Tier 2 — Required Capability
- Tier 3 — Required Behavior
- Tier 4 — Implementation Choice
- Tier 5 — Configuration / Operational Parameter
- Tier 6 — Performance Target / SLO

V2 adds a separate **Evidence Status dimension**:

- UNPLANNED
- PLANNED
- SPECIFIED
- IMPLEMENTED
- TESTED
- VERIFIED
- ACCEPTED
- DEPRECATED
- RETIRED

This means an implementation choice can be IMPLEMENTED but not VERIFIED, while an invariant can be RATIFIED but still lack runtime evidence in a particular environment.

The Evidence Status is not a replacement for the architectural tier; it is orthogonal to it.

---

## 9. Stable Identity V2 Extension

The SID model is preserved for requirements, phases, components, artifacts, contracts, database objects, services, workers, queues, APIs, configuration, tests, observability, security, documents, deployment, and performance.

V2 additionally assigns stable IDs to process artifacts:

| Prefix | Meaning |
|---|---|
| TO | Task Order |
| BR | Build Report |
| AR | Audit Report |
| EL | Execution Log |
| ADR | Architecture Decision Record |
| CHK | Checkpoint |
| OQ | Open Question |
| CHG | Change Ledger Entry |

An implementation chain becomes traceable, for example:

`TO -> BR -> AR -> EL -> CHK`

No process artifact may be considered authoritative solely because it exists in a chat message.

---

## 10. V2 Source-of-Truth Model

| Information Type | Authoritative Location |
|---|---|
| Constitution | `docs/constitution/` |
| Architecture | `docs/architecture/` |
| Entity identity | `docs/registry/` |
| Architectural decisions | `docs/decisions/` |
| Current state | `docs/state/CURRENT_CHECKPOINT.json` |
| Open questions | `docs/state/OPEN_QUESTIONS.yaml` |
| Change history | `docs/state/CHANGE_LEDGER.yaml` |
| Environment | `docs/environment/ENVIRONMENT_MANIFEST.yaml` |
| Verification rules | `docs/verification/` |
| Source code | Git repository |
| CI evidence | CI artifacts / reports |
| VPS execution evidence | Operator EXEC-LOG |

ChatGPT, Gemini, Claude, GLM, or another AI is a working participant, not the ultimate source of truth.

---

## 11. Project State Model

`CURRENT_CHECKPOINT.json` becomes the machine-readable bootstrap state for all new AI sessions.

Minimum fields:

- schema_version
- project_version
- phase
- step
- gate
- status
- last_approved_task_order
- last_build_report
- last_audit_report
- last_execution_log
- verified_artifacts
- unverified_artifacts
- open_questions
- active_assumptions
- deferred_decisions
- last_verified_commit
- updated_at_utc

A checkpoint is a state record, not an architectural decision.

---

## 12. Architecture of Open Questions and Deferred Decisions

Open questions and deferred decisions must be persistent and machine-readable.

Each Open Question records:

- ID
- Severity
- Blocking status
- Description
- Affected SIDs
- Owner
- Evidence required
- Resolution status

Each Deferred Decision records:

- ID
- Decision domain
- Why deferred
- Trigger for resolution
- Owner
- Affected future phases

This prevents unresolved issues from disappearing inside conversation history.

---

## 13. Persistence Safety Model

Every authoritative or high-volume dataset must declare before implementation:

1. Logical identity
2. Primary/unique key
3. Duplicate policy
4. Idempotency key where applicable
5. Retention policy
6. Compression/archive policy where applicable
7. Expected event rate
8. Expected daily growth
9. Maximum tolerated backlog
10. Growth alert threshold
11. Recovery/truncation policy for disposable test data
12. Replay/backfill semantics

A data store without these fields is **NOT READY FOR IMPLEMENTATION APPROVAL** for V2.

---

## 14. Queue and Worker Safety Model

Every queue record must define:

- owner
- producer
- consumer
- purpose
- payload contract
- retry policy
- timeout
- concurrency bound
- backlog limit or alert threshold
- dead-letter behavior
- idempotency requirements
- recovery/drain method

Every worker record must define:

- single primary responsibility
- allowed dependencies
- forbidden responsibilities
- input queues
- output queues
- side effects
- resource budget
- failure isolation

This is specifically designed to prevent the worker-domain coupling and stale-backlog problems observed in V1.

---

## 15. External Provider Reliability Contract

For each provider/feed, V2 must specify:

- authentication mode
- permissions required
- REST endpoints or equivalent interface class
- WebSocket/stream interface class
- event schema
- timestamp semantics
- sequence semantics if present
- connection lifecycle
- heartbeat
- reconnect policy
- gap detection
- snapshot/bootstrap behavior
- resynchronization behavior
- rate limits
- retry/backoff
- circuit breaking
- provider isolation
- stale-feed classification
- semantic health checks

For order books specifically, provider sequence semantics must be proven by replayable fixtures before live recovery behavior is trusted.

---

## 16. Health Model

V2 health is layered:

```text
PROCESS
   ↓
CONNECTION
   ↓
DATA FLOW
   ↓
SEMANTIC VALIDITY
   ↓
FRESHNESS
   ↓
SUSTAINED STABILITY
```

A process being alive does not imply that market data is correct.

A WebSocket being connected does not imply that a valid market stream is flowing.

A valid stream does not imply freshness.

A fresh stream does not imply sustained stability.

Each layer has its own evidence and status.

---

## 17. Resource Protection and Host Safety

The V2 design preserves the principle:

> Meylux protects its intelligence first, while protecting the host through safe resource management.

This becomes a two-part policy:

### Intelligence Preservation
Do not silently reduce analytical correctness, data integrity, deterministic computation, or evidence quality merely to keep the host comfortable.

### Host Protection
Use bounded queues, concurrency caps, backpressure, disk-growth alarms, memory budgets, circuit breakers, and safe workload shedding where the architecture permits it.

A system must not solve resource pressure by silently degrading the truthfulness of intelligence.

---

## 18. Vertical Slice Policy

V2 requires an early controlled vertical slice demonstrating a minimal real chain across representative boundaries.

The first slice should prove:

```text
Real/controlled input
 -> Provider boundary
 -> Canonical contract
 -> Validation
 -> Persistence or controlled transport
 -> Deterministic computation
 -> Structured evidence
 -> Minimal intelligence output
 -> Verification evidence
```

The slice is not the final product. It is an architectural integration proof.

The slice must be replayable and must expose failures rather than bypass them.

---

## 19. Venue Intelligence in V2

Venue Intelligence remains a first-class domain track but not a new global phase.

The existing Section 23 principle that Venue work rides existing phases P2..P6, with evaluation in P9, is retained as the architectural direction. The V2 hardening requirement is that Venue dependencies, SIDs, contracts, data-model assumptions, and gate riders must be registered from the beginning rather than attached late.

The Venue track must preserve:

- read-only semantics
- deterministic spread/executable calculations
- explicit freshness/alignment
- instrument equivalence validation
- distinction between headline and executable spread
- analytical inventory constraints only
- explicit degradation states
- provenance
- replay and zero-lookahead rules
- historical outcome evaluation

No Venue feature creates trading authority.

---

## 20. Intelligence Architecture Hardening

Market Intelligence must preserve the existing doctrine:

- no fabricated market facts
- explicit missing-data states
- evidence hierarchy
- specialist independence
- correlation-aware evidence weighting
- multi-timeframe reasoning
- contradiction analysis
- scenario analysis
- valid NO TRADE output
- separation of Opportunity Score, Analytical Confidence, and Data Quality

V2 additionally requires every final intelligence output to expose, directly or indirectly:

- evidence provenance
- data-quality condition
- model/prompt version where AI was used
- uncertainty/degradation state
- invalidating evidence or conditions
- evaluation linkage where historical evaluation is available

---

## 21. Governance Hardening

The Reviewer / Producer / Operator logical roles are retained.

### Reviewer
Owns audit, gate decisions, task specification, and approval authority. Does not execute on the VPS.

### Producer
Originates implementation content inside the task scope. Does not change architecture silently, does not execute on the VPS, and reports only actual test evidence.

### Operator
Human bridge and execution authority. Relays artifacts verbatim and runs approved execution commands.

No party silently edits another party's artifact. Corrections occur through the artifact cycle.

---

## 22. AI Continuation Protocol

A new AI joining V2 must read, in order:

1. Constitution
2. Master Architecture
3. Governance / Role Contract
4. Artifact Protocol
5. Current Checkpoint
6. Open Questions
7. Deferred Decisions
8. Relevant ADRs
9. Registry entries for current scope
10. Latest approved task/report/audit/evidence chain

The new AI must not infer completion, architecture, or next steps from chat memory alone.

This protocol is a formal V2 requirement.

---

## 23. ChatGPT Project Structure

V2 should use **one ChatGPT Project** for the project as a whole.

Recommended logical chats inside it:

- `MEYLUX V2 — CONTROL / REVIEWER`
- `MEYLUX V2 — PRODUCER RELAY`
- `MEYLUX V2 — MARKET INTELLIGENCE`
- `MEYLUX V2 — TROUBLESHOOTING`

These chats are role workspaces, not authoritative state stores.

The Project-level instructions should contain only durable governance and role rules. Large architecture text, registries, state, and decisions should live in version-controlled project files/repository.

---

## 24. V2 Document Set Resulting from Hardening

The minimum formal document set becomes:

1. `MEYLUX_CONSTITUTION_V2.md`
2. `MASTER_ARCHITECTURE_V2.md`
3. `ROLE_CONTRACT_V2.md`
4. `ARTIFACT_PROTOCOL_V2.md`
5. `AI_CONTINUATION_PROTOCOL_V2.md`
6. `TEST_STRATEGY_V2.md`
7. `EVIDENCE_POLICY.md`
8. `GATE_DEFINITIONS.md`
9. `ENVIRONMENT_MANIFEST.yaml`
10. Registry YAML/JSON files
11. ADR index and ADR records
12. `CURRENT_CHECKPOINT.json`
13. `OPEN_QUESTIONS.yaml`
14. `CHANGE_LEDGER.yaml`
15. Operational runbooks

The exact final filenames may be frozen during the next design step; this list is the required document capability set, not permission to create all implementation artifacts immediately.

---

## 25. What V2 Intentionally Does Not Do

This hardening document does not:

- implement runtime code
- create database migrations
- create Docker services
- connect to Binance/MEXC
- alter V1
- define every future function/class
- force premature library selections
- define final AI model vendors when intentionally deferred
- promise performance numbers without evidence
- create a trading execution subsystem

---

## 26. Acceptance Criteria for Architecture Hardening

Architecture Hardening is complete only when all of the following are true:

- V1 lessons are mapped to explicit V2 controls.
- Core mission and invariants are ratified.
- Architecture and state are separated.
- Stable identity policy is ratified.
- Registry schema is ratified.
- Artifact protocol is ratified.
- Continuation protocol is ratified.
- Environment contract is defined.
- Persistence safety policy is defined.
- Queue/worker safety policy is defined.
- External-provider reliability contract is defined.
- Verification and evidence model is defined.
- Gate semantics are defined.
- Vertical Slice policy is defined.
- Venue track placement is defined.
- Market Intelligence doctrine is defined.
- V2 document set is ratified.
- Any remaining unresolved blocking questions are explicitly recorded in `OPEN_QUESTIONS.yaml`.

Only after these conditions are met may the project enter implementation-oriented Phase 0 freeze.

---

## 27. Known Design Considerations

The following are intentionally not blocking the current hardening step but must be revisited before their activating phase:

- exact implementation technology for components where the architecture deliberately leaves alternatives open
- future embedding model and vector dimensions
- final production hardware baseline after the V2 target environment is selected
- advanced scanner optimizations
- future market classes outside the initial crypto scope
- future provider additions

These are not defects. They are controlled deferred choices.

---

## 28. Final V2 Design Principle

Meylux V2 must be designed so that the system can answer, for every important capability:

```text
What is it?
Why does it exist?
Who owns it?
What does it consume?
What does it produce?
What does it depend on?
What can break it?
How does it degrade?
How do we test it?
How do we verify it?
What evidence proves it?
Where is its state recorded?
How can another AI continue it?
```

If any critical capability cannot answer these questions, it is not yet fully specified for V2 implementation.

---

## 29. Source Materials Used for This Hardening

This document was derived from and reconciles the following Meylux source materials available at the time of drafting:

- Meylux project understanding / Base Structure
- MEYLUX MASTER TARGET ARCHITECTURE v5.1.1
- Meylux Reviewer / Producer Role Contract
- Market Intelligence v4
- Master Project Handoff / Current State documentation
- Operational lessons observed during the V1 construction and verification workflow, including data-growth incidents, queue backlog/recovery, provider stream verification, order-book sequencing/resynchronization behavior, worker coupling, and evidence-based gate closure.

This list identifies source categories. Exact authoritative filenames and final V2 document versions will be frozen in the V2 registry.

---

**Document Status:** Pending Ratification  
**Next Required Artifact:** `MEYLUX V2 CONSTITUTION & ARCHITECTURE FREEZE PACKAGE`  
**V1 Mutation Permission Granted by This Document:** NO
