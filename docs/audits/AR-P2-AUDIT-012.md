# AR-P2-AUDIT-012 — CONTROL Independent Audit — MEXC Capability-Preservation Architectural Assessment

**Audit Report SID:** `AR-P2-AUDIT-012`
**Project:** MEYLUX V2
**Auditor Role:** CONTROL / REVIEWER — `ROL-V2-001`
**Producer Role:** PRODUCER / ARCHITECT-BUILDER — `ROL-V2-002`
**Task Order:** `TO-P2-012`
**Build Report:** `BR-P2-012`
**Boundary:** `PH-P2 / STEP-P2-006 / A-P2-MEXC-CAPABILITY-ARCHITECTURE`
**Audit class:** Independent post-closure architectural investigation verification
**Audit status:** APPROVED / VERIFIED
**Audit date:** 2026-09-27 UTC

## 1. Audit conclusion

CONTROL independently audited `BR-P2-012` against the authorized requirements of `TO-P2-012`, the actual Producer delivery commit, the complete Build Report retrieved by its reported Blob SHA, current Meylux contracts/implementation, and current authoritative MEXC documentation/schema.

The Build Report is **VERIFIED** and the architectural conclusion is accepted:

> A technically defensible capability-preservation architecture exists conceptually within the current frozen architecture, but it does not establish MEXC candle finality or public trade-stream completeness.

The assessment correctly distinguishes:

1. **Mechanism failure:** MEXC public trade-stream sequence integrity / exact REST reconciliation remains `UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`.
2. **Specific route failure:** a Trade→Candle route dependent on unsupported trade continuity or inferred finality is not defensible on current evidence.
3. **Broader architecture:** the evidence does not establish that MEXC is unusable or that no capability-preserving architecture exists.

## 2. Producer artifact integrity and scope

The Build Report was retrieved using its reported Blob SHA:

`685ed2d7080b0dd6c61567c7caaf7f75dbd584b0`

Producer delivery commit:

`3a45758f69bc19008279d1a63d915f1c2be0686d`

Independent commit inspection establishes that this delivery commit adds the Build Report artifact and does not contain implementation source, contract, schema, persistence, migration, or runtime mutation.

The Build Report explicitly remains `PRODUCED / NOT VERIFIED` and makes no project-level VERIFIED/CLOSED claim.

No VPS mutation or deployment was performed.

## 3. Requirements coverage

The report covers the authorized `TO-P2-012` requirements, including:

- authoritative MEXC documentation and official protobuf schema inspection;
- bounded read-only provider observations;
- current Meylux contract/implementation inspection;
- preservation of the fixed `TO-P2-009` / `TO-P2-011` semantic dispositions;
- first-principles candidate mechanism analysis;
- capability-specific assessment;
- semantic-laundering rejection;
- historical/live distinction;
- canonicalization-boundary analysis;
- conceptual preferred architecture;
- governance/change-control boundaries;
- explicit distinction between mechanism failure, route failure, and broader architectural conclusion;
- no implementation or repository/runtime mutation;
- definitive final architectural disposition.

The report also explicitly identifies unresolved questions rather than converting them into unsupported facts.

## 4. Independent verification of the positive order-book mechanism

CONTROL independently checked the current MEXC Spot API documentation.

MEXC's current documentation explicitly states that its aggregated depth stream uses `fromVersion` and `toVersion`, and its local-order-book procedure requires:

- a REST depth snapshot;
- each new `fromVersion` to equal the previous `toVersion + 1`;
- reinitialization from the REST snapshot when continuity fails;
- ignoring outdated updates;
- detection of missing data when the incoming `fromVersion` is beyond the snapshot version;
- integration of updates only when the snapshot version falls within the update range.

This is a provider-documented continuity/recovery mechanism, not an inference from a finite observation. The same documentation also explicitly warns that snapshot depth is limited and that the reconstructed local book may differ slightly from the real book outside the initial snapshot scope.

The official MEXC protobuf schema independently defines `fromVersion` and `toVersion`.

Therefore the Producer's characterization is correct:

**MEXC provides an authoritative provider-grounded version/recovery mechanism for aggregated order-book depth.**

This does **not** establish:

- complete infinite-depth state;
- historical transition completeness;
- trade-stream completeness;
- candle finality.

The Producer report correctly preserves those boundaries.

## 5. Independent verification of canonical-boundary reasoning

The current Meylux repository at the inspected revision contains:

- `CanonicalTrade` as an individual immutable semantic trade-event contract;
- `CanonicalOrderBook` as a provider-neutral snapshot contract;
- `CanonicalCandle.is_closed` as a boolean canonical semantic;
- raw/staging `AcquisitionEnvelope` persistence retaining payload, provenance, event/receipt timing and source sequence;
- MEXC normalization paths for trade, candle and order-book observations.

The report correctly distinguishes individual observed trade semantics from proof of a complete MEXC trade population.

It also correctly refuses to derive MEXC candle finality from `windowEnd`, elapsed time, repeated messages, REST availability, next-interval observation, or other temporal inference.

The existing canonical candle contract is therefore not weakened by this assessment.

## 6. Capability-preservation conclusion

The evidence supports the following capability-preserving conceptual boundary:

**MEXC provider observation/evidence → existing acquisition/raw boundary → promote only independently defensible semantic facts → keep unsupported finality/completeness outside canonical truth.**

The following are supported by the current evidence at the stated semantic level:

- raw/acquisition MEXC observations can remain preserved;
- individual MEXC trade observations may be represented by the existing `CanonicalTrade` semantics without claiming population completeness, subject to ordinary contract validation;
- MEXC REST order-book snapshots are compatible with the existing `CanonicalOrderBook` semantics as bounded snapshots;
- MEXC documented depth version continuity provides a defensible conceptual basis for future live snapshot+delta reconstruction;
- MEXC instrument metadata can use the existing canonical instrument boundary;
- ticker/book-ticker and other observations can remain provider evidence where no governed canonical contract exists;
- historical datasets can remain provenance-preserving evidence where target canonical semantics are not established.

The report does not overclaim that all of these are already implemented.

## 7. Historical/live and semantic-laundering checks

The report correctly separates live WebSocket observations, REST observations, historical data and future reconstructed state.

The semantic-laundering analysis is also adequate: provider availability, temporal coincidence, repetition, absence of further messages, and statistical agreement are not promoted into unsupported canonical finality or completeness.

The bounded live depth chain is treated as empirical corroboration only; the provider documentation is correctly treated as the source of the universal continuity rule.

The bounded live K-line observation is correctly used only to demonstrate mutability within an interval, not as a universal proof of every possible MEXC behavior.

## 8. Governance and implementation boundary

The Producer stayed within the authorized investigation-only boundary.

No:

- implementation;
- contract change;
- schema change;
- migration;
- persistence mutation;
- historical rewrite;
- new canonical state;
- Trade→Candle implementation;
- VPS mutation;
- deployment;
- automatic `TO-P2-010` resume/cancel/redirect

was performed.

The report explicitly identifies future implementation boundaries as requiring separate authorization.

In particular, the report's identification of **MEXC order-book snapshot + versioned WebSocket delta reconstruction** as a future implementation candidate is advisory only and does not authorize that work.

## 9. Important limitations retained

The audit accepts the following limitations as correctly stated:

- MEXC candle finality remains unavailable;
- MEXC public trade-stream completeness remains unavailable;
- exact public WebSocket trade-ID to REST-ID reconciliation remains unavailable on the evidence reviewed;
- historical downloadable-data semantics were not fully characterized for every possible canonical target;
- live order-book reconstruction is not implemented;
- bounded observations do not replace provider documentation for universal guarantees.

These limitations prevent the report from becoming an overbroad claim that all MEXC data is canonical-ready.

## 10. Fixed historical decisions preserved

The following remain unchanged:

`MEXC_FINALITY: UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`

`MEXC_TRADE_SEQUENCE_INTEGRITY: UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`

`TO-P2-010: AUTHORIZED / SUSPENDED`

`TO-P2-011: VERIFIED / COMPLETE`

`AR-P2-AUDIT-011: APPROVED / VERIFIED`

No automatic implementation decision follows from this audit.

## 11. Audit disposition

`BR-P2-012` is **VERIFIED**.

`TO-P2-012` is **VERIFIED / COMPLETE**.

The architectural disposition is:

**A defensible MEXC capability-preservation architecture exists conceptually under the current frozen architecture, while MEXC candle finality and public trade-stream completeness remain unavailable.**

The broader result is therefore positive but bounded:

**maximum valid MEXC capability can be preserved without weakening canonical truth, but only capability-by-capability and semantic-layer-by-semantic-layer.**

This audit does not authorize implementation and does not decide the future of `TO-P2-010`.

`PH-P2` remains `CLOSED / VERIFIED`.

`STEP-P2-006` remains `COMPLETE / VERIFIED`.

`TO-P2-010` remains `AUTHORIZED / SUSPENDED`.

## 12. Closure boundary

The natural independent-audit boundary for `TO-P2-012` has been reached.

CONTROL must now perform the complete ADR-GOVERNANCE-012 peripheral synchronization and final machine read-back.

Closure synchronization is CONTROL-owned and is not delegated to Producer.

---END---
