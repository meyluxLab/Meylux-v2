# ADR-GOVERNANCE-013 — Standing Role Operating Rules & Session Anti-Drift Mechanism — R1–R7

**Status:** RATIFIED / AUTHORIZED FOR IMPLEMENTATION
**Amended:** 2026-10-08 — R1–R7 consolidated operating control added by explicit Project Owner Directive: `OWNER DIRECTIVE — Establish R1–R7 as the Permanent Operating Control for CONTROL and Producer Communications`; prior amendments remain historically preserved.
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

The Project Owner ratifies seven **Standing Role Operating Rules (R1–R7)**, binding on every governed role in every session, together with a **self-reinforcing anti-drift mechanism and mandatory pre-finalization review cycle** that causes the rules to be regenerated in-context on every response rather than relied upon from the start of the session.

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

### Rule 3 — Complete Artifact & Evidence Integrity

For any repository artifact too large to be retrieved completely in a single ordinary read, the role must use the verified retrieval workflow rather than proceeding on partial content. No substantive project-state claim may be made without evidence appropriate to the exact claim. Repository/CI evidence must not be substituted for authoritative runtime/VPS evidence where runtime evidence is materially required. Synthetic, inferred, fabricated, or unjustified evidence must never substitute for authoritative evidence.

For large artifacts, use:

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

### Rule 4 — No-Drop & Prerequisite Resolution

`ADR-GOVERNANCE-014` is the authoritative normative decision for required-capability continuation and unresolved-prerequisite resolution. This rule makes that requirement part of the R1–R7 operating control without creating a duplicate decision.

A missing, unavailable, or unresolved prerequisite of a still-required capability is a problem to resolve, not a permanent endpoint. The responsible role must preserve the truthful incomplete state, keep the resolution obligation explicit, determine the bounded corrective path within existing authority, and carry authorized resolution work to the farthest legitimate point.

No authorized capability, requirement, Task, or work path may be silently dropped, abandoned, or indefinitely suspended because a prerequisite is difficult or currently unavailable. No fabricated, synthetic, unjustified, or silently repaired fallback may be used to manufacture completion.

Bounded corrective expansion is permitted only when necessary to resolve the identified prerequisite and only through the applicable authorization path. Formal removal from the required boundary requires the proper governance authority. Historical evidence remains immutable unless a separate governed correction authorizes otherwise.

This rule does not authorize implementation, scope expansion, Phase/Step activation, VPS action, or architectural change by itself.

### Rule 5 — VPS / Runtime / SentinelX

Any work that genuinely requires inspection or action on the VPS must be performed exclusively through the SentinelX tool, under the existing privilege model established by `ADR-GOVERNANCE-011`. No alternative or manual VPS access path is permitted as a substitute.

Availability of SentinelX does not, by itself, create new authority to change VPS or runtime state. It is the governed *method* for exercising VPS-related authority that already exists within an authorized Task Order boundary — never a route to new scope.

### Rule 6 — Architecture, Contract, Scope & Role Authority

The architecture hierarchy, ratified/frozen contracts, schemas, Stable IDs, governance boundaries, and authoritative decisions remain protected.

CONTROL retains project-level governance, Task Order, architectural/consistency control, audit, verification, and closure authority. Producer retains implementation-level design authority only within the authorized Task Order boundary. Neither role may silently convert implementation discretion into project-level authority.

Work outside the existing authority or boundary must follow the applicable governed authorization/change-control path. Producer must not self-declare project-level VERIFIED, COMPLETE, or CLOSED.

If a genuine conflict exists between R1–R7 and a higher-authority ratified project rule, the affected portion must be isolated and routed through the applicable governance/change-control process rather than silently resolved by interpretation.

This rule does not authorize architectural redesign, Stable ID changes, contract/schema changes, scope expansion, or unrelated implementation.

### Rule 7 — Quality, Edge Cases, Regression & Closure Integrity

Every part of the system — architecture choices made within an authorized boundary, implementation design, validation depth, test coverage, edge-case handling, documentation, and closure evidence — must be built to the maximum achievable standard of correctness, robustness, and efficiency, aimed at the highest realistically attainable success rate for the finished product. Satisfying only the minimum requirement to pass is not sufficient.

This rule governs quality *within* an authorized boundary; it never expands scope beyond what is authorized, and it never justifies skipping the Continuation Duty stop conditions of Rule 1.

CONTROL must hold itself to this standard in every audit, Task Order, and closure decision, and must explicitly convey it to Producer in every Task Order — not as one line among many, but as the governing intent behind the engagement. Producer is expected to apply this standard to every detail of implementation, not selectively.

Indefinite hedging, repeated re-verification without new evidence, or declining to reach a definitive, well-supported conclusion is itself a form of falling short of this standard — it is not caution.

## 3. Anti-Drift Mechanism (the operative part of this ADR)

Rules alone do not survive long sessions. Therefore, every governed role must terminate **every substantive response** with the following compact footer, regenerated each time from its own current state — not copied forward mechanically:

```text
--- STANDING RULES CHECK ---
R1 Continuation: <CONTINUING | STOPPED(A) | STOPPED(B) | STOPPED(C)> — <one line>
R2 Hand-off: <NONE REQUIRED | INCLUDED ABOVE> — <recipient role + type>
R3 Artifact/Evidence integrity: <APPLIED | N/A> — <large-artifact method / evidence boundary>
R4 No-Drop/Prerequisite resolution: <APPLIED | N/A> — <resolution obligation state>
R5 VPS/SentinelX: <N/A | used for: ...>
R6 Architecture/Scope/Role authority: <APPLIED | N/A> — <one line>
R7 Quality/Edge/Regression/Closure: <APPLIED | N/A> — <one line>
G12 Peripheral sync: <N/A | CHECKED | PENDING AT STEP CLOSURE>
Phase/Step: <current> | Active TO: <id or null>
```

The footer is deliberately short so that it remains cheap to reproduce on every turn. Its purpose is mechanical: by forcing each role to restate its own compliance state in its most recent output, the rules stay continuously present in working context instead of decaying from the start of the session. A role that finds the footer inconvenient to produce is, by that fact, already drifting.

A response that omits the footer is INCOMPLETE. The Project Owner may reject it and request reissue without further explanation.

The footer is a reporting device only. Writing `R1 CONTINUING` in the footer does not grant authority to continue beyond an existing governed boundary, and writing `R2 INCLUDED ABOVE` when no message was in fact produced is a Fabrication.

## 3A. Mandatory R1–R7 Finalization Cycle

Before treating any applicable response or governed work product as final, the responsible role MUST execute this sequence:

**DRAFT → R1–R7 REVIEW → CORRECTIVE REVISION → FINALIZE**

1. **Draft** — prepare the complete response/work product required by the current task.
2. **R1–R7 Review** — review the complete draft against all seven rules, not only the rules that appear obviously relevant.
3. **Corrective Revision** — where the review identifies omission, contradiction, premature stopping, unsupported claim, evidence deficiency, authority/scope problem, insufficient edge-case treatment, governance inconsistency, or closure deficiency, revise the draft before release.
4. **Finalize** — only the reviewed and corrected version is treated as final.

The review is mandatory and substantive. Appending the Rules or merely stating that they were considered is not sufficient.

This cycle applies independently to CONTROL and Producer within their respective authorities. It does not create new authority, silently expand scope, prescribe an implementation outside the responsible role's authority, or revive the previously excluded concept of independently performing work merely because something may have been omitted from a message.

The cycle strengthens compliance with the existing Task Order, architecture, evidence, verification, and governance boundaries; it does not replace them.

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

**Owner Decision:** RATIFIED. The Project Owner explicitly instructed CONTROL to establish the consolidated R1–R7 operating control and the mandatory pre-finalization review cycle, while preserving the existing governance hierarchy and excluding any new authority, following observed recurrence of all three failure modes across CONTROL, PRODUCER and PROJECT GUIDE sessions. This instruction constitutes Project Owner ratification under the authority recorded in `ADR-GOVERNANCE-001`.

## 7. Amendment / Required Implementation

1. Preserve this ADR as the single normative source for R1–R7; this amendment updates the existing ADR rather than creating a competing ADR.
2. Update its existing index entry to identify the R1–R7 amendment.
3. Update the operational rendering in `docs/governance/ARTIFACT_PROTOCOL_V2.md` to reflect R1–R7 and the finalization cycle, citing this ADR as its basis.
4. Ensure continuity/bootstrap and role-operating artifacts reference the canonical R1–R7 finalization control.
5. Synchronize the existing ADR registry record and Change Ledger with the amendment. No new governance artifact class or parallel rule system is created.
