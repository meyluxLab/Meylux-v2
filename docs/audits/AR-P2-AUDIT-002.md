# AR-P2-AUDIT-002 — CONTROL Independent Audit — TO-P2-002

**Phase:** `PH-P2`
**Step:** `STEP-P2-002`
**Task Order:** `TO-P2-002`
**Auditor:** `ROL-V2-001 — CONTROL / REVIEWER`
**Status:** `CORRECTION REQUIRED / NOT VERIFIED`
**Verification date:** `2026-09-11`

## 1. Audit Scope

CONTROL independently reviewed the authoritative Repository implementation and Producer Build Report for `TO-P2-002` / `STEP-P2-002` against:

- `PH-P2`;
- `TO-P2-002`;
- `CMP-P2-001` — Provider-Neutral Acquisition Boundary;
- `CTR-P2-001` — AcquisitionEnvelope Provider-Neutral Acquisition Contract;
- `GOV-BOUNDARY-001`;
- the previously verified `AR-P2-AUDIT-001` baseline;
- the Producer evidence recorded in `BR-P2-002`.

The audit is based on direct Repository inspection. The Producer's reported external Binance transport probes are treated as Producer execution evidence and are not converted into independent CONTROL execution evidence.

## 2. Current Producer Disposition

The Producer correctly reports:

`IMPLEMENTED / TESTED / UNVERIFIED`

The Build Report also correctly states that the authoritative repository unit tests were not executed during the Producer cycle and that the stale VPS checkout prevented a truthful repository-suite execution claim.

CONTROL accepts that evidence boundary. No repository test pass count or CI success is claimed by this audit.

## 3. Findings

### F1 — Bounded WebSocket reconnect is not actually bounded across clean disconnects

**Classification: BLOCKING / CORRECTION REQUIRED**

The implementation documents `max_reconnects` as a hard upper bound for one `stream()` invocation. However, the implementation increments `reconnects` only inside the exception path. A normal WebSocket context exit reaches the `binance.stream.disconnected` telemetry call and then immediately enters the outer `while True` again without incrementing the reconnect counter.

Therefore a clean provider-side disconnect can produce an unlimited reconnect cycle within a single `stream()` invocation, despite the documented `max_reconnects` contract.

This is a direct correctness failure against the Task Order requirement for bounded reconnect behavior and is especially material because Binance documents that a market-stream connection is valid for 24 hours and should be expected to disconnect at that boundary. citeturn0search0

Required correction:

- make the reconnect accounting cover both exceptional disconnects and normal/clean connection termination;
- ensure the configured bound is a true hard upper bound for the entire invocation;
- ensure bounded delay/telemetry remain deterministic and observable;
- add a regression test that simulates clean connection termination repeatedly and proves the configured bound is enforced.

Do not redesign the provider-neutral contract to solve this.

### F2 — Provider failure/degradation is not mapped into the canonical acquisition failure semantics

**Classification: BLOCKING / CORRECTION REQUIRED**

`CTR-P2-001` explicitly defines canonical acquisition failure states and a `ProviderError` structure. The current Binance implementation imports `ProviderError` but does not construct or emit a canonical failure envelope. REST transport/HTTP/JSON failures and exhausted WebSocket reconnect failures are instead surfaced as `BinanceTransportError` exceptions.

This leaves the adapter without the required provider-specific-to-canonical failure/degradation mapping required by `TO-P2-002`, while the canonical contract already provides the necessary states (`DEGRADED`, `UNAVAILABLE`, `DISCONNECTED`, `RATE_LIMITED`, etc.) and requires `provider_error` for those states. fileciteturn178file0L2-L2

Required correction:

- map applicable Binance provider failure/degradation conditions into the existing `AcquisitionEnvelope` failure semantics and `ProviderError` structure;
- preserve exception behavior only where it is appropriate as an internal/transport mechanism, without allowing provider-specific exceptions to be the sole externally visible failure semantics where a canonical acquisition state is required;
- distinguish at minimum rate-limit, unavailable/transport, disconnected/reconnect-exhausted, and malformed/invalid provider payload conditions where the existing contract supports them;
- add deterministic tests for the mapping and required `provider_error` presence.

No new canonical enum/state/contract is authorized by this finding. Use the existing P2-001 contract.

### F3 — Producer self-tests are incomplete for the authorized acceptance boundary

**Classification: BLOCKING FOR VERIFICATION / CORRECTION REQUIRED**

The repository test file exists and provides useful coverage, but the Producer explicitly did not execute it against the authoritative repository checkout. Therefore CONTROL cannot verify the implementation through the required repository test evidence.

In addition, inspection shows that the current test file does not adequately cover the two material findings above, including clean-disconnect reconnect bounding and canonical provider-error/failure-state mapping. Coverage also remains incomplete for several implemented stream mappings and malformed/degraded cases required by the Task Order.

Required correction/validation:

- add the regression tests required by F1 and F2;
- execute the authoritative repository test suite relevant to the changed acquisition contracts/adapter from a checkout that contains the authoritative current implementation;
- report exact commands and actual results;
- execute compilation/static validation for the changed code;
- keep external-network probes explicitly separate from local deterministic test evidence.

The stale VPS checkout limitation is accepted as an evidence fact; it is not itself a reason to fabricate repository test results or to modify credentials/governance to bypass the limitation.

## 4. Non-Findings / Accepted Matters

The following were inspected and are accepted as non-blocking for this audit:

- Binance-specific transport and wire parsing remain inside the provider adapter implementation. fileciteturn176file0L2-L2
- The existing `AcquisitionEnvelope` is reused rather than replaced by a competing canonical envelope. fileciteturn178file0L2-L2
- No MEXC implementation was introduced.
- No trading, account, leverage, capital, withdrawal, or custody behavior was introduced.
- No Phase 3 validation/normalization or Phase 4 quantitative computation was introduced.
- REST retry attempts are bounded by the configured `RetryPolicy`.
- The Producer correctly separated external-network probes from repository unit-test evidence in `BR-P2-002`. fileciteturn182file0L2-L2
- The current Phase 2 state correctly keeps `STEP-P2-003` inactive. fileciteturn181file0L2-L2

## 5. Governance / Scope Decision

No new architecture decision is required to resolve F1, F2, or F3.

The corrections must remain inside `TO-P2-002` and must use the already-established provider-neutral boundary and canonical acquisition contract. No redesign, new Stable ID, MEXC activation, production deployment, or future-step implementation is authorized by this audit.

`STEP-P2-003` remains `DEFINED / INACTIVE / NOT AUTHORIZED` until `TO-P2-002` is independently verified and the normal governed progression occurs.

## 6. Final Audit Decision

The implementation is **not independently verified** at this time.

Current governed state:

- `TO-P2-002` → **CORRECTION REQUIRED / ACTIVE**
- `STEP-P2-002` → **ACTIVE / CORRECTION REQUIRED**
- `BR-P2-002` → **PRODUCER EVIDENCE / VALIDATION INCOMPLETE / UNVERIFIED**
- `AR-P2-AUDIT-002` → **CORRECTION REQUIRED / NOT VERIFIED**
- `PH-P2` → **ACTIVE / AUTHORIZED**
- `STEP-P2-003` → **DEFINED / INACTIVE / NOT AUTHORIZED**

No closure, verification, or progression to `STEP-P2-003` is authorized by this audit.

## 7. Correction Handoff

The Producer is directed to perform only the bounded corrections identified in F1–F3 under the existing `TO-P2-002` authority and then return an updated Producer Completion Report / Build Report evidence package to CONTROL.

The correction cycle does not require new Owner authorization because it remains within the already-authorized Task Order boundary and standing continuation authority.

CONTROL will re-audit the corrected implementation and, if all material findings are resolved with actual evidence, may advance the Step to independent verification and normal Phase 2 progression.
