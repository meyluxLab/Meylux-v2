# EXEC-LOG-TO-P2-015-CONTROL-RUNTIME-20261007

**Task Order:** `TO-P2-015`  
**Role:** CONTROL / REVIEWER — `ROL-V2-001`  
**Host:** `server-l6rf`  
**Authorization:** Project Owner full-resolution authorization dated 2026-10-06

## Scope

Bounded real Binance Spot TRADE acceptance for the explicit venue-evidence correction.

## Exact revision

Producer head deployed for acceptance:

`87b74954cd4fbd2d004a3212d965f42b97c3e870`

Merged SoT commit after independent verification:

`56bebeb4114aacd8d8999da3325b25c193db0b1a`

## Deployment verification

Relevant deployed files were copied from a Git archive of the exact Producer revision into the existing specialist container.

SHA-256:

- `src/meylux/acquisition/binance.py` = `79a555456de06f0f990950ed7401e728084211de6daf2efd5df4b76a7b774379`
- `contracts/quality_evidence.py` = `68b1b7719a88b85c794d4ff50bd0f412ab4dea50f83823076ae6c319112d3b1e`

Repository archive and deployed container hashes matched.

## Real execution

Real Binance Spot REST trade acquisition was executed for `BTCUSDT`.

Observed persisted raw trade:

- provider: `binance`
- event type: `TRADE`
- acquisition state: `AVAILABLE`
- trade id: `6740830622`
- payload venue: `BINANCE`

Observed persisted quality evidence:

- provider: `binance`
- venue: `BINANCE`
- event time: `2026-10-06 21:15:38.869+00`
- knowledge time: `2026-10-06 21:15:38.999358+00`

Observed canonical trade:

- instrument: `BINANCE:BTCUSDT`
- quality state: `VALID`
- source-record lineage preserved
- identity hash persisted

## Replay

A second bounded acquisition was executed with `replay_same_evidence=true`.

Observed:

- available trades: 1
- raw inserted: 1
- raw duplicates: 1
- quality evidence inserted: 1
- quality evidence duplicates: 1
- quality evidence contradictory: 0
- canonical inserted: 1
- canonical duplicates: 1
- replay executed: true
- invalid/unavailable: 0

## Runtime restoration

After acceptance:

- `compose-worker-specialist-1`: stopped
- `compose-redis-1`: stopped
- `compose-db-1`: remained healthy/running
- `/srv/meylux-v2`: returned to the pre-existing checkout `d7c3fa31cb092543440f2769ffbf9b6022c29a6a`
- pre-existing unrelated working-tree modifications were preserved

No unrelated runtime state was changed.

**CONTROL runtime evidence conclusion: ACCEPTED.**
