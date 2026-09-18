# EXEC-LOG-TO-P3-008-VERTICAL-SLICE-RETRY-20260918-VALIDATION-FOLLOWUP

- Role: CONTROL / REVIEWER
- Task Order: TO-P3-008 Revision 1.1
- Host: server-l6rf / host_3774c70bc3624713
- Repository: /srv/meylux-v2
- Repository commit executed: 737e2b557cd1db0f8ed3ab5e228d51ff0aeb3032
- PR #31 merged by CONTROL as 737e2b557cd1db0f8ed3ab5e228d51ff0aeb3032

## Deployment
CONTROL synchronized the VPS to the merged main commit, rebuilt the api/collector/worker-quant/worker-ai images, and force-recreated those services. Database and Redis dependencies reported healthy.

The repository migration harness initially could not run on the host because psql is not installed there. CONTROL therefore executed the same governed migration harness inside the authorized db container, with the compose-provided database environment. Migrations 0001/0002/0003 completed and the harness reported database migration: PASS.

## Vertical-slice execution
CONTROL executed the authorized runner with the explicit Python entrypoint:
sudo docker compose --env-file .env -f infrastructure/compose/docker-compose.yml run --rm --entrypoint python api -m meylux.runtime.p3_008_vertical_slice

The runner progressed through raw event reconstruction; structural validation = valid; temporal validation = valid; normalization = valid; quality = VALID; canonical_eligible = True.

Observed raw event: f12b8c638b3a2e742c88bad720ca2f6b6a5f19df4f38ab3983cdcb251fbc7d7a.

The runner then failed at canonical persistence with asyncpg.exceptions.CheckViolationError: new row for relation canonical_trades violates check constraint canonical_trades_quality_state_check.

The failing row carried quality_state = VALID. The deployed/authoritative migration constraint is quality_state = 'valid', while the authoritative DataQualityState.VALID enum value is 'VALID'. The persistence path passes record.quality_state.value directly to the database.

## Classification
IMPLEMENTATION DEFECT — CONFIRMED.

This is a repository/schema boundary mismatch. It is not a stale-image or deployment-version discrepancy: the VPS was synchronized to 737e2b557cd1db0f8ed3ab5e228d51ff0aeb3032 and images were rebuilt before execution. It is not an authoritative contract conflict: contracts/data_quality.py defines DataQualityState.VALID = 'VALID', while the SQL check is an implementation constraint that does not accept that authoritative value.

No canonical row was inserted by this failed attempt; the database rejected the insert before commit. No event handoff or G-3 evidence was established. No synthetic/fabricated/fallback market data was used.

## Disposition
STEP-P3-008 remains ACTIVE / CORRECTION REQUIRED. The natural correction boundary is returned to Producer. The bounded correction must align the persistence/schema boundary with the authoritative quality-state contract without weakening append-only/quality rules, include deterministic regression coverage for the integration boundary, produce fresh CI, update BR-P3-008, and return the result to CONTROL.

No Production, G-3, Checkpoint closure, registry closure, or Phase-3 lifecycle closure is claimed by this execution.