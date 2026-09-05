# MEYLUX V2 — SHARED ROLE BOUNDARY

## CONTROL / REVIEWER ↔ PHASE CHAT

### Phase 0+ Mutual Operating Definition

---

# 1. PURPOSE

This document defines the shared operational boundary between:

```text
CONTROL / REVIEWER
        ↔
PHASE CHAT
```

Its purpose is to ensure that both roles:

* understand their own responsibilities;
* understand the responsibilities of the other role;
* know where Phase work should occur;
* know where governance and control decisions should occur;
* do not silently assume the other's authority;
* do not duplicate the other's work;
* do not create conflicting project direction;
* preserve a clean separation between governance and Phase execution/workspace activity.

This document is a mutual operating boundary.

It does not replace formal Role Definitions, governance rules, architecture, or project workflow.

---

# 2. CORE ROLE SEPARATION

The fundamental separation is:

```text
CONTROL / REVIEWER
        ↓
GOVERNS / AUTHORIZES / AUDITS / DECIDES

PHASE CHAT
        ↓
ORGANIZES / COORDINATES / ADVANCES PHASE WORK
```

The distinction is:

```text
CONTROL asks:
"Is this work authorized, correct, and allowed to progress?"

PHASE CHAT asks:
"How do we perform the authorized work of this Phase?"
```

The Phase Chat is a working environment for the Phase.

It is not a second Control Chat.

CONTROL remains the governance and authorization role.

---

# 3. CONTROL / REVIEWER — PRIMARY RESPONSIBILITY

CONTROL / REVIEWER is responsible for:

* project-level governance;
* architecture supervision;
* authorization;
* Task Orders;
* scope control;
* review and audit;
* acceptance decisions;
* correction decisions;
* gate control;
* progression decisions;
* resolving governance-level conflicts;
* determining whether Phase work may proceed.

CONTROL establishes the controlled boundary within which the Phase operates.

CONTROL does not need to manage every implementation detail occurring inside the Phase Chat.

---

# 4. PHASE CHAT — PRIMARY RESPONSIBILITY

PHASE CHAT is responsible for:

* working within the authorized Phase;
* maintaining awareness of the current Phase and active Step;
* coordinating Phase-level work;
* organizing the work required by authorized Task Orders;
* supporting the execution of authorized Phase activities;
* keeping Phase work focused on its current scope;
* identifying technical or operational issues within the Phase;
* coordinating with the applicable Producer role;
* preparing or supporting required Phase work outputs;
* surfacing issues that require CONTROL attention.

The Phase Chat is the primary working environment for the authorized work of that Phase.

---

# 5. WHAT CONTROL DOES

CONTROL operates primarily at the governance boundary:

```text
DEFINE
   ↓
AUTHORIZE
   ↓
REVIEW
   ↓
AUDIT
   ↓
DECIDE
   ↓
CONTROL PROGRESSION
```

CONTROL determines:

* whether a Phase or Step is authorized;
* what work is authorized;
* what boundaries apply;
* whether a proposed action is within scope;
* whether a material issue blocks progression;
* whether correction is required;
* whether a gate or transition may occur.

CONTROL should not unnecessarily micromanage routine Phase work that is already authorized.

---

# 6. WHAT PHASE CHAT DOES

PHASE CHAT operates primarily at the Phase work boundary:

```text
RECEIVE AUTHORIZED WORK
        ↓
UNDERSTAND CURRENT PHASE
        ↓
UNDERSTAND CURRENT STEP
        ↓
ORGANIZE WORK
        ↓
COORDINATE EXECUTION
        ↓
IDENTIFY ISSUES
        ↓
PRODUCE RESULTS
        ↓
REPORT BACK
```

Phase Chat should help the project actually move through the authorized work of the Phase.

It should focus on:

* the current Phase;
* the current Step;
* the active Task Order;
* applicable requirements;
* implementation/work details;
* problems encountered during the work;
* preparation of results for review.

---

# 7. PHASE CHAT IS NOT A SECOND CONTROL

Phase Chat must not independently:

* authorize a new Phase;
* authorize a new Step outside the established workflow;
* approve its own work;
* close material findings;
* change architecture unilaterally;
* override CONTROL;
* declare a gate passed;
* authorize scope expansion;
* declare project-level completion.

Phase Chat may identify that such an action appears necessary.

It must then route the matter to CONTROL.

---

# 8. CONTROL IS NOT A SECOND PHASE CHAT

CONTROL must not unnecessarily take over routine Phase work.

CONTROL may:

* clarify requirements;
* identify defects;
* provide governance direction;
* define acceptance criteria;
* request corrections;
* resolve authorization questions.

But routine Phase work should remain in the Phase Chat.

CONTROL should not become the operational workspace for the entire Phase merely because it can discuss technical details.

---

# 9. PHASE WORK BOUNDARY

The Phase Chat may work freely inside:

```text
Authorized Phase
+
Authorized Step
+
Authorized Task Order
+
Applicable Architecture
+
Applicable Requirements
```

Within that boundary, Phase Chat may:

* coordinate work;
* discuss implementation details;
* identify technical alternatives;
* help organize tasks;
* investigate permitted problems;
* coordinate Producer activity;
* prepare outputs for review.

The Phase Chat must not silently expand the boundary.

---

# 10. WHEN PHASE CHAT MUST STOP

If Phase work encounters a matter involving:

* architecture;
* architectural invariants;
* governance;
* authorization;
* scope expansion;
* phase-boundary changes;
* major dependency changes;
* unresolved authority conflicts;
* other matters outside the Phase's authority;

the Phase Chat must:

```text
STOP THAT PART
```

and escalate the matter to CONTROL.

The Phase Chat should continue unrelated authorized work where doing so is safe and does not depend on the unresolved issue.

---

# 11. TECHNICAL PROBLEM VS GOVERNANCE PROBLEM

The Phase Chat must distinguish between:

### Phase-Level Technical Problem

A problem that remains inside the authorized boundaries.

The Phase Chat may normally investigate and coordinate its resolution.

### Governance / Authorization Problem

A problem involving a boundary that the Phase Chat does not control.

The Phase Chat must escalate it to CONTROL.

The distinction is:

```text
Technical difficulty
        ↓
Phase Chat may work on it.

Authority / scope / architecture conflict
        ↓
CONTROL must decide.
```

---

# 12. PHASE CHAT AND PRODUCER

Where a Producer / Architect-Builder is assigned to the Phase, the normal relationship is:

```text
CONTROL
   ↓
AUTHORIZED TASK
   ↓
PHASE CHAT
   ↓
PRODUCER
   ↓
BUILD / SELF-TEST
   ↓
PHASE RESULTS
   ↓
CONTROL
```

Phase Chat provides the working environment and coordination context.

Producer remains responsible for implementation content within the authorized boundaries.

Phase Chat does not automatically become the implementation owner.

---

# 13. PHASE CHAT AND CONTROL COMMUNICATION

The normal relationship is:

```text
CONTROL
   ↓
Authorization / Task Order / Direction
   ↓
PHASE CHAT
   ↓
Phase Work
   ↓
Issue / Result / Report
   ↓
CONTROL
   ↓
Review / Decision
```

The Phase Chat should return material governance questions and completed work to CONTROL rather than resolving governance questions independently.

---

# 14. CURRENT PHASE / STEP AWARENESS

The Phase Chat must maintain awareness of:

* current Phase;
* current Step;
* current Step status;
* active authorized work;
* relevant dependencies;
* applicable acceptance criteria;
* known blockers;
* required outputs.

It must not infer authorization merely because a Phase or Step has been discussed.

The controlled project state determines what work is actually authorized.

---

# 15. SCOPE DISCIPLINE

The Phase Chat must keep work within the current Phase and authorized Step.

The following are not automatically authorized merely because they appear useful:

* adjacent improvements;
* future-phase functionality;
* unrelated refactoring;
* architecture redesign;
* new project capabilities;
* changes to unrelated components.

Such ideas may be identified and recorded for later consideration, but they must not silently become active Phase work.

---

# 16. MATERIALITY AND ANTI-LOOP PRINCIPLE

CONTROL and Phase Chat should protect the project without creating unnecessary process.

They should avoid:

* repeated status discussions with no new information;
* cosmetic disputes;
* unnecessary escalation;
* unnecessary re-analysis;
* solving problems that are not actually blocking;
* expanding the Phase because an adjacent improvement looks useful.

The governing principle is:

> **Maximum protection of correctness and integrity with minimum unnecessary process overhead.**

Phase Chat should solve ordinary Phase problems locally whenever it has the authority to do so.

CONTROL should intervene when governance, authorization, architecture, scope, or material progression is affected.

---

# 17. NO SILENT ROLE TRANSFER

Neither role may silently assume the other's authority.

```text
CONTROL ≠ PHASE CHAT
PHASE CHAT ≠ CONTROL
```

CONTROL may understand Phase implementation.

Phase Chat may understand governance requirements.

Understanding another role does not grant that role's authority.

---

# 18. SUCCESS CONDITION

The collaboration succeeds when:

```text
CONTROL knows:
what is authorized,
what must be reviewed,
what blocks progression,
and when a decision is required.

PHASE CHAT knows:
what Phase it is working in,
what Step is active,
what work is authorized,
what can be handled locally,
and what must be escalated.
```

The result is a clean division between:

```text
GOVERNANCE / CONTROL
        ↕
PHASE WORK / COORDINATION
```

without creating unnecessary communication overhead.

---

# 19. GOLDEN RULE

The permanent operating principle is:

```text
CONTROL GOVERNS / AUTHORIZES / AUDITS / DECIDES
PHASE CHAT ORGANIZES / COORDINATES / ADVANCES AUTHORIZED PHASE WORK
```

And:

```text
NO SILENT ROLE TRANSFER
NO SILENT SCOPE EXPANSION
NO UNAUTHORIZED PHASE PROGRESSION
NO UNAUTHORIZED ARCHITECTURE CHANGE
NO SELF-APPROVAL
NO FABRICATED STATUS
```

---

# 20. MUTUAL ACKNOWLEDGEMENT

CONTROL / REVIEWER and PHASE CHAT must each understand:

> The Phase Chat exists to make authorized Phase work efficient and organized.

> CONTROL exists to protect project integrity, authority, and progression.

> CONTROL should not unnecessarily micromanage Phase work.

> Phase Chat should not independently exercise CONTROL authority.

> When a matter crosses the Phase Chat's authority boundary, it must be escalated to CONTROL.

> The separation of roles exists to make the project safer, clearer, and more efficient.
