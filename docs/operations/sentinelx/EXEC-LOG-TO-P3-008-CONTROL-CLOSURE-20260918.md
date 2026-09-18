# EXEC-LOG — TO-P3-008 CONTROL End-to-End Completion and G-3 Verification

**execution_id:** EXEC-LOG-TO-P3-008-CONTROL-CLOSURE-20260918
**task_id:** TO-P3-008
**step_id:** STEP-P3-008
**target:** server-l6rf / /srv/meylux-v2
**executor_role:** ROL-V2-001 — CONTROL / REVIEWER
**start_time_utc:** 2026-09-18T19:02:01.670338Z (first observed successful vertical-slice runtime timestamp in this execution cycle)
**end_time_utc:** 2026-09-18T19:07:23.948688Z (CONTROL SentinelX execution timestamp)
**authorization_reference:** Project Owner explicit end-to-end completion authorization for STEP-P3-008, 2026-09-18; TO-P3-008 Revision 1.1
**repository_version_context:** main, runtime-verified implementation commit fb17a034805abd219bad8fccc757fefc8faca27e; final closure documentation commits follow without runtime-code changes

## 1. Repository and deployment identity

CONTROL synchronized the VPS checkout to:
`fb17a034805abd219bad8fccc757fefc8faca27e`

Repository path:
`/srv/meylux-v2`

The working tree was clean after synchronization.

Governed Compose services:
db, redis, api, collector, worker-quant, worker-ai.

CONTROL rebuilt api/collector/worker-quant/worker-ai images and force-recreated those services.

## 2. Migration and schema correction

CONTROL corrected the confirmed canonical quality-state boundary defect directly under the explicit Owner authorization.

Correction:
- added `migrations/versions/0004_canonical_quality_state_alignment.sql`;
- updated `infrastructure/postgres/migrate.sh` to execute migration 0004 after 0003;
- added deterministic migration/schema regression coverage.

Authoritative contract:
`DataQualityState.VALID.value = "VALID"`

Migration 0004 changes the five canonical quality-state checks to accept exactly `'VALID'` and records:
`0004_canonical_quality_state_alignment`

Migration harness result:
`database migration: PASS`

Independent database inspection confirmed:
- migration 0004 is recorded;
- all five canonical quality-state constraints require `VALID`;
- `meylux_app` has INSERT privilege on canonical trades;
- `meylux_app` has no UPDATE or DELETE privilege on canonical trades;
- append-only trigger `trg_canonical_trades_append_only` is enabled.

## 3. Automated verification

Dedicated P3-008 test discovery:
`PYTHONPATH=src:. python3 -m unittest discover -s tests -p 'test_p3_008*.py'`

Result:
`24 tests — OK`

Full repository regression:
`PYTHONPATH=src:. python3 -m unittest discover -s tests -p 'test*.py'`

Result:
`285 tests — OK`

CI Core:
- Run #645
- Run ID `35383756721`
- job `repository-foundation`
- job ID `105725748357`
- tested commit `fb17a034805abd219bad8fccc757fefc8faca27e`
- conclusion: SUCCESS
- P3-008 persistence/event test stage: SUCCESS
- full foundation regression: 285 tests, SUCCESS

A separate current Docker Foundation CI run was not triggered for this push event. CONTROL therefore does not claim a new Docker Foundation CI run. Local Production Docker build/recreate, migration, and runtime execution below provide the actual Docker runtime evidence.

## 4. Controlled real-data vertical slice

CONTROL executed:

`sudo docker compose --env-file .env -f infrastructure/compose/docker-compose.yml run --rm --entrypoint python api -m meylux.runtime.p3_008_vertical_slice`

The runner selected the existing governed AVAILABLE raw acquisition event:

`f12b8c638b3a2e742c88bad720ca2f6b6a5f19df4f38ab3983cdcb251fbc7d7a`

Observed validation path:
- structural = valid
- temporal = valid
- normalized = valid
- quality = VALID
- canonical_eligible = True

No fabricated, synthetic, fallback, or repaired market data was used.

## 5. Canonical persistence evidence

Observed successful persistence:

record_id:
`80349ae7db22c1b15a18020b9219ed8eaa7be80334e1444fb632463558e3a9a3`

event_id:
`3b143c10856995e0519ae2080da17d5669627fe74d0e288af1b6d5d1daf122fe`

outbox sequence:
`1`

Independent PostgreSQL read-back confirmed:
- quality_state = VALID;
- source_record_id equals the governed raw event ID;
- lineage_parent_id equals the governed raw event ID;
- deterministic identity_hash is present;
- exactly one canonical trade row exists for the verified record.

The quality log contains one corresponding record.

## 6. Event handoff evidence

The canonical outbox row was published to:
`stream:canonical:market_events`

Observed Redis stream ID:
`1789758121669-0`

The stream body contained the same canonical event_id, record_id, event type, quality state, source identity, lineage and canonical payload.

The outbox publication acknowledgement contains:
- published_at populated;
- published_stream_id = `1789758121669-0`.

The Redis idempotency key for the event exists.

## 7. Deterministic replay / duplicate evidence

CONTROL executed the same authorized vertical-slice runner a second time against the same governed raw evidence.

Observed:
- inserted = False;
- same canonical record_id;
- same outbox sequence = 1;
- published = 0.

This establishes deterministic canonical replay/idempotency without creating a duplicate canonical record or duplicate event publication.

## 8. Restart and recovery evidence

CONTROL restarted the governed api/collector/worker services and later restarted both DB and Redis through the authorized SentinelX path.

After DB/Redis restart:
- the canonical record remained present;
- quality_state remained VALID;
- the outbox publication acknowledgement remained present;
- the Redis idempotency key remained present;
- all required services returned to running/healthy state.

The persistence layer therefore retained the authoritative canonical record and event publication state across dependency restart.

Automated P3-008 integration tests also establish explicit transport failure isolation: Redis publication failure raises EventHandoffError and does not mark the database outbox event as published.

## 9. Quality, quarantine/DLQ and lineage boundary

P3-007 remains independently VERIFIED under AR-P3-007.

The final P3-008 controlled slice:
- used the real governed AVAILABLE raw evidence;
- preserved source_record_id and lineage_parent_id;
- produced explicit VALID quality state;
- promoted only canonical-eligible evidence.

P3-007 automated and verified behavior remains the authoritative quarantine/DLQ boundary. No rejected or unavailable evidence was promoted into canonical truth.

## 10. Security boundary

CONTROL independently confirmed:
- runtime canonical tables are INSERT/SELECT accessible to `meylux_app` but not UPDATE/DELETE;
- append-only trigger is enabled on canonical trades;
- migration authority remains separate from application DML;
- secret values were not placed in repository evidence or this EXEC-LOG;
- no trading, capital, custody, leverage, transfer or withdrawal functionality was introduced.

## 11. Observability / health

The controlled runner emitted explicit machine-readable stage/result output for validation, quality, persistence and event handoff.

Compose DB and Redis dependencies reported healthy during execution and after restart. The governed application services returned to running state after restart.

## 12. Scope / future-phase boundary

No Phase 4 quantitative or market-structure computation, specialist intelligence, AI interpretation, opportunity/arbitrage analysis, trading, capital control, V1 mutation or unrelated future-phase functionality was introduced.

The normalized event stream remains the P4-ready handoff boundary only.

## 13. Performance target

The architecture target of >5,000 normalization events/sec/core was not measured in this controlled slice. It is explicitly unverified and is not claimed as a P3-008 acceptance result.

## 14. Multi-symbol witness

A second-symbol production witness was not available from the governed raw acquisition staging boundary during this execution. The raw staging evidence contained one governed AVAILABLE event. CONTROL did not fabricate or manufacture a second-symbol witness. This criterion is therefore explicitly recorded as not demonstrated in the current production slice rather than falsely claimed.

## 15. Final result

The authorized P3-008 end-to-end path is established for the controlled real-data slice:

P2 staging → Validation → Normalization → Quality → Canonical persistence → Canonical event outbox → Redis normalized event stream → read-back/replay/restart evidence.

G-3 evidence is established for the tested controlled slice, subject to the explicit non-measured performance target and unavailable second-symbol witness noted above.

Final execution disposition:
`SUCCESS — G-3 EVIDENCE ESTABLISHED`

No unresolved technical blocker remains within the authorized P3-008 boundary.

Closure synchronization is now performed by CONTROL under ADR-GOVERNANCE-012.
