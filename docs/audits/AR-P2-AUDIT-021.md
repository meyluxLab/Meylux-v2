# AR-P2-AUDIT-021 — Independent Audit of BR-P2-019

**Audit SID:** AR-P2-AUDIT-021  
**Task Order:** TO-P2-019  
**Build Report:** BR-P2-019  
**CONTROL:** ROL-V2-001  
**Producer:** ROL-V2-002  
**Audit date:** 2026-10-11  
**Disposition:** APPROVED / VERIFIED — INVESTIGATION REPORT ACCEPTED  
**Reviewed PR:** [#76](https://github.com/meyluxLab/Meylux-v2/pull/76)  
**Reviewed branch-head commit:** `2e66932ac558b5925b26abab7cd80a95dc787df9`  
**Report Blob SHA:** `de56cf74d65409cf961480b4ba50629204239a62`  
**Pre-merge main commit:** `99401df8c35494eaff49c1bc3c32e3bba6f1cb4c`  
**Merge commit:** `baa4398d99fea7ce2edb21ba17ab63ea2f759147`

## 1. Definitive conclusion

**BR-P2-019 is APPROVED / VERIFIED as an accurate investigation report under TO-P2-019. Its primary disposition B — NO QUALIFIED ROUTE ESTABLISHED — is accepted.**

This acceptance means the report accurately distinguishes documented provider facts, repository facts, unresolved claims, and rejected inference within the authorized investigation-only scope. It does **not** mean PRQ-3 is delivered, that S-04 is available, that any provider/product has been selected, or that STEP-P5-007 is authorized.

The report preserves `available_persisted_claim: NONE`, the unresolved PRQ-3 obligation, and the separate canonical-derivatives-to-quality-evidence joined read-back blocker. No implementation or runtime evidence is claimed.

## 2. Repository and integration evidence independently checked

CONTROL retrieved the current Source of Truth files and compared the producer branch against its stated current-main parent.

- Current checkpoint: `docs/state/CURRENT_CHECKPOINT.json`, Blob SHA `02e28b6a1f5fa7a593eaee50c715874b59161927`. It identifies `PH-P5`, `STEP-P5-006`, active `TO-P2-019`, and `available_persisted_claim: NONE`.
- Active Task Order: `docs/task-orders/TO-P2-019.md`, Blob SHA `3e569cdd590b46c9817f5e18afc2c7a8bf5c287c`.
- Artifact Protocol: `docs/governance/ARTIFACT_PROTOCOL_V2.md`, Blob SHA `ea6a993714430320a6f427ecf32de95a9fccfaf5`.
- ADR-GOVERNANCE-012: Blob SHA `3499ada1f0ad093212e59d8798beeefcab6f18ff`.
- ADR-GOVERNANCE-013: Blob SHA `16958ed80a59bd40fadf263229d40bf80e16b492`.
- Producer report `docs/build-reports/BR-P2-019.md): complete 381-line file retrieved; Blob SHA `de56cf74d65409cf961480b4ba50629204239a62`.
- Registry on the producer branch: `docs/registry/artifacts.yaml`, Blob SHA `f1c516c4dee2f9e4d56c90607993f4f69440fff8`.
- README: Blob SHA `373c002468e578c3d86bf909cb85da58de7ce777`.
- Phase record: `docs/phases/PH-P5.md`, Blob SHA `49f2668f743ff2021c4fb39772298fcad9342be6`.

GitHub comparison of base `99401df8c35494eaff49c1bc3c32e3bba6f1cb4c` to branch head `2e66932ac558b5925b26abab7cd80a95dc787df9` reported exactly one commit ahead, zero behind, and exactly two changed paths:
1. `docs/build-reports/BR-P2-019.md` added;
2. `docs/registry/artifacts.yaml` modified with seven added lines and no deletions.

The report Blob SHA remained unchanged after reconciliation. The registry retained current-main entries and included one BR-P2-019 record with the pending-audit status before this audit. PR #76 was merged after the independent content and integration audit; GitHub returned merge commit `baa4398d99fea7ce2edb21ba17ab63ea2f759147`. The report and registry changes are therefore integrated. The audit and subsequent CONTROL-owned synchronization are recorded separately here.

## 3. Finding-by-finding audit

### F-01 — Exact scope and disposition

**PASS.** TO-P2-019 authorizes public authoritative-documentation research and repository inspection only, requires a route-by-route assessment for Funding, OI, and direct Basis for exact BTCUSDT and SOLUSDT instrument scopes, and explicitly excludes implementation, live provider APIs, provider selection, protected contract/schema changes, VPS/SentinelX/runtime operations, and STEP-P5-007 activation. BR-P2-019 follows those limits and selects exactly one permitted primary disposition: B.

### F-02 — Binance USDⓈ-M OI semantics and SOLUSDT identity

**PASS — gap correctly preserved.** The report distinguishes the current official Chinese page from the legacy URL, records that the legacy URL did not yield a retrievable version-pinned historical page, and does not falsely attribute current wording to a verified historical version. The labels “total holding quantity” and “total holding value” narrow but do not resolve the exact unit, aggregation/calculation, valuation currency/method, or relationship of the current/historical OI fields. Historical OI period-end semantics and the limited history window are kept distinct from current OI time semantics. Product-specific SOLUSDT references are acknowledged without generalizing a generic schema into complete exact-product qualification.

Official source checked independently for Bybit/route contrast and current Gate documentation:
- Bybit Open Interest: https://bybit-exchange.github.io/docs/v5/market/open-interest
- Gate API v4 Futures documentation: https://www.gate.com/docs/developers/apiv4/en/futures/

The Bybit page explicitly defines BTCUSDT linear OI in BTC and BTCUSD inverse OI in USD, supports interval history and cursor pagination, and does not itself establish the exact SOLUSDT unit or the required Basis semantics. Gate documentation identifies OI fields as contracts and quote-currency value but does not establish a direct provider-supplied Basis route in the inspected guide. These checks are consistent with the report's bounded conclusions.

### F-03 — Bybit Basis scope

**PASS.** The report confines the empty `basis` / `basisRate` observation to the documented inverse BTCUSD example and does not generalize it to linear BTCUSDT or SOLUSDT perpetuals. It correctly treats field presence as insufficient without exact formula, units, metric timestamp, and history/coverage evidence.

### F-04 — OKX historical OI and Basis evidence

**PASS.** The report explicitly distinguishes direct inspection of the official API guide from secondary endpoint-index and SDK corroboration. It treats `GET /api/v5/rubik/stat/contracts/open-interest-history` as endpoint-existence evidence only, not as a complete authoritative response contract or exact-instrument route qualification. It rejects premium index as a substitute for canonical signed price-difference Basis.

### F-05 — Other provider candidates and exact product identity

**PASS.** Bitget, Gate.io, MEXC, and Binance COIN-M are not promoted beyond the evidence described. Missing metrics and missing semantics remain unresolved; the report does not substitute BTCUSD COIN-M for BTCUSDT USDⓈ-M, nor infer SOLUSDT guarantees from BTCUSDT examples. The report's negative finding means “not established by the inspected evidence,” not “provider cannot support the capability.”

### F-06 — Frozen contracts, normalizer, and S-04 persistence/read-back

**PASS.** The report distinguishes numeric field representability from authoritative provider semantics and correctly records that the current normalizer is Binance/MEXC-only. It does not use that limitation alone to declare a protected-contract conflict or disposition C. It separately identifies that generic Snapshot temporal validation and component-level persistence/read-back do not prove a unique identity-checked join between a canonical derivatives row and its authoritative quality-evidence record returning authoritative `knowledge_time` and complete `EvidenceRef`.

### F-07 — Evidence, source limits, failure cases, and non-claims

**PASS.** The report provides official URLs, product/instrument identifiers, timestamps and coverage limits where established; separates facts from inference and unknowns; records exact reconsideration triggers; addresses missing history, stale/contradictory values, identity mismatch, invalid numbers, and provenance; and makes no claim of tests, implementation, live API calls, current listing, persisted availability, or runtime execution.

## 4. Disposition assessment

The report's B disposition is supported. No candidate is demonstrated by the inspected authoritative evidence to supply all required Funding, OI, and direct Basis facts for both exact BTCUSDT and SOLUSDT scopes with the required units, product identity, timestamp semantics, coverage, provenance, and compatibility. Disposition C is not justified because no specific frozen architecture/contract/schema conflict has been demonstrated to necessarily prevent a viable route. Disposition A is not justified because the documented gaps remain material.

The report therefore accurately preserves:
- primary disposition **B — NO QUALIFIED ROUTE ESTABLISHED**;
- `available_persisted_claim: NONE`;
- PRQ-3 as a required unresolved capability;
- STEP-P5-007 as **NOT ACTIVATED**;
- the independent S-04 persisted-evidence blocker;
- no provider/product selection and no implementation/runtime authorization.

## 5. Lifecycle and closure boundary

PR #76 is merged. This audit accepts the Build Report as an investigation report only. It does not close PRQ-3, activate STEP-P5-007, or reopen any historical PH-P2 / STEP-P2-006 / STEP-P5-006 closure.

Under ADR-GOVERNANCE-012, CONTROL owns the remaining synchronization of the Checkpoint, artifact registry, README, Phase status-bearing documents, and any specialized/status registries that apply. The next authorized action must continue the unresolved PRQ-3 evidence obligation under a distinct bounded Task Order; a B investigation result is not a capability-completion endpoint.

## 6. FORMAL ENGLISH MESSAGE READY TO SEND — PRODUCER

**TO:** PRODUCER / ARCHITECT-BUILDER — ROL-V2-002  
**FROM:** CONTROL / REVIEWER — ROL-V2-001  
**SUBJECT:** AR-P2-AUDIT-021 — BR-P2-019 Accepted; PRQ-3 Continues Unresolved

Producer,

CONTROL independently audited the complete BR-P2-019 at Blob SHA `de56cf74d65409cf961480b4ba50629204239a62`, the active TO-P2-019, the current Checkpoint, governance rules, registry change, and the reconciled PR #76 diff. PR #76 was merged at `baa4398d99fea7ce2edb21ba17ab63ea2f759147`.

**Disposition: APPROVED / VERIFIED — INVESTIGATION REPORT ACCEPTED.** The report's primary disposition **B — NO QUALIFIED ROUTE ESTABLISHED** is accepted. The report correctly preserves the exact Binance USDⓈ-M OI and SOLUSDT gaps, the limited Bybit Basis evidence, the distinction between OKX endpoint-existence corroboration and authoritative response qualification, the other candidate gaps, and the independent S-04 canonical-to-quality-evidence joined read-back blocker.

This acceptance is not PRQ-3 delivery, S-04 availability, provider selection, implementation authorization, or STEP-P5-007 activation. `available_persisted_claim: NONE` remains unchanged. CONTROL retains responsibility for all closure synchronization and continuation.

Respectfully,  
ROL-V2-001 — CONTROL / REVIEWER

## 7. CONTROL conclusion

**AR-P2-AUDIT-021: APPROVED / VERIFIED — BR-P2-019 ACCEPTED AS AN INVESTIGATION REPORT; PRIMARY DISPOSITION B ACCEPTED; PRQ-3 REMAINS UNRESOLVED.**

---END---
