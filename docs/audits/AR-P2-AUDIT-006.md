# AR-P2-AUDIT-006 — CONTROL Independent Audit of TO-P2-006 Producer Evidence

**Audit SID:** `AR-P2-AUDIT-006`
**Phase:** `PH-P2`
**Step:** `STEP-P2-006`
**Task Order audited:** `TO-P2-006`
**Issuer:** `ROL-V2-001` CONTROL / REVIEWER
**Producer:** `ROL-V2-002` PRODUCER / ARCHITECT-BUILDER
**Audit status:** `APPROVED WITH MATERIAL FINDING / CORRECTION AUTHORIZED`

## 1. Audit Objective

Independently assess the Producer completion report and evidence for `TO-P2-006 / STEP-P2-006`, determine whether the reported MEXC live WebSocket defect is material and correctly localized, determine the current verification state, and authorize the minimum governed next action required to complete P2-006 without architectural drift.

## 2. Audited Repository State

Producer verification PR: `#17`

Producer reported final PR HEAD: `258f2bae4eae5582fa994dffb2a8817fc004f6f4`

PR state at audit: `OPEN / UNMERGED`

Producer evidence branch: `feat/p2-006-e2e-verification`

Verification branch base: `952f73ba71cf154cb427fdd954597dfce2dbd4f2`

The PR contains the P2-006 evidence/build-report and traceability changes. The Producer did not merge the PR and did not claim Phase 2 closure.

## 3. Evidence Accepted

CONTROL accepts the Producer's evidence as sufficient to establish, subject to the stated boundaries:

- actual Binance REST acquisition;
- actual Binance live WebSocket acquisition;
- actual MEXC REST acquisition;
- receipt of an actual MEXC protobuf market-data frame from the live provider;
- successful parsing of that actual protobuf frame by the existing parser;
- provider-isolation behavior through the collector boundary;
- bounded raw/staging persistence and read-back;
- bounded Redis queue transport, duplicate detection, ACK, and backpressure;
- observed structured acquisition/queue telemetry;
- bounded runtime cleanup;
- repository regression evidence.

The reported repository regression result of `159 tests` / `OK` is accepted as regression evidence for the tested repository state, not as a substitute for live-provider evidence.

## 4. Material Finding Accepted

CONTROL accepts `D-P2-006-001 — MEXC Live WebSocket Subscription-Acknowledgement Handling` as a material implementation defect affecting the Phase 2 live acquisition boundary.

The evidence establishes a concrete protocol sequence: the MEXC server first returns a JSON subscription acknowledgement/control response, followed by protobuf market-data bytes. The existing stream loop passes the acknowledgement into the market-data parser, which rejects it as `MEXC_INVALID_STREAM_PAYLOAD`, preventing the normal stream loop from consuming the subsequent protobuf frame.

The separate successful parse of the actual subsequent protobuf bytes materially supports the Producer's localization of the defect to acknowledgement/control-message handling rather than to the protobuf parser itself.

## 5. Current Verification Determination

`STEP-P2-006` is **NOT VERIFIED / NOT COMPLETE**.

`PH-P2` remains **ACTIVE / NOT CLOSED**.

`TO-P2-006` remains **EXECUTED / UNVERIFIED** from the Producer evidence perspective.

Phase 2 closure cannot be granted because the required MEXC live WebSocket end-to-end path is not currently proven through the governed adapter and collector boundary.

## 6. Governance Determination on OQ-P2-006-001

`OQ-P2-006-001` is resolved by this audit as follows:

**CONTROL AUTHORIZES the minimum correction described in TO-P2-007.**

The Producer is authorized to recognize/ignore the valid MEXC subscription acknowledgement/control response, continue the existing stream loop, and allow the subsequent protobuf market-data frame to flow through the existing parser and provider-neutral acquisition boundary.

This authorization does not authorize a protocol redesign, parser replacement, contract change, architecture change, or broader provider refactor.

## 7. Required Next Action

`TO-P2-007` is issued and **AUTHORIZED TO EXECUTE**.

It is bound to `STEP-P2-006` and exists solely to correct `D-P2-006-001` and perform the required post-correction re-verification.

The Producer may continue PR `#17` for traceability, but must explicitly report all implementation changes and post-correction evidence. PR `#17` must remain unmerged until CONTROL audits the corrected evidence.

## 8. Acceptance Criteria for Closure Path

CONTROL will consider the finding closure path satisfied only when actual evidence demonstrates, on the corrected implementation state:

1. the real MEXC subscription acknowledgement does not terminate the stream;
2. the subsequent real protobuf market-data frame is consumed by the normal `MEXCAdapter.stream()` path;
3. the resulting event is converted into the governed provider-neutral acquisition representation;
4. malformed/non-market-data payload validation remains intact;
5. targeted MEXC tests pass;
6. full repository regression passes;
7. applicable dual-provider live-stream collector evidence is obtained where the authorized environment permits;
8. bounded runtime cleanup is confirmed;
9. no architecture, contract, Stable ID, Phase 3/4, production, V1, or trading scope was introduced.

## 9. Explicit Non-Closure

This audit does **not** approve Phase 2 closure.

This audit does **not** mark `STEP-P2-006` VERIFIED / COMPLETE.

This audit does **not** authorize Phase 3 or Phase 4.

This audit does **not** authorize production deployment or any trading/account/capital functionality.

## 10. Governance Outcome

`AR-P2-AUDIT-006 → APPROVED WITH MATERIAL FINDING / CORRECTION AUTHORIZED`

`D-P2-006-001 → ACCEPTED / OPEN FOR CORRECTION`

`OQ-P2-006-001 → RESOLVED BY CONTROL AUTHORIZATION`

`TO-P2-007 → AUTHORIZED TO EXECUTE`

`STEP-P2-006 → ACTIVE / UNVERIFIED`

`PH-P2 → ACTIVE / NOT CLOSED`

The next governed transition is:

`TO-P2-007 execution → Producer correction/re-verification evidence → CONTROL audit → P2-006 closure decision`
