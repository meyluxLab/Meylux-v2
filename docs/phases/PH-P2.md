# PH-P2 — Data Acquisition & Market Data Foundation

**Status:** AUTHORIZED / ACTIVE — Step 2 authorized; implementation not yet evidenced
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

Repository scope: provider abstraction package, acquisition envelopes/contracts, capability/error/degradation semantics, provider-neutral identity/time/sequence fields, deterministic serialization requirements, tests, and required registry/traceability updates.

VPS scope: inspection only for this Step. No provider runtime is activated by this Step.

Completion requires: implementation is within frozen architecture; provider-specific behavior remains behind the boundary; contracts are deterministic and testable; missing/stale/unavailable/error states are explicit; no network/provider runtime execution is claimed; Build Report exists and CONTROL audit can objectively verify the result.

### `STEP-P2-002` — Binance Acquisition Adapter

**Order:** 2  
**Status:** AUTHORIZED / ACTIVE  
**Predecessor:** `STEP-P2-001`  
**Task Order:** `TO-P2-002`

Objective: implement the Binance adapter against the approved provider boundary for the Phase 2 acquisition scope, including required REST/bootstrap and live-stream capabilities, bounded retry/reconnect behavior, provider isolation, and evidence-compatible telemetry.

Repository scope: Binance provider adapter implementation and the governed tests/traceability artifacts required to demonstrate integration with the existing provider-neutral acquisition boundary. Provider-specific wire/API behavior must remain behind the provider boundary.

VPS scope: deployment/configuration only after Producer implementation and within the authorized development/validation context established by `TO-P2-002`; provider credentials, if later required, must use approved secret handling and must never enter repository artifacts.

Completion requires: Binance behavior is implemented within the frozen architecture and approved acquisition contracts; required REST/bootstrap and live-stream capabilities are exercised to the authorized extent; retry/reconnect behavior is bounded; provider isolation is demonstrated; evidence-compatible telemetry is present; no trading/capital activity occurs; Build Report exists and CONTROL can independently verify the result.

### `STEP-P2-003` — MEXC Acquisition Adapter

**Order:** 3  
**Status:** DEFINED / INACTIVE  
**Predecessor:** `STEP-P2-002`

Objective: implement the MEXC adapter against the same provider boundary with equivalent acquisition semantics and independent failure handling.

VPS scope: same governed deployment/configuration boundary as Step 2.

### `STEP-P2-004` — Live Collector, Raw/Staging Persistence & Replay Safety

**Order:** 4  
**Status:** DEFINED / INACTIVE  
**Predecessor:** `STEP-P2-003`

Objective: integrate provider acquisition into the collector, establish raw/staging persistence and transport semantics, bounded queue/backpressure behavior, duplicate/idempotency controls, sequence/reconnect handling, and replay-safe acquisition behavior.

VPS scope: deployment, migration where required, runtime restart/recreation, service activation, persistence initialization, and runtime evidence are required where authorized by the Step Task Order.

### `STEP-P2-005` — Dual-Provider Operational Hardening

**Order:** 5  
**Status:** DEFINED / INACTIVE  
**Predecessor:** `STEP-P2-004`

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
