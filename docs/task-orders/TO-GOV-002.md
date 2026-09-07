# MEYLUX V2 — GOVERNANCE TASK ORDER

## TO-GOV-002 — PROJECT GUIDE Role-Aware Continuity Bootstrap Integration

**Task Order ID:** `TO-GOV-002`
**Governance Class:** Post-Freeze Governance / Governance Activity
**Phase:** `NONE`
**Step:** `NONE`
**Issuer:** CONTROL / REVIEWER (`ROL-V2-001`)
**Recipient:** PRODUCER / ARCHITECT-BUILDER (`ROL-V2-002`)
**Status:** `AUTHORIZED TO EXECUTE`
**Authority:** `ADR-GOVERNANCE-001`; `ADR-GOVERNANCE-005`; `ADR-GOVERNANCE-006`; `ADR-GOVERNANCE-007`
**Target Role:** `PROJECT GUIDE` (`ROL-V2-008`)
**Build Report ID:** `BR-GOV-002`
**Build Report Path:** `docs/build-reports/BR-GOV-002.md`

## 1. Sole Objective

Integrate the formally established PROJECT GUIDE role into Meylux V2's existing AI-to-AI Continuity and Bootstrap mechanism so that a successor AI explicitly assigned the PROJECT GUIDE role can first perform Role Familiarization from the authoritative PROJECT GUIDE Role Contract, then reconstruct authoritative project state from the repository, and only thereafter determine the next authorized action.

This Task Order is a continuity/governance integration task. It does not create a new continuity system and does not grant PROJECT GUIDE any governance, implementation, execution, ratification, approval, or verification authority.

## 2. Required Outcome

The successor-AI path must support this controlled sequence:

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

Role Familiarization must occur before Continuity Reconstruction, but Role Familiarization must never be treated as authorization.

## 3. Scope In

The Producer shall:

1. Review the current authoritative continuity artifacts and the ratified PROJECT GUIDE Role Contract.
2. Update `docs/continuity/MEYLUX_V2_BOOTSTRAP.md` so that the bootstrap path explicitly supports PROJECT GUIDE / `ROL-V2-008` and directs the successor AI to read the canonical PROJECT GUIDE Role Contract before continuing project-state analysis when that role is declared.
3. Update `docs/governance/AI_CONTINUATION_PROTOCOL_V2.md` so that the authoritative role model includes PROJECT GUIDE / `ROL-V2-008`, its canonical Role Contract path, and the required role-familiarization behavior.
4. Preserve the existing continuity principles: GitHub is Source of Truth; hidden memory/chat is not authoritative; current state must be reconstructed from repository evidence; no authorization may be inferred from continuity material alone.
5. Reconcile stale pre-Phase-0 continuation wording where it conflicts with the current authoritative post-Phase-0 repository state, using the current checkpoint and ratified governance artifacts as authority.
6. Preserve all existing role identities and role boundaries.
7. Ensure the Project Guide Role Contract remains the authoritative role-specific behavior source and that continuity artifacts do not duplicate or override its substantive authority boundary.
8. Produce `BR-GOV-002` at `docs/build-reports/BR-GOV-002.md` containing actual changes, evidence, self-test results, deviations, open questions, and explicit non-claims.
9. Keep `BR-GOV-002` unverified pending independent CONTROL audit.

## 4. Scope Out / Explicit Prohibitions

The Producer MUST NOT:

- modify the PROJECT GUIDE Role Contract's substantive content under this Task Order;
- modify `DOC-V2-ARCH-001`;
- modify the Constitution;
- reopen or alter `PH-P0` or any completed Phase 0 Step;
- modify `CURRENT_CHECKPOINT.json` as part of this Task Order;
- invent or alter Stable IDs;
- create a competing continuity, checkpoint, registry, or governance system;
- grant PROJECT GUIDE governance, ratification, approval, implementation, execution, deployment, trading, capital, or verification authority;
- treat Role Familiarization as authorization;
- authorize Phase 1;
- perform runtime, VPS, provider-runtime, market-data execution, trading, capital, or V1 activity;
- fabricate current state, evidence, verification, hashes, tests, or completion;
- silently rewrite historical evidence.

## 5. Required Canonical Role Discovery

The integrated bootstrap must recognize:

```text
PROJECT GUIDE
Stable ID: ROL-V2-008
Role Contract: docs/governance/ROLE_CONTRACT_PROJECT_GUIDE_V2.md
Canonical Chat: MEYLUX V2 — PROJECT GUIDE
```

The authoritative Role Registry remains:

```text
docs/registry/artifacts.yaml
```

Role identity remains independent of chat name, filename, repository path, or model identity.

## 6. Continuity Reconstruction Requirements

A successor AI operating as PROJECT GUIDE must be able to reconstruct at minimum:

- project identity and mission;
- Source of Truth;
- frozen/ratified architecture state;
- governance state;
- current gate and phase state;
- current checkpoint;
- active or most recently authorized Task Order;
- Stable IDs and registry state;
- ratified ADRs;
- open questions;
- deferred decisions;
- verified and unverified evidence;
- latest verified commit where authoritative;
- next authorized action;
- relevant environment/runtime boundary.

The mechanism must distinguish authoritative current state from historical transfer material and working discussion.

## 7. Acceptance Criteria

CONTROL may consider `BR-GOV-002` for audit only if actual evidence demonstrates that:

- PROJECT GUIDE / `ROL-V2-008` is discoverable from the authoritative registry;
- the canonical PROJECT GUIDE Role Contract is explicitly part of Role Familiarization;
- Role Familiarization precedes Continuity Reconstruction;
- the bootstrap/protocol identify the current repository state from authoritative artifacts rather than stale pre-Phase-0 assumptions;
- current checkpoint is treated as current-state evidence and not as a replacement for architecture/governance authority;
- the successor AI can determine the next authorized action without relying on hidden chat memory;
- no authority is granted merely by role declaration or continuity reconstruction;
- existing role identities and boundaries remain intact;
- no frozen architecture, Constitution, Phase 0 artifact, or checkpoint is improperly modified;
- no Phase 1 implementation or runtime activity is authorized;
- all changes are traceable in `BR-GOV-002`.

## 8. Verification Boundary

Producer completion means only:

```text
CONTINUITY INTEGRATION IMPLEMENTED
+
BR-GOV-002 PRODUCED
+
ACTUAL EVIDENCE REPORTED
```

It does not mean `VERIFIED`, `APPROVED`, `RATIFIED`, or `CLOSED`.

Independent CONTROL audit remains required.
