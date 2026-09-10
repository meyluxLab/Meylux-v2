# PHASE 2 DETERMINATION REPORT

**Document ID:** `DOC-P2-001`  
**Phase:** `PH-P2`  
**Status:** DETERMINED / AUTHORIZED / ACTIVE  
**Basis:** Project Owner Phase 2 authorization; `DOC-V2-ARCH-001` RATIFIED / FROZEN; Constitution; Phase 1 closure evidence

## 1. Determination

Phase 2 is established as **Data Acquisition & Market Data Foundation**. Its purpose is to establish the governed, provider-isolated acquisition boundary for real market data and deliver raw/staging acquisition output to the Phase 3 Validation, Normalization & Data Quality boundary.

This determination does not amend or redesign the frozen architecture.

## 2. Architectural and constitutional basis

Applicable authoritative constraints include:

- `DOC-V2-ARCH-001` RATIFIED / FROZEN;
- `INV-V2-001` strict read-only;
- `INV-V2-002` deterministic baseline;
- `INV-V2-003` no fabrication;
- `INV-V2-004` evidence provenance;
- `INV-V2-006` stable logical identity;
- `INV-V2-007` single authoritative persistence;
- `INV-V2-008` provider isolation;
- `INV-V2-010` evidence-backed state;
- V1 isolation;
- execution/verification separation;
- existing CONTROL bounded VPS execution authority.

## 3. Scope

Phase 2 covers provider abstraction, acquisition contracts, Binance and MEXC acquisition adapters, live collector integration, raw/staging persistence and transport, replay/idempotency/sequence safety, provider isolation, bounded operational behavior, and end-to-end runtime verification.

## 4. Explicit non-scope

Phase 2 does not own validation/normalization, deterministic quantitative/market-structure computation, specialist AI analysis, trading/capital/custody/leverage, V1 mutation, or unrelated infrastructure improvements.

## 5. Step order

1. `STEP-P2-001` — Provider Boundary & Acquisition Contracts — **ACTIVE / AUTHORIZED**
2. `STEP-P2-002` — Binance Acquisition Adapter — DEFINED / INACTIVE
3. `STEP-P2-003` — MEXC Acquisition Adapter — DEFINED / INACTIVE
4. `STEP-P2-004` — Live Collector, Raw/Staging Persistence & Replay Safety — DEFINED / INACTIVE
5. `STEP-P2-005` — Dual-Provider Operational Hardening — DEFINED / INACTIVE
6. `STEP-P2-006` — End-to-End Acquisition Verification & Phase 2 Closure — DEFINED / INACTIVE

## 6. Repository / VPS boundary by Step

| Step | Repository | VPS / Runtime |
|---|---|---|
| P2-001 | Provider boundary, acquisition contracts, tests | Inspection only |
| P2-002 | Binance adapter and tests | Deployment/config/runtime after authorized implementation |
| P2-003 | MEXC adapter and tests | Deployment/config/runtime after authorized implementation |
| P2-004 | Collector, raw/staging, replay/idempotency, persistence/transport | Migration/deployment/restart/initialization/runtime |
| P2-005 | Operational hardening and tests | Runtime configuration/recovery/verification |
| P2-006 | Exit tests, evidence and closure artifacts | End-to-end runtime verification |

## 7. Producer responsibilities

Producer implements only the Repository scope of the currently authorized Task Order, self-tests actual changes, reports exact evidence, and does not silently alter architecture, Stable IDs, contracts, or scope.

## 8. CONTROL responsibilities

CONTROL determines/maintains governed boundaries, audits Producer output, performs authorized VPS/runtime operations for applicable Steps, records EXEC-LOG evidence, and performs separate verification. CONTROL must not silently repair Producer implementation defects.

## 9. Acceptance / Definition of Done

Phase 2 requires every Step to be COMPLETE / VERIFIED, all required repository artifacts/tests to exist, actual provider/runtime execution evidence where applicable, successful dual-provider isolation/degradation behavior, raw/staging persistence and replay safety evidence, and a separate Phase 2 exit audit/checkpoint.

## 10. Relevant Open Questions / Deferred Decisions / Known Design Considerations

No Phase-2-specific Open Question or Deferred Decision is currently recorded in the authoritative lists. The Constitution Stable-ID identity question remains unrelated to Phase 2 execution and is not a blocker for the current Step.

Known Design Consideration: existing environment/governance documents contain historical status wording from pre-ratification stages. Their content must not override the ratified architecture or current checkpoint. Any material stale wording affecting a later Phase 2 runtime boundary must be reconciled through controlled governance bookkeeping before that runtime boundary is activated.

## 11. Actual V2 VPS baseline relevant to Phase 2

Direct inspection of the actual V2 VPS established:

- Host: `server-l6rf`.
- OS: Ubuntu 24.04 LTS.
- CPU: 4 vCPU.
- Memory: 15 GiB total; approximately 14 GiB available at inspection.
- Swap: none.
- Root filesystem: 76 GiB total, approximately 68 GiB available at inspection.
- Repository: `/srv/meylux-v2`.
- VPS repository HEAD: `1a2c28f29016454dc396a6872e64e6976575f558` (`governance: correct P1 audit registry path`).
- VPS local branch reports `main...origin/main [ahead 22]`; the local tracking ref is stale and is not treated as a current authoritative GitHub divergence.
- Docker Compose runtime services present and running: `api`, `collector`, `db`, `redis`, `worker-ai`, `worker-quant`.
- DB: TimescaleDB `2.29.2-pg16`, healthy.
- Redis: `7.4.6-alpine`, healthy.
- V2 persistent volume: `meylux-db-data`.
- Root `.env`: `root:root`, mode `0600`.
- The actual source tree contains foundation/runtime/observability/queue code and canonical candle/orderbook/trade contracts, but no implemented Binance/MEXC provider adapter layer was found in the inspected V2 source tree.

## 12. Repository ↔ VPS drift findings

The VPS is not treated as a second source of truth. The observed `ahead 22` state is explicitly classified as **non-authoritative tracking-ref drift** because the VPS has not performed an authenticated fetch against the current GitHub main during this determination. No force reset, force push, destructive synchronization, or apparent-consistency operation was performed.

Material Phase-2 finding: the current VPS runtime contains the Phase-1 foundation and a running collector service, but the Phase-2 provider acquisition implementation is not present. This is expected and is not a Phase-1 defect.

## 13. VPS readiness

For `STEP-P2-001`, VPS readiness is sufficient because the Step requires inspection only and no provider runtime activation. Existing Docker/DB/Redis foundation is available for later Steps, subject to Step-specific deployment/runtime authorization and actual verification.

No provider credentials are currently present or required for `STEP-P2-001`.

## 14. Required repository changes before Phase 2 runtime

- Complete `STEP-P2-001`.
- Implement and verify Binance and MEXC adapters only in their authorized Steps.
- Establish raw/staging persistence and collector runtime only in the authorized Step.
- Reconcile any stale governance/environment wording that materially affects a later runtime boundary before that boundary is activated.

## 15. First executable boundary

**`STEP-P2-001` is the first executable Phase 2 boundary.**

**Task Order:** `TO-P2-001` — Provider Boundary & Acquisition Contracts.

**VPS:** inspection only for this Step.

## 16. Genuine blocker / escalation

No blocker prevents execution of `TO-P2-001`. No new architecture, security boundary, constitutional exception, or Project Owner decision is required for this Step.

The next governed transition is:

`TO-P2-001 → Producer Implementation → BR-P2-001 → CONTROL Audit → authorized STEP-P2-002`
