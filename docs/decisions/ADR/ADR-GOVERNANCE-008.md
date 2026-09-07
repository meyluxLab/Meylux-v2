# ADR-GOVERNANCE-008 — Post-Freeze Governance Audit Report Identity Convention

**Project:** Meylux V2  
**Status:** RATIFIED / FROZEN  
**Decision ID:** `ADR-GOVERNANCE-008`  
**Decision Authority:** PROJECT OWNER  
**Ratifying Authority:** PROJECT OWNER  

## 1. Decision Purpose

This ADR establishes the permanent identity convention for Audit Reports produced by CONTROL / REVIEWER for formally governed post-freeze governance activities that do not belong to an active Phase.

## 2. Ratified Convention

The permanent Audit Report identity convention is:

```text
AR-GOV-<NNN>
```

where:

- `AR` = Audit Report
- `GOV` = Post-Freeze Governance / Governance Activity
- `<NNN>` = permanent three-digit sequential identifier
- identifiers are never reused

The canonical repository path is:

```text
docs/audits/AR-GOV-<NNN>.md
```

## 3. Scope

This convention applies only to Audit Reports produced by CONTROL / REVIEWER for post-freeze governance activities governed through `TO-GOV-<NNN>` and corresponding `BR-GOV-<NNN>` artifacts.

Existing Phase-bound Audit Reports such as `AR-P0-AUDIT-*` remain historical and unchanged.

## 4. Identity Rules

1. Audit Report IDs use the form `AR-GOV-<NNN>`.
2. `<NNN>` is sequential within the post-freeze governance audit namespace.
3. Audit IDs are permanent and must never be reused.
4. Existing Phase-bound Audit Report identities remain unchanged.
5. An Audit Report identity does not itself establish verification, approval, ratification, or closure.
6. Audit Reports must be based on independent CONTROL review and actual repository evidence.
7. Producer self-test results must remain distinct from independent CONTROL verification.
8. CONTROL must not fabricate evidence, test results, hashes, or lifecycle state.
9. This convention does not grant authority beyond the existing CONTROL / REVIEWER role and applicable governance process.
10. The first reserved application is `AR-GOV-001` for the independent CONTROL audit of `BR-GOV-001`.

## 5. Workflow Relationship

The governed post-freeze evidence chain remains:

```text
TO-GOV-<NNN>
→ BR-GOV-<NNN>
→ CONTROL Independent Audit
→ AR-GOV-<NNN>
→ applicable Project Owner ratification/decision where required
→ verification / lifecycle synchronization
```

An Audit Report records the result of independent review. It does not replace the applicable Project Owner authority or other required governance decisions.

## 6. Boundary

Ratification of this convention:

- does not reopen Phase 0;
- does not modify the frozen Master Architecture;
- does not modify the Constitution;
- does not modify frozen Phase 0 artifacts;
- does not authorize Phase 1;
- does not authorize runtime, VPS, provider-runtime, market-data execution, trading, capital, or V1 activity;
- does not establish or ratify PROJECT GUIDE by itself;
- does not claim that `AR-GOV-001` has been produced, executed, verified, or approved.

## 7. Ratification Statement

The Project Owner formally ratified the proposed Post-Freeze Governance Audit Report Identity Convention, approved all ten stated rules, and approved the first reserved application `AR-GOV-001` for the independent CONTROL audit of `BR-GOV-001`.

## 8. Effective State

```text
Convention:
AR-GOV-<NNN>

Canonical Path:
docs/audits/AR-GOV-<NNN>.md

Status:
RATIFIED / FROZEN

Authority:
PROJECT OWNER

First Reserved Application:
AR-GOV-001 → BR-GOV-001
```
