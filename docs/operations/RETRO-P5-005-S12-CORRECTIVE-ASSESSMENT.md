# DOC-P5-003 — Retrospective / Corrective Assessment — P5-005 / S-12 Liquidity

**Stable Document ID:** `DOC-P5-003`  
**Artifact Type:** ASSESSMENT  
**Assessment Basis:** `ADR-GOVERNANCE-014`  
**Affected Boundary:** `PH-P5 / STEP-P5-005 / TO-P5-005`  
**Status:** CLOSED / VERIFIED  
**Assessment Owner:** `ROL-V2-001 — CONTROL / REVIEWER`  
**Date:** 2026-10-05

## 1. Purpose

This document applies the project-wide rule established by `ADR-GOVERNANCE-014` to the specific historical P5-005 / S-12 Liquidity case.

It is a retrospective/corrective assessment only. It is not:

- a reopening of `STEP-P5-005`;
- an amendment to `AR-P5-005`;
- an amendment to `BR-P5-006`;
- an implementation authorization;
- a corrective Task Order;
- an architectural decision; or
- a technical solution selection.

All historical evidence remains unchanged.

## 2. Historical Evidence Boundary

The following artifacts were read from the repository Source of Truth for this assessment:

- `docs/task-orders/TO-P5-005.md`
- `docs/build-reports/BR-P5-006.md`
- `docs/audits/AR-P5-005.md`
- `docs/operations/sentinelx/EXEC-LOG-TO-P5-005-CONTROL-RUNTIME-20261005.md`
- `docs/phases/PH-P5.md`
- `docs/requirements/P5_002_FACT_REQUIREMENTS_MATRIX.md`
- `docs/blueprint/PHASE5_ROADMAP.md`
- `docs/task-orders/TO-P4-013.md`
- `docs/build-reports/BR-P4-013.md`
- `docs/audits/AR-P4-020.md`
- `docs/quantitative/P4_003_MARKET_STRUCTURE_SEMANTICS.md`
- `docs/decisions/ADR/ADR-QUANTITATIVE-001.md`
- `src/meylux/specialists/group_b.py`
- `tests/test_p5_005_group_b.py`

No historical artifact listed above has been modified by this assessment.

## 3. Governing Question

The first question is:

> **Is the questioned prerequisite genuinely required for the intended S-12 capability?**

The second question, only after the first is established, is:

> **Why was the required fact surface unavailable or unresolved in the historical acceptance runtime?**

The second question must not be answered by assuming a technical mechanism.

## 4. Requirement Determination

### 4.1 S-12 is a required capability

`TO-P5-005` explicitly includes S-12 — Liquidity within its authorized required outcome.

Its required behavior includes:

- nearest applicable liquidity zones;
- `SWEPT` / `UNSWEPT` state using candles occurring after zone formation;
- explicit `PARTIAL` behavior where depth evidence is unavailable;
- depth-dependent interpretation only when authoritative snapshot depth is present.

The Task Order therefore establishes that liquidity interpretation is not optional enrichment within the P5-005 boundary.

### 4.2 Authoritative P5 fact requirement

The authoritative P5-002 Fact Requirements Matrix records for S-12:

**Required fact family:** liquidity zones / optional depth.

Its governed disposition is tied to the upstream fact-availability boundary rather than to fabrication or an assumed local fallback.

The Phase-5 roadmap independently identifies S-12 as dependent on the Group-B P4 structural event/zone fact surface.

Therefore, an authoritative fact surface capable of establishing the liquidity-zone formation/sweep state is a genuine prerequisite to fully establishing the intended S-12 capability.

### 4.3 Authoritative P4 liquidity semantics

The ratified P4 market-structure semantic authority `DOC-P4-002` defines liquidity pools as structural facts:

- bullish-side pools are formed from repeated confirmed same-side Swing High levels with exact Decimal equality;
- bearish-side pools are formed from repeated confirmed same-side Swing Low levels with exact Decimal equality;
- a pool remains active until a closed candle closes strictly beyond the pool level;
- that event is recorded as a structural pool-sweep/invalidation fact;
- the engine must not manufacture a liquidity pool when required evidence is absent.

This establishes that liquidity-pool formation and sweep are authoritative P4 structural facts rather than a P5 invention.

### 4.4 Critical distinction: required fact family ≠ guaranteed non-empty runtime result

The assessment does **not** conclude that at least one `LIQUIDITY_POOL` record must exist in every runtime snapshot.

A valid market-data snapshot may contain no qualifying repeated swing levels. In that situation, the correct capability behavior may be an evidence-backed empty/no-applicable-zone result rather than a fabricated pool.

Therefore:

> **The prerequisite is authoritative ability to determine and evidence the liquidity-pool formation/sweep fact state, not the artificial existence of at least one liquidity-pool record.**

This distinction is material.

## 5. Historical Runtime Finding

The CONTROL runtime execution recorded:

- snapshot: `b4197da28bfea856fe9817f8bfe0cdf67ac4d85379078783f4a677dbea1d65f8`;
- `as_of = 2026-10-01T18:33:59.999Z`;
- 18 facts;
- 6 canonical candles;
- 12 structural events;
- S-12 first persistence: `inserted=true`;
- S-12 replay: `inserted=false`;
- S-12 read-back: `true`;
- final S-12 runtime status: `INSUFFICIENT_DATA`.

The execution log explicitly records that the governed database contained no `LIQUIDITY_POOL` records and that no synthetic data was introduced.

This evidence is valid and remains unchanged.

## 6. What the Historical Evidence Proves — and Does Not Prove

### Established

The historical runtime proves that:

1. S-12 executed;
2. its specialist output was persisted and read back;
3. replay was idempotent;
4. no `LIQUIDITY_POOL` records were available to that governed snapshot/database boundary;
5. S-12 therefore returned explicit `INSUFFICIENT_DATA`;
6. no synthetic liquidity data or provider expansion was used.

### Not Established

The historical evidence does **not** establish which of the following explains the absence:

1. the canonical candle history genuinely contained no repeated equal confirmed swing levels capable of forming a liquidity pool;
2. the P4 engine correctly determined that no pool formed but the resulting fact surface was not represented in the snapshot in the expected form;
3. the P4 persistence/runtime path failed to expose a qualifying liquidity-pool formation/sweep fact;
4. the P5 snapshot/FRM inclusion boundary omitted an authoritative fact family that existed upstream;
5. another evidence-context or temporal condition prevented authoritative admission.

No one of these causes is selected without additional evidence.

## 7. Assessment Classification

### **Historical Production Classification: D — UNRESOLVED REQUIRED PREREQUISITE**

The authoritative requirements establish that S-12 requires a real, authoritative liquidity-zone/pool fact surface to determine the requested liquidity interpretation.

The historical runtime establishes that this fact surface was not available within the governed snapshot boundary.

The evidence does **not** yet establish whether that absence represents:

- a truthful "no qualifying liquidity pool formed" market condition; or
- an unresolved upstream fact-generation/persistence/snapshot availability condition.

Consequently, the required prerequisite/evidence boundary remains unresolved.

This is sufficient to trigger the ADR-GOVERNANCE-014 resolution obligation, but **not** sufficient to select a technical corrective mechanism.

## 8. Corrective Mechanism — Intentionally Not Predetermined

This assessment does not conclude that resolution requires:

- a new provider;
- a new data source;
- new acquisition;
- a new calculation;
- a new database table;
- a schema modification;
- a contract modification;
- a migration;
- a P4 reopening;
- a P5 implementation change;
- or any other specific mechanism.

The next governed work must first establish the causal boundary from authoritative evidence.

Only after that causal determination may CONTROL define the minimum bounded corrective outcome.

## 9. Required Next Evidence

A future corrective assessment/Task Order, if authorized, must establish at minimum:

1. the exact canonical candle set relevant to the historical S-12 snapshot;
2. whether that evidence contains qualifying repeated same-side confirmed swing levels under `DOC-P4-002`;
3. whether the authoritative P4 engine produced a liquidity-pool formation/sweep fact for that evidence;
4. whether such a fact was persisted through the authoritative P4 boundary;
5. whether it was included or correctly excluded by the P5 Input Snapshot;
6. whether the `INSUFFICIENT_DATA` result represents unavailable required evidence or a legitimate absence of an applicable liquidity zone;
7. the exact ownership boundary of any identified defect;
8. the minimum evidence required to establish the intended S-12 capability.

No corrective implementation should begin before these questions are answered.

## 10. Historical Closure Protection

This assessment does not reopen or alter:

- `STEP-P5-005`;
- `TO-P5-005`;
- `BR-P5-006`;
- `AR-P5-005`;
- the runtime execution log;
- the historical snapshot;
- the historical statuses;
- or the existing Phase-5 closure synchronization.

The historical S-12 `INSUFFICIENT_DATA` result remains the truthful historical runtime result.

The current project checkpoint remains:

**PH-P5 = ACTIVE / AUTHORIZED**  
**STEP-P5-005 = COMPLETE / VERIFIED**  
**TO-P5-005 = VERIFIED / COMPLETE**  
**active_task_order = null**

## 11. Governance Path

The governed relationship is:

`ADR-GOVERNANCE-014`  
→ project-wide no-drop prerequisite rule

`DOC-P5-003`  
→ case-specific retrospective/corrective assessment

Future governed Task Order(s), only if warranted by the assessment  
→ bounded corrective implementation

Producer Build Report / evidence  
→ CONTROL independent verification

CONTROL closure synchronization  
→ only after a legitimate corrective completion boundary.

## 12. Current Verified Conclusion

The historical S-12 liquidity fact/evaluation surface was genuinely relevant to the required capability, and the historical absence of `LIQUIDITY_POOL` records is now causally explained by `AR-P5-006`: **Branch A — no qualifying liquidity pool existed in the authoritative P4 input/output boundary.**

The causal investigation found no P4 production defect, persistence defect, P5 admission defect, provider/data-source deficiency, or other unresolved prerequisite requiring corrective implementation for this historical case.

The historical `INSUFFICIENT_DATA` result remains unchanged and truthful. No liquidity pool is to be fabricated merely to produce a non-empty runtime result.

**Disposition: Causal Branch A — ESTABLISHED.**

**Corrective implementation: NOT AUTHORIZED / NOT REQUIRED BY THIS INVESTIGATION.**

**Historical evidence: PRESERVED.**

**P5-005 reopening: NOT AUTHORIZED.**

## 13. CONTROL Self-Audit / Closure Verification

Under the Project Owner's explicit authorization dated 2026-10-06, CONTROL performed a self-audit of this assessment against `AR-P5-006` and the current authoritative governance state.

The audit found one stale substantive field: the historical production classification remained D after the causal investigation had established Branch A. CONTROL corrected that assessment conclusion without modifying any historical evidence.

Self-audit record: `AR-P5-007`.

**Self-audit result: PASS.**

**Final lifecycle status: CLOSED / VERIFIED.**
