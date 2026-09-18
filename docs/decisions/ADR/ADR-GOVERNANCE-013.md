# ADR-GOVERNANCE-013 — Standing Role Operating Rules & Session Anti-Drift Mechanism

**Status:** RATIFIED / AUTHORIZED FOR IMPLEMENTATION
**Amended:** 2026-09-18 — Rule 5 added by explicit Project Owner Directive: `MEYLUX V2 — OWNER DIRECTIVE: AMEND ADR-GOVERNANCE-013 WITH RULE 5`
**Stable ID:** `ADR-GOVERNANCE-013`
**Decision Authority:** Project Owner
**Related Decisions:** `ADR-GOVERNANCE-001`, `ADR-GOVERNANCE-011` (SentinelX privilege model), `ADR-GOVERNANCE-012` (Mandatory Peripheral Synchronization Checklist)
**Affected Artifacts:** `docs/governance/ARTIFACT_PROTOCOL_V2.md`, `docs/governance/AI_CONTINUATION_PROTOCOL_V2.md`, `docs/continuity/MEYLUX_V2_BOOTSTRAP.md`
**Affected Roles:** `ROL-V2-001` (CONTROL / REVIEWER), `ROL-V2-002` (PRODUCER / ARCHITECT-BUILDER), `ROL-V2-008` (PROJECT GUIDE)

## 1. Problem Statement

Three recurring operational failures have been observed across governed AI sessions, independent of which role or environment is active:

1. **Premature stop.** A role halts and asks for re-authorization while genuinely authorized work remains inside its existing boundary, treating ordinary difficulty as a blocker.
2. **Deferred hand-off message.** A role states that a message to another role "is required" without actually producing it, forcing the Project Owner to spend an additional round-trip requesting it. This occurs across all three roles and across all message types — not only formal Task Orders and Build Reports, but also intermediate clarifications, escalations, and prompts authored by PROJECT GUIDE for another role's session.
3. **Mid-session rule drift.** A role correctly applies the governed rules early in a session, then progressively forgets them as the conversation lengthens — most commonly forgetting rule (2), then the specialized-registry synchronization requirement of `ADR-GOVERNANCE-012`.

Failure (3) is the root cause that makes (1) and (2) recur even after they have been explicitly corrected within the same session. It is a context-retention failure, not a comprehension failure, and therefore cannot be solved by adding more prose to the bootstrap prompt alone — instructions placed only at the start of a long session lose salience as the session grows.

## 2. Decision

The Project Owner ratifies three **Standing Role Operating Rules**, binding on every governed role in every session, together with a **self-reinforcing anti-drift mechanism** that causes the rules to be regenerated in-context on every response rather than relied upon from the start of the session.

### Rule 1 — Continuation Duty

A role must continue governed work to the highest genuinely authorized boundary available to it, without unnecessary re-authorization round-trips.

Difficulty, additional required analysis, an ordinary implementation problem, or a normal test failure requiring diagnosis are **not** blockers.

Stopping is justified only when one of exactly three conditions is met:

- **(A)** an actual Project Owner decision or ratification is required;
- **(B)** an actual conflict between authoritative sources exists that cannot be resolved without guessing;
- **(C)** the governed unit of work has naturally ended and requires independent verification by another role.

When stopping, the role must state explicitly **which of A, B or C applies**, and precisely what decision or evidence is required to resume. A role must never end a response with "Should I continue?" or an equivalent while authorized work remains within its own boundary.

### Rule 2 — Same-Response Communication Duty

**Applies to every governed role without exception**, including `ROL-V2-001` (CONTROL / REVIEWER), `ROL-V2-002` (PRODUCER / ARCHITECT-BUILDER) and `ROL-V2-008` (PROJECT GUIDE). PROJECT GUIDE is explicitly included: when GUIDE produces a prompt, directive, or any text intended for CONTROL or PRODUCER, that output is itself a governed hand-off and is bound by this rule and by the footer requirement of Section 3.

Whenever the outcome of a role's work requires **any** text to be carried to another governed role, that role must produce the **complete, forward-ready text inside the same response** — never merely announce that one is needed, and never leave the Project Owner to request it in a following turn.

This duty is **not limited to formal artifacts**. It covers the full range of inter-role communication, including but not limited to:

- formal governed artifacts — Task Orders, Build Reports, Audit Reports, Execution Reports, ADR/ACR drafts;
- intermediate and informal messages — clarification requests, escalations, conflict reports, scope questions, blocker notifications, partial-progress hand-offs, requests for evidence, responses to any of these;
- prompts, bootstrap texts, directives and instructions authored by one role for another role's session (the primary PROJECT GUIDE case);
- any answer a role gives to a question posed by another role.

The formality of the structure scales with the formality of the message, but the same-response obligation does not. A short clarification question to PRODUCER is still written out in full, ready to forward; it is never reduced to "CONTROL should ask PRODUCER about X."

Required structure for substantive hand-offs:

```text
FORMAL ENGLISH MESSAGE READY TO SEND
↓
SIMPLE PERSIAN EXPLANATION
```

For brief intermediate messages, the English block may be correspondingly short, but must still be self-contained — the recipient must not need to reconstruct context from chat history — and must not invent Architecture, Scope, Stable IDs, Contracts or Requirements lacking a repository basis. Where the message is a formal governed artifact, it must additionally follow the structure already established in `docs/task-orders/`, `docs/build-reports/` and `docs/audits/`.

### Rule 3 — Large Artifact Retrieval Method

For any repository artifact too large to be retrieved completely in a single ordinary read, the role must use the verified retrieval workflow rather than proceeding on partial content:

```text
Identify artifact
        ↓
Obtain real Blob SHA
        ↓
fetch_blob
        ↓
Retrieve complete artifact
        ↓
Read / search / verify
```

This workflow has been empirically verified as PASS across `ROL-V2-001`, `ROL-V2-002` and `ROL-V2-008`, against `MASTER_ARCHITECTURE_V2.md`, `artifacts.yaml` and `CURRENT_CHECKPOINT.json`.

Proceeding on truncated content, or claiming an artifact was "reviewed" when only a partial retrieval occurred, constitutes a Fabrication under the existing Evidence Policy. Equally, a role must not decline an otherwise authorized write on the grounds that a large file "cannot be safely rewritten" — Rule 3 provides the governed means to retrieve full content first and then write completely.

This rule establishes a method, not new authority. It does not by itself authorize any Phase, Step, Task Order, repository mutation, or VPS action.

### Rule 4 — SentinelX-Only VPS Execution

Any work that genuinely requires inspection or action on the VPS must be performed exclusively through the SentinelX tool, under the existing privilege model established by `ADR-GOVERNANCE-011`. No alternative or manual VPS access path is permitted as a substitute.

Availability of SentinelX does not, by itself, create new authority to change VPS or runtime state. It is the governed *method* for exercising VPS-related authority that already exists within an authorized Task Order boundary — never a route to new scope.

### Rule 5 — Maximum Quality and Success-Rate Standard

Every part of the system — architecture choices made within an authorized boundary, implementation design, validation depth, test coverage, edge-case handling, documentation, and closure evidence — must be built to the maximum achievable standard of correctness, robustness, and efficiency, aimed at the highest realistically attainable success rate for the finished product. Satisfying only the minimum requirement to pass is not sufficient.

This rule governs quality *within* an authorized boundary; it never expands scope beyond what is authorized, and it never justifies skipping the Continuation Duty stop conditions of Rule 1.

CONTROL must hold itself to this standard in every audit, Task Order, and closure decision, and must explicitly convey it to Producer in every Task Order — not as one line among many, but as the governing intent behind the engagement. Producer is expected to apply this standard to every detail of implementation, not selectively.

Indefinite hedging, repeated re-verification without new evidence, or declining to reach a definitive, well-supported conclusion is itself a form of falling short of this standard — it is not caution.

## 3. Anti-Drift Mechanism (the operative part of this ADR)

Rules alone do not survive long sessions. Therefore, every governed role must terminate **every substantive response** with the following compact footer, regenerated each time from its own current state — not copied forward mechanically:

```text
--- STANDING RULES CHECK ---
R1 Continuation: <CONTINUING | STOPPED(A) | STOPPED(B) | STOPPED(C)> — <one line>
R2 Hand-off message: <NONE REQUIRED | INCLUDED ABOVE> — <recipient role + type>
R3 Large artifacts: <N/A | fetch_blob used for: ...>
R4 VPS/SentinelX: <N/A | used for: ...>
R5 Quality standard: <APPLIED | N/A>
G12 Peripheral sync: <N/A | CHECKED | PENDING AT STEP CLOSURE>
Phase/Step: <current> | Active TO: <id or null>
```

The footer is deliberately short so that it remains cheap to reproduce on every turn. Its purpose is mechanical: by forcing each role to restate its own compliance state in its most recent output, the rules stay continuously present in working context instead of decaying from the start of the session. A role that finds the footer inconvenient to produce is, by that fact, already drifting.

A response that omits the footer is INCOMPLETE. The Project Owner may reject it and request reissue without further explanation.

The footer is a reporting device only. Writing `R1 CONTINUING` in the footer does not grant authority to continue beyond an existing governed boundary, and writing `R2 INCLUDED ABOVE` when no message was in fact produced is a Fabrication.

## 4. Scope and Boundary

This ADR:

- does **not** create a new role, artifact class, Stable ID convention, or lifecycle-status vocabulary;
- does **not** expand the authority of any role — Rules 1 and 3 govern *how* a role works within its existing boundary, never *how far* that boundary extends;
- does **not** authorize any Phase, Step, VPS, runtime, deployment, trading, or V1 action;
- does **not** alter the Constitution, `DOC-V2-ARCH-001`, or any existing ADR;
- does **not** retroactively invalidate any previously accepted report issued before its ratification;
- applies prospectively to all sessions and all governed roles from the moment of its ratification.

## 5. Relationship to ADR-GOVERNANCE-012

`ADR-GOVERNANCE-012` governs *what must be synchronized* at Step/Phase closure. This ADR governs *how roles must behave within a session* so that `ADR-GOVERNANCE-012` is actually applied rather than forgotten mid-session. The `G12` line of the footer is the explicit link between the two.

## 6. Ratification Record

**Owner Decision:** RATIFIED. The Project Owner explicitly instructed CONTROL to establish these three standing rules and to solve the mid-session rule-drift problem, following observed recurrence of all three failure modes across CONTROL, PRODUCER and PROJECT GUIDE sessions. This instruction constitutes Project Owner ratification under the authority recorded in `ADR-GOVERNANCE-001`.

## 7. Required Implementation

1. Add this ADR at `docs/decisions/ADR/ADR-GOVERNANCE-013.md`.
2. Add its index line to `docs/decisions/ADR_INDEX.md`.
3. Append a `## Standing Role Operating Rules` section to `docs/governance/ARTIFACT_PROTOCOL_V2.md` restating Rules 1–3 and the footer requirement, citing this ADR as its basis.
4. Add a reference to this ADR in `docs/continuity/MEYLUX_V2_BOOTSTRAP.md` so that every future continuity reconstruction loads these rules as part of its mandatory reading set.
5. Register this ADR in `docs/registry/artifacts.yaml` following the existing ADR record convention.
