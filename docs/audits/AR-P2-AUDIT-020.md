# AR-P2-AUDIT-020 — Independent Re-Audit of Corrected BR-P2-018

**Audit SID:** AR-P2-AUDIT-020  
**Task Order:** TO-P2-018  
**Build Report:** BR-P2-018  
**CONTROL:** ROL-V2-001  
**Producer:** ROL-V2-002  
**Audit date:** 2026-10-09  
**Disposition:** APPROVED / VERIFIED — INVESTIGATION REPORT ACCEPTED  
**Reviewed PR:** #75, head `163dfd24a5b2de07797cdb39d21a1db943bc23ad`  
**Reviewed report Blob SHA:** `ec34008fad9cfa0e6d873a1579c30325d4f7f77b`

## 1. Definitive conclusion

**BR-P2-018 is APPROVED / VERIFIED as an investigation report.** The report incorporates the corrections requested by AR-P2-AUDIT-018 and AR-P2-AUDIT-019, and its primary disposition **B — NO QUALIFIED ROUTE ESTABLISHED** is defensible under TO-P2-018.

This approval means the report accurately records the evidence found and the limits of that evidence. It does **not** mean PRQ-3 is delivered, that S-04 is available, that any route has been selected, or that STEP-P5-007 is authorized.

## 2. Independent evidence inspected

CONTROL retrieved and examined the current PR #75 report at its current Blob SHA, the full TO-P2-018, the current checkpoint, and the exact repository files/functions cited in §6 of the report:

- `src/meylux/persistence/canonical.py` — `CanonicalRecord.__post_init__`, `CanonicalPersistence.persist`, and `CanonicalPersistence.fetch`; Blob SHA `72a46beb7d84d6536c64ce17dd56e9633148f7c6`.
- `src/meylux/persistence/quality_evidence.py` — `QualityEvidencePersistence.persist`, `fetch`, `resolve`, and `resolve_evidence_ref`; Blob SHA `32bfbfe7031660adbb6e223c54a02f282a6fbdc3`.
- `src/meylux/specialists/snapshot.py` — `SnapshotRecord.__post_init__`, `InputSnapshotBuilder._validate_temporal_boundary`, and `InputSnapshotBuilder.build`; Blob SHA `5651830a4a4dbc46430a1f5d2f7593778828c5c8`.
- `contracts/specialist.py` — `EvidenceRef`, `SnapshotFact`, and `InputSnapshot`; Blob SHA `fbfeca24a4595fcf5bdfe1f95693a3be03d45191`.
- `docs/state/CURRENT_CHECKPOINT.json` — Blob SHA `fded71662501573eff930eafda67aa92098008ed`.

The current PR changes only `docs/build-reports/BR-P2-018.md`; the changed-file listing was checked. No code, tests, migrations, or protected contracts are changed by PR #75.

## 3. Finding-by-finding re-audit

### F-01 from AR-P2-AUDIT-019 — documentation qualification versus runtime verification

**Resolved.** The revised report explicitly grounds B in documentary, semantic, and representation gaps. It identifies current listing/runtime availability as a non-claim and later validation requirement, not as a failure criterion for this documentation-only investigation. BTCUSDT is distinguished from SOLUSDT: BTCUSDT is used in official endpoint examples; SOLUSDT's exact product-specific evidence remains less specific. No live endpoint claim is made.

### F-02 from AR-P2-AUDIT-019 — EvidenceRef, knowledge-time, and persistence chain

**Resolved as an evidence-boundary finding, not as implementation completion.** The report accurately distinguishes component-level implementation from an end-to-end authoritative joined read-back:

- Canonical persistence has transactional insert, identity-conflict handling, and fetch/read-back, but the canonical derivatives table carries `event_time` and `persisted_at`, not authoritative `knowledge_time`.
- Quality-evidence persistence/read-back and logical-fact resolution can return a structured EvidenceRef with knowledge time; multiple distinct identities for one logical fact are rejected.
- Generic Snapshot validation checks the supplied record and EvidenceRef metadata, including identity and timestamp consistency, and rejects `knowledge_time > snapshot.as_of`.
- The Snapshot builder consumes caller-supplied records and performs no database resolution. The inspected repository does not establish a unique identity-checked join between a canonical derivatives row and its authoritative quality-evidence row followed by joined read-back.

This is the correct boundary conclusion. It does not overstate generic temporal validation as proof of end-to-end S-04 eligibility. The report preserves the checkpoint's `available_persisted_claim: NONE` and does not claim `AVAILABLE_PERSISTED`.

### F-03 from AR-P2-AUDIT-019 — editorial defect

**Resolved.** The malformed phrase in §5.3 has been corrected.

## 4. Route qualification and disposition assessment

The corrected report's B disposition follows the evidence:

1. **Binance USDⓈ-M BTCUSDT:** official documentation establishes Funding, current OI, historical OI, and direct Basis endpoint/field capability. The exact unit/quantity semantics of current and historical OI remain unspecified in the inspected official schema, preventing complete canonical OI qualification without inference.
2. **Binance USDⓈ-M SOLUSDT:** assessed separately; generic schemas and BTCUSDT examples do not independently establish the same product-specific documentation scope. The USDⓈ-M OI unit gap also remains.
3. **Binance COIN-M BTCUSD:** Funding, OI, and Basis are documented for COIN-M, but the report correctly refuses to substitute this distinct product/instrument identity for BTCUSDT USDⓈ-M/Spot.
4. **MEXC BTC_USDT Futures:** Funding is documented, but the inspected evidence does not establish authoritative canonical OI units/semantics or direct Basis for the exact instrument. The report does not promote `holdVol` or fair price by inference.
5. **History windows and timestamps:** the report keeps Funding event time, current OI transaction time, historical OI period-end time, and Basis period-start time distinct. It does not claim unlimited retention, gap-free coverage, live availability, or retrospective history beyond documented windows.

No specific provider/product is selected. Disposition C is not warranted because the report does not demonstrate a protected-boundary conflict that necessarily requires contract change control; the evidence supports B.

## 5. Scope and non-claims

No live provider API call, implementation, provider/product selection, protected contract/schema change, VPS/SentinelX/runtime action, migration, deployment, or STEP-P5-007 activation occurred. No test execution is claimed. Historical PH-P2 / STEP-P2-006 and STEP-P5-006 closure records remain preserved.

## 6. Lifecycle conclusion and mandatory continuation

- `BR-P2-018`: **APPROVED / VERIFIED** as an investigation report.
- `TO-P2-018`: **VERIFIED / COMPLETE** as the bounded documentation/repository investigation that it authorized, with primary outcome B.
- `PRQ-3`: remains an unresolved required capability.
- `S-04`: not established as `AVAILABLE_PERSISTED`.
- `STEP-P5-007`: NOT ACTIVATED.

Under TO-P2-018 §10 and ADR-GOVERNANCE-014, disposition B does not permit silent abandonment of PRQ-3. CONTROL must continue the evidence-supported route investigation under a separately identified continuation boundary. The follow-up is limited to public authoritative documentation and repository evidence; it must not turn unresolved documentation into a provider guarantee, select a provider on the Owner's behalf, or authorize implementation/runtime work.

## 7. CONTROL hand-off

### FORMAL ENGLISH MESSAGE READY TO SEND — PRODUCER

**TO:** PRODUCER / ARCHITECT-BUILDER — ROL-V2-002  
**FROM:** CONTROL / REVIEWER — ROL-V2-001  
**SUBJECT:** AR-P2-AUDIT-020 — BR-P2-018 Accepted; PRQ-3 Investigation Continues

Producer,

CONTROL independently re-audited the corrected report at Blob SHA `ec34008fad9cfa0e6d873a1579c30325d4f7f77b` and approves `BR-P2-018` as an accurate investigation report. The report resolves both findings from AR-P2-AUDIT-019 and corrects the editorial defect. Its primary disposition B — NO QUALIFIED ROUTE ESTABLISHED — is accepted.

This is not PRQ-3 delivery or S-04 availability. The report correctly preserves the USDⓈ-M OI unit-semantics gap, the less-specific SOLUSDT documentary evidence, the MEXC OI/Basis gaps, and the unestablished canonical-derivatives-to-quality-evidence joined read-back path. `available_persisted_claim: NONE` remains unchanged. No implementation or runtime action is authorized.

CONTROL will complete the repository closure synchronization for TO-P2-018 and continue the required PRQ-3 evidence investigation under a distinct continuation Task Order. Do not interpret this audit as provider selection or permission to implement.

Respectfully,  
ROL-V2-001 — CONTROL / REVIEWER

---END---
