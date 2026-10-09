# AR-P2-AUDIT-019 — Independent Re-Audit of Corrected BR-P2-018 / TO-P2-018

**Audit SID:** AR-P2-AUDIT-019  
**Task Order:** TO-P2-018  
**Build Report:** BR-P2-018  
**CONTROL:** ROL-V2-001  
**Producer:** ROL-V2-002  
**Disposition:** REQUEST CHANGES — INVESTIGATION INCOMPLETE  
**Audit date:** 2026-10-09  
**Scope:** Independent re-audit of corrected report at PR #75 and existing repository evidence; no implementation, provider selection, or runtime authorization.

## 1. Definitive conclusion

The corrected report resolves the material omission recorded in AR-P2-AUDIT-018: it now identifies the official Binance USDⓈ-M endpoint/field contracts for Funding, current and historical OI, and direct Basis, and it correctly retains the USDⓈ-M OI unit/quantity-semantics gap. The COIN-M identity boundary, MEXC gaps, and distinct timestamp meanings are also preserved.

**BR-P2-018 is not yet accepted.** Two substantive corrections remain:

1. The report repeatedly treats absent current listing/runtime verification as part of the route-qualification failure, although TO-P2-018 expressly authorizes repository and public-documentation investigation only and prohibits live provider API calls. Runtime verification must remain a clearly stated non-claim and later-stage evidence requirement, not be conflated with the documentation-level qualification criteria of this Task Order. The BTCUSDT example establishes documented route shape; it does not establish live availability. SOLUSDT remains less specifically evidenced because only generic parameters are shown.
2. The report states that `knowledge_time <= snapshot.as_of` must be enforced, but does not demonstrate the exact existing repository path that enforces that predicate for S-04 EvidenceRef eligibility or show the actual join/read-back relationship between the canonical derivatives observation and its authoritative quality-evidence record. The current checkpoint separately records `available_persisted_claim: NONE` and states that authoritative `knowledge_time` is not present in the inspected P4 persistence families. The report must distinguish contract-level representability from implemented enforcement and from runtime-verified `AVAILABLE_PERSISTED` status.

The primary disposition **B — NO QUALIFIED ROUTE ESTABLISHED** remains defensible on the unresolved USDⓈ-M OI unit semantics alone, alongside the incomplete exact SOLUSDT evidence and the unqualified MEXC routes. This audit does not require live calls or implementation and does not authorize them.

## 2. Findings

### F-01 — Documentation qualification and runtime verification are conflated

**Evidence:** TO-P2-018 §§4, 6, 8 and 9 authorize exact public-documentation/repository evidence assessment only and explicitly prohibit live provider API calls. The corrected report's Executive Determination, Candidate A status, coverage summary, Gap G1b, Gap G4 and §9 nevertheless make missing current listing/runtime verification part of the route's not-qualified rationale.

**Assessment:** It is correct not to claim a current listing, live response, operational availability, or production freshness. It is not correct to treat prohibited runtime evidence as if it were a missing item that this documentation-only investigation was required to obtain before classifying the documented route. Separate the questions:
- documentation-level endpoint/product capability and semantic qualification within TO-P2-018;
- current listing and live/runtime availability, which remain explicitly UNVERIFIED and require a separately authorized later boundary if needed.

For BTCUSDT, retain the precise limit that official examples establish the documented route shape, not a current runtime claim. For SOLUSDT, retain the gap that generic parameters and BTCUSDT examples do not prove exact SOLUSDT product-specific documentation or listing. Do not generalize across instruments.

**Required correction:** Rewrite the overall rationale and candidate summary so the B disposition is grounded in actual documentation/semantic/representation gaps within this investigation. Keep listing/runtime evidence as a non-claim and future validation requirement, not as a requirement that silently expands TO-P2-018.

### F-02 — EvidenceRef / knowledge-time / persistence enforcement is asserted, not demonstrated

**Evidence:** BR-P2-018 §5.3 says the route “must” require `knowledge_time <= snapshot.as_of`, and §6 describes AcquisitionEnvelope, QualityEvidenceRecord, and append-only canonical/quality-evidence persistence. It does not identify the exact current S-04 EvidenceRef construction/filter/read-back code path that applies the predicate, how a canonical derivatives record is linked to the matching quality-evidence row, or what happens when the evidence row is absent, late-arriving, contradictory, or not persisted. The current `CURRENT_CHECKPOINT.json` records `available_persisted_claim: NONE` and the absence of authoritative `knowledge_time` in the inspected P4 persistence families.

**Assessment:** A contract field and a stated rule do not prove the rule is implemented or that a persisted derivatives fact is eligible for an authoritative snapshot. The report currently moves from “the contracts can preserve the fields” to a broad compatibility conclusion without showing the required enforcement chain. It must not imply that S-04 is currently `AVAILABLE_PERSISTED`; it must also not infer a protected-contract conflict solely from this evidence gap.

**Required correction:** Within repository-inspection scope, cite exact source paths/functions and actual behavior for:
1. canonical derivatives persistence and read-back;
2. quality-evidence persistence and retrieval;
3. canonical observation ↔ quality-evidence/provenance linkage;
4. EvidenceRef eligibility and the exact `knowledge_time <= snapshot.as_of` filter;
5. absent/late/duplicate/contradictory evidence behavior; and
6. whether the current S-04 path can enforce these rules or whether the evidence is only contract-level design.

If no enforcing path exists or it cannot be established from the repository, state that precisely as an implementation/evidence-compatibility gap, list the evidence needed to resolve it, preserve `AVAILABLE_PERSISTED = NONE`, and do not propose or implement a fix under this Task Order.

### F-03 — Minor editorial defect

BR-P2-018 §5.3 contains the malformed phrase `event_time and received_at) independently`. Correct the parenthesis during the same report revision.

## 3. Findings accepted from the previous audit

The following corrections are accepted as present in the revised report:
- Official Binance USDⓈ-M Funding, current OI, historical OI, and direct Basis endpoint/field capability is documented, with direct official source URL and BTCUSDT examples.
- USDⓈ-M current `openInterest`, historical `sumOpenInterest`, and `sumOpenInterestValue` unit/quantity semantics remain explicitly unresolved; COIN-M units are not borrowed.
- Funding event time, current OI transaction time, historical OI period-end time, and Basis period-start time are kept distinct.
- The latest-one-month OI history and latest-30-days Basis history are assessed against the stated current/adjacent-prior S-04 analyses without asserting gap-free coverage or unlimited history.
- BTCUSDT and SOLUSDT are treated separately; COIN-M BTCUSD is not treated as an identity-preserving substitute for BTCUSDT USDⓈ-M/Spot.
- MEXC `holdVol` is not silently promoted to canonical OI, and fair/index price is not substituted for direct Basis.
- No implementation, live provider API call, provider/product selection, VPS/SentinelX operation, protected contract/schema change, or STEP-P5-007 activation is claimed.

## 4. Required Producer correction cycle

Revise BR-P2-018 on the existing PR #75 branch, within TO-P2-018's investigation-only boundary, to:
1. Correct F-01 by separating documentation-level qualification from current listing/runtime verification; retain the latter as explicitly unverified and outside this Task Order.
2. Correct F-02 with exact repository path/function evidence for the EvidenceRef, knowledge-time, provenance, and persistence/read-back chain, or state the precise unestablished enforcement gap without claiming implementation.
3. Correct the editorial defect in F-03.
4. Preserve the defensible B disposition and all valid corrections accepted in §3.
5. Do not run live APIs, implement code, select a provider/product, change protected contracts/schemas, perform VPS/SentinelX/runtime actions, activate STEP-P5-007, or declare this Task Order complete.

CONTROL will independently re-audit the corrected report. Producer must not self-declare verification or perform closure synchronization.

## 5. Governance state

- PRQ-3 remains a required unresolved capability; S-04 is not established as `AVAILABLE_PERSISTED`.
- TO-P2-018 remains active and investigation-only; it is not VERIFIED / COMPLETE / CLOSED.
- STEP-P5-007 remains NOT ACTIVATED.
- No provider/product is selected for implementation.
- Historical PH-P2 / STEP-P2-006 and STEP-P5-006 closure records remain preserved.
- This audit is a correction-cycle disposition, not a closure decision.

---

## FORMAL ENGLISH MESSAGE READY TO SEND — PRODUCER

**TO:** PRODUCER / ARCHITECT-BUILDER — ROL-V2-002  
**FROM:** CONTROL / REVIEWER — ROL-V2-001  
**SUBJECT:** AR-P2-AUDIT-019 — Further Corrections Required to BR-P2-018

Producer,

Thank you for correcting the principal USDⓈ-M documentation omission. The revised report now records the official Funding, current/historical OI, and direct Basis endpoint contracts and preserves the unresolved OI unit question. The BTCUSDT/SOLUSDT distinction, timestamp semantics, history-window analysis, and COIN-M identity boundary are also materially improved.

**CONTROL disposition: REQUEST CHANGES — INVESTIGATION INCOMPLETE.**

Two issues remain. First, do not treat absence of current listing/runtime verification as a qualification failure that this documentation-only Task Order required you to close. Keep runtime/listing as an explicit non-claim and later validation requirement; ground the present B disposition in the unresolved documentary/semantic/representation gaps. Second, provide exact repository evidence for the existing canonical derivatives and quality-evidence persistence/read-back linkage and the actual S-04 EvidenceRef enforcement of `knowledge_time <= snapshot.as_of`. A contract field or a statement of the required rule does not establish that the current path enforces it. If no enforcing path is present or verifiable, state that gap accurately and preserve `AVAILABLE_PERSISTED = NONE`; do not implement a fix within this Task Order. Please also correct the small editorial defect noted in F-03.

Continue only within TO-P2-018: no implementation, live provider APIs, provider selection, protected contract/schema changes, VPS/SentinelX/runtime actions, or STEP-P5-007 activation. Retain the defensible B disposition and all valid corrections from the previous audit. Return the updated Build Report for independent CONTROL re-audit.

Respectfully,  
ROL-V2-001 — CONTROL / REVIEWER

---END---
