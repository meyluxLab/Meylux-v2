# PH-P2 — Data Acquisition & Market Data Foundation

**Status:** AUTHORIZED / ACTIVE — Step 5 authorized; implementation pending Producer execution
**Phase SID:** `PH-P2`
**Architectural basis:** `DOC-V2-ARCH-001` RATIFIED / FROZEN; Constitution and Architectural Invariants
**Predecessor:** `PH-P1` CLOSED / VERIFIED
**Objective:** establish the governed, provider-isolated, evidence-backed acquisition boundary that obtains real market data for V2 and hands it to the canonical validation/normalization boundary without moving validation/normalization ownership into Phase 2.

## Scope

Phase 2 establishes the first real market-data acquisition layer for V2. It covers provider abstraction, provider adapters, acquisition transports, raw/staging representation, bounded persistence/transport needed for acquisition, replay/idempotency and sequencing controls, collector integration, and dual-provider runtime verification.

The first-class providers for this phase are **Binance** and **MEXC**. Provider-specific behavior must remain behind the provider abstraction and provider failure must remain isolated.

Phase 2 output is acquisition evidence and raw/staging data suitable for the Phase 3 Validation, Normalization & Data Quality Engine. Phase 2 does not make raw provider payloads authoritative analytical truth.

## Explicit non-scope

- deterministic quantitative/market-structure computation (Phase 4);
- Phase 3 validation/normalization ownership;
- specialist AI analysis or intelligence synthesis;
- trading, order placement, leverage, custody, balances, transfers, or capital control;
- V1 mutation or V1 runtime activity;
- provider credentials in repository/chat/build reports;
- redesign of frozen architecture;
- unrelated infrastructure improvement.

## Phase 2 Step sequence

### `STEP-P2-001` — Provider Boundary & Acquisition Contracts

**Order:** 1  
**Status:** VERIFIED / COMPLETE  
**Predecessor:** `PH-P1` / `STEP-P1-008`  
**Task Order:** `TO-P2-001`  
**Audit:** `AR-P2-AUDIT-001`

Objective: define and implement the provider-neutral acquisition boundary and contracts required by later provider adapters.

### `STEP-P2-002` — Binance Acquisition Adapter

**Order:** 2  
**Status:** VERIFIED / COMPLETE  
**Predecessor:** `STEP-P2-001`  
**Task Order:** `TO-P2-002`  
**Audit:** `AR-P2-AUDIT-002`

Objective: implement the Binance adapter against the approved provider boundary for the Phase 2 acquisition scope, including required REST/bootstrap and live-stream capabilities, bounded retry/reconnect behavior, provider isolation, and evidence-compatible telemetry.

### `STEP-P2-003` — MEXC Acquisition Adapter

**Order:** 3  
**Status:** VERIFIED / COMPLETE  
**Predecessor:** `STEP-P2-002`  
**Task Order:** `TO-P2-003`  
**Audit:** `AR-P2-AUDIT-003`

Objective: implement the MEXC adapter against the same provider boundary with equivalent acquisition semantics and independent failure handling.

CONTROL verified the corrected current Spot protobuf WebSocket implementation and successful repository CI evidence. Live external MEXC connectivity remains explicitly unverified because no live network probe was available; this does not negate repository-level Step verification.

### `STEP-P2-004` — Live Collector, Raw/Staging Persistence & Replay Safety

**Order:** 4  
**Status:** VERIFIED / COMPLETE  
**Predecessor:** `STEP-P2-003`  
**Task Order:** `TO-P2-004`  
**Audit:** `AR-P2-AUDIT-004`

Objective: integrate provider acquisition into the collector, establish raw/staging persistence and transport semantics, bounded queue/backpressure behavior, duplicate/idempotency controls, sequence/reconnect handling, and replay-safe acquisition behavior.

CONTROL independently verified the final repository implementation and evidence. PR #15 was merged after final traceability correction. Final evidence included CI Core #253 (`154 tests ... OK`, with explicit Binance and P2-004 suites each `16 OK`) and Docker Foundation #56 (`SUCCESS`). Raw/staging remains non-authoritative analytical evidence. No live provider network execution or production deployment is claimed.

### `STEP-P2-005` — Dual-Provider Operational Hardening

**Order:** 5  
**Status:** AUTHORIZED / ACTIVE  
**Predecessor:** `STEP-P2-004`  
**Task Order:** `TO-P2-005`

Objective: harden acquisition for provider isolation, rate-limit behavior, bounded reconnects, resource growth, observability, degraded-provider behavior, and operational recovery without changing higher-level architecture.

VPS scope: runtime configuration, health/recovery verification, and bounded operational recovery where explicitly authorized.

### `STEP-P2-006` — End-to-End Acquisition Verification & Phase 2 Closure

**Order:** 6  
**Status:** DEFINED / INACTIVE  
**Predecessor:** `STEP-P2-005`

Objective: prove the Phase 2 acquisition boundary end-to-end using real provider/runtime evidence, replay/idempotency evidence, persistence evidence, dual-provider isolation evidence, and the required exit criteria.

VPS scope: full authorized runtime verification for the Phase 2 boundary, followed by separate CONTROL verification and Phase 2 closure evidence.

## Phase 2 completion boundary

Phase 2 is complete only when all six Steps are `COMPLETE / VERIFIED`, all required Repository artifacts and tests exist, all required VPS/runtime operations have actual execution evidence, both first-class providers have been exercised within the authorized acquisition boundary, raw/staging persistence and replay safety are verified, provider isolation/degradation behavior is verified, and the Phase 2 exit audit and checkpoint are recorded.

`IMPLEMENTED != EXECUTED != VERIFIED` remains mandatory.
