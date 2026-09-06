# Meylux V2 — Artifact Protocol

Status: Draft — Phase 0 Operational Clarification

## Official artifact chain

`TASK-ORDER (TO) → BUILD-REPORT (BR) → AUDIT-REPORT (AR) → EXEC-LOG (EL) → CHECKPOINT (CHK)`

## Rules

1. Every official artifact has a stable ID.
2. Artifact content is not authoritative merely because it appears in chat.
3. Approved artifacts and verified evidence are recorded in the repository.
4. No silent edits.
5. Anything not actually executed is explicitly marked unverified or not executed.

## Phase 0 Operational Artifact Convention

For Producer Build Reports, the governed identity/path convention is:

- Stable ID form: `BR-P<phase>-<sequence>`.
- Phase 0 instance for `TO-P0-001`: `BR-P0-001`.
- Repository path: `docs/build-reports/BR-P0-001.md`.
- The Build Report is produced by the Producer and remains `NOT YET PRODUCED` until the actual report is created and its contents are truthful and traceable.
- This operational convention does not ratify the Master Architecture, close any Gate, or authorize runtime implementation.
