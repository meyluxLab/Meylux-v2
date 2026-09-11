# AR-P2-AUDIT-003 — CONTROL Independent Audit — TO-P2-003

**Phase:** `PH-P2`
**Step:** `STEP-P2-003`
**Task Order:** `TO-P2-003`
**Auditor:** `ROL-V2-001 — CONTROL / REVIEWER`
**Status:** `CORRECTION REQUIRED / VERIFICATION BLOCKED`
**Verification date:** `2026-09-11`

## 1. Audit Scope

CONTROL independently reviewed the authoritative Repository PR #14, Producer Build Report `BR-P2-003`, MEXC adapter implementation, MEXC adapter tests, and available CI execution evidence against:

- `PH-P2`;
- `TO-P2-003`;
- `CMP-P2-001` — Provider-Neutral Acquisition Boundary;
- `CTR-P2-001` — AcquisitionEnvelope Provider-Neutral Acquisition Contract;
- `GOV-BOUNDARY-001`;
- previously verified Phase 2 acquisition baseline.

## 2. Execution Evidence

The claimed CI execution evidence is real and independently discoverable for implementation commit `849be42d60e422a27e861b337ca3c103b2feedd9`.

- Workflow: `CI Core`
- Run #209: `34624254253` — `SUCCESS`
- Run #210: `34624278495` — `SUCCESS`
- Required compile/test commands completed successfully in the reported repository-foundation validation boundary.

This establishes compilation/test execution evidence for the tested tree. It does not by itself establish live compatibility with the current MEXC WebSocket service.

## 3. Scope / Contract / Isolation Disposition

The submitted implementation is materially within the authorized P2-003 scope. No modification of `CTR-P2-001` or `CMP-P2-001` was identified in the PR diff. The MEXC adapter remains provider-isolated, public-market-data-only, and does not introduce trading/account/capital behavior or later Phase 2 work.

**Disposition: ACCEPTED subject to the WebSocket correctness blocker below.**

## 4. Material Finding — Current MEXC WebSocket Protocol Mismatch

The implementation's public WebSocket path is not compatible with the current MEXC Spot V3 WebSocket service.

The authoritative MEXC Spot V3 API documentation states that the current WebSocket push uses Protocol Buffers and documents `.pb` channels, including examples such as:

- `spot@public.aggre.deals.v3.api.pb@100ms@BTCUSDT`
- `spot@public.kline.v3.api.pb@BTCUSDT@Min15`
- `spot@public.limit.depth.v3.api.pb@BTCUSDT@5`

The same documentation describes the current WebSocket push as protobuf and requires protobuf deserialization. MEXC's March 4, 2025 service-replacement announcement states that the upgraded WebSocket access uses Protocol Buffers and that the legacy daily URL `wss://wbs.mexc.com/ws` was discontinued for Open API users on August 4, 2025.

The submitted adapter instead constructs non-`.pb` JSON subscription channels and parses the legacy JSON message representation. The submitted tests reproduce those same non-`.pb` JSON assumptions. Consequently, the green CI result validates the local implementation against its own legacy protocol fixtures, but does not establish compatibility with the current MEXC public WebSocket service.

This is a material correctness defect because live WebSocket acquisition is explicitly within the authorized P2-003 capability and is part of the provider adapter's required acquisition behavior.

**Finding disposition: BLOCKING — STOP THAT PART.**

## 5. Required Correction Boundary

The Producer must correct the MEXC WebSocket portion only, preserving the existing architecture and contracts.

Required:

1. Implement the current documented public MEXC WebSocket protocol, including protobuf transport/deserialization and current `.pb` channel forms required for the authorized trade/depth/kline capabilities.
2. Update deterministic local tests so they exercise the current wire/protocol representation rather than the obsolete JSON assumptions.
3. Preserve bounded reconnect behavior and canonical `AcquisitionState` / `ProviderError` failure mapping.
4. Preserve provider-neutral envelope identity, provenance, timestamps, sequencing, and deterministic serialization semantics.
5. Update `BR-P2-003` with the corrected scope and actual CI evidence.

Not authorized:

- changes to `CMP-P2-001` or `CTR-P2-001`;
- new competing Stable IDs;
- credentials/private API behavior;
- trading/account/capital behavior;
- `STEP-P2-004` or later Steps;
- V1 activity;
- production deployment.

## 6. Verification Decision

CONTROL cannot verify `TO-P2-003` / `STEP-P2-003` in its current state.

The REST/bootstrap portion and repository execution evidence are not being rejected merely because live external probing was unavailable. The blocker is specifically the current MEXC WebSocket protocol incompatibility.

**CONTROL DECISION: CORRECTION REQUIRED / VERIFICATION BLOCKED.**

## 7. Governed State

- `TO-P2-003` → `AUTHORIZED / ACTIVE` — remains active; not verified.
- `STEP-P2-003` → `AUTHORIZED / ACTIVE` — remains active; not verified.
- `BR-P2-003` → `PRODUCER EVIDENCE / PENDING CORRECTION AND CONTROL VERIFICATION`.
- `AR-P2-AUDIT-003` → `CORRECTION REQUIRED / VERIFICATION BLOCKED`.
- `PH-P2` → `ACTIVE / AUTHORIZED`.

No Phase 2 progression to `STEP-P2-004` is authorized by this audit.

## 8. External Evidence Basis

Current MEXC official API documentation was consulted for the protocol assessment. MEXC's official March 4, 2025 WebSocket service replacement announcement was also consulted. External documentation is used here as current protocol evidence, not as runtime execution evidence.
