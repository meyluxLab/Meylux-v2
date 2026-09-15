# MEYLUX V2 — CROSS-AI BOOTSTRAP

YOU ARE ENTERING AN EXISTING GOVERNED MEYLUX V2 PROJECT.

DO NOT START NEW WORK IMMEDIATELY.

FIRST RECONSTRUCT THE PROJECT STATE FROM THE AUTHORITATIVE REPOSITORY.

## Operating rules

1. Treat the GitHub repository and governed repository artifacts as the durable Source of Truth.
2. Do not use hidden chat memory, prior-AI identity, or user recollection as authoritative project state.
3. Read only the minimum bootstrap artifacts listed in the Continuation Package before requesting clarification.
4. Do not reopen completed Pre-Project work or closed Phase 0 work.
5. Do not invent architecture, Stable IDs, task IDs, execution evidence, verification evidence, or runtime state.
6. Do not activate future work merely because continuation material describes it; activate only when the current repository state and established authority authorize it.
7. Preserve the existing Reviewer / Producer / Operator governance model and all established role boundaries.
8. If authoritative repository state is internally consistent and the next action is already authorized, CONTINUE.
9. If a genuine repository/package conflict exists, report it concisely and stop only the affected action. Do not independently reconcile or redesign it.
10. Distinguish information needed to understand state from information needed to execute the next task.
11. Ask the user only for information that cannot be established from authoritative artifacts and is genuinely required for the next authorized action.
12. Role Familiarization establishes understanding only; it never grants authorization.

## First action

Read, in order:

1. `docs/continuity/MEYLUX_V2_TRANSFER_STATE.yaml`
2. `docs/state/CURRENT_CHECKPOINT.json`
3. `docs/governance/AI_CONTINUATION_PROTOCOL_V2.md`

### Role Governance Context

When a role is declared, first complete Role Familiarization for that role. For PROJECT GUIDE, read the canonical PROJECT GUIDE Role Contract before continuing project-state analysis.

Role Familiarization is a prerequisite to Continuity Reconstruction. It establishes role identity, responsibility, authority boundaries, and interaction boundaries; it does not grant authority or replace project authorization.

4. `docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md` when `PROJECT GUIDE` / `ROL-V2-008` is declared
5. Applicable other Role Contract / Role Definition artifacts and required Shared Role Boundary documents for the declared role and required interactions

### Role Identity Discovery

After Role Familiarization, read the authoritative Role Registry records:

6. `docs/registry/artifacts.yaml`

The authoritative PROJECT GUIDE identity is:

```text
PROJECT GUIDE
Stable ID: ROL-V2-008
Role Contract: docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md
Canonical Chat: MEYLUX V2 — PROJECT GUIDE
```

Role identity is independent of chat name, filename, repository path, or model identity. The Role Registry remains authoritative for Stable ID and role-to-artifact mapping.

The AI must confirm that it has completed Role Familiarization by reading the applicable Role Contract / Role Definition, required Shared Role Boundary artifacts, and the Role Registry before continuing project-state analysis.

### Remaining Project Context

Continue reading:

7. `docs/governance/ARTIFACT_PROTOCOL_V2.md`
8. `docs/architecture/MASTER_ARCHITECTURE_V2.md`
9. `docs/state/OPEN_QUESTIONS.yaml`
10. `docs/state/DEFERRED_DECISIONS.yaml`
11. Relevant ADRs / ACRs when required by the current task or role context, including `ADR-GOVERNANCE-013` when standing role operating rules are applicable
12. Phase-specific execution/continuity reports discoverable from the authoritative Registry and/or phase directory, for every completed or currently relevant Phase. These reports MUST be read when present, even when their filenames were not supplied externally.
13. Latest approved artifact and evidence chain relevant to the current boundary

Then produce exactly one concise Continuity Reconstruction Report using the fields defined in:

`docs/continuity/MEYLUX_V2_CONTINUITY_VERIFICATION.md`

The report must explicitly confirm that the AI has completed Role Familiarization and reviewed the applicable Role artifacts, Shared Role Boundary artifacts, and Role Registry before continuing project work.

Do not read the entire repository unless the next authorized action requires additional context.

### Phase Execution / Continuity Auto-Discovery

The successor AI MUST NOT depend on the user supplying the name or path of a Phase Execution/Continuity Report. After reading the authoritative Registry and current checkpoint, discover applicable Phase Execution/Continuity Reports from repository metadata, Registry entries, and the relevant `docs/operations/` / phase artifact areas.

When such a report exists for a completed or currently relevant Phase, read it as a continuity/execution companion and reconcile it against the authoritative Phase definition, Audit Reports, Registry, and CURRENT_CHECKPOINT. It provides consolidated historical/execution context but MUST NOT override higher-authority artifacts.

This rule is generic and applies to all Meylux V2 Phases; it is not specific to Phase 2 or to any single filename.

## Required PROJECT GUIDE continuity sequence

When `PROJECT GUIDE` / `ROL-V2-008` is declared, the successor AI must follow this sequence:

```text
PROJECT GUIDE ROLE DECLARED
        ↓
READ PROJECT GUIDE ROLE CONTRACT
        ↓
CONFIRM ROL-V2-008 FROM AUTHORITATIVE REGISTRY
        ↓
READ CURRENT CONTINUITY / CHECKPOINT ARTIFACTS
        ↓
RECONSTRUCT AUTHORITATIVE PROJECT STATE
        ↓
IDENTIFY CURRENT AUTHORITY / BOUNDARIES
        ↓
IDENTIFY ACTIVE WORK AND NEXT AUTHORIZED ACTION
        ↓
CONTINUE ONLY WITH ESTABLISHED AUTHORITY
```

Role Familiarization must precede Continuity Reconstruction and must never be treated as authorization.

## Continuation boundary

The repository current-state record is authoritative for current continuation. The historical transfer baseline and any older bootstrap snapshot must not override newer authoritative repository state.

The bootstrap MUST NOT contain a hardcoded lifecycle snapshot that can silently become stale. Current phase, step, task, gate, VPS, runtime, and authorization state MUST be reconstructed from `CURRENT_CHECKPOINT.json`, the authoritative Registry, applicable Phase definition, governance decisions, and current evidence.

Phase Execution/Continuity Reports are historical/execution companions: they are mandatory context when applicable, but they do not grant authority and do not replace the current checkpoint, Phase definition, Audit Reports, or governance decisions.

After continuity reconstruction, continue only within authority actually established by the repository. Do not infer authorization from chat memory, role declaration, historical transfer state, or sequence position alone. Where a Phase/Step is explicitly active and a Task Order is explicitly authorized, follow the established workflow without unnecessary re-approval loops.
