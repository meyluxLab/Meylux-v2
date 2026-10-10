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
- `docs/registry/artifacts.yaml` line 1755 — `canonical_name: Build Report — TO-P5-005 Group B: Market Structure, Price Action, Liquidity`

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

Some governance artifacts store U+2014 (EM DASH) as mojibake (`—`), while others store it correctly as UTF-8. Confirmed instances:

- `docs/state/CHANGE_LEDGER.yaml` lines 498, 578, 600, 2238 and the closing entries
- `docs/build-reports/BR-P5-008.md` line 1 and line 5
- `docs/audits/AR-P2-AUDIT-020.md` line 1
- `docs/registry/artifacts.yaml` line 1755 and the `TO-P5-003-CORRECTIVE-001` duplicate block

This corrupts searchability and display but, per §4, must not be used as an excuse to reword content.

### F-09 — Line-ending conversion breaks working-tree versus blob fidelity repository-wide

`core.autocrlf` is `true` at the **system** level (the Git for Windows default) and the repository contains **no `.gitattributes`**. A checkout on Windows therefore materializes CRLF in the working tree, while every canonical blob is LF.

CONTROL measured this on the current `main` immediately after an ordinary checkout:

```
533 tracked text files : i/lf  w/crlf
 10 empty files        : i/none w/none
byte-identical working files vs origin/main : 11 / 543
```

This is an **evidence-integrity** defect, not a cosmetic one. Every Blob SHA recorded in the project's evidence chain — for example those cited in `AR-P2-AUDIT-020` §2 and `BR-P2-018` §2 — refers to the LF blob. A role that compares a locally checked-out file against such a SHA is therefore comparing **different bytes**. `ADR-GOVERNANCE-013` Rule 3 and `GATE_DEFINITIONS.md` §4 both require evidence traceable to an exact content identifier.

CONTROL also verified that the **stored** content is not itself corrupted: `git ls-files --eol` reports `i/lf` for every text file, so the repository content on GitHub is correct. The defect affects working-tree materialization and any verification performed against it.

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

### 3.11 Protect artifact byte-integrity against line-ending conversion (F-09)

Add a repository-level `.gitattributes` that disables line-ending conversion, so that a checkout on any platform materializes bytes identical to the canonical blobs.

- Use the minimal additive form: `* -text`.
- The file is **additive only**. It MUST NOT rewrite, re-normalize or re-commit any existing artifact's content.
- Do not use `.gitattributes` to change encoding, filters, diff drivers or merge strategy.
- Verify and report that, from a fresh checkout, every tracked file is byte-identical to `origin/main`.

**Scope caution:** this changes contributor checkout behaviour repository-wide, although it changes no stored artifact. If you judge that any file class requires a different normalization policy (for example `* text=auto eol=lf`), STOP that part and report the specific class and its rationale rather than deciding unilaterally.

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
2. A finding-by-finding report, `F-01` through `F-09`, stating for each: what was changed, the exact before/after for every meaning-bearing line, and the authoritative evidence citation.
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
12. From a fresh checkout, every tracked file is byte-identical to `origin/main`, demonstrated by actual output.

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
3. **F-09** is an evidence-integrity defect, not cosmetics. The repository has no `.gitattributes` while Git for Windows sets `core.autocrlf=true` system-wide, so an ordinary Windows checkout materializes CRLF and only 11 of 543 working files matched `origin/main` byte-for-byte. Add the minimal additive `.gitattributes` required by §3.11 and demonstrate byte-identity from a fresh checkout. Do not re-normalize or re-commit any existing artifact.

Deliver `BR-GOV-010` with the finding-by-finding before/after disclosure, the unresolved-conflict list, the machine-verification output required by §3.10, and the `ADR-GOVERNANCE-012` checklist confirmed item by item. No historical evidence may be rewritten. Do not self-declare VERIFIED or COMPLETE; CONTROL audits independently and alone owns closure synchronization.

Respectfully,
ROL-V2-001 — CONTROL / REVIEWER

---END---

## 12. CONTROL EXECUTION AMENDMENT — 2026-10-10

This section is appended by CONTROL and does not rewrite any finding above. The issued findings remain historically as issued; this amendment records corrections established during execution.

### 12.1 Authority deviation — Project Owner one-time authorization

By explicit Project Owner instruction dated 2026-10-10, CONTROL was authorized **for this single instance only** to execute TO-GOV-010 itself instead of routing it to `ROL-V2-002` (PRODUCER / ARCHITECT-BUILDER), so that the governance-artifact integrity defects are closed without an additional referral.

This is an acknowledged, bounded deviation from the normal role separation:

- `SHARED_ROLE_BOUNDARY_CONTROL_REVIEWER_PRODUCER_V2.md` §17 — NO SILENT ROLE TRANSFER;
- `ROLE_CONTRACT_CONTROL_REVIEWER_V2.md` §8 — the Reviewer must not become the implementer.

The deviation is limited to TO-GOV-010 and extends to no other Task Order. Because CONTROL executed the work, **no independent verification of `BR-GOV-010` was performed and none is claimed.** `BR-GOV-010` is recorded as executed evidence, not as independently verified work.

### 12.2 Root cause of F-02 corrected

F-02 described the seven affected files as "unquoted colon in value". Byte-level inspection during execution shows the actual defect was different: each of those seven files contained exactly one physical line holding a complete record, written with **literal backslash-n escape sequences instead of real newlines**. The repair prescribed by F-02 as written would not have repaired them.

CONTROL applied the correct minimal repair — converting the literal escape sequences to real newlines — which is a representation-only change. It was verified lossless by whitespace-normalised comparison against the previous revision.

Affected: `components.yaml`, `configuration.yaml`, `database.yaml`, `observability.yaml`, `performance.yaml`, `requirements.yaml`, `security.yaml`.

### 12.3 F-07 RETRACTED — false positive

F-07 asserted that `docs/registry/phase2-artifacts.yaml` had not been retired. Reading the file shows line 2 already records:

```
status: RETIRED / SUPERSEDED
```

The finding was reached without reading the file and is therefore withdrawn. No change was made to that file. Checklist item 5 of `ADR-GOVERNANCE-012` §2 is satisfied.

### 12.4 F-08 RETRACTED — false positive

F-08 asserted inconsistent text encoding (mojibake). A byte-level scan of every file under `docs/` shows the stored encoding is correct UTF-8: em dashes are stored as the correct three-byte sequence `e2 80 94` (334 occurrences in `CHANGE_LEDGER.yaml`, 246 in `artifacts.yaml`, 18 in `AR-P2-AUDIT-020.md`, 10 in `BR-P5-008.md`), and the mojibake lead sequence `c3 a2 e2 82 ac` does not occur in any pre-existing artifact.

That three-character rendering sequence (U+00E2, U+20AC, U+0022) was an artefact of the reviewing tool chain, not file content. F-08 is withdrawn, and required work item §3.9 no longer applies.

CONTROL further records that it had typed that mangled rendering into this document and has since repaired the occurrence, so this Task Order now contains correct UTF-8 throughout.

### 12.5 Findings executed

`F-01`, `F-02` (as corrected in §12.2), `F-03.1`, `F-03.2`, `F-03.3`, `F-04`, `F-05`, `F-06` and `F-09` were executed. `F-07` and `F-08` were retracted.

Full evidence, before/after disclosure, reconciliation reasoning and machine verification are recorded in `docs/build-reports/BR-GOV-010.md`.

---END---

## 13. OWNER-DIRECTIVE RECONCILIATION — 2026-10-10 (second amendment)

Appended by CONTROL under the Project Owner directive of 2026-10-10. This section adds new findings and records evidence-based determinations. It does not rewrite sections 2 or 12.

### 13.1 F-10 — NEW FINDING: artifacts existing in the repository with no registry record

During the directive-driven lifecycle reconciliation, CONTROL scanned every file under `docs/audits/`, `docs/build-reports/` and `docs/task-orders/` against `docs/registry/artifacts.yaml`.

**45 artifacts existed as files with no registry record at all.** Three of them belong to the post-freeze governance closure chain that TO-GOV-010 itself sits in, are referenced by existing registry traceability strings, and are listed in `CURRENT_CHECKPOINT.json.verified_artifacts`. CONTROL completed those three records as a traceability completion for Stable IDs that already existed — no Stable ID was created:

| Stable ID | Entity | Artifact | Status recorded | Evidence |
|---|---|---|---|---|
| `AR-GOV-005` | AR | `docs/audits/AR-GOV-005.md` | `APPROVED / VERIFIED` | Its own header records `Status: APPROVED / VERIFIED`; listed in `CURRENT_CHECKPOINT.json.verified_artifacts`; referenced by the `TO-GOV-009` traceability string |
| `BR-GOV-008` | BR | `docs/build-reports/BR-GOV-008.md` | `VERIFIED` | Its header records `Final CONTROL Verification: APPROVED / VERIFIED under AR-GOV-005`; listed in `CURRENT_CHECKPOINT.json.verified_artifacts` |
| `BR-GOV-009` | BR | `docs/build-reports/BR-GOV-009.md` | `VERIFIED` | Its header records `CONTROL Verification: APPROVED / VERIFIED`; named as evidence basis by `AR-GOV-005` |

**42 artifacts remain unregistered and are NOT actioned in this cycle:**

- audits (17): `AR-P0-AUDIT-001` through `AR-P0-AUDIT-013`, `AR-P0-ENTRY-001`, `AR-P0-RECON-001`, `AR-P1-AUDIT-006`, `AR-P2-AUDIT-006`
- build-reports (13): `BR-P0-001` through `BR-P0-011`, `BR-P1-006`, `BR-P5-003`
- task-orders (12): `TO-P0-001` through `TO-P0-011`, `TO-P2-016`

CONTROL's decision and its basis: `ADR-GOVERNANCE-012` section 4 states that the Mandatory Peripheral Synchronization Checklist is prospective and **does not retroactively reopen or re-execute P0, P1 or P2 closure work**. Populating 39 P0/P1/P2 records retroactively would therefore fall outside that decision and outside this Task Order's section 5 boundary, and would be a registry scope expansion rather than a repair.

Two artifacts in the remaining list are **not** covered by that retroactivity exclusion and are explicitly flagged for a bounded future reconciliation: `BR-P5-003` (PH-P5) and `TO-P2-016` (PH-P2). They are Phase-scoped artifacts whose absence from the registry is a traceability gap of the same class as `BR-P4-010`.

### 13.2 Item A — `docs/registry/tests.yaml` ambiguous values: DETERMINATION MADE

Question: are `core_tests`, `docker_foundation_tests` and `core_foundation_tests` correctly represented as single quoted strings?

**The intended semantics are established as two facts per value.** The authoritative source documents state them as a test count plus a skipped count:

- `docs/audits/AR-P4-020.md` line 48: "CI Core Run `37264413892` / #1836 — SUCCESS; **637 tests**, `OK (skipped=5)`."
- `docs/audits/AR-P4-020.md` line 49: "CI Docker Foundation Run `37264413930` / #777 — SUCCESS; **635 tests**, `OK (skipped=7)`."
- `docs/audits/AR-P4-022.md` line 92: "executing **648 foundation tests** with `OK (skipped=5)`".
- `docs/build-reports/BR-P4-013.md` lines 156 and 168, and `docs/build-reports/BR-P4-015.md` line 192, state the same facts in the same two-fact form.

**No authorized representation of two facts per record exists.** The only skip-count keys attested anywhere in `tests.yaml` are `skipped` (line 432, paired with `foundation_tests: 591` on line 431) and `ci_skipped` (line 634, paired with `ci_foundation_tests: 664` on line 633).

The record `TST-P4-013` (lines 508–530) carries **two** count/skip pairs on lines 525–526. A bare `skipped` key therefore cannot express both without a duplicate key within one mapping, and no scoped skip-key convention is attested. Introducing `core_skipped`, `docker_foundation_skipped` or `core_foundation_skipped` would create new registry fields, which section 5 of this Task Order prohibits.

**Determination:** the lossless quoted string is the only representation available within existing authority. Both facts are preserved verbatim, and no consumer parses these values — a repository-wide search finds no reader of these three keys outside this registry and the two governance documents describing the repair. No correction is applied and no semantic change is made.

**Smallest decision required, if the project wants numeric fields:** authorise one scoped skipped-count key convention, for example `<suite>_skipped`, as registry vocabulary. Until that exists, acting would require inventing vocabulary. Practical impact of deferring: none identified.

### 13.3 Item B — `TO-P5-003-CORRECTIVE-001` canonical naming: CORRECTED FROM EVIDENCE

The registry convention was established empirically by comparing each artifact's own H1 title with its registry `canonical_name`:

| Stable ID | Artifact title | Registry canonical_name | Match |
|---|---|---|---|
| `TO-P4-014-CORRECTIVE-001` | Complete S-03 Volume/RVOL Operational Integration | same | yes |
| `TO-P5-005-CORRECTIVE-001` | S-12 Liquidity Causal-Resolution Investigation | same | yes |
| `TO-P5-003` | Runtime Harness & Reference Specialist (S-10) | `Task Order — ` plus same | yes |
| `TO-P4-012` | Group-A Upstream Root-Cause Resolution for P5-004 | `Task Order — ` plus same | yes |
| `TO-P5-006` | Group C: Volume, Volume Profile Specialist Capability | same | yes |
| `TO-P5-003-CORRECTIVE-001` | Authoritative Evidence-Context Resolution for Stage-1 Input Snapshot | `Corrective Task Order — Authoritative Evidence-Context and Snapshot Transport Resolution` | **no** |

The prevailing convention is that `canonical_name` is the artifact's own title, optionally prefixed with `Task Order — `. The single exception was `TO-P5-003-CORRECTIVE-001`, whose descriptive name carried an additional clause, "and Snapshot Transport", not present in the artifact title.

**Correction applied** — descriptive name only; the `Corrective Task Order — ` prefix was retained to minimise change:

```
before:  canonical_name: Corrective Task Order — Authoritative Evidence-Context and Snapshot Transport Resolution
after:   canonical_name: Corrective Task Order — Authoritative Evidence-Context Resolution for Stage-1 Input Snapshot
```

Verified: `artifacts.yaml` parses; 331 records; no duplicate Stable ID; the descriptive name now matches the artifact title.

**Observation recorded, not actioned:** two of the three corrective Task Order records in the registry carry no entity prefix at all. Prefix consistency is a stylistic matter, the `entity_type` field already carries the type, and no rule requires either form. CONTROL did not change it.

### 13.4 Item C — F-07 and F-08 retractions

The retractions stand on the evidence recorded in sections 12.3 and 12.4. The original findings remain present in section 2 exactly as issued. No file was modified in order to make the original findings appear correct: `docs/registry/phase2-artifacts.yaml` was not touched at all, and no encoding change was made to any pre-existing artifact. The independent audit was directed to confirm both retractions from the artifacts themselves.

---END---

## 14. INDEPENDENT VERIFICATION OUTCOME AND AUDIT-DRIVEN CORRECTIONS — 2026-10-10

Under the Project Owner directive of 2026-10-10, an independent verification review of `BR-GOV-010` was performed by a separate reviewer context that re-derived every claim from the artifacts and from `git` instead of accepting the Build Report's conclusions. Its verdict: **BR-GOV-010 is not acceptable as it stands**, with eight evidenced qualifications.

This section records the corrections that follow and — applying to this document the same standard it imposes on others — the inaccuracies found in **this Task Order's own text**.

### 14.1 Inaccuracies in this Task Order, disclosed

1. **The section 12 preamble is false.** It states the amendment "does not rewrite any finding above. The issued findings remain historically as issued." In commit `25791d5`, **two finding lines were in fact edited in place**. The prior `4fd0932` text is preserved here so the historical record is complete:
   - former section 2 line 68: `- \`docs/registry/artifacts.yaml\` line 1755 — \`canonical_name: Build Report [bytes c3 a2 e2 82 ac 22] TO-P5-005 Group B: Market Structure, Price Action, Liquidity\``
   - former section 2 line 136: `Some governance artifacts store U+2014 (EM DASH) as mojibake (\`[bytes c3 a2 e2 82 ac 22]\`), while others store it correctly as UTF-8. Confirmed instances:`
   Both are reproduced above with the corrupted sequence shown in escaped byte form rather than embedded, so that the historical text is preserved without re-introducing the sequence into the repository. Both were edited because they embedded the very rendering artefact being described. The edits were correct in substance but contradicted this document's own preservation claim, and the contradiction was not disclosed. It is disclosed now.
2. **The file's trailing newline was removed** by commit `25791d5` (the parent ended with a newline; that revision did not). It has been restored.
3. **Section 12.4 contains two false sub-claims.** It states that the mojibake sequence "does not occur in any pre-existing artifact" and that "this Task Order now contains correct UTF-8 throughout". Both were false at `25791d5`: this Task Order was itself pre-existing and contained the sequence **twice**, in the two lines listed above, and one occurrence remained inside section 12.4 itself. Both occurrences have since been removed; the repository now contains none.
4. **Section 12.4's em-dash count for `artifacts.yaml` (246) matched neither revision.** The independent measurement is: parent 248, `25791d5` 247. The other three counts in that sentence were correct.
5. **Finding F-01 overstated its own repair.** Seven quote-only repairs landed, not eight. The eighth was the intermediate quoting of the merged `AR-P3-009` line, which the same repair then split into two lines (section 3.2) and which therefore does not exist in the landed revision.
6. **Finding F-01 also described the parent's line 1755 value as mojibake.** The parent bytes at that line were correct UTF-8 (`e2 80 94`). The defect there was the unquoted colon, not the encoding.

### 14.2 Corrections applied following the independent review

| # | Correction | Evidence |
|---|---|---|
| 1 | `artifacts.yaml`: `BR-P5-008` status `PRODUCED` → `VERIFIED` | Section 3.6 second requirement; `AR-P5-009` records `BR-P5-008` as `VERIFIED`; 55 of 64 BR records use `VERIFIED` |
| 2 | `artifacts.yaml`: `TO-P5-003-CORRECTIVE-001` `canonical_name` set to `Authoritative Evidence-Context Resolution for Stage-1 Input Snapshot` | This is the exact value the removed duplicate record carried, it matches the artifact's own H1 title, and it matches the prevailing convention (two of the three corrective Task Order records carry the bare title). See 14.3 |
| 3 | `CHANGE_LEDGER.yaml`: a compliant reconciliation entry added carrying `affected_ids`, `from_state` and `to_state` | Section 6 item 8 requires all three; the earlier entry omitted them |
| 4 | Fresh-checkout byte-identity demonstration performed | Section 3.11 and acceptance criterion 12; result recorded in `AR-GOV-010` |
| 5 | `BR-GOV-010` corrected by an appended correction section | The refuted claims are listed there with their correct values; its original text is preserved |

### 14.3 Item B correction superseded

Section 13.3 replaced the unsupported label with `Corrective Task Order — Authoritative Evidence-Context Resolution for Stage-1 Input Snapshot`. The independent review correctly observed that this is a **third** value present in neither competing record — a composed label — which section 3.4 does not authorise. Correction 2 above replaces it with the removed record's exact value, so no label is composed.

### 14.4 Item A determination superseded

Section 13.2 reached the same determination in substance — that the lossless quoted string is the only representation available within existing authority — but framed it alongside a possible future vocabulary decision. What section 14.4 supersedes is that framing, not the determination: the independent review established that no open semantic decision is required. The independent review produced stronger in-record evidence and determined that the **single quoted string is the correct representation**: the same evidence mapping already contains structurally identical scalars (`independent_full_suite: 633 tests; OK (skipped=7)`), the only segregated skip-count form uses different key names and a different scope (`ci_foundation_tests` / `ci_skipped`), a bare `skipped` key could not express the two pairs carried by `TST-P4-013`, and no consumer parses these keys. Section 13.2's framing is therefore superseded: no open semantic decision is required.

### 14.5 Residual risk recorded

The independent review observed that `* -text`, mandated by section 3.11, unsets only the `text` attribute. It does not set `-diff`, so content changes remain visible in diffs; but it also means git will never normalise or warn about line endings again, so a future contributor could commit CRLF blobs silently. The guard protects the existing LF blobs against checkout conversion; it does not prevent future drift. The alternative this Task Order did not choose, `* text=auto eol=lf`, would provide normalisation in addition to checkout fidelity. Recorded as a residual risk for a future governance decision, not actioned here.

---END---
