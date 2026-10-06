# AR-P2-AUDIT-015 — Independent Verification of TO-P2-015

**Task Order:** `TO-P2-015`  
**Producer:** `ROL-V2-002`  
**CONTROL / Reviewer:** `ROL-V2-001`  
**PR:** `#71`  
**Producer delivery head:** `87b74954cd4fbd2d004a3212d965f42b97c3e870`  
**Merged SoT commit:** `56bebeb4114aacd8d8999da3325b25c193db0b1a`  
**Status:** **VERIFIED / COMPLETE**

## 1. Independent conclusion

CONTROL independently verifies that the authorized `TO-P2-015` outcome has been genuinely established.

The Binance Spot TRADE acquisition boundary now emits explicit source-scoped `BINANCE` venue evidence; P3 quality evidence preserves and enforces that venue semantics; real Binance Spot runtime acquisition on the governed VPS produced persisted raw trade, quality-evidence, and canonical-trade lineage with `venue=BINANCE`; and deterministic replay behavior was directly observed.

No provider-to-venue inference, synthetic trade evidence, historical rewriting, P5 specialist implementation, or unrelated architecture change was used.

**TO-P2-015: VERIFIED / COMPLETE.**

The correction establishes the venue prerequisite only. It does not by itself verify `STEP-P5-006`.

## 2. Repository / implementation verification

CONTROL verified PR #71 and the delivered implementation.

The implementation boundary includes:

- `src/meylux/acquisition/binance.py`
  - REST Spot TRADE payloads carry explicit `venue=BINANCE`;
  - live `trade` and `aggTrade` payloads carry the same source-scoped venue;
  - contradictory explicit venue fails closed;
  - venue is established at acquisition rather than inferred downstream.
- `contracts/quality_evidence.py`
  - Binance TRADE requires explicit `BINANCE`;
  - `BINANCE` attached to a non-Binance provider is rejected.
- Regression coverage covers REST propagation, stream propagation, contradictory venue, missing venue, and cross-provider misuse.
- Existing TO-P2-014 fixture updates add the now-required authoritative venue field; they do not weaken acceptance.

The producer Build Report remains historical evidence of the Producer boundary and is not rewritten.

## 3. CI verification

Current producer-head CI was independently checked after the Producer handoff.

- CI Core run **#2124**, run ID `37531793405`: **SUCCESS** after rerun.
- CI Docker Foundation run **#949**, run ID `37531793409`: **SUCCESS**.
- The Core run's dedicated P3-009 PostgreSQL stage executed migrations 0001–0009 and passed **7/7**.
- The initial transient PostgreSQL foundation failure was rerun successfully; it is not treated as a TO-P2-015 implementation defect.

Therefore terminal CI evidence is established for the delivered head.

## 4. Real runtime verification

CONTROL used the authorized SentinelX-only path on `server-l6rf`.

The exact Producer head `87b74954cd4fbd2d004a3212d965f42b97c3e870` was fetched from GitHub, built into an isolated image, and the relevant `src/`, `contracts/`, and `config/` content was deployed into the existing stopped specialist container.

Independent SHA-256 verification:

- `src/meylux/acquisition/binance.py`:
  `79a555456de06f0f990950ed7401e728084211de6daf2efd5df4b76a7b774379`
- `contracts/quality_evidence.py`:
  `68b1b7719a88b85c794d4ff50bd0f412ab4dea50f83823076ae6c319112d3b1e`

Both deployed hashes matched the exact Git revision archive.

Real Binance Spot REST TRADE acquisition was then executed against `BTCUSDT`.

Direct PostgreSQL read-back established, among other rows:

- raw acquisition event:
  - provider `binance`;
  - event type `TRADE`;
  - acquisition state `AVAILABLE`;
  - payload explicitly contains `"venue":"BINANCE"`;
  - real Binance trade ID `6740830622`.
- quality evidence:
  - provider `binance`;
  - venue `BINANCE`;
  - authoritative event time;
  - knowledge time later than event time and persisted as evidence metadata.
- canonical trade:
  - `instrument_id=BINANCE:BTCUSDT`;
  - `VALID`;
  - source-record lineage preserved;
  - deterministic identity hash persisted.

No manually inserted trade or synthetic payload was used.

## 5. Replay verification

CONTROL executed the authorized pipeline with `replay_same_evidence=True`.

Observed result:

- `available_trades=1`
- `raw_inserted=1`
- `raw_duplicates=1`
- `quality_evidence_inserted=1`
- `quality_evidence_duplicates=1`
- `quality_evidence_contradictory=0`
- `canonical_inserted=1`
- `canonical_duplicates=1`
- `replay_executed=true`
- `invalid_or_unavailable=0`

The duplicate path therefore preserved deterministic replay/idempotency semantics rather than producing a contradictory quality-evidence row.

## 6. Scope / architecture verification

CONTROL found no evidence of:

- provider-to-venue inference;
- second truth source;
- new venue registry;
- P5 specialist modification;
- P4 mathematical redesign;
- MEXC/Futures/Forex expansion;
- trading/capital/account/custody behavior;
- historical evidence rewriting.

The ratified architecture remains unchanged.

## 7. VPS restoration

The runtime acceptance was bounded.

After evidence collection:

- `compose-worker-specialist-1` was stopped;
- `compose-redis-1` was stopped;
- the pre-existing `compose-db-1` remained running and healthy;
- `/srv/meylux-v2` remained at its pre-existing unrelated revision `d7c3fa31cb092543440f2769ffbf9b6022c29a6a`;
- its pre-existing unrelated working-tree modifications remained untouched.

No unrelated runtime state was retained from the acceptance execution.

## 8. Acceptance mapping

| Requirement | CONTROL disposition |
|---|---|
| Explicit Binance venue at acquisition boundary | **VERIFIED** |
| Provider identity distinct from venue | **VERIFIED** |
| P3 preservation/enforcement | **VERIFIED** |
| Contradictory/missing venue fails closed | **VERIFIED** |
| Cross-provider Binance venue rejected | **VERIFIED** |
| Real Binance Spot runtime evidence | **VERIFIED** |
| PostgreSQL persistence/read-back | **VERIFIED** |
| Canonical lineage | **VERIFIED** |
| Deterministic replay/idempotency | **VERIFIED** |
| Repository CI | **VERIFIED** |
| Architecture preservation | **VERIFIED** |
| Historical evidence preservation | **VERIFIED** |

## 9. Lifecycle disposition

`TO-P2-015` is **VERIFIED / COMPLETE**.

The trade venue-evidence prerequisite required for the next Group-C resolution boundary is now established.

Per ADR-GOVERNANCE-012, CONTROL owns the complete closure synchronization for this Task Order.

Per ADR-GOVERNANCE-014, the remaining Group-C fact population problem is not removed by this closure. `TO-P4-015` is therefore promoted from `DEFINED / INACTIVE` to the next authorized corrective boundary.

`STEP-P5-006` remains **ACTIVE / AUTHORIZED** and is not declared complete.

## 10. Non-claims

This audit does not claim:

- `STEP-P5-006` VERIFIED;
- S-03 final acceptance;
- S-17 final acceptance;
- authoritative 15m Volume Profile population;
- complete historical Binance trade coverage;
- Phase 5 closure.

**FINAL CONTROL DISPOSITION: TO-P2-015 VERIFIED / COMPLETE.**
