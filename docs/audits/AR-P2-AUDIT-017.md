# AR-P2-AUDIT-017 — Independent Audit of TO-P2-017

**Audit SID:** `AR-P2-AUDIT-017`  
**Task Order:** `TO-P2-017`  
**Build Report:** `BR-P2-017`  
**CONTROL:** `ROL-V2-001`  
**Producer:** `ROL-V2-002`  
**Disposition:** **APPROVED / VERIFIED**  
**Audit boundary:** Independent repository, contract, governance, provider-semantic and evidence audit; no implementation authorization implied.

## 1. Audit conclusion

**BR-P2-017 is APPROVED / VERIFIED.**

The Producer's definitive **PATH A — IMPLEMENTABLE WITHIN EXISTING FROZEN CONTRACT/ARCHITECTURE** is supported by the authoritative repository evidence and the provider-semantic evidence independently checked by CONTROL.

No substantive correction is required.

This approval establishes only that the **PRQ-3 acquisition/change-control assessment** is complete and that the identified minimum future implementation boundary can be pursued without a new canonical contract, Stable ID, truth layer, or architecture invariant solely for representation.

It does **not** establish PRQ-3 delivery, S-04 availability, Futures implementation, runtime verification, or STEP-P5-007 activation.

## 2. Evidence audited

CONTROL independently verified:

- PR #74 and its base/head relationship;
- Producer head `d046432200d4bbe14a45ee40721affccbb38b5bb`;
- complete `BR-P2-017.md` read-back;
- exact one-file PR diff;
- `TO-P2-017` authorization and scope;
- `CURRENT_CHECKPOINT.json`;
- `PH-P5` and Phase-5 PRQ-3 gate;
- `P5_002_FACT_REQUIREMENTS_MATRIX.md`;
- `contracts/acquisition.py`;
- `contracts/quality_evidence.py`;
- `contracts/canonical/derivatives.py`;
- canonical persistence migration `0003`;
- quality-evidence persistence migration `0009`;
- quality-evidence persistence/read-back implementation;
- P4 derivatives semantic contract;
- P5 EvidenceRef and no-lookahead requirements;
- PRQ-4 / P3-009 knowledge-time semantics;
- no-implementation/no-runtime boundary.

The PR was merged after audit at:

`1f60113f8ade41b86b35e42d09c8611de3745707`.

## 3. PATH A verification

The conclusion is technically sound for the stated boundary.

### Acquisition layer

`AcquisitionEnvelope` already expresses:

- provider identity;
- canonical/provider instrument identity;
- provenance;
- `EventType.DERIVATIVES`;
- event time;
- receipt time;
- acquisition state;
- source sequence;
- provider errors/capability;
- deterministic identity/deduplication.

No new transport contract is necessary merely to admit a Futures derivatives adapter.

### P3 evidence layer

Persisted quality evidence already provides:

- source record identity;
- provider/adapter identity;
- canonical/provider instrument identity;
- event time;
- received time;
- authoritative `knowledge_time = received_at`;
- acquisition/quality/lifecycle state;
- provenance/lineage;
- timeframe/venue;
- deterministic evidence identity;
- append-only persistence;
- EvidenceRef resolution.

This is important because `canonical_derivatives` itself does not contain a dedicated `knowledge_time` column. CONTROL verified that this is not a contradiction with PATH A: P5's required knowledge boundary is supplied through the authoritative P3 quality-evidence source, not fabricated from canonical `persisted_at`.

### Canonical layer

`CTR-V2-CANONICAL-DERIVATIVES` already represents funding, OI, derived ordered changes/velocity, basis and provenance.

Missing optional fields remain `None`; no fabrication is required.

### Persistence layer

Existing `meylux.canonical_derivatives` and `meylux.quality_evidence` persistence provide the required append-only source/evidence chain. No new derivatives migration is required merely to represent the capability.

### P5 boundary

The roadmap explicitly assigns PRQ-3 to P2 and gates S-04 on it. The Producer correctly did not activate STEP-P5-007 and did not claim S-04 availability.

## 4. Provider evidence audit

CONTROL independently cross-checked the Producer's provider claims against official provider documentation.

### Binance

Official Binance COIN-M documentation confirms a direct Basis endpoint under `/futures/data/basis`, with basis, basis rate, futures price, index price and timestamp fields; the endpoint is explicitly within the COIN-M Futures API. It therefore supports the Producer's product-specific basis qualification and does not justify generalizing the route to all Binance Futures products. citeturn1search0

The same official documentation also exposes COIN-M Futures open-interest statistics and index/mark-price/funding fields. citeturn1search0

### MEXC

Current official MEXC material confirms Futures funding and index/fair-price semantics, including the relationship between index price, funding and basis-derived fair-price calculation. citeturn0search5turn0search10

CONTROL did **not** find sufficient official public Market-API evidence in the inspected material to elevate MEXC OI acquisition to an established Meylux provider capability. The Producer's negative disposition is therefore appropriately conservative.

Crucially, the MEXC fair-price documentation itself describes basis as part of the fair-price calculation; this does not by itself authorize Meylux to manufacture a canonical basis fact. The Producer correctly requires an explicit provider-authoritative route or a separately governed deterministic formula before admission to canonical truth. citeturn0search0turn0search5

## 5. Critical semantic finding independently confirmed

The principal semantic issue audited was the relationship between:

`event_time`  
`received_at`  
`knowledge_time`  
canonical `persisted_at`.

CONTROL confirms:

- `event_time` remains provider observation time;
- `received_at` remains acquisition receipt time;
- P3 quality evidence defines `knowledge_time = received_at`;
- canonical persistence time is not promoted to knowledge time;
- P5 requires `knowledge_time <= snapshot.as_of`;
- absence of a legitimate knowledge boundary must remain non-eligible.

Therefore the Producer did not weaken the P5 temporal boundary merely because canonical derivatives lacks a direct `knowledge_time` column.

## 6. Scope / architecture / authority

PASS.

No evidence of:

- architecture redesign;
- contract weakening;
- Stable-ID mutation;
- schema/migration change;
- new truth layer;
- P5 implementation;
- Futures implementation;
- runtime activation;
- VPS/SentinelX mutation;
- historical closure rewriting;
- cross-provider substitution;
- fabricated market evidence.

The proposed future implementation remains correctly bounded:

**P2 Futures acquisition → existing AcquisitionEnvelope → P3 quality evidence → existing CanonicalDerivatives → existing persistence → P5 S-04.**

Provider/product selection remains a prerequisite of the future implementation boundary rather than an implicit assumption.

## 7. R1–R7 audit

| Rule | Result | CONTROL finding |
|---|---|---|
| R1 Continuation | PASS | Producer completed the authorized investigation to the independent-audit boundary. |
| R2 Same-response handoff | PASS | BR-P2-017 returned the complete evidence package to CONTROL. |
| R3 Artifact/evidence integrity | PASS | Complete report read-back and direct repository evidence used; no decision from truncated excerpts. |
| R4 No-Drop | PASS | PRQ-3 remains explicit; unresolved provider/product limitations were not silently converted into capability. |
| R5 VPS/runtime | PASS | No unauthorized runtime/VPS activity claimed or performed. |
| R6 Architecture/scope/role | PASS | No protected architecture/contract/role boundary was crossed. |
| R7 Quality/edge/regression/closure | PASS | Edge, contradiction, temporal, identity, replay, persistence and unavailable semantics were explicitly covered; closure remains CONTROL-owned. |

## 8. Required disposition

**APPROVED / VERIFIED**

No Producer correction cycle is open.

The next legitimate boundary is a **new separately governed implementation Task Order** only after the concrete provider/product route is selected and its funding/OI/basis semantics are pinned.

That future Task Order is not created by this audit.

## 9. Closure synchronization

CONTROL now owns the closure synchronization for `TO-P2-017` under ADR-GOVERNANCE-012.

The following are synchronized in this closure cycle:

- `TO-P2-017` → `VERIFIED / COMPLETE`;
- `BR-P2-017` → `VERIFIED`;
- `AR-P2-AUDIT-017` → `APPROVED / VERIFIED`;
- `active_task_order` → `null`;
- PRQ-3 remains a subsequent governed dependency;
- `STEP-P5-007` remains unactivated;
- `STEP-P5-006` remains historical `COMPLETE / VERIFIED`;
- `TO-P2-013` remains historical `VERIFIED / COMPLETE`;
- no historical closure chain is reopened.

No Producer closure synchronization was performed.

**FINAL AUDIT DISPOSITION: APPROVED / VERIFIED**

---END---
