# MEYLUX V2 — CONTROL Verification — TO-GOV-005

**Task Order:** `TO-GOV-005`
**Execution ID:** `exec-gov-005-20260909T213904Z`
**Verifier:** `ROL-V2-001` — CONTROL / REVIEWER
**Target:** dedicated V2 VPS `server-l6rf`; Host ID `host_3774c70bc3624713`
**Verification time UTC:** `2026-09-09T22:32:16Z`
**Repository/version verified:** `main` / `258e3cccea3fd024294e5c86d56ff070a6cd1cb8`

## Verification Boundary

This is a separate CONTROL verification of the actual TO-GOV-005 VPS execution. It does not reopen P1-001, P1-002, or P1-003; it does not implement P1-004; it does not authorize later Steps; it does not modify V1; and it does not authorize market/provider/trading/capital activity.

## Verification Results

1. **Target identity — PASS**
   - Fresh SentinelX execution resolved target hostname `server-l6rf`.
   - Host ID matched the authorized V2 target.

2. **Execution authorization — PASS**
   - Execution log cites `TO-GOV-005`, `ADR-GOVERNANCE-010`, `ADR-GOVERNANCE-011`, `AR-GOV-004`, and Project Owner direction.

3. **OS baseline — PASS**
   - Ubuntu 24.04 LTS, x86_64, 4 vCPU, 15 GiB RAM.
   - Adequate disk/inode headroom and active time synchronization were established.

4. **Docker / Compose — PASS**
   - Docker `29.8.0`; Compose `v5.5.1`.
   - All six repository-defined services are running.
   - DB and Redis report healthy.

5. **Repository/version state — PASS**
   - `HEAD == origin/main == 258e3cccea3fd024294e5c86d56ff070a6cd1cb8`.
   - Working tree clean.
   - Remote is the official `meyluxLab/Meylux-v2` repository.

6. **Configuration / secret boundary — PASS**
   - `.env` exists only as execution-local foundation configuration, is root-owned mode `600`, and `git ls-files .env` returned zero entries.
   - Secret values were not printed or recorded.
   - No matching secret-bearing log pattern was found in the consolidated runtime logs.

7. **Database foundation — PASS**
   - PostgreSQL `16.15`.
   - TimescaleDB `2.29.2`.
   - `meylux` schema present.
   - `0001_database_foundation` present in `meylux.schema_migrations`.
   - Application role has schema USAGE and migration-table SELECT, while INSERT/UPDATE/DELETE on `schema_migrations` are false.
   - Database timezone `UTC`.

8. **Redis foundation — PASS**
   - Redis readiness returned `PONG`.
   - Redis is attached to `meylux-net`.

9. **Application runtime — PASS within current implementation boundary**
   - `api`, `collector`, `worker-quant`, and `worker-ai` are running.
   - Internal DNS from the API container resolved `db` and `redis`.
   - TCP connectivity from the API container to `db:5432` and `redis:6379` passed.
   - The current repository runtime entrypoint is explicitly a minimal foundation process; no claim is made that it implements later API, collection, worker, market, or database functionality.

10. **Network/security boundary — PASS**
    - No published host ports were present for API, collector, or workers.
    - DB and Redis were not published to host ports; only container ports `5432/tcp` and `6379/tcp` were exposed internally.
    - UFW was inactive; no unapproved firewall change was made.
    - SentinelX authenticated root context was confirmed without exposing credential material.

11. **Persistence / restart — PASS**
    - `meylux-db-data` exists and is used by the DB service.
    - Controlled DB restart completed successfully.
    - After restart, migration marker, UTC timezone, and TimescaleDB extension state remained present.

12. **Runtime health / resources — PASS**
    - All six services remained running.
    - DB and Redis healthy.
    - Restart counts were zero at verification snapshot.
    - Resource usage remained low at observation.
    - Docker storage inventory showed active project resources with no reclaimable container/image/volume residue.

13. **Repository ↔ VPS consistency — PASS**
    - Deployed repository commit matches `origin/main`.
    - Compose source is the repository checkout.
    - Runtime environment file is external to Git tracking.
    - No V1 dependency or V1 mutation observed.

14. **Prohibited activity absence — PASS**
    - No V1 activity, market/provider runtime activity, trading, capital movement, withdrawal, order execution, or leverage activity occurred.

15. **EXEC-LOG integrity — PASS**
    - The execution log records actual successes, the two genuine operational failures and their remediation, non-exercised recovery classes, and the separation between execution and verification.
    - No secret values are recorded.

## Known Design Considerations / Non-Blocking Observations

- The Redis container logged the upstream `vm.overcommit_memory` recommendation. No host sysctl change was made because it was not an authorized requirement of this execution boundary.
- TimescaleDB initialization emitted an informational version notice during startup; the running extension was verified as `2.29.2`, matching the authoritative image tag.
- The initial host-side invocation of `migrate.sh` failed because `psql` is intentionally not installed on the host; the unchanged authoritative harness was correctly executed inside the DB container, where its required PostgreSQL client exists.

These observations do not invalidate the completed V2 foundation verification.

## Final Verification Decision

**CONTROL VERIFICATION = PASS**

TO-GOV-005 physical V2 VPS foundation execution is independently verified at this boundary.

This verification does **not** change Phase/Step lifecycle state. `CURRENT_CHECKPOINT.json` remains unchanged until the applicable governance state update is performed from this verified evidence.
