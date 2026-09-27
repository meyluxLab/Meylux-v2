# AR-P2-AUDIT-010 — CONTROL Independent Audit of TO-P2-010

**Project:** MEYLUX V2  
**Role:** CONTROL / REVIEWER — `ROL-V2-001`  
**Phase / Step:** `PH-P2 / STEP-P2-006`  
**Task Order:** `TO-P2-010`  
**Build Report:** `BR-P2-010`  
**Audit Status:** **APPROVED / VERIFIED**  
**Audit Boundary:** Independent repository, implementation, test/CI, architecture, contract, identity, persistence, and governance verification.

## 1. Audit conclusion

CONTROL independently verifies that the authorized `TO-P2-010` corrective implementation satisfies the applicable Task Order acceptance criteria.

Final implementation revision:

`935a7368ceea971a1d9a7b5bfde47f9d30a7b733`

The corrected semantic boundary is:

`MEXC acquisition → raw/acquisition evidence preserved → P3 normalization → unavailable provider finality rejected → no CanonicalCandle → no canonical persistence/downstream closed-candle fact`

The frozen `CanonicalCandle.is_closed: bool` contract remains unchanged.

**Final disposition:**

- `BR-P2-010` → **VERIFIED**
- `TO-P2-010` → **VERIFIED / COMPLETE**
- `AR-P2-AUDIT-010` → **APPROVED / VERIFIED**
- `PH-P2` → historical **CLOSED / VERIFIED**; unchanged
- `STEP-P2-006` → historical **COMPLETE / VERIFIED**; unchanged
- `TO-P2-013` → **PREPARED / NOT ACTIVATED**; unchanged
- no VPS/SentinelX operation performed
- no architecture or canonical-contract change performed

## 2. Evidence independently verified

CONTROL independently verified:

1. `BR-P2-010.md` exists in the repository and records lifecycle `PRODUCED / NOT VERIFIED` pending this audit.
2. Producer final implementation revision `935a7368ceea971a1d9a7b5bfde47f9d30a7b733` exists as a real repository commit.
3. The comparison from the actual pre-implementation governance baseline `2045fac5e496f54229d3bc2de0c44d3b9a067488` to the final implementation revision contains exactly five changed paths:
   - `contracts/normalization.py`
   - `docs/registry/artifacts.yaml`
   - `src/meylux/acquisition/mexc.py`
   - `tests/test_acquisition/test_mexc_adapter.py`
   - `tests/test_contracts/test_p3_005_normalization.py`
4. No migration, database schema, canonical contract, architecture document, identity algorithm, G-4 identity material, or runtime deployment file was changed by the implementation delta.
5. `contracts/normalization.py` now rejects MEXC candle canonicalization with existing `ValidationCode.PROVIDER_FIELD`, field `is_closed`, before `CanonicalCandle` construction.
6. The MEXC REST adapter preserves the raw row and requested interval; it does not manufacture finality.
7. MEXC WebSocket and REST paths are both explicitly tested.
8. Existing `CanonicalCandle.is_closed` remains boolean and the candle contract file is unchanged.
9. Existing downstream P3-008 flow checks normalized eligibility before canonical persistence.
10. Canonical persistence accepts canonical records rather than constructing provider candles and contains no MEXC finality inference.
11. The quantitative worker requires closed canonical candles and does not create them from raw MEXC evidence.
12. Binance production finality code is outside the implementation delta.

## 3. Independent construction-path audit

CONTROL searched the repository for MEXC-originated candle construction and inspected the relevant production boundaries.

### A. Provider normalization

`contracts/normalization.py::_candle` is the provider-to-canonical MEXC candle boundary.

The MEXC branch parses structural/time/OHLCV fields and then raises:

`ValidationCode.PROVIDER_FIELD / field=is_closed`

before reaching the shared `CanonicalCandle(...)` constructor.

Therefore unavailable MEXC provider finality cannot produce a canonical candle through this path.

### B. Runtime canonicalization/persistence

`src/meylux/runtime/p3_008_vertical_slice.py` performs normalization and quality assessment before calling `build_canonical_event` and `CanonicalPersistence.persist`.

When normalization is invalid, the runtime returns before canonical event construction/persistence.

Therefore the corrected MEXC rejection is upstream of canonical persistence.

### C. Canonical persistence

`src/meylux/persistence/canonical.py` persists an already-created `CanonicalRecord`. It does not translate MEXC raw evidence into `CanonicalCandle` and contains no finality inference.

### D. Quantitative worker

`src/meylux/runtime/quant_worker.py` reconstructs already-canonical candle payloads and explicitly requires closed candles. It is not a raw MEXC acquisition-to-canonical path.

### E. Contract constructors

`contracts/canonical/candle.py` is unchanged. No alternate MEXC-specific canonical candle contract or constructor was introduced.

**Independent conclusion:** no alternate production MEXC path was found that can promote an unavailable-finality observation into canonical `is_closed=True`.

## 4. Validation semantics and precedence

The existing validation vocabulary was independently inspected.

`ValidationCode.PROVIDER_FIELD` is an existing governed code and is appropriate for an unavailable provider field/semantic required for canonical finality.

No new validation taxonomy was introduced.

The implementation validates structural/time/OHLCV fields before the explicit MEXC finality rejection. CONTROL verified the corresponding regression test:

- malformed `windowEnd` is classified structurally;
- a structurally valid MEXC candle is classified as unavailable finality;
- result is independent of payload dictionary ordering.

This satisfies deterministic precedence within the authorized correction boundary.

## 5. Anti-inference audit

CONTROL verified that the implementation does not use:

- `windowEnd` as finality;
- REST close-time availability;
- event/create/send time;
- receipt time;
- local clock;
- elapsed age;
- repeated observation;
- next interval;
- OHLC geometry;
- REST/WS agreement;
- synthetic provider finality;
- `False`;
- `None`;
- an UNKNOWN canonical state.

The temporal regression test explicitly changes `windowEnd` values and still obtains the same unavailable-finality rejection.

## 6. Raw evidence and replay

The correction preserves acquisition evidence rather than deleting it.

The MEXC REST row remains retained under the acquisition payload and the requested interval is retained as provider context.

Replay tests establish:

- stable event identity;
- stable canonical acquisition bytes;
- stable normalization result;
- stable rejection issue;
- no canonical value on replay.

No identity algorithm or G-4 identity material changed.

No historical canonical population was rewritten.

## 7. REST / WebSocket coverage

CONTROL independently inspected and verified dedicated tests for:

- MEXC REST historical kline → acquisition succeeds, raw row preserved, normalization rejects unavailable finality;
- MEXC WebSocket kline → acquisition succeeds, normalization rejects unavailable finality;
- malformed structural timestamp versus unavailable finality;
- temporal variation without finality promotion;
- replay/idempotency.

The existing normalization regression suite was updated to reflect the now-correct fail-closed MEXC semantic.

## 8. CI evidence

CONTROL independently fetched the final CI Core workflow run:

- workflow: `CI Core`
- run number: `1397`
- run ID: `36342830440`
- final commit: `935a7368ceea971a1d9a7b5bfde47f9d30a7b733`
- repository-foundation job: `108686134426`
- result: **SUCCESS**

The job steps relevant to the governed regression completed successfully, including compilation, Binance acquisition, P2 acquisition/hardening, P3 quality/persistence-event tests and foundation regression.

The Producer's reported full regression result of **547 tests — OK** is consistent with the final CI run evidence.

The Producer also reported 26 MEXC adapter cases and 27 Binance finality cases in the full suite; no failure is present in the final CI result.

### Docker evidence

No successful Docker Foundation execution on the final implementation revision was found in the evidence delivered for this audit.

CONTROL therefore makes **no Docker-success claim**.

This is not an acceptance failure because `TO-P2-010` requires real applicable test/CI evidence but does not make a final-revision Docker Foundation run an unconditional acceptance criterion, and the final implementation has authoritative successful CI Core evidence.

The intermediate Docker failures remain correctly classified as intermediate-cycle evidence rather than silently converted into success.

## 9. Architecture / contract / persistence audit

CONTROL verified that the implementation delta contains no:

- `CanonicalCandle` contract change;
- architecture invariant change;
- new canonical truth layer;
- migration;
- database schema mutation;
- historical canonical rewrite;
- canonical identity algorithm change;
- G-4 identity change;
- VPS/runtime deployment mutation;
- Trade→Candle reconstruction;
- MEXC trade-sequence reconstruction;
- `TO-P2-013` implementation.

The frozen architecture remains intact.

## 10. Acceptance criteria disposition

| Criterion | Independent disposition |
|---|---|
| Remove MEXC `closed=True` synthesis | **PASS** |
| Exhaustive MEXC canonical construction-path inspection | **PASS** |
| Existing validation vocabulary | **PASS** |
| Deterministic validation precedence | **PASS** |
| Preserve raw/acquisition evidence | **PASS** |
| Reject unavailable finality before canonical candle construction | **PASS** |
| No false/None/time inference | **PASS** |
| REST + WebSocket coverage | **PASS** |
| Malformed/boundary handling | **PASS** |
| Replay/idempotency protection | **PASS** |
| Canonical persistence/downstream protection | **PASS** |
| Binance preservation | **PASS** |
| Identity/serialization/G-4 preservation | **PASS** |
| No silent architecture/contract change | **PASS** |
| Real reproducible CI evidence | **PASS** |
| No unsupported MEXC finality claim | **PASS** |
| Build Report complete for independent audit | **PASS** |

No open correction finding remains within the authorized `TO-P2-010` boundary.

## 11. Governance disposition

The implementation has reached the natural independent-verification boundary.

CONTROL therefore authorizes closure of the **Task Order lifecycle** only:

`TO-P2-010 → BR-P2-010 → AR-P2-AUDIT-010`

This does **not** reopen or alter the historical `PH-P2 / STEP-P2-006` closure.

The separate `TO-P2-013` order-book capability remains exactly:

**PREPARED / NOT ACTIVATED**

and is not affected by this audit.

## 12. Final audit conclusion

**AR-P2-AUDIT-010: APPROVED / VERIFIED**

**TO-P2-010: VERIFIED / COMPLETE**

The known MEXC canonical-finality defect has been technically corrected within the authorized frozen architecture:

> MEXC provider finality remains unavailable; the repository no longer converts that absence into canonical `is_closed=True`.

No unsupported canonical fact was introduced.

No correction cycle is required.

CONTROL now proceeds to the mandatory ADR-GOVERNANCE-012 closure synchronization and final machine read-back.

---
