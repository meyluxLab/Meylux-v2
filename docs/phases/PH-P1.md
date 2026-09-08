# MEYLUX V2 — PHASE P1

**Phase ID:** `PH-P1`  
**Logical Name:** Infrastructure Foundation  
**Status:** ACTIVE / IN_PROGRESS  
**Entry Gate:** `G-1`  
**Project Scope:** Meylux V2 only

## 1. Authority and Basis

This Phase is formally established by Project Owner authorization issued to CONTROL / REVIEWER under the standing **General Continuation and Phase Progression Authority** already incorporated into `ROL-V2-001`.

Authoritative architectural basis:
- `docs/architecture/MASTER_ARCHITECTURE_V2.md` — Section 9 Phase Model and Section 11 Phase P1.
- `docs/registry/phases.yaml` — existing Phase Registry mechanism.
- Existing V2 Governance / Artifact Protocol and Role Contract.
- Approved project Phase 1 roadmap as carried into the governed Phase 1 step sequence below.

Phase 0 remains historical and closed. No Phase 0 identity or record is modified.

## 2. Objective

Create the smallest reproducible runtime foundation capable of safely hosting later Meylux V2 phases, while establishing persistence, messaging, resource protection, configuration, observability, and recovery foundations.

The architecture defines P1 as **Runtime foundation, persistence, messaging, reproducibility** and requires reproducible runtime, migrations harness, queue foundation, logs, resource controls, and critical failure behavior to be verified at exit.

## 3. Scope Boundary

P1 is limited to infrastructure foundation. It does not authorize market acquisition, provider-runtime activity, specialist/AI intelligence, trading, capital control, or V1/V1 VPS mutation.

The frozen V2 invariants remain in force, including strict read-only behavior, deterministic baseline, no fabrication, evidence provenance, provider isolation, single authoritative persistence, and evidence-backed completion.

## 4. Complete Step Sequence

### `STEP-P1-001` — Repository Foundation

**Order:** 1  
**Predecessor:** Phase entry / `G-1`  
**Purpose:** Establish the governed V2 repository/runtime project foundation required for subsequent P1 work.  
**Scope:** Repository structure, baseline project metadata, development/build conventions, required directory foundation, and reproducibility prerequisites.  
**Outputs:** Repository foundation artifacts and corresponding registry/state updates where required.  
**Basis:** Master Architecture target repository structure; P1 reproducibility objective.  
**Completion boundary:** Foundation is implemented within the authorized scope, self-tested by Producer, independently reviewed by CONTROL, and required evidence is recorded.

### `STEP-P1-002` — Docker Foundation

**Order:** 2  
**Predecessor:** `STEP-P1-001`  
**Purpose:** Establish the reproducible container/service foundation for the V2 runtime without activating unauthorized external/runtime operations.  
**Scope:** Docker/Compose foundation, service topology required by P1, bounded service configuration, and reproducible local/container execution prerequisites.  
**Outputs:** Container and compose foundation artifacts, tests/evidence as applicable.  
**Basis:** Master Architecture target repository/runtime architecture; P1 reproducibility and safe-hosting objective.  
**Completion boundary:** Container foundation is implemented and its required structural/behavioral evidence is independently reviewed.

### `STEP-P1-003` — Database Foundation

**Order:** 3  
**Predecessor:** `STEP-P1-002`  
**Purpose:** Establish the authoritative persistence foundation for V2.  
**Scope:** PostgreSQL/TimescaleDB foundation, migration harness, governed roles/privileges, persistence conventions, and recovery/replay prerequisites.  
**Outputs:** Database/migration artifacts, registry records, and verification evidence as applicable.  
**Basis:** Master Architecture P1 persistence requirements; single authoritative persistence invariant.  
**Completion boundary:** Persistence foundation and migration path satisfy the authorized requirements and are independently verified.

### `STEP-P1-004` — Data Contracts

**Order:** 4  
**Predecessor:** `STEP-P1-003`  
**Purpose:** Establish the canonical V2 data-contract foundation required for deterministic, validated downstream processing.  
**Scope:** Canonical contract definitions, type/precision/time semantics, validation boundaries, immutability and contract testing required by P1.  
**Outputs:** Contract artifacts and contract-test evidence.  
**Basis:** Master Architecture canonical data rule and deterministic/evidence doctrine.  
**Completion boundary:** Required contracts and their verification evidence are present and independently accepted for the P1 boundary.

### `STEP-P1-005` — Data Quality Foundation

**Order:** 5  
**Predecessor:** `STEP-P1-004`  
**Purpose:** Establish the foundational data-quality representation and handling required before later market-data phases.  
**Scope:** Explicit quality states, validation/rejection boundaries, degradation representation, and foundational quality evidence.  
**Outputs:** Data-quality artifacts, tests, and registry/evidence updates where required.  
**Basis:** Master Architecture data states/data-quality rules; P1 foundation dependency for later acquisition/normalization phases.  
**Completion boundary:** Data-quality foundation is implemented and independently verified without fabricating unavailable market data.

### `STEP-P1-006` — Async Worker & Queue Foundation

**Order:** 6  
**Predecessor:** `STEP-P1-005`  
**Purpose:** Establish bounded asynchronous worker and messaging infrastructure for later V2 workloads.  
**Scope:** Queue/transport foundation, worker responsibilities, bounded concurrency, timeout/retry/backpressure semantics, and failure isolation within P1.  
**Outputs:** Worker/queue artifacts and reproducible test evidence.  
**Basis:** Master Architecture P1 worker requirements and messaging scope; host/resource protection principles.  
**Completion boundary:** Worker/queue foundation demonstrates required behavior under authorized tests and is independently verified.

### `STEP-P1-007` — Observability Foundation

**Order:** 7  
**Predecessor:** `STEP-P1-006`  
**Purpose:** Establish structured observability sufficient to diagnose and verify P1 behavior and failures.  
**Scope:** Structured logging, correlation/context propagation, secret scrubbing, health/diagnostic signals, and evidence-compatible observability conventions.  
**Outputs:** Observability artifacts, tests, and verification evidence.  
**Basis:** Master Architecture P1 observability requirement and evidence provenance doctrine.  
**Completion boundary:** Required observability behavior is demonstrated and independently verified; secrets are not exposed.

### `STEP-P1-008` — Disaster Recovery / Restore Verification & Phase 1 Closure

**Order:** 8  
**Predecessor:** `STEP-P1-007`  
**Purpose:** Verify recovery/restore behavior for the P1 foundation and establish the evidence boundary required for Phase 1 closure.  
**Scope:** Backup/restore path, restore verification, critical failure/recovery behavior, reproducibility evidence, and final P1 closure evidence.  
**Outputs:** Recovery/restore evidence, final verification/audit artifacts, and governed Phase 1 closure state.  
**Basis:** Master Architecture P1 exit requirement and evidence-backed state invariant.  
**Completion boundary:** P1 exit requirements are evidenced and independently verified; only then may P1 become CLOSED / VERIFIED.

## 5. Step Activation Rule

Only the currently activated Step may be executed. Completion of a Step does not by itself authorize unrelated future work; progression to an already-defined next Step occurs through the General Continuation and Phase Progression Authority after the current Step is completed and verified, subject to all higher-level governance boundaries.

## 6. Phase Exit

P1 may close only when its defined Steps and required evidence establish:

- reproducible runtime foundation;
- migrations harness;
- queue/messaging foundation;
- structured logs/observability;
- resource controls;
- critical failure and recovery behavior;
- required independent verification and governed closure evidence.

No P1 exit claim is made merely by defining or implementing these items.
