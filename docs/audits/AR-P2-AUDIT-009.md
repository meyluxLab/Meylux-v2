# AR-P2-AUDIT-009 — CONTROL Independent Audit of TO-P2-009

**Project:** MEYLUX V2  
**Role:** ROL-V2-001 — CONTROL / REVIEWER  
**Task Order:** TO-P2-009  
**Build Report:** BR-P2-009  
**Boundary:** PH-P2 / STEP-P2-006 / A-P2-MEXC  
**Audit disposition:** APPROVED / VERIFIED  
**Verification date:** 2026-09-25 UTC

## 1. Independent evidence baseline

CONTROL independently re-read the governing checkpoint, Artifact Protocol, ADR-GOVERNANCE-012, ADR-GOVERNANCE-013, TO-P2-009, BR-P2-009, artifact registry, phase registry, README, Change Ledger, relevant repository implementation files, and the current Phase-5 state.

The Producer's corrected Build Report is present in the repository at:

`docs/build-reports/BR-P2-009.md`

Build Report blob SHA:

`efa7df5da36b60fcf5b0cd935de0d0fc98b1f147`

The Producer lifecycle is correctly preserved as:

`PRODUCED / NOT VERIFIED`

The Build Report was added by commit:

`d8f0846ad23bdf9c431c443d87617a5e21d01e8a`

CONTROL independently verified that this is an evidence/report-only addition and that no implementation correction was performed under TO-P2-009.

## 2. Authoritative MEXC finality determination

CONTROL independently checked the cited current MEXC Spot documentation and the official Protobuf schema evidence.

The current Spot K-line surface documents timing/OHLCV fields and current-candle updates, but does not expose an authoritative provider-declared candle-finality flag. The cited Protobuf K-line schema likewise contains the nine K-line fields identified by the Build Report and no finality field. The current Spot REST K-line response documents open/close time fields but no finality declaration.

The evidence supports the bounded conclusion:

`MEXC_FINALITY: UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`

The conclusion is intentionally limited to the authoritative current Spot surfaces inspected. It does not assert knowledge of undocumented/private/internal mechanisms.

## 3. Timing / no-lookahead determination

CONTROL accepts the report's distinction between:

- candle start/end boundaries;
- provider event timing;
- transport timing;
- local receipt timing;
- persistence timing;
- repeated updates;
- REST row existence.

None of these observations is silently promoted to provider finality.

MEXC's documented current-candle update behavior does not establish finality merely because a later update is observed.

No lookahead or synthetic finality mechanism was introduced.

## 4. Material repository semantic finding

CONTROL independently verified the material finding in `contracts/normalization.py`:

The MEXC candle normalization path assigns:

`closed=True`

The current provider evidence does not establish MEXC finality.

Therefore the existing `closed=True` is repository behavior, not provider evidence.

CONTROL classifies this as:

`MATERIAL SEMANTIC IMPLEMENTATION FINDING`

It is correctly recorded but intentionally NOT corrected under TO-P2-009.

This is required scope discipline: TO-P2-009 is investigation-only and does not authorize MEXC normalization, canonical-contract, identity, persistence, migration, or architecture changes.

The finding is preserved for a separately authorized governance/implementation boundary if the Owner later decides that such work is required.

## 5. Repository and identity evidence

CONTROL independently verified the report's repository references for:

- MEXC acquisition adapter;
- Protobuf K-line decoding;
- REST K-line path;
- AcquisitionEnvelope;
- provenance;
- source sequence;
- event identity/deduplication;
- canonical candle representation;
- raw acquisition persistence;
- existing G-4/identity material.

No identity algorithm, canonical bytes, G-4 implementation, persistence model, migration, or provider-neutral contract was changed by TO-P2-009.

The report correctly notes that raw acquisition payload is identity-bearing. Any future semantic correction would therefore require explicit identity/replay/G-4 review rather than an implicit fix.

## 6. Test / CI evidence determination

The Build Report correctly states:

`TEST EXECUTION: NOT EXECUTED`  
`CI EXECUTION: NOT EXECUTED`  
`REPOSITORY INSPECTION: PERFORMED`

CONTROL does not convert test inspection into test execution and does not claim CI success for this investigation.

Because TO-P2-009 is a bounded documentation/evidence investigation and no production implementation was changed, the absence of test execution is not a blocker to the investigation disposition.

No tests registry entry is required from this investigation because no test execution evidence was produced.

## 7. Scope and architecture determination

CONTROL independently confirms that the Producer remained within the authorized investigation boundary.

No:

- MEXC implementation;
- normalization correction;
- Binance change;
- P3/P5 implementation;
- Futures/Forex work;
- provider activation;
- VPS/SentinelX operation;
- persistence/migration;
- identity/canonical-byte change;
- Phase-2 reopening

was performed.

Frozen architecture and G-4 remain unchanged.

## 8. Required final disposition

The investigation disposition is verified as:

`MEXC_FINALITY: UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED`

and:

`NO MEXC IMPLEMENTATION TASK ORDER IS JUSTIFIED OR AUTHORIZED FROM THIS OUTCOME.`

No further Producer implementation is authorized or required under TO-P2-009.

## 9. Lifecycle determination

The Producer correction cycle reached its natural evidence boundary.

CONTROL therefore determines:

- `BR-P2-009 = VERIFIED / ACCEPTED AS BUILD REPORT`
- `TO-P2-009 = VERIFIED / COMPLETE`
- `STEP-P2-006 = COMPLETE / VERIFIED` remains unchanged
- `PH-P2 = CLOSED / VERIFIED` remains unchanged
- `PH-P5 = ACTIVE / AUTHORIZED` remains unchanged
- `STEP-P5-002 = COMPLETE / VERIFIED` remains unchanged
- `STEP-P5-003 = NOT AUTHORIZED` remains unchanged
- `active_task_order = null`

This is a post-closure investigation completion and does NOT reopen Phase 2.

## 10. ADR-GOVERNANCE-012 closure synchronization

CONTROL performed the required closure synchronization after reaching the independent affirmative audit boundary.

Checked and synchronized:

1. `CURRENT_CHECKPOINT.json`;
2. `docs/registry/phases.yaml`;
3. `docs/registry/artifacts.yaml`;
4. README current-state text;
5. Change Ledger;
6. specialized registries for applicability — no new execution evidence was produced, so no test/database/security/configuration/runtime/observability record was invented;
7. standalone status-bearing Phase documents — historical PH-P2 and current PH-P5 lifecycle remain consistent;
8. supplemental/staging registry state — no stranded TO-P2-009 staging record was introduced.

The synchronization preserves the historical Phase-2 closure and does not activate any next Phase-5 Step.

## 11. Final CONTROL determination

**TO-P2-009 = VERIFIED / COMPLETE.**

**BR-P2-009 = VERIFIED / ACCEPTED.**

**PH-P2 = CLOSED / VERIFIED — preserved.**

**STEP-P2-006 = COMPLETE / VERIFIED — preserved.**

**PH-P5 = ACTIVE / AUTHORIZED — preserved.**

**STEP-P5-002 = COMPLETE / VERIFIED — preserved.**

**STEP-P5-003 = NOT AUTHORIZED.**

**Active Task Order = null.**

**MEXC_FINALITY = UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED.**

**No MEXC implementation Task Order is justified or authorized from this outcome.**

The material `closed=True` semantic finding remains recorded for future governed decision-making and is not silently corrected or absorbed into this investigation closure.

No further Producer action is required for TO-P2-009. The project proceeds from the existing PH-P5 / STEP-P5-002 state, with no automatic activation of STEP-P5-003.
