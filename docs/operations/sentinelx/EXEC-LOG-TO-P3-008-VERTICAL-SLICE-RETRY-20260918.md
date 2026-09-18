# EXEC-LOG-TO-P3-008-VERTICAL-SLICE-RETRY-20260918

**Task Order:** TO-P3-008 Revision 1.1
**Role:** ROL-V2-001 — CONTROL / REVIEWER
**Host:** server-l6rf / host_3774c70bc3624713
**VPS repository:** /srv/meylux-v2
**Execution date:** 2026-09-18
**Boundary:** authorized Production vertical-slice re-execution after Producer JSONB correction

## Repository synchronization

CONTROL merged PR #29 and synchronized the VPS repository to main. The repository was then corrected to restore the verified JSONB correction implementation from the Producer-validated state.

Current VPS repository HEAD at execution: `9e39d1032a8dc63fe49217ad25ef0fdc430b375d`.

The restored implementation content was limited to the previously Producer-validated JSONB correction files:
- `src/meylux/runtime/p3_008_vertical_slice.py`
- `tests/test_p3_008_persistence.py`

The Build Report remained the corrected Producer artifact.

## Deployment and database

CONTROL executed:
- Compose image rebuild with `--build --force-recreate`;
- all six governed Compose services recreated successfully;
- database and Redis health checks passed;
- migrations 0001, 0002 and 0003 were re-executed idempotently;
- migration result: `database migration: PASS`.

No secret values were recorded.

## Vertical-slice execution

The first attempted command without an entrypoint override demonstrated the image ENTRYPOINT is the foundation service boundary and therefore did not execute the requested runner. This was diagnosed from the Dockerfile and running-container logs; no acceptance evidence was attributed to that invocation.

CONTROL then executed the authorized runner with an explicit Python entrypoint:

`sudo docker compose --env-file .env -f infrastructure/compose/docker-compose.yml run --rm --entrypoint python api -m meylux.runtime.p3_008_vertical_slice`

The runner reached the corrected JSONB reconstruction path, confirming the former `TypeError: payload must be a mapping` defect was not the observed failure at this boundary.

A new runtime failure occurred at quality-signal construction:

`AttributeError: 'ValidationResult' object has no attribute 'result'`

The failing expression is in `src/meylux/runtime/p3_008_vertical_slice.py`:

`outcome.result.value`

The actual `outcome` object returned by `validation_outcome(...)` is a `ValidationResult` and does not expose a nested `result` attribute.

## Disposition

This is a new Producer-owned implementation/runtime defect. It is distinct from:
1. the corrected Docker `contracts` packaging defect;
2. the prior zero-row acquisition condition;
3. the corrected PostgreSQL jsonb-to-Mapping defect.

No synthetic/fabricated/fallback market data was introduced.

Canonical persistence, canonical read-back, event receipt, runtime failure/recovery verification and G-3 were not established by this execution.

**Current state:** `STEP-P3-008 = ACTIVE / CORRECTION REQUIRED`
**G-3:** `NOT ESTABLISHED`

CONTROL stops at the natural independent-correction boundary under ADR-GOVERNANCE-013 Rule 1(C).