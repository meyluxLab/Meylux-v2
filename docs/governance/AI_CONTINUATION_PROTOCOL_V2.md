# Meylux V2 — AI Continuation Protocol

**Status:** DRAFT — RECONCILED BY PRODUCER / PENDING CONTROL APPROVAL
**Scope:** V2 AI-to-AI continuation and resumability
**Authority boundary:** This document defines the continuation protocol candidate; it does not itself ratify architecture, authorize Steps, close gates, or authorize runtime activity.

## 1. Purpose

A successor AI must be able to reconstruct Meylux V2 project state from governed repository artifacts and actual evidence without relying on hidden chat memory, prior-model identity, or user recollection as authoritative state.

The repository remains the durable Source of Truth. Chat is a working/coordination surface only.

## 2. Mandatory Bootstrap Sequence

The successor AI MUST read the following in order, stopping only the affected action if a genuine repository conflict is found:

1. `docs/continuity/MEYLUX_V2_TRANSFER_STATE.yaml`
2. `docs/state/CURRENT_CHECKPOINT.json`
3. `docs/governance/AI_CONTINUATION_PROTOCOL_V2.md`
4. Applicable Role Contract / Role Definition artifacts for the declared role.
5. Required Shared Role Boundary artifacts.
6. `docs/registry/artifacts.yaml`
7. `docs/governance/ARTIFACT_PROTOCOL_V2.md`
8. `docs/architecture/MASTER_ARCHITECTURE_V2.md`
9. `docs/state/OPEN_QUESTIONS.yaml`
10. `docs/state/DEFERRED_DECISIONS.yaml`
11. Relevant ADRs / ACRs.
12. Latest approved artifact and evidence chain relevant to the current boundary.
13. Additional repository state only when required by the next authorized action.

The bootstrap sequence is a minimum reconstruction path, not permission to read or modify unrelated project areas.

## 3. Role Familiarization

Before Continuity Reconstruction and before authorized project work, the successor AI MUST reconstruct the applicable role model from repository artifacts.

When `PROJECT GUIDE` is declared, the role-specific familiarization sequence MUST be:

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

The PROJECT GUIDE role is:

- Stable ID: `ROL-V2-008`
- Canonical Role Contract: `docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md`
- Canonical Chat: `MEYLUX V2 — PROJECT GUIDE`

The authoritative Role Registry is `docs/registry/artifacts.yaml`. Role identity is independent of filename, path, chat name, or model identity.

The PROJECT GUIDE Role Contract is the authoritative role-specific behavior source. Continuity artifacts must not duplicate, weaken, or override its substantive authority boundary.

Role familiarization establishes understanding only. It does not grant authority, replace a Task Order, gate, formal authorization, ratification, approval, or verification.

For other declared roles, read the applicable Role Contract / Role Definition and required Shared Role Boundary artifacts before state reconstruction.

## 4. State Reconstruction Requirements

The successor AI MUST reconstruct, from authoritative artifacts and evidence, at minimum:

- project identity and mission;
- Source of Truth;
- frozen/ratified architecture state;
- governance state;
- current gate and phase state;
- current checkpoint;
- active or most recently authorized Task Order;
- Stable IDs and registry state;
- ratified ADRs / governance decisions;
- open questions;
- deferred decisions;
- verified and unverified evidence;
- latest verified commit where authoritative;
- next authorized action;
- relevant environment/runtime boundary.

The reconstruction MUST distinguish:

```text
FACT / AUTHORITATIVE STATE
vs
HISTORICAL EVIDENCE
vs
CLAIM / UNVERIFIED REPORT
vs
ASSUMPTION
vs
OPEN QUESTION
vs
DEFERRED DECISION
```

## 5. Authority and Precedence

When records describe the same concern, use the project's established authority hierarchy. Lower-authority or stale transfer material MUST NOT override newer authoritative repository state.

The CURRENT_CHECKPOINT is the machine-readable current-state record; it is not a replacement for the Constitution, Master Architecture, governance decisions, or Artifact Protocol.

A transfer package transfers state; it does not grant new authority.

A prior transfer baseline remains historical when superseded by a newer authoritative checkpoint/evidence chain.

Role declaration and Role Familiarization likewise do not grant authority.

## 6. Current Continuation Boundary

Continuation is allowed only when:

1. authoritative repository state is internally consistent for the requested action; and
2. the next action is already authorized by the existing governance process.

The successor AI MUST NOT infer authorization from:

- chat history;
- model memory;
- an old transfer package;
- architecture text alone;
- the existence of a future Step;
- role declaration;
- Role Familiarization;
- continuity reconstruction itself.

If a genuine architecture, governance, identity, scope, or authority conflict is found:

```text
STOP THAT PART
→ identify authoritative sources
→ report the conflict
→ use the controlled resolution path
```

Do not silently reconcile a conflict by personal interpretation.

## 7. Active Work and Next Action

The successor AI MUST identify the single currently authorized execution boundary, if one exists:

```text
CURRENT PHASE
→ CURRENT STEP
→ ACTIVE TASK ORDER
→ REQUIRED OUTPUT
→ ACCEPTANCE BOUNDARY
→ NEXT AUTHORIZED ACTION
```

Completed work, historical work, unverified work, and future defined work MUST remain distinguishable.

The next authorized action MUST be established from the current authoritative repository state, not inferred from sequence position alone.

## 8. Evidence and Lifecycle Discipline

Continuation MUST preserve the distinction between:

```text
DESIGNED
DRAFT
PROPOSED
APPROVED
IMPLEMENTED
EXECUTED
VERIFIED
FROZEN
RATIFIED
CLOSED
```

A Build Report is Producer evidence and is not independently verified until CONTROL performs the applicable audit.

No successor AI may convert unsupported state assertions into `EXECUTED`, `COMPLETE`, `VERIFIED`, `APPROVED`, `FROZEN`, or `RATIFIED` state.

## 9. Stable Identity and Traceability

The successor AI MUST preserve existing Stable IDs and historical lineage.

It MUST NOT invent, renumber, reuse, merge, split, or silently reinterpret identities.

When identity cannot be established from authoritative records:

```text
IDENTITY UNCONFIRMED
```

must remain explicit until controlled resolution.

## 10. Continuity Reconstruction Report

After the mandatory bootstrap reading sequence, the successor AI MUST produce one concise Continuity Reconstruction Report containing exactly these fields:

```text
PROJECT:
SOURCE OF TRUTH:
ARCHITECTURE STATE:
CURRENT CHECKPOINT:
CURRENT GATE:
CURRENT PHASE:
CURRENT STEP:
OPEN QUESTIONS:
DEFERRED DECISIONS:
ACTIVE TASK:
LATEST VERIFIED COMMIT:
NEXT AUTHORIZED ACTION:
CONTINUITY STATUS:
```

The report MUST also include the required role-model reconstruction confirmation. For PROJECT GUIDE, this confirmation must identify `ROL-V2-008` and confirm that `docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md` was read before Continuity Reconstruction.

The report must state facts established by authoritative artifacts only. It must not claim independent verification merely because a transfer package or prior AI prepared the material.

## 11. Information vs Execution

Information needed to understand state does not automatically become permission to execute.

Before executing a Task Order, the AI MUST identify:

- the specific authorized Task Order;
- affected Stable IDs / paths;
- required evidence;
- required output;
- applicable acceptance criteria;
- Operator prerequisites, where physical/environment execution is required.

Do not require the entire historical chat when the governed repository already contains the necessary information.

## 12. Prohibited Continuation Behavior

The successor AI MUST NOT:

- replace repository authority with hidden memory;
- reopen completed Pre-Project or closed Phase 0 work without authorization;
- activate future Steps;
- issue future Task Orders without Reviewer authority;
- ratify or freeze architecture outside its formal process;
- change Stable IDs or historical identities;
- create competing continuity, governance, checkpoint, registry, or approval systems;
- fabricate execution, verification, runtime, market, provider, or repository state;
- perform V1/VPS/runtime/market/trading/capital/provider-runtime activity without explicit authorization;
- silently rewrite historical evidence;
- treat role familiarization as authorization.

## 13. Continuity Success Condition

Continuity is successful when a successor AI can reconstruct authoritative project state, identify what is current versus historical/unverified, understand the applicable role boundaries, identify the active authorized work, and determine the next authorized action without requiring hidden chat memory.

This protocol candidate does not authorize Phase progression, runtime implementation, V1 activity, market/trading/capital activity, or architecture ratification/freeze.
