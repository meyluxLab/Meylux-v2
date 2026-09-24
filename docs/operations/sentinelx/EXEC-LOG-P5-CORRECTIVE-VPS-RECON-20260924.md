# EXEC-LOG-P5-CORRECTIVE-VPS-RECON-20260924

**Project:** MEYLUX V2  
**Authority:** Project Owner — Corrective VPS Reconciliation, Synchronization and Bring-Up — 2026-09-24  
**Executor:** ROL-V2-001 — CONTROL / REVIEWER  
**Mechanism:** SentinelX only  
**Host:** server-l6rf  
**Target:** /srv/meylux-v2

## 1. Historical boundary

This execution is new corrective execution. It is not retroactively attributed to TO-P5-001 or TO-P5-002. STEP-P5-002 remains COMPLETE / VERIFIED.

## 2. Pre-mutation repository baseline

- Repository: meyluxLab/Meylux-v2
- main before correction: 2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2
- Expected main after independent remote read: 2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2
- VPS deployed before correction: fb7d9847498323bec067ba98a1e2729f869c0697
- VPS working tree: clean, detached HEAD
- VPS migration files before correction: 0001–0005 only
- VPS compose file: infrastructure/compose/docker-compose.yml
- Existing compose containers were exited.

## 3. Pre-mutation VPS / DB baseline

- Docker volume: meylux-db-data
- Volume mount: /var/lib/docker/volumes/meylux-db-data/_data
- Volume data size before mutation: 75M
- Existing containers:
  - compose-api-1: Exited (137)
  - compose-worker-quant-1: Exited (137)
  - compose-collector-1: Exited (0)
  - compose-worker-ai-1: Exited (0)
  - compose-db-1: Exited (0)
  - compose-redis-1: Exited (0)
- Actual DB engine after controlled DB start: PostgreSQL 16.15
- Database: meylux
- DB migration state before correction:
  - 0001_database_foundation
  - 0002_raw_acquisition_staging
  - 0003_canonical_persistence_event_outbox
  - 0004_canonical_quality_state_alignment
  - 0005_quantitative_foundation
  - 0006_application_role_grant_hardening
- 0007_specialist_foundation was absent from the actual applied migration state.
- meylux.specialist_outputs was absent before 0007.
- Existing persisted-data baseline:
  - raw_acquisition_events: 2995
  - canonical_candles: 156
  - calculated_indicator_vectors: 3
  - market_structure_events: 1
  - market_structure_zones: 0
  - market_regime_states: 1
  - canonical_trades: 1
  - canonical_orderbook_depth: 0
  - canonical_derivatives: 0
  - volume_profile_sessions: 0
  - data_quality_logs: 157
  - canonical_event_outbox: 157

## 4. Recovery point

PostgreSQL was stopped before the recovery capture. CONTROL created a filesystem recovery archive of the protected database volume before migration/bring-up mutation.

Recovery directory:
`/var/backups/meylux-v2-p5-corrective-20260924T140710Z`

Recovery archive:
`meylux-db-data.tar`

Archive SHA-256:
`3249cfb922b2b5a40632f511ee7019ad86926dd87ad8235a37e58e95f0901c87`

A pre-correction logical data dump was also captured:

`meylux-data-pre-corrective.sql`

SHA-256:
`c2a0ee9f6756170fcb0c980afe2a35c2d61b87d0407ac7362659a2fb252adaa0`

The recovery point is therefore an actual recoverable volume state, not a nominal rollback statement.

## 5. Corrective actions actually executed

### 5.1 Repository synchronization

CONTROL fetched the current remote main reference and independently confirmed:

`origin/main = 2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2`

The VPS checkout was detached at that exact commit.

After synchronization the VPS contained:
- migrations 0001 through 0007;
- current governed compose configuration;
- current repository source.

Compose SHA-256 on the VPS:
`af8f44b6ad9b6255bacfa17e51168cb8fd73e2666d4feb2bddda036a49148880`

### 5.2 Migration reconciliation and application

Actual DB state was checked first. The database had 0001–0006 applied and 0007 absent.

Repository migration `migrations/versions/0007_specialist_foundation.sql` was verified as the next migration. Its VPS SHA-256 at execution:
`3a97f9539fc12d007f6501eb71668a65af1e72ef69f6f1238bec3b67cb143eff`

The migration was applied with ON_ERROR_STOP=1 and completed:
- SET
- CREATE TABLE
- CREATE INDEX
- trigger creation
- GRANT
- REVOKE
- GRANT
- schema_migrations INSERT 0 1

No 0001–0006 migration file was modified.

### 5.3 Controlled bring-up

The existing governed compose stack was brought up using the repository compose definition and existing /srv/meylux-v2/.env configuration. Images were rebuilt from the synchronized repository source; no new service or topology was introduced.

Final runtime:
- compose-api-1: running
- compose-collector-1: running
- compose-worker-quant-1: running
- compose-worker-ai-1: running
- compose-db-1: running / healthy
- compose-redis-1: running / healthy

Redis real probe returned PONG.

Foundation service logs reported successful startup for collector and worker-ai. No startup error was observed in the final service log checks.

## 6. Database / schema / privilege verification

Final migration state is exactly 0001 through 0007.

`meylux.specialist_outputs` exists and is empty, as expected; no fabricated specialist output was inserted.

Verified P5 foundation privileges for `meylux_app`:
- SELECT: true
- INSERT: true
- UPDATE: false
- DELETE: false
- TRUNCATE: false

The append-only trigger `trg_specialist_outputs_append_only` is enabled.

Application-role runtime connectivity was independently exercised from compose-api-1:
- current_user = meylux_app
- current_database = meylux
- canonical_candles = 156
- specialist_outputs = 0

## 7. Data preservation

Final existing-data counts exactly match the pre-correction baseline.

A pre-correction logical data dump and post-correction dump of all existing data excluding the newly added schema_migrations/specialist_outputs state were normalized for pg_dump-generated transient tokens/comments and compared byte-for-byte.

Result:
`DATA_PRESERVATION_DUMP_COMPARE=IDENTICAL`

Normalized SHA-256 for both:
`b3d650edb7c6d4aedc39948ec57072294a0e9cd30ec5e11038baed95b71d6`

The post-correction existing-data dump was separately retained:
`meylux-data-post-existing.sql`

Raw post-dump SHA-256:
`02fb6c62848110228536f22a1aa735d3523d27404a2fbcceaea01cc3f3d20676`

No truncation, destructive recreation, volume replacement, reset, or cleanup was performed.

## 8. Re-execution / idempotency evidence

CONTROL safely re-executed the exact repository 0007 migration after its successful first application.

Observed:
- CREATE TABLE completed with existing-relation notice;
- CREATE INDEX completed with existing-relation notice;
- schema_migrations INSERT 0 0;
- migration state remained exactly 0001–0007;
- specialist_outputs row count remained 0;
- canonical_candles remained 156;
- raw_acquisition_events remained 2995.

This establishes safe repeat behavior for the authorized migration path without manufacturing data.

## 9. AVAILABLE_PERSISTED determination

The runtime/database availability gap itself is resolved: the authoritative VPS database is running and the persisted P4 tables are queryable with real data.

However, **AVAILABLE_PERSISTED is NOT established for the P5 authoritative Snapshot facts.**

Reason: the P5-002 Fact Requirements Matrix requires an explicit authoritative `knowledge_time` for persisted facts. The inspected P4 persistence families expose `event_time` and/or `persisted_at` / `logged_at`, but do not expose a dedicated `knowledge_time` column. CONTROL therefore does not substitute event/persistence timestamps for knowledge_time.

Current disposition remains:
- runtime persistence reachable: YES
- persisted source records physically present: YES
- P5 authoritative AVAILABLE_PERSISTED claim: NONE
- USR-03 disposition: UNAVAILABLE_DISPOSITIONED
- governing issue: OQ-P5-002-PRQ1-FACT-AVAILABILITY and related PRQ OQs

This is a semantic upstream evidence boundary, not a VPS outage.

## 10. Scope / architecture integrity

No:
- STEP-P5-003 activation;
- specialist execution;
- Futures/Forex implementation;
- provider credential change;
- architecture/canonical-contract change;
- 0001–0006 modification;
- trading/capital/custody activity;
- destructive DB operation;
- unrelated cleanup;
- historical retroactive attribution.

## 11. Final execution state

VPS repository revision: 2ed8aad3c1353801ab1ea68b2a8e953ecaf258e2  
DB migration head: 0007_specialist_foundation  
Compose stack: running; DB and Redis healthy  
Protected DB volume: preserved  
Existing data: preserved by normalized logical dump comparison  
P5 specialist_outputs: present, empty  
P5 authoritative AVAILABLE_PERSISTED: not established  
Next project action: governed separately; STEP-P5-003 remains NOT AUTHORIZED
