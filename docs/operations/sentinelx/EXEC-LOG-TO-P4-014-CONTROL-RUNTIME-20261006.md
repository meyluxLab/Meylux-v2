# EXEC-LOG-TO-P4-014-CONTROL-RUNTIME-20261006 — CONTROL S-17 Runtime Acceptance

**Execution Log SID:** `EXEC-LOG-TO-P4-014-CONTROL-RUNTIME-20261006`  
**Task Order:** `TO-P4-014`  
**Build Report:** `BR-P4-015`  
**CONTROL:** `ROL-V2-001`  
**Execution mechanism:** SentinelX-only bounded CONTROL runtime verification  
**Implementation revision tested:** `73b4d73c15f1ec0e35980c6c649a941b7c100450`  
**PR:** `#68`  
**Merged revision:** `cda0982bcbe6304c6b1a0fcf1135b1699510472f`

## 1. Boundary

This execution independently verifies the S-17 P4 prerequisite path authorized by `TO-P4-014`. It does not implement or activate P5-006.

## 2. Runtime method

CONTROL used SentinelX to inspect the real PostgreSQL runtime and executed the exact corrected S-17 implementation revision in a temporary isolated runtime environment because the corrected revision had not yet been merged at the time of runtime verification. No source mutation, deployment mutation, migration, synthetic trade insertion, manual quality-evidence insertion, or direct Volume Profile persistence was used to manufacture the acceptance result.

## 3. Real input lineage

The accepted trade lineage was:

`raw TRADE` → source record `f12b8c638b3a2e742c88bad720ca2f6b6a5f19df4f38ab3983cdcb251fbc7d7a` → P3 quality evidence `7458bdeb170d2d1a8482fecac9157455e8ba4eba278d91fa1547d6b6a8ac23d6` → `CanonicalTrade` record `80349ae7db22c1b15a18020b9219ed8eaa7be80334e1444fb632463558e3a9` → CanonicalTrade event identity `3b143c10856995e0519ae2080da17d5669627fe74d0e288af1b6d5d1daf122fe`.

The source acquisition state was `AVAILABLE`; quality was `VALID`; lifecycle was `CANONICAL`; event type was `TRADE`; `knowledge_time == received_at == 2026-09-18T17:09:36.184325Z`; venue remained NULL because no authoritative venue was present in the raw lineage.

## 4. Explicit S-17 execution boundary

Instrument: `BINANCE:BTCUSDT`  
Timeframe: `1h`  
Interval: `[2026-09-18T17:00:00Z, 2026-09-18T18:00:00Z)`  
Price bin size: `1`  
HVN threshold: `0.5`  
LVN threshold: `0.1`

The interval was supplied explicitly. No calendar/session discovery, rolling-session inference, or provider-derived session boundary was introduced.

## 5. Persistence and replay evidence

First execution:

- `volume_profile_sessions` new rows: **1**
- persisted session identity: `3eab3854fa6b634320360697364cdc1239bd11dde09e793c4cf0d076db32084a`
- status: `valid`
- reason: `volume_profile_analysis`
- `knowledge_time`: `2026-09-18T17:09:36.184325Z`
- venue context: NULL

Replay execution:

- new `volume_profile_sessions` rows: **0**

Final matching persisted session count remained exactly **1**.

Direct PostgreSQL read-back confirmed the persisted Volume Profile session and the supporting quality-evidence lineage.

## 6. CI evidence

Docker Foundation Run `#885`, run ID `37503933559`: **SUCCESS**.

Affected PostgreSQL evidence suite: **11/11 PASS**.  
Dedicated P3-009 PostgreSQL stage: **7/7 PASS**.

Core Run `#2029`, run ID `37503933510`, initially encountered one PostgreSQL lifecycle-race failure. CONTROL reran the failed repository-foundation job `112420916363`; the retry completed **SUCCESS**, with **648 foundation tests**, `OK (skipped=5)`, migration pass, and P3-009 PostgreSQL `7/7 PASS`.

The transient PostgreSQL lifecycle failure was not reproduced and required no implementation change.

## 7. Evidence conclusion

The real acceptance chain is established:

**raw TRADE → P3 quality evidence → CanonicalTrade → explicit interval → VolumeProfileEngine → `volume_profile_sessions` → PostgreSQL read-back → replay/idempotency**

No synthetic market data, fabricated quality evidence, provider-to-venue inference, candle substitution, manual Volume Profile insertion, or historical rewrite was used.

This execution establishes the runtime evidence required for CONTROL's independent TO-P4-014 verification. It does not itself establish P5-006 specialist completion.

**Execution disposition: EXECUTED — SUFFICIENT FOR INDEPENDENT CONTROL VERIFICATION.**
