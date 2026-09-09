# MEYLUX V2 — CONTROL V2 VPS FOUNDATION EXECUTION TASK ORDER

## TO-GOV-005 — V2 VPS Foundation Deployment & Verification

**Task Order ID:** `TO-GOV-005`
**Governance Class:** Post-Freeze Governance / Authorized V2 Environment Execution
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Executor:** CONTROL / REVIEWER (`ROL-V2-001`)
**Status:** `AUTHORIZED TO EXECUTE`
**Authority:** `ADR-GOVERNANCE-010` + `ADR-GOVERNANCE-011` + `AR-GOV-004` + Project Owner direction
**Target:** Dedicated Meylux V2 VPS only; target identity is established and authenticated through the governed execution context and is not duplicated here as a credential or secret.

## 1. Objective

Establish, execute, evidence, and separately verify the physical V2 VPS foundation required to run the already implemented and independently verified Phase 1 foundation on the dedicated V2 server.

This Task Order exists specifically to close the gap between repository/CI verification and real V2 VPS execution evidence. It does not reopen `STEP-P1-001`, `STEP-P1-002`, or `STEP-P1-003`, does not alter their historical states, and does not authorize implementation of `STEP-P1-004` or any later Step.

The objective is a reproducible, traceable, repository-aligned V2 runtime foundation with explicit evidence for every material operational stage.

## 2. Governing Principles

1. GitHub and governed repository artifacts are the durable Source of Truth.
2. No command, configuration, migration invocation, health endpoint, secret mechanism, firewall change, Python dependency procedure, image reference, or runtime behavior may be invented from general knowledge when the repository can establish the authoritative project-specific behavior.
3. Before each operational stage, CONTROL shall inspect the relevant authoritative repository artifact(s) and derive the exact operation from those sources.
4. A technically reasonable command that conflicts with an authoritative Meylux V2 contract is not permitted.
5. Actual execution state is never inferred from design, CI, chat, or previous VPS assumptions.
6. `IMPLEMENTED != EXECUTED != VERIFIED`.
7. Every material completed execution section shall have repository evidence committed according to the established Git history and artifact protocol, without fabricating runtime evidence.
8. Secrets and credentials shall never be written into this Task Order, repository artifacts, ordinary evidence, or EXEC-LOGs.
9. V1 remains completely outside scope.
10. No trading, order execution, capital movement, leverage, custody, withdrawal, provider-runtime, or market activity is authorized.
11. No destructive whole-host action is authorized as ordinary execution or recovery.
12. Any architecture, governance, security, authority, scope, or contract conflict is `R4`: stop the affected part, preserve evidence, and escalate.

## 3. Lifecycle Boundary

The following remain unchanged:

- `STEP-P1-001` — Repository Foundation: `COMPLETE / VERIFIED`
- `STEP-P1-002` — Docker Foundation: `COMPLETE / VERIFIED`
- `STEP-P1-003` — Database Foundation: `COMPLETE / VERIFIED`
- `STEP-P1-004` — Data Contracts: `ACTIVE / IN PROGRESS` under `TO-P1-004`

This Task Order is an operational execution boundary and must not be used to silently change any Phase/Step lifecycle state.

`CURRENT_CHECKPOINT.json` shall not be changed merely because this Task Order is issued or because an individual command succeeds. State updates require actual evidence and the applicable verification decision.

## 4. Execution Model

The execution is divided into the following controlled sections. Each section has its own evidence boundary and repository history boundary.

```text
A  Target / Host Baseline
B  OS Prerequisites
C  Git / Repository State
D  Python / Runtime Prerequisites
E  Docker Engine / Compose
F  Configuration / Secret Provisioning
G  Compose Validation
H  Image Pull / Build
I  Database + Redis Startup
J  Database Foundation Execution
K  Application Runtime Startup
L  Network / Security Verification
M  Persistence / Restart Verification
N  Runtime Health / Observability
O  Repository ↔ VPS Consistency
P  Execution Evidence / EXEC-LOG
Q  Separate CONTROL Verification
R  Governance State Update
```

A section is not considered complete merely because its command returned zero. Completion requires the evidence defined by the section and repository recording where required.

## 5. Section A — Target / Host Baseline

Establish a before-change baseline of the authenticated target.

Required observations include, as applicable:

- hostname and target identity;
- operating system and kernel;
- architecture;
- CPU and RAM;
- disk/filesystem/inode capacity;
- uptime and system time/time synchronization;
- mounted filesystems;
- listening ports;
- relevant users/groups;
- relevant installed packages;
- `/opt` and `/srv` state;
- Docker state;
- Git state;
- Python state;
- SentinelX service/identity state relevant to the execution path.

Explicitly confirm the target is the dedicated V2 VPS and not the frozen V1 environment.

No application deployment occurs in this section.

**Section evidence:** baseline observations and target-isolation evidence.

**Repository boundary:** commit the completed baseline evidence/reference artifact before proceeding to Section B, using the established repository artifact convention and a commit message that identifies `TO-GOV-005`.

## 6. Section B — OS Prerequisites

Bring the host to the minimum OS prerequisite state required by the authoritative V2 runtime/deployment artifacts.

Before changing the host, inspect the authoritative environment/runtime documentation and repository configuration to determine exactly which prerequisites are required.

Required checks include, as applicable:

- package repository availability;
- package metadata freshness;
- required system packages;
- time synchronization;
- disk/inode headroom;
- RAM/swap state;
- host resource suitability.

Do not install unrelated packages. Do not create swap or alter firewall policy unless an authoritative requirement and this Task Order explicitly establish that operation as in scope.

**Section evidence:** actual package/version changes, outputs, exit codes, and final prerequisite state.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section C.

## 7. Section C — Git / Repository State

Prepare the V2 repository on the target without modifying source content.

Before execution, inspect the authoritative repository state and checkpoint to establish the permitted deployment/version context. `CURRENT_CHECKPOINT.json` is authoritative for its recorded `last_verified_commit`; it must not be confused with Repository HEAD.

Required operations include, as applicable:

- verify Git;
- establish the official repository `meyluxLab/Meylux-v2`;
- create the approved V2 checkout location;
- clone/fetch the repository;
- select the authorized branch/commit state;
- verify remote, branch, commit, and clean status;
- verify required repository structure.

No source, architecture, registry, checkpoint, or contract file may be modified as a side effect of deployment.

**Section evidence:** exact repository/version context and clean-state evidence.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section D.

## 8. Section D — Python / Runtime Prerequisites

Determine the exact host-side Python requirement from authoritative repository artifacts before installing or changing anything.

The repository currently establishes the project Python range as `>=3.12,<3.14`; the existing host Python must be validated against that contract.

Determine from authoritative artifacts whether any host-level Python environment is actually required. Do not install application dependencies on the host merely because Python exists if the V2 runtime contract is containerized.

**Section evidence:** Python/pip/runtime prerequisite state and provenance of any installed host dependency.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section E.

## 9. Section E — Docker Engine / Compose

Install and configure Docker only according to the authoritative V2 deployment requirements for Ubuntu 24.04.

Required outcomes include:

- Docker Engine installed at an acceptable supported version;
- Compose plugin available;
- Docker daemon active and enabled where required;
- daemon functionality verified;
- storage/resource state recorded;
- no unintended public Docker API exposure;
- baseline Docker network/resource state recorded.

Exact installation commands and package source shall be derived from authoritative repository/project deployment requirements before execution.

**Section evidence:** actual installation/version/service/network/storage evidence.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section F.

## 10. Section F — Configuration / Secret Provisioning

Establish only the configuration required by the authoritative V2 runtime contract.

Before provisioning, inspect:

- `.env.example` or equivalent;
- Compose configuration;
- application configuration modules;
- environment manifest;
- approved secret-handling mechanism;
- any relevant security/governance artifacts.

Determine exactly:

- required non-secret configuration;
- required secrets;
- secret source/provisioning mechanism;
- file locations;
- ownership and permissions;
- environment-specific values;
- configuration precedence.

Secrets must never be committed to GitHub or included in evidence. Do not print secret values in command output.

The known `ENVIRONMENT_MANIFEST.yaml` authority wording discrepancy regarding physical execution must be treated as a governance reconciliation item; it must not be silently rewritten during deployment.

**Section evidence:** configuration provenance, non-secret values where safe, permission/ownership evidence, and secret-presence evidence without secret values.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section G.

## 11. Section G — Compose Validation

Using the repository-authoritative Compose configuration, validate the intended topology before startup.

Required verification includes, as applicable:

- services: `db`, `redis`, `api`, `collector`, `worker-quant`, `worker-ai`;
- network: `meylux-net`;
- database volume: `meylux-db-data`;
- image references and pins;
- environment interpolation;
- dependency configuration;
- published ports;
- absence of unintended DB/Redis public exposure.

The exact validation command shall be derived from the repository's authoritative deployment artifacts.

**Section evidence:** actual validated Compose output and relevant configuration checks.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section H.

## 12. Section H — Image Pull / Build

Obtain and build only the images required by the authoritative Compose/runtime definition.

The current repository baseline includes pinned foundation images such as:

- `python:3.12.11-slim`
- `timescale/timescaledb:2.29.2-pg16`
- `redis:7.4.6-alpine`

These values must be re-read from the authoritative repository state at execution time rather than treated as an independent source of truth.

Record actual image identifiers/digests where available and reliable.

**Section evidence:** pull/build results, image inventory, IDs/digests/tags, failures and remediation.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section I.

## 13. Section I — Database + Redis Startup

Start the foundation services according to authoritative Compose dependencies.

Required verification:

- `db` container state;
- PostgreSQL readiness;
- `redis` container state;
- Redis readiness;
- Docker network connectivity;
- absence of restart loops;
- relevant logs.

Do not proceed merely because containers are in `running` state if readiness checks fail.

**Section evidence:** actual service state/readiness/log evidence.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section J.

## 14. Section J — Database Foundation Execution

Execute the database foundation on the real V2 VPS using the exact migration mechanism defined by the authoritative repository artifacts.

No migration command may be guessed.

Required verification includes, as applicable:

- PostgreSQL version;
- TimescaleDB extension/version;
- migration harness behavior;
- migration `0001_database_foundation`;
- `meylux` schema;
- `meylux.schema_migrations`;
- roles `meylux_admin`, `meylux_app`, `meylux_backup`;
- privilege boundaries;
- UTC configuration;
- migration state consistency;
- no unintended schema drift.

The CI evidence for P1-003 is historical implementation/CI evidence. It is not substituted for actual V2 VPS execution evidence.

**Section evidence:** actual database queries/outputs, migration result, role/privilege verification, and exit codes without exposing credentials.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section K.

## 15. Section K — Application Runtime Startup

Only after Sections I and J establish a healthy foundation, start the application services according to authoritative Compose/runtime configuration.

Required services:

- `api`
- `collector`
- `worker-quant`
- `worker-ai`

Required verification includes:

- successful startup;
- DB connectivity;
- Redis connectivity;
- internal service DNS behavior;
- absence of crash/restart loops;
- startup logs;
- service health checks where the repository defines them.

No market/provider runtime or trading activity is authorized merely by starting these foundation services.

Exact health endpoint/path, if any, must be obtained from authoritative repository artifacts; it must not be invented.

**Section evidence:** service status, connectivity, logs, and health evidence.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section L.

## 16. Section L — Network / Security Verification

Verify the runtime security boundary without introducing unapproved security changes.

Required checks include:

- host listening ports;
- Docker published ports;
- DB non-public exposure;
- Redis non-public exposure;
- application exposure exactly as authorized by the runtime contract;
- firewall state;
- SentinelX execution boundary;
- sensitive file permissions;
- absence of credentials/tokens in logs.

Firewall modifications are not authorized merely because a hardening improvement seems desirable. Any required change must be traceable to an authoritative requirement and remain within this Task Order.

**Section evidence:** actual network/security observations.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section M.

## 17. Section M — Persistence / Restart Verification

Verify that the authoritative database persistence boundary survives controlled service restart.

Required checks include:

- existence of `meylux-db-data`;
- controlled DB restart;
- readiness after restart;
- persistence of the verified foundation state;
- cleanup of any temporary verification-only state.

No destructive volume recreation is permitted as a shortcut.

**Section evidence:** before/after state and persistence result.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section N.

## 18. Section N — Runtime Health / Observability

Perform a consolidated runtime health review.

Required observations include:

- CPU;
- RAM;
- disk;
- Docker storage;
- container health;
- logs;
- restart counts/loops;
- resource pressure;
- obvious queue/stream growth where relevant to the currently deployed foundation;
- absence of unexplained errors.

Do not promote observed runtime behavior into architecture or permanent configuration without the appropriate governance process.

**Section evidence:** actual health/resource/log observations.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section O.

## 19. Section O — Repository ↔ VPS Consistency

Perform final consistency checks between the deployed V2 state and the authoritative repository.

Required verification includes:

- exact deployed Git commit;
- branch/remote state;
- Compose source/version;
- configuration provenance;
- image provenance;
- migration/version state;
- absence of uncommitted source changes;
- no accidental V1 dependency;
- no unapproved runtime artifact outside the defined V2 environment boundary.

**Section evidence:** repository/runtime consistency record.

**Repository boundary:** commit the completed section evidence/reference artifact before proceeding to Section P.

## 20. Section P — Execution Evidence / EXEC-LOG

Create the actual repository-backed EXEC-LOG for `TO-GOV-005`.

The record must include the minimum fields required by the Artifact Protocol:

```text
execution_id
task_id
step_id
target
executor_role
start_time_utc
end_time_utc
actions
commands
outputs
exit_codes
failures
diagnosis
remediation
retries
final_result
evidence_references
escalation_status
authorization_reference
verification_reference
repository/version_context
```

Only actual runtime values may be recorded.

Conditional recovery classes R0–R4 must be recorded as `not exercised` when no genuine triggering condition occurred; failures must never be manufactured.

**Repository boundary:** EXEC-LOG is committed after actual execution evidence is complete and before verification.

## 21. Section Q — Separate CONTROL Verification

Execution completion is not verification.

CONTROL shall separately verify, using the actual evidence:

1. target identity;
2. execution authorization;
3. OS baseline;
4. Docker/Compose;
5. repository/version state;
6. configuration/secret boundary;
7. database migration/schema/roles/privileges/UTC;
8. Redis foundation;
9. application service runtime;
10. network/security boundary;
11. persistence;
12. resource/health state;
13. repository ↔ VPS consistency;
14. prohibited-activity absence;
15. completeness and integrity of EXEC-LOG.

Verification result must be separately recorded and must not be inferred from successful execution alone.

**Repository boundary:** commit the verification artifact/result after the verification decision.

## 22. Section R — Governance State Update

Only after execution and separate verification are complete may the applicable governance records be updated.

Potential outcomes are evidence-dependent:

- `EXECUTED`
- `EXECUTED WITH DEVIATIONS`
- `FAILED`
- `PARTIALLY EXECUTED`

Verification is separately one of:

- `VERIFIED`
- `VERIFIED WITH ACCEPTED DEVIATIONS`
- `NOT VERIFIED`

`CURRENT_CHECKPOINT.json`, registry state, and/or change ledger shall be changed only where the applicable verified governance transition requires it. Historical P1-001/002/003 states must remain intact.

No state shall be promoted merely because the intended commands were prepared or because a CI workflow passed.

## 23. Commit Discipline

For every completed major execution section:

```text
Complete section
→ capture actual evidence
→ create/update the appropriate repository evidence artifact
→ review for secret leakage / unsupported claims
→ commit to main through the established repository workflow
→ record commit SHA in the execution/evidence chain
→ proceed to next section
```

A commit is a historical record, not proof that the underlying runtime operation succeeded. Runtime evidence and verification remain mandatory.

If repository history contains concurrent changes, stale content, or an authorization conflict, preserve the existing history and resolve through the established governance mechanism; do not force-overwrite or rewrite history.

## 24. Recovery / Failure Handling

Use the existing governed R0–R4 boundaries from `ADR-GOVERNANCE-010`:

- R0: bounded transient recovery;
- R1: ordinary bounded operational recovery within scope;
- R2: bounded configuration/environment remediation only when authorized, non-architectural, and in scope;
- R3: implementation defect → Producer correction; CONTROL does not silently rewrite Producer implementation;
- R4: architecture/governance/security/authority/scope conflict → stop affected part, preserve evidence, escalate.

Do not manufacture failures to exercise recovery paths.

## 25. Explicit Non-Authorization

This Task Order does NOT authorize:

- reopening `STEP-P1-001`, `STEP-P1-002`, or `STEP-P1-003`;
- implementation of `STEP-P1-004` or later Phase 1 Steps;
- Phase 2+ functionality;
- V1 access or mutation;
- market/provider runtime activity;
- trading or order execution;
- capital movement, custody, withdrawals, deposits, or leverage;
- architectural redesign;
- silent contract/schema/interface changes;
- speculative Stable IDs;
- secret publication;
- destructive whole-host reset/rebuild;
- firewall/security changes outside authoritative scope;
- using Redis as durable Source of Truth;
- treating CI as a substitute for real VPS execution evidence.

## 26. Required Final Evidence Chain

The minimum final chain for this operational boundary is:

```text
TO-GOV-005
→ Section Evidence / Repository Commits
→ EXEC-LOG
→ Separate CONTROL Verification
→ Governance State Update
```

Where a repository evidence artifact is required by the existing artifact protocol, it shall be created using the existing identity/path conventions rather than inventing a parallel artifact class.

## 27. Completion Boundary

`TO-GOV-005` is not complete merely because Docker starts, the repository is cloned, or the application containers become healthy.

Completion requires the full authorized scope to have been executed or explicitly recorded as not executed/failed, actual evidence to exist, the EXEC-LOG to be complete, and separate CONTROL verification to have been performed.

The final result must state exactly what is and is not established on the physical V2 VPS.
