# Meylux V2

Meylux V2 is an AI-first, deterministic-baseline, **read-only AI Market Intelligence and Decision Support Platform**.

It is **not a trading bot** and has no authority to place, modify, cancel, or execute trades, manage leverage, move funds, or control trading accounts. This boundary is an architectural invariant of the project and is not configurable.

## Repository Status

**This section is derived from `docs/state/CURRENT_CHECKPOINT.json` and `docs/registry/phases.yaml`, the project's authoritative current-state records. It must be re-synchronized against those files at the close of every Step or Phase (see `docs/governance/ARTIFACT_PROTOCOL_V2.md`, "Mandatory Peripheral Synchronization Checklist", `ADR-GOVERNANCE-012`) — it is never authoritative on its own, and never edited without re-checking the Checkpoint first.**

- **Formation:** `PP-00` through `PP-12` — `APPROVED / CLOSED`.
- **G-0:** `CLOSED / VERIFIED`. **G-0R:** `RATIFIED / VERIFIED`.
- **Master Architecture (`DOC-V2-ARCH-001`):** `RATIFIED / FROZEN`, version `2.0.0`, amended (execution-authority scope only, not content) by `ADR-GOVERNANCE-010`.
- **Phase 0 — Constitution, Architecture, Specification Foundation:** `CLOSED / VERIFIED`.
- **Phase 1 — Infrastructure Foundation:** `CLOSED / VERIFIED`.
- **Phase 2 — Data Acquisition & Market Data Foundation:** `CLOSED / VERIFIED` (final audit `AR-P2-AUDIT-007`).
- **Phase 3 — Validation, Normalization & Data Quality Engine:** `CLOSED / VERIFIED`. `STEP-P3-001` through `STEP-P3-008` are `COMPLETE / VERIFIED`; final audit `AR-P3-008` and G-3 evidence are established.
- **Phase 4 — Deterministic Quantitative & Market Structure Engine:** `CLOSED / VERIFIED`. `STEP-P4-001` through `STEP-P4-006` are `COMPLETE / VERIFIED`; final Step audit `AR-P4-015`; **G-4: `ESTABLISHED / VERIFIED`**. Historical audits and correction cycles remain preserved for traceability.
- **Phase 5 — Specialist Market Intelligence Layer:** `ACTIVE / AUTHORIZED`. `STEP-P5-006` — `DEFINED / INACTIVE`; its upstream prerequisite resolution is active under `TO-P4-014-CORRECTIVE-001`; `STEP-P5-005` remains `COMPLETE / VERIFIED` under `AR-P5-005`. Scope remains bounded by the authorized Phase-5 roadmap; Forex remains future intent only.
- **Latest completed Task Order:** `TO-P4-014-CORRECTIVE-001` — bounded S-03 Volume/RVOL continuation under `TO-P4-014`; `active_task_order = TO-P4-014-CORRECTIVE-001`; historical `STEP-P5-005 / TO-P5-005` closure remains preserved; P5-006 specialist implementation is not activated.
- **Registry:** `INITIALIZED_VERIFIED`.
- **GitHub installation:** `INSTALLED_VERIFIED`. This repository is the live, populated V2 Source of Truth — it is not an empty baseline package.
- **VPS:** `SET UP / VERIFIED`.
- **Last verified commit:** see `docs/state/CURRENT_CHECKPOINT.json` (`last_verified_commit`) for the exact runtime-verified implementation commit; it is not duplicated here to avoid a second, driftable copy of the same fact.

**Open governance items currently on record** (see `docs/state/CURRENT_CHECKPOINT.json.open_questions` and `docs/state/OPEN_QUESTIONS.yaml` for full detail — not restated here to avoid drift):

- Constitution Stable ID: `IDENTITY UNCONFIRMED`.
- `OQ-P4-006-MEXC-RESOURCEWARNING` remains on record.
- Futures acquisition capability is not present in the current Binance/MEXC adapters; the bounded dependency route remains through the owning P2 boundary when a concrete P5 need arises.

The existence of any file in this repository does not, by itself, constitute implementation, execution, verification, ratification, or authorization of anything beyond what `CURRENT_CHECKPOINT.json` and the Registry explicitly record. When this README and `CURRENT_CHECKPOINT.json` ever appear to disagree, `CURRENT_CHECKPOINT.json` is authoritative and this file is stale and due for correction.

## Source-of-Truth Model

The governed repository/artifact model is the durable project record. Chat sessions and AI continuity threads are working environments, not authoritative state stores.

- Constitution: `docs/constitution/`
- Architecture: `docs/architecture/`
- Governance: `docs/governance/`
- Decisions (ADR/ACR): `docs/decisions/`
- Registry: `docs/registry/`
- Current state: `docs/state/CURRENT_CHECKPOINT.json`
- Open questions: `docs/state/OPEN_QUESTIONS.yaml`
- Deferred decisions: `docs/state/DEFERRED_DECISIONS.yaml`
- Change history: `docs/state/CHANGE_LEDGER.yaml`
- Verification rules (Gate Definitions, Evidence Policy): `docs/verification/`
- Environment model: `docs/environment/`
- Phase specifications: `docs/phases/`
- Task Orders / Build Reports / Audit Reports: `docs/task-orders/`, `docs/build-reports/`, `docs/audits/`
- Reference-only planning Blueprints for not-yet-authorized Phases: `docs/blueprint/`
- Continuity / AI bootstrap material: `docs/continuity/`
- Source code: repository root (`src/`, `contracts/`, `tests/`, etc.)

No single document overrides this hierarchy silently. Precedence is: **Constitution → Ratified/Frozen Master Architecture → ADR/ACR → Master Registry → Phase/Step specifications → Task Orders → implementation artifacts → verification evidence → `CURRENT_CHECKPOINT`** (see `docs/architecture/MASTER_ARCHITECTURE_V2.md`, §0.2).

## Governance Model

Meylux V2 is built and continued through a governed Producer/CONTROL model:

- **CONTROL / REVIEWER** (`ROL-V2-001`) — governance, audit, Task Order issuance, independent verification, and bounded authorized continuation.
- **PRODUCER / ARCHITECT-BUILDER** (`ROL-V2-002`) — implementation against an authorized Task Order, with its own Build Report evidence.
- Independent CONTROL verification (Audit Reports) is required before any Producer claim of completion is treated as `VERIFIED`.

Full role definitions are in `docs/governance/`. AI sessions resuming work on this project should follow `docs/continuity/MEYLUX_V2_BOOTSTRAP.md` for the required continuity-reconstruction procedure before taking any action.

## V1 Boundary

V1 is frozen historical/reference material and remains outside V2. Nothing in this repository grants permission to modify, resume, or integrate V1 runtime infrastructure. V1 lessons are incorporated into V2 only as documented source material (see `docs/architecture/MEYLUX_V2_ARCHITECTURE_HARDENING_LESSONS_LEARNED.md`), never as a codebase fork.


## Phase 5 Current State

Phase 5 is established and authorized under the Project Owner Phase 5 Re-Direction Directive dated 2026-09-23. Current governed boundary: `STEP-P5-006` — `DEFINED / INACTIVE`; Active Task Order: `TO-P4-014` for bounded upstream Group-C prerequisite resolution; S-03 Volume/RVOL corrective integration `TO-P4-014-CORRECTIVE-001` is `VERIFIED / COMPLETE` under `AR-P4-021`; `TO-P5-005` is `VERIFIED / COMPLETE` under `AR-P5-005`; `TO-P4-013` remains `VERIFIED / COMPLETE` under `AR-P4-020`; Completion Audit: `AR-P5-005`; `TO-P3-009` remains historically `VERIFIED / COMPLETE`; controlled reattachment `TO-P3-009-REATTACH-001` is `VERIFIED / COMPLETE` under `AR-P3-009-REATTACH-001`; PRQ-4 is `RESOLVED / VERIFIED`; `TO-P5-002` is `VERIFIED / COMPLETE` under `AR-P5-002`. `STEP-P5-003` was separately authorized by the Project Owner on 2026-09-29 and formalized/activated by CONTROL under `TO-P5-003`.


## Post-Closure Investigation State

`TO-P3-010` is `VERIFIED / COMPLETE` under `AR-P3-010`; PR #58 merged as `56ba10f5c964319e966b8272c008823c3128b765`. The corrected P3-009 Docker evidence harness now requires Timescale initialization completion plus final-server SQL readiness before migrations and preserves actionable subprocess/container diagnostics. Historical P3-009 failures remain preserved; no P3/P5 semantic boundary or Phase/Step closure was reopened. `STEP-P5-004` / `TO-P5-004` is independently verified and closed under `AR-P5-004`. `STEP-P5-005` / `TO-P5-005` is complete and independently verified under `AR-P5-005`; `TO-P5-005-CORRECTIVE-001` is also VERIFIED / COMPLETE under `AR-P5-006`, establishing the historical S-12 Branch-A causal result; `TO-P4-013` / `AR-P4-020` established the required Group-B upstream capability.


TO-P2-009 (A-P2-MEXC investigation-only) was independently verified and closed under `AR-P2-AUDIT-009`; `MEXC_FINALITY` remains `UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`. `TO-P2-010` reached `VERIFIED / COMPLETE` under `AR-P2-AUDIT-010`; `TO-P2-011` and `TO-P2-012` are also `VERIFIED / COMPLETE`; `TO-P2-013` remains `PREPARED / NOT ACTIVATED`. These post-closure P2 records remain separate from the active `PH-P5 / STEP-P5-003` boundary.


## TO-P5-004 Closure

`TO-P5-004` / `STEP-P5-004` — Group A Technical, Multi-Timeframe and Volatility — is independently verified and closed under `AR-P5-004`. The corrected implementation/test revision is `45915b9f4ceb4c84349835d4e47d00897ba74eca`, PR #63 merged as `8f014e216a03378853cd2d74b869ef03d65e907b`. CONTROL independently verified the authoritative EMA alias semantics, closed-candle temporal boundary, EvidenceRef provenance, Redis → specialist worker → PostgreSQL persistence/read-back, replay idempotency, append-only UPDATE/DELETE protection, and runtime performance/resource baseline. `STEP-P5-005` is complete and independently verified under `AR-P5-005`; no later Phase 5 Step is activated.


## Post-Closure S-12 Causal Resolution

`TO-P5-005-CORRECTIVE-001` is **VERIFIED / COMPLETE** under `AR-P5-006`. CONTROL established Branch A: no qualifying liquidity pool existed in the authoritative P4 input/output boundary for the historical S-12 case. No corrective implementation is required by that investigation; historical `STEP-P5-005 / TO-P5-005` remains COMPLETE / VERIFIED and `STEP-P5-006` is established but remains unactivated pending independent verification of its PRQ-1 Group-C / PRQ-2 trade gate.
