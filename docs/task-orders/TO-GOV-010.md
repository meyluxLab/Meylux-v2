# TO-GOV-010 — Governance Artifact Parse Integrity & Status-Drift Reconciliation

**Task Order SID:** TO-GOV-010
**Project:** MEYLUX V2
**Issuing Role:** CONTROL / REVIEWER — ROL-V2-001
**Producer Role:** PRODUCER / ARCHITECT-BUILDER — ROL-V2-002
**Boundary:** Cross-cutting governance / registry / documentation integrity. This Task Order closes no Phase and no Step.
**Status:** AUTHORIZED TO EXECUTE
**Predecessor:** TO-GOV-009 / BR-GOV-008 / AR-GOV-005
**Governing decisions:** ADR-GOVERNANCE-012 (Mandatory Peripheral Synchronization Checklist), ADR-GOVERNANCE-013 R1–R7, ADR-GOVERNANCE-014, ADR-GOVERNANCE-006, ADR-GOVERNANCE-008
**Issued:** 2026-10-10

## 1. Purpose and authority

CONTROL established this Task Order after reconstructing the authoritative project state from the current repository Source of Truth and discovering a class of governance-artifact integrity defects that are **not** recorded anywhere in the repository.

The defects are material because:

1. `docs/registry/artifacts.yaml` is the **authoritative Stable ID, path and traceability registry** (see `MASTER_ARCHITECTURE_V2.md` §3.3 and §5). It does not currently parse as YAML.
2. Twelve further registry / state files do not parse as YAML either, including `docs/registry/phases.yaml` and `docs/state/CHANGE_LEDGER.yaml`.
3. Consequently the "machine-readable" guarantee the project relies on for continuity (see `ROLE_CONTRACT_CONTROL_REVIEWER_V2.md` §25, `AI_CONTINUATION_PROTOCOL_V2.md` §4, and `MASTER_ARCHITECTURE_V2.md` §6.1) does not hold today.

This Task Order is issued under:

- `ROLE_CONTRACT_CONTROL_REVIEWER_V2.md` §3 (Task Order issuance, governance consistency control, evidence review);
- §4A.1 (Unforeseen-Problem Authority — minimum controlled action to protect project integrity);
- §7 (Task Order authority);
- `ADR-GOVERNANCE-012` §2 item 2 (registry records must not retain stale/incorrect status; corrections belong to the governing Task Order, not a deferred cleanup);
- the established `TO-GOV-006` → `TO-GOV-007` → `TO-GOV-008` → `TO-GOV-009` State/Registry reconciliation precedent.

**This Task Order is a repair-and-record exercise only.** It authorizes no new capability, no Phase or Step activation, no architecture or governance semantic change, and no runtime activity.

## 2. Authoritative findings

All findings below were observed by CONTROL on the current `main` and are reproducible with a standard YAML parser (PyYAML `safe_load`).

### F-01 — `docs/registry/artifacts.yaml` does not parse

`ScannerError` at **line 953, column 28**: an unquoted colon inside a plain scalar value.

```
    canonical_name: Group A: Technical, Multi-Timeframe, Volatility
```

The identical value appears twice, at **line 953** and **line 959**. The later instance does not fail on its own only because parsing aborts at the first error.

### F-02 — Twelve further registry / state files do not parse

| File | Failing line | Failure class |
|---|---|---|
| `docs/registry/components.yaml` | 132 | ScannerError — unquoted colon in value |
| `docs/registry/configuration.yaml` | 98 | ScannerError — unquoted colon in value |
| `docs/registry/contracts.yaml` | 295 | ParserError — block-sequence indentation |
| `docs/registry/database.yaml` | 255 | ScannerError — unquoted colon in value |
| `docs/registry/observability.yaml` | 76 | ScannerError — unquoted colon in value |
| `docs/registry/performance.yaml` | 73 | ScannerError — unquoted colon in value |
| `docs/registry/phases.yaml` | 516 | ScannerError — unquoted colon in value |
| `docs/registry/requirements.yaml` | 61 | ScannerError — unquoted colon in value |
| `docs/registry/runtime.yaml` | 274 | ParserError — block-sequence indentation |
| `docs/registry/security.yaml` | 108 | ScannerError — unquoted colon in value |
| `docs/registry/tests.yaml` | 525 | ScannerError — unquoted colon in value |
| `docs/state/CHANGE_LEDGER.yaml` | 2056 | ParserError — block-sequence indentation |

Known value-level instances include:

- `docs/registry/phases.yaml` lines 516, 541, 569, 724 — `logical_name: Group A|B|C: ...`
- `docs/registry/tests.yaml` lines 525, 526, 551 — `core_tests: 637; skipped: 5` and similar
- `docs/registry/artifacts.yaml` line 1755 — `canonical_name: Build Report â€" TO-P5-005 Group B: Market Structure, Price Action, Liquidity`

Known indentation instances: `contracts.yaml` line 295 (`- stable_id: CTR-P5-005`), `runtime.yaml` line 274 (`- stable_id: RUN-P4-014`) and `CHANGE_LEDGER.yaml` line 2056 (`- ledger_id: CL-P5-STEP-002-CLOSURE-20260924`) each begin at column 1 while their sibling sequence entries are indented.

### F-03 — Structural corruption and duplicate identities in `artifacts.yaml`

1. **Line 1637**: a new record begins on the *same line* as another record's status field.

   ```
       status: APPROVED / VERIFIED  - stable_id: AR-P3-009
   ```

2. **Duplicate `stable_id` occurrences** (each appears twice):

   `TO-P4-012`, `BR-P4-012`, `TST-P4-012`, `DB-P4-012`, `CFG-P4-012`, `RUN-P4-012`, `AR-P4-019`, `TO-P5-003`, `TO-P5-003-CORRECTIVE-001`

   **These are not byte-identical duplicates.** CONTROL verified that the repeated blocks differ in `canonical_name`, `traceability` and in one case character encoding. They are therefore **conflicting duplicate records for the same Stable ID**, not mechanical repetition. See §3.4 and §4.

3. **Mislabeled record**, lines 1609–1614: a record carries `stable_id: TO-P4-012` together with `entity_type: BR`, `canonical_name: Build Report — P4 Authoritative Knowledge-Time Semantic & Persistence Correction`, and `artifact_path: docs/build-reports/BR-P4-010.md`.

   CONTROL verified that **`BR-P4-010` has no other registry record anywhere in `artifacts.yaml`**. The artifact exists on disk (`docs/build-reports/BR-P4-010.md`) and is referenced by `AR-P4-017`. The mislabel therefore both duplicates `TO-P4-012` and leaves `BR-P4-010` unregistered.

### F-04 — `README.md` claims a stale active Task Order

`README.md` line 20 states:

> **Active Task Order:** `TO-P2-018` — AUTHORIZED TO EXECUTE, investigation only; Producer report `BR-P2-018` is under CONTROL correction cycle …

This contradicts:

- `docs/state/CURRENT_CHECKPOINT.json` line 25 — `"active_task_order": "TO-P2-019"`;
- the same line 21 — `"last_approved_task_order": "TO-P2-019"`;
- `docs/task-orders/TO-P2-018.md` line 10 and `docs/audits/AR-P2-AUDIT-020.md` §6 — `TO-P2-018` is `VERIFIED / COMPLETE`;
- `README.md` line 116 itself, which already states that `TO-P2-018` is `VERIFIED / COMPLETE` and that `TO-P2-019` was activated.

This is precisely the `README`-versus-Checkpoint drift class that `TO-GOV-008` root-caused and `ADR-GOVERNANCE-012` was established to prevent.

### F-05 — `phases.yaml` lifecycle metadata contradicts other authoritative records

`docs/registry/phases.yaml` lines 478–489 record `STEP-P5-002` with:

```
    completed_task_order: TO-P5-003
    completion_audit: AR-P5-003
```

This contradicts:

- `docs/registry/artifacts.yaml` lines 972–983, where `STEP-P5-002` is registered with `TO-P5-002` / `AR-P5-002`;
- `docs/phases/PH-P5.md`, which closes `STEP-P5-002` under `AR-P5-002`;
- `docs/registry/phases.yaml` lines 494–513, where `STEP-P5-003` itself is registered with `TO-P5-003` / `AR-P5-003`.

### F-06 — Stale status-bearing document

`docs/build-reports/BR-P5-008.md` carries the header status:

```
**Producer status:** `PRODUCED — pending CONTROL independent verification`
```

`docs/audits/AR-P5-009.md` records `BR-P5-008` as `VERIFIED`, and `TO-P5-006` / `STEP-P5-006` as `VERIFIED / COMPLETE` and `COMPLETE / VERIFIED` respectively. `CURRENT_CHECKPOINT.json` lists `BR-P5-008` in `verified_artifacts`. The document is therefore stale, and `artifacts.yaml` line 2115 still records it as `PRODUCED`.

### F-07 — Supplemental / staging registry not retired

`docs/registry/phase2-artifacts.yaml` is a supplemental/staging registry whose content has been absorbed into the canonical registry, yet it has not been marked superseded/retired. This is checklist item 5 of `ADR-GOVERNANCE-012` §2.

### F-08 — Inconsistent text encoding

Some governance artifacts store U+2014 (EM DASH) as mojibake (`â€"`), while others store it correctly as UTF-8. Confirmed instances:

- `docs/state/CHANGE_LEDGER.yaml` lines 498, 578, 600, 2238 and the closing entries
- `docs/build-reports/BR-P5-008.md` line 1 and line 5
- `docs/audits/AR-P2-AUDIT-020.md` line 1
- `docs/registry/artifacts.yaml` line 1755 and the `TO-P5-003-CORRECTIVE-001` duplicate block

This corrupts searchability and display but, per §4, must not be used as an excuse to reword content.

## 3. Required work

### 3.1 Restore YAML parse validity (F-01, F-02)

For every file in F-01 and F-02, repair the defect **minimally** so that the file parses with a standard YAML parser, while preserving the intended value exactly.

Required approach:

- **Unquoted colon in a scalar value:** quote the scalar (single quotes preferred where the value contains no single quote) so the intended string is preserved verbatim. Do not rewrite, shorten, translate or "improve" the value.
- **Block-sequence indentation:** align the offending sequence entry with its siblings. Change indentation only.

Do **not** restructure a registry, rename a key, reorder records, or introduce a new YAML dialect, anchor, alias or merge key.

### 3.2 Repair the `artifacts.yaml` structural defect (F-03.1)

Split line 1637 so that `- stable_id: AR-P3-009` begins on its own line at the correct sequence indentation, leaving the preceding record's `status:` value intact.

### 3.3 Recover the mislabeled record (F-03.3)

Correct lines 1609–1614 so the record identifies the artifact it actually describes:

```
  - stable_id: BR-P4-010
    canonical_name: Build Report — P4 Authoritative Knowledge-Time Semantic & Persistence Correction
    entity_type: BR
    artifact_path: docs/build-reports/BR-P4-010.md
    traceability: TO-P4-010 / PH-P4 / STEP-P4-006 / AR-P4-017
    status: VERIFIED
```

Preserve the existing `traceability` string and the existing `VERIFIED` status. This correction is required because `BR-P4-010` is otherwise unregistered, and `docs/build-reports/BR-P4-010.md` and `AR-P4-017` are existing authoritative artifacts.

### 3.4 Reconcile the conflicting duplicate records (F-03.2)

For each duplicated Stable ID listed in F-03.2, reconcile to **exactly one** registry record.

**Mandatory reconciliation discipline — this is the governing constraint of this Task Order:**

1. Determine the correct `canonical_name`, `traceability` and `status` from **authoritative evidence only**: the artifact file named in `artifact_path`, the Audit Report that closed it, the Build Report, the relevant Phase definition, and `docs/state/CHANGE_LEDGER.yaml`.
2. Where the authoritative closure evidence establishes one record as reflecting the final verified closure state, keep that record, and remove the other.
3. If the two records carry **different traceability strings that are each individually true of different lifecycle points**, keep the single record that reflects the **final verified closure state**, and record the consolidated traceability.
4. **STOP CONDITION:** if for any pair the correct resolution cannot be established from authoritative evidence — because the two records assert mutually incompatible identities, statuses or artifact paths, and no authoritative artifact resolves which is correct — then you MUST:
   - leave both records untouched,
   - raise the item in `BR-GOV-010` as an explicit unresolved conflict with the exact competing values,
   - and list precisely which authoritative source would resolve it.

   You MUST NOT select a winner by plausibility, recency of position in the file, or assumption.
5. Do not renumber, reuse, merge or split any Stable ID. Do not invent a new ID for any record.

### 3.5 Correct the stale lifecycle metadata (F-05)

Correct `docs/registry/phases.yaml` lines 478–489 so that `STEP-P5-002` records the values established by the authoritative closure evidence. Use only already-established repository vocabulary for `status` / `authorization_state`.

### 3.6 Correct the stale status-bearing document (F-06)

Update the `BR-P5-008` header status line in `docs/build-reports/BR-P5-008.md` to reflect the independently verified state recorded by `AR-P5-009`, and reconcile `artifacts.yaml` line 2115 accordingly.

**Historical-evidence constraint:** the body of `BR-P5-008.md` — including its Producer findings, counts and evidence — MUST remain unchanged. Only the stale lifecycle status line may be corrected, and the correction must be disclosed in `BR-GOV-010` with the exact before/after text. This follows `ADR-GOVERNANCE-014` §9.

### 3.7 Correct the `README.md` active-Task-Order drift (F-04)

Correct `README.md` line 20 so the repository-status summary matches `docs/state/CURRENT_CHECKPOINT.json`. Use only value vocabulary already present in the Checkpoint. Do not add new claims, forecasts or narrative.

### 3.8 Retire the supplemental registry (F-07)

Mark `docs/registry/phase2-artifacts.yaml` as superseded/retired using **existing repository vocabulary only**, preserving its historical content unchanged. If the correct retirement vocabulary is not already established in the repository, STOP that item and raise it in `BR-GOV-010` as an Open Question rather than inventing a status value.

### 3.9 Encoding correction (F-08)

Repair the mojibake U+2014 sequences listed in F-08 so the affected files store correct UTF-8.

**Constraint:** the correction must be character-for-character limited to the corrupted sequence. Do not reflow, reword, re-wrap, or reformat any line. Where repair would alter any other character, leave that instance untouched and report it.

### 3.10 Machine verification (all findings)

Provide, as part of the evidence, a reproducible check demonstrating that:

- every file listed in F-01 and F-02 now parses successfully with a standard YAML parser;
- every `stable_id` in `docs/registry/artifacts.yaml` is unique;
- every file listed in F-08 no longer contains the corrupted sequence.

The check must be reproducible from the repository alone. Do not report a passing result without the actual command and its actual output.

## 4. Reconciliation and evidence discipline

1. **No guessing.** Every semantic correction (identity, status, traceability) must cite the authoritative artifact that establishes it.
2. **No semantic invention.** Do not introduce a new status value, lifecycle state, entity type, Stable ID convention, or registry field.
3. **No history rewrite.** Historical evidence remains immutable. Later corrections are recorded as later state, not as retroactive edits to what a historical report said at the time.
4. **Minimum change.** Change only what is required to satisfy the finding. Do not opportunistically reformat, reorder, or "tidy" a file.
5. **Disclosure.** For every changed line that carries a *meaning* (not pure syntax), record the exact before/after text in `BR-GOV-010`.
6. **Stop-and-report.** Where the correct resolution cannot be established from authoritative evidence, stop that item and report it. Do not resolve a genuine conflict by personal interpretation — this is the `ROLE_CONTRACT_CONTROL_REVIEWER_V2.md` §14 STOP THAT PART rule.

## 5. Explicit scope exclusions

This Task Order authorizes **no**:

- change to the Constitution, `DOC-V2-ARCH-001`, any ADR, `ARTIFACT_PROTOCOL_V2.md`, `AI_CONTINUATION_PROTOCOL_V2.md`, or any Role Contract;
- change to any ratified semantic specification (`DOC-P4-002`, `DOC-P4-003`, `ADR-QUANTITATIVE-001`, `ADR-QUANTITATIVE-002`, `NUMERIC_POLICY_P4_001`);
- creation, renumbering, merging, splitting or retirement of any Stable ID;
- new artifact class, role, lifecycle state, status vocabulary, or registry field;
- reopening, re-verification or re-closure of any Phase, Step, Task Order, Build Report or Audit Report;
- change to any `CURRENT_CHECKPOINT.json` *value* other than what ADR-GOVERNANCE-012 closure synchronization requires;
- **`TO-GOV-010` itself registering or reconciling `BR-P2-019`**: `BR-P2-019` currently exists only on the unmerged branch `producer/to-p2-019-br-p2-019` and its lifecycle is governed separately by `TO-P2-019` → `BR-P2-019` → `AR-P2-AUDIT-021`. Do not touch it;
- implementation code, tests, migrations, contracts, schemas, configuration or infrastructure change;
- VPS / SentinelX / deployment / restart / migration / runtime operation;
- provider API activity, market-data collection, trading, capital, custody, leverage or Forex activity;
- Phase 6 or any later Phase activation.

If satisfying a finding appears to require any excluded change, STOP that item and report it as a governance boundary rather than proceeding.

## 6. Required output

Deliver **`BR-GOV-010`** containing:

1. Exact repository baseline revision inspected (commit SHA) for each file changed.
2. A finding-by-finding report, `F-01` through `F-08`, stating for each: what was changed, the exact before/after for every meaning-bearing line, and the authoritative evidence citation.
3. The complete unresolved-conflict list from §3.4 with exact competing values and the authoritative source that would resolve each.
4. The machine-verification output required by §3.10.
5. Explicit confirmation that §5 exclusions were respected.
6. Explicit non-claims: no verification, no closure, no ratification, no Phase/Step activation.

Additionally:

7. One `TO-GOV-010` registry record in `docs/registry/artifacts.yaml` is already established by CONTROL (§7 below); do not duplicate it.
8. Append one Change Ledger entry to `docs/state/CHANGE_LEDGER.yaml` recording this corrective action, including `affected_ids` and `from_state` / `to_state` for every reconciled record.
9. **`ADR-GOVERNANCE-012` Mandatory Peripheral Synchronization Checklist** — because this Task Order's entire subject is peripheral synchronization, `BR-GOV-010` MUST report against each of the five checklist items **individually**:
   1. `README.md` versus `CURRENT_CHECKPOINT.json`
   2. `docs/registry/artifacts.yaml` stale pre-activation statuses
   3. specialized registries (`components.yaml`, `contracts.yaml`, `requirements.yaml`, `tests.yaml`, `runtime.yaml`, `database.yaml`, `security.yaml`, `configuration.yaml`, `performance.yaml`, `observability.yaml`)
   4. standalone status-bearing documents
   5. supplemental / staging registry disposition

   A report that addresses the checklist without individually confirming each item is incomplete and will not be accepted as `VERIFIED`.

## 7. CONTROL-established registry record

CONTROL has established the following record in `docs/registry/artifacts.yaml` under its own registry authority, so that this Task Order is traceable:

```
  - stable_id: TO-GOV-010
    canonical_name: Governance Artifact Parse Integrity & Status-Drift Reconciliation
    entity_type: TO
    artifact_path: docs/task-orders/TO-GOV-010.md
    traceability: TO-GOV-009 / AR-GOV-005 / ADR-GOVERNANCE-012 / ADR-GOVERNANCE-013
    status: AUTHORIZED TO EXECUTE
```

CONTROL notes for the record that `docs/registry/artifacts.yaml` does not currently parse as YAML, so this record cannot yet be machine-read. Restoring parse validity is F-01 / F-02 of this Task Order, and the record becomes machine-readable upon successful execution.

## 8. Acceptance criteria

`BR-GOV-010` is acceptable only when, verified from the repository:

1. Every file in F-01 and F-02 parses successfully with a standard YAML parser, demonstrated by actual command output.
2. `docs/registry/artifacts.yaml` contains no duplicate `stable_id`.
3. `BR-P4-010` is registered exactly once, correctly labeled.
4. Every reconciled duplicate preserves the final verified closure state and cites its authoritative evidence.
5. Every unresolved conflict is explicitly reported rather than silently resolved.
6. `README.md` line 20 matches `CURRENT_CHECKPOINT.json`.
7. `STEP-P5-002` metadata matches the authoritative closure evidence.
8. `BR-P5-008` status is consistent with `AR-P5-009`, with its body unchanged.
9. The `ADR-GOVERNANCE-012` checklist is individually confirmed, item by item.
10. No §5 exclusion was violated.
11. Every meaning-bearing change is disclosed with exact before/after text.

## 9. Audit, closure and lifecycle

Lifecycle: `TO-GOV-010 → BR-GOV-010 → AR-GOV-010 → CONTROL-owned closure synchronization`.

- PRODUCER must not self-declare `VERIFIED` or `COMPLETE`.
- CONTROL independently audits `BR-GOV-010` and the underlying repository evidence, and alone owns closure synchronization under `ADR-GOVERNANCE-012`.
- No historical evidence is rewritten. `PH-P0` through `PH-P5`, their Steps, and all closed Task Orders remain closed and are not reopened.
- `PH-P5` remains `ACTIVE / AUTHORIZED`; `STEP-P5-006` remains `COMPLETE / VERIFIED`; `TO-P2-019` remains the active Task Order; `STEP-P5-007` remains `NOT ACTIVATED`.

## 10. Standing rules

`ADR-GOVERNANCE-013` R1–R7 and `ADR-GOVERNANCE-014` apply.

Carry the authorized work to the natural independent-audit boundary. Ordinary difficulty, a large number of affected files, or an awkward YAML construct is not by itself a stop. Apply the R7 maximum-quality standard: minimum change, exact evidence, complete edge coverage, and no unsupported conclusions.

Preserve truthful incomplete state. Where §3.4's stop condition is met, the correct outcome is an explicitly reported unresolved conflict, not a guessed resolution.

## 11. FORMAL ENGLISH MESSAGE READY TO SEND — PRODUCER

**TO:** PRODUCER / ARCHITECT-BUILDER — ROL-V2-002
**FROM:** CONTROL / REVIEWER — ROL-V2-001
**SUBJECT:** TO-GOV-010 Activated — Governance Artifact Parse Integrity & Status-Drift Reconciliation

Producer,

CONTROL has completed continuity reconstruction against the current authoritative Source of Truth and found a class of governance-artifact integrity defects that are recorded nowhere in the repository. `docs/registry/artifacts.yaml` — the authoritative Stable ID and traceability registry — does not parse as YAML, and twelve further registry and state files do not parse either. `README.md` also still advertises `TO-P2-018` as the active Task Order, and one Build Report carries a superseded status.

`TO-GOV-010` is issued and activated to repair this. It is a bounded repair-and-record Task Order. It authorizes no new capability, no Phase or Step activation, no architecture or governance semantic change, and no runtime activity.

Read `docs/task-orders/TO-GOV-010.md` in full; it is the operative authority and it enumerates every finding with exact file and line evidence. Repair each defect minimally, preserving intended values exactly and using only established repository vocabulary.

Two constraints govern this work and are not negotiable:

1. **Conflicting duplicate records must be resolved from authoritative evidence only.** `TO-P4-012`, `BR-P4-012`, `TST-P4-012`, `DB-P4-012`, `CFG-P4-012`, `RUN-P4-012`, `AR-P4-019`, `TO-P5-003` and `TO-P5-003-CORRECTIVE-001` each appear twice with **differing** metadata. Where the correct resolution cannot be established from the authoritative artifacts, STOP that item, keep both records untouched, and report the exact competing values. Do not choose a winner by plausibility or by position in the file.
2. **`BR-P4-010` is currently unregistered** — its record was mislabeled with `stable_id: TO-P4-012`. Correct the label; do not remove the record.

Deliver `BR-GOV-010` with the finding-by-finding before/after disclosure, the unresolved-conflict list, the machine-verification output required by §3.10, and the `ADR-GOVERNANCE-012` checklist confirmed item by item. No historical evidence may be rewritten. Do not self-declare VERIFIED or COMPLETE; CONTROL audits independently and alone owns closure synchronization.

Respectfully,
ROL-V2-001 — CONTROL / REVIEWER

---END---
