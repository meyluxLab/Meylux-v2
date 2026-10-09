# AR-P2-AUDIT-018 — Independent Audit of BR-P2-018 / TO-P2-018

**Audit SID:** AR-P2-AUDIT-018  
**Task Order:** TO-P2-018  
**Build Report:** BR-P2-018  
**CONTROL:** ROL-V2-001  
**Producer:** ROL-V2-002  
**Disposition:** REQUEST CHANGES — INVESTIGATION INCOMPLETE  
**Audit date:** 2026-10-09  
**Scope:** Independent audit of the submitted report and current-route evidence; no implementation, provider selection, or runtime authorization.

## 1. Definitive audit conclusion

**BR-P2-018 is not accepted as a complete investigation report in its current form.** The report's overall disposition B may remain the final disposition if the strict qualification criteria remain unmet, but its Binance USDⓈ-M route analysis contains a material evidence omission and must be corrected before CONTROL can conclude whether the route is qualified or which exact semantic gap prevents qualification.

The report states that official USDⓈ-M Funding, OI, and Basis documentation was not successfully retrieved and therefore classifies all three metrics as not established. CONTROL independently retrieved the current official Binance USDⓈ-M Market Data documentation, which explicitly documents all three endpoint families for the required product family and gives BTCUSDT examples:

- Funding: `GET /fapi/v1/fundingRate`, with `symbol`, `fundingRate`, `fundingTime`, and associated `markPrice`. The page shows BTCUSDT and millisecond event time.
- Current OI: `GET /fapi/v1/openInterest`, with `symbol`, `openInterest`, and `time`; the example uses BTCUSDT.
- Historical OI: `GET /futures/data/openInterestHist`, with `symbol`, `sumOpenInterest`, `sumOpenInterestValue`, and a period-end `timestamp`; maximum response limit 500 and only the latest one month is documented.
- Basis: `GET /futures/data/basis`, with `pair=BTCUSDT`, `contractType=PERPETUAL`, `period`, direct `basis` and `basisRate` fields, and a period-start millisecond `timestamp`; maximum response limit 500 and only the latest 30 days is documented.

Primary official source: https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data  
Relevant source sections: Basis; Get Funding Rate History; Open Interest; Open Interest Statistics.

Therefore, the report's assertion that none of the three USDⓈ-M metrics was established in the retrieved official material is factually incomplete. The existence of these documented endpoints does **not**, by itself, prove that the route qualifies under TO-P2-018. Qualification still requires explicit and compatible metric units/semantics, exact instrument/product scope, temporal behavior, provenance, coverage, and truthful existing-contract/persistence representation.

## 2. Findings by acceptance condition

### F-01 — Official USDⓈ-M endpoint coverage omitted

**Finding:** The report did not examine the official USDⓈ-M Market Data reference that documents Funding, current and historical OI, and Basis. This is a material investigation omission, not merely a failed documentation retrieval.  
**Evidence:** The official source above, specifically the documented endpoints and BTCUSDT examples.  
**Disposition:** Correction required. Rebuild the USDⓈ-M candidate row using these endpoint contracts and distinguish endpoint existence from full semantic qualification.

### F-02 — OI unit/semantic qualification remains open

**Finding:** The official API reference labels `openInterest` as open interest and labels historical `sumOpenInterest` / `sumOpenInterestValue` as total open interest / total open-interest value, but the retrieved USDⓈ-M API field descriptions do not explicitly declare the unit for `openInterest` or `sumOpenInterest`. The field's existence must not be mistaken for sufficient unit proof.  
**Disposition:** The Producer must seek an authoritative Binance source defining the relevant USDⓈ-M OI field's unit and exact semantics, or explicitly retain this as the remaining qualification gap with the exact reason it prevents canonical representation. Do not infer units solely from an example value, field name, symbol, or the COIN-M API documentation.

### F-03 — Temporal and coverage constraints need a complete route-level assessment

**Finding:** The official docs distinguish Funding's `fundingTime`, current OI's transaction `time`, historical OI's period-end timestamp, and Basis's period-start timestamp. Historical OI is limited to the latest one month; Basis is limited to the latest 30 days.  
**Disposition:** Correct the matrix to preserve independent event times and explain whether these windows satisfy the actual S-04 analysis/configured history requirements. No single synthetic timestamp may be assigned to metrics with different temporal meanings.

### F-04 — Exact BTCUSDT/SOLUSDT product scope is not fully demonstrated

**Finding:** The official API schema examples establish BTCUSDT route parameters, but the investigation did not perform live symbol discovery (and TO-P2-018 prohibits live API calls). The docs alone do not establish current runtime listing/availability for each exact symbol.  
**Disposition:** Distinguish documented endpoint capability from verified current symbol listing and runtime availability. Identify which facts can be established without live API calls and which require a later separately authorized runtime task. Do not claim SOLUSDT runtime availability from a BTCUSDT example.

### F-05 — Existing-contract compatibility is plausible but not yet sufficient to close the gap

**Finding:** The existing canonical derivatives model contains Decimal fields for funding, OI and basis, while instrument metadata and acquisition/quality evidence can preserve instrument identity, event time, receipt/knowledge time, and provenance. However, generic fields and persistence support do not cure missing provider-field semantics or metric units. The P5 fact matrix also records S-04 persistence as unverified and no dedicated `knowledge_time` column in the canonical derivatives persistence family.  
**Disposition:** The corrected report must map each route observation to its actual acquisition/evidence/persistence representation, show how `knowledge_time <= snapshot.as_of` is enforced without substituting `event_time` or `persisted_at`, and separate data availability from `AVAILABLE_PERSISTED` runtime acceptance.

## 3. Current-route determination

The current route has **not** been shown incapable of satisfying S-04. Official Binance USDⓈ-M documentation now establishes the existence of endpoints for all three required metric families for the BTCUSDT product scope. The remaining questions are semantic and qualification questions—especially OI units, exact SOLUSDT scope, historical coverage, and downstream evidence/persistence compatibility—not evidence that the provider lacks all three metrics.

Consequently, alternatives must not yet be elevated as the preferred resolution path. Under the Owner's directive, alternative routes should be investigated only after the current route has been examined thoroughly and its inability to meet the acceptance conditions is established. COIN-M remains a distinct product family and must not be substituted for USDⓈ-M BTCUSDT merely because its own endpoints are documented.

## 4. Owner hypotheses — considered after current-route findings

- **BTCUSD COIN-M for BTCUSDT USDⓈ-M:** Not an identity-preserving substitution. The contracts differ in product/margin/settlement family and must remain separate instruments. COIN-M observations cannot be silently merged into the USDⓈ-M BTCUSDT fact record.
- **COIN-M as a separate analytical route:** It may be separately assessed only as a distinct product/instrument pathway if the authoritative requirement and Owner-approved scope permit it. Its existence does not resolve the required USDⓈ-M route by substitution.
- **Mappings/conversions:** Only explicit, authoritative, semantically valid mappings may be used. Display-symbol changes are not equivalence proof. No conversion or mixed-product metric aggregation is authorized by this audit.

These hypotheses do not change the primary finding: the report must first correct and complete the official USDⓈ-M route assessment.

## 5. Governance and lifecycle disposition

- PRQ-3 remains a required, unresolved capability; S-04 is not delivered or available.
- TO-P2-018 remains the active Task Order and is **not** VERIFIED, COMPLETE, or CLOSED.
- STEP-P5-007 remains NOT ACTIVATED.
- No provider/product is selected for implementation by this audit.
- No implementation, live API call, VPS/SentinelX operation, migration, deployment, or protected contract/schema/Stable-ID change is authorized here.
- Historical closure artifacts remain unchanged.
- CONTROL requests a Producer correction cycle within the existing investigation-only boundary. The Producer must not self-declare verification or perform closure synchronization.

## 6. Required Producer correction

Revise BR-P2-018 in its own PR branch to:

1. Add the official USDⓈ-M Market Data reference and document the Funding, current OI, historical OI, and Basis endpoint contracts.
2. Correct the inaccurate “all three not established in retrieved official evidence” statement.
3. Resolve the authoritative USDⓈ-M OI unit question or state it as a precise remaining blocker; do not infer or borrow COIN-M semantics.
4. Reassess the 1-month OI and 30-day Basis history limits against S-04's actual analytical/history requirements.
5. Cover BTCUSDT and SOLUSDT separately, distinguishing documented schema capability from current listing/runtime evidence.
6. Reconcile event-time differences, provider instrument identity, receipt/knowledge-time, EvidenceRef eligibility, append-only provenance, and current canonical persistence limitations.
7. Keep alternatives secondary until the current route's insufficiency is demonstrated; then examine materially relevant alternatives as TO-P2-018 requires.
8. Preserve the original report's valid findings on COIN-M identity incompatibility, MEXC's unestablished OI/Basis semantics, no implementation, and no unauthorized runtime activity.
9. Deliver a corrected Build Report and explicitly list any remaining gaps and the exact next evidence needed.

## 7. CONTROL disposition

**REQUEST CHANGES — INVESTIGATION INCOMPLETE.** This is an independent audit finding, not a closure decision. The report's current B disposition is not accepted as a final evidence-backed determination until the material omission and remaining semantic questions are corrected and re-audited.

---END---
