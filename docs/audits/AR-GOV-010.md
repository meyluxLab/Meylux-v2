# AR-GOV-010 — CONTROL Independent Verification — BR-GOV-010 / TO-GOV-010

**Status:** `APPROVED / VERIFIED`
**Audit ID:** `AR-GOV-010`
**Auditor / Verification Role:** `ROL-V2-001` — CONTROL / REVIEWER
**Verification performed by:** a separate independent reviewer context, engaged under the Project Owner directive of 2026-10-10, whose findings CONTROL records here
**Subject:** `BR-GOV-010`, `TO-GOV-010`, and the changes landed by commit `25791d5`
**Related:** `ADR-GOVERNANCE-012`, `ADR-GOVERNANCE-013`, `ADR-GOVERNANCE-014`

## 1. Why a separate context was used

CONTROL executed `TO-GOV-010` itself under a one-time Project Owner authorization. A role cannot verify its own execution, and `GATE_DEFINITIONS.md` §5 forbids substituting self-certification for independent verification. The Project Owner therefore directed that a distinct reviewer context perform the verification.

The verification was carried out by a separate reviewer context that shared no reasoning with the executing session. It was instructed to treat every statement in `BR-GOV-010` as a claim to be tested rather than a fact, and it re-derived each claim from the artifacts, from `git`, and from executable checks. It was explicitly authorised to refute the report and to report anything it could not verify.

**Honest limit of this mechanism.** This is independent verification by a separate AI reviewer context, not by an independent human, organisation, or third party. It is materially stronger than self-certification — the reviewer reproduced measurements, froze the subject to a commit, and refuted eight claims the executing role had asserted — but it is not external audit. That limitation is recorded rather than glossed.

## 2. Verification method

| Aspect | Detail |
|---|---|
| Subject revision | `25791d5441cd76f643668075daeb58984ad71022` (parent `4fd0932`), materialised byte-exactly with `git archive` so a mutating working tree could not distort the subject |
| Tooling | Python 3.12 with PyYAML `safe_load`; `git show`, `git diff`, `git ls-tree`, `git hash-object`, `git archive` |
| Comparison basis | Every claim checked against the parent and head blobs directly, not against the report's prose |
| Corrections round | A second, delta-scoped round verified the eight corrections against the working tree, tied to explicit blob hashes |
| Repository modification | None. The reviewer made no change to any file |

## 3. Outcome

**First round — `BR-GOV-010` was NOT acceptable as an accurate record as it stood.** Eight evidenced qualifications were raised. Substantively confirmed: YAML parse validity across all nineteen `docs/` YAML files; Stable ID uniqueness; the corrected `F-02` root cause in full; the `BR-P4-010` mislabel recovery; the six byte-identical duplicate blocks; the `README` and `STEP-P5-002` corrections; the `F-07` retraction; the `F-09` guard and absence of CRLF; and scope compliance with no excluded change.

**Second round — all eight qualifications are resolved in substance**, and `BR-GOV-010` together with its appended correction notice is **acceptable as an accurate record** of the changes landed by `25791d5`.

## 4. Refuted claims and the corrections applied

| # | Claim in `BR-GOV-010` | Finding | Correction |
|---|---|---|---|
| 1 | `F-06` "RESOLVED"; checklist item 2 "no record retained a pre-activation status" | **REFUTED** — `artifacts.yaml` still carried `BR-P5-008` at `PRODUCED`; the reconciliation required by `TO-GOV-010` §3.6 was never performed | `status` reconciled to `VERIFIED`, consistent with `AR-P5-009` |
| 2 | Change Ledger content required by §6 item 8 | **NOT SATISFIED** — the appended entry carried none of `affected_ids`, `from_state`, `to_state` | A compliant entry, `CL-TO-GOV-010-INDEPENDENT-VERIFICATION-20261010`, added with all three keys and 7 `affected_ids` |
| 3 | §4 `artifacts.yaml records=327 unique=327` | **WRONG** — the landed revision had 328 records: 326 keyed `stable_id` plus 2 keyed `id` | Corrected value disclosed |
| 4 | §4 `CHANGE_LEDGER.yaml ... 146` | **WRONG** — 147 entries | Corrected value disclosed |
| 5 | §4 `files with mojibake: 0` | **WRONG at that revision** — two files contained the sequence, one of them the report itself | Both cleaned; the repository now contains none |
| 6 | §6 "`TO-GOV-010`'s original findings remain as issued ... not by editing the findings" | **FALSE** — two finding lines in `TO-GOV-010.md` were edited in place, and that file's trailing newline was removed | Disclosed in `TO-GOV-010` §14.1 with the prior text reproduced in escaped byte form; trailing newline restored |
| 7 | `F-01` "Eight scalar values" | **OVERSTATED** — seven quote-only repairs landed | Corrected |
| 8 | §2 `ALL LOSSLESS ... True` for all thirteen files | **OVERSTATED** — established for ten; three files changed substantively by design | Corrected |
| — | §1 "byte-identical to `origin/main` for all 543 tracked files" | **AMBIGUOUS** — measured after CONTROL had normalised its own working copy, while `F-09`'s 11/543 figure was measured on a stock Windows checkout | Corrected and distinguished |
| — | Acceptance criterion 12 / §3.11 fresh-checkout demonstration | **ABSENT** from the report | Performed and independently reproduced, §6 below |
| — | `BR-GOV-010` registry record addition | **UNDISCLOSED** — protocol-required, so no exclusion breach, but a meaning-bearing change omitted from disclosure | Disclosed |
| — | §4 "files checked=19" beside a sixteen-row table | **TABLE INCOMPLETE** | Disclosed |

Two further wording defects in the correction notice itself were raised in the second round and have been fixed: the notice's claim that "nothing in it has been rewritten" was false, and its characterisation of `TO-GOV-010` §13.2 was inaccurate. Both are corrected in the final revision.

## 5. Reconciliation decisions specifically verified

- **Six duplicate records** were confirmed **byte-identical** to the surviving copies, so their removal lost nothing.
- **`BR-P4-010`** was confirmed to have had no other registry record, and the mislabelled record was confirmed to describe that artifact. The correction recovered a missing record rather than merely deleting a duplicate.
- **`TO-P5-003` and `TO-P5-003-CORRECTIVE-001`**: the reviewer performed an item-level comparison and confirmed **no factual traceability item, date or actor was lost**; the sole wording variance (`Authorization` to `Directive`) is grounded in the artifact, which records `Owner Authorization: Project Owner directive`.
- The corrective `canonical_name` was confirmed to **byte-match** the value the removed duplicate record carried and to match the artifact's own title, so no label was composed.
- **Item A (`tests.yaml`)**: the reviewer's determination is adopted — the **single quoted string is the correct representation**, on in-record evidence (a structurally identical scalar already exists in the same evidence mapping; the only segregated skip-count form uses different key names and a different scope; a bare `skipped` key could not express the two pairs carried by `TST-P4-013`; and no consumer parses the keys). No open semantic decision remains.
- **Item B**: the reviewer established that `ADR-GOVERNANCE-005`, `-006` and `-008` govern only Stable ID forms and contain no `canonical_name` rule; the binding factor is therefore convention, and the convention supports the artifact title. The final value reflects that.

## 6. Acceptance criteria assessment — `TO-GOV-010` §8

| # | Criterion | Result |
|---|---|---|
| 1 | Every `F-01`/`F-02` file parses | **MET** — 19 of 19 `docs/` YAML files parse with zero failures, independently reproduced |
| 2 | No duplicate `stable_id` | **MET** — 331 records, 331 unique |
| 3 | `BR-P4-010` registered exactly once, correctly labelled | **MET** |
| 4 | Reconciled duplicates preserve the final verified closure state and cite evidence | **MET** — no factual traceability item lost |
| 5 | Every unresolved conflict explicitly reported | **MET** — none remained; both conflicting pairs were resolved from authoritative evidence |
| 6 | `README.md` line 20 matches `CURRENT_CHECKPOINT.json` | **MET** |
| 7 | `STEP-P5-002` metadata matches the closure evidence | **MET** — `TO-P5-002` / `AR-P5-002` |
| 8 | `BR-P5-008` consistent with `AR-P5-009`, body unchanged | **MET after correction** — registry status now `VERIFIED`; the document body confirmed byte-identical by the reviewer |
| 9 | `ADR-GOVERNANCE-012` checklist individually confirmed | **MET** — §9 below |
| 10 | No §5 exclusion violated | **MET** — no ADR, architecture, contract, schema, code, test or migration change; the two disclosure qualifications are resolved by disclosure |
| 11 | Every meaning-bearing change disclosed with before/after text | **MET after correction** — the initially undisclosed registry record is now disclosed |
| 12 | Fresh checkout byte-identical to `origin/main` | **MET** — see below |

**Acceptance criterion 12 evidence.** A genuine clone with `core.autocrlf=true` and `core.eol=native`, simulating a stock Windows checkout, produced:

```
EOL: 535 x i/lf w/lf | 10 x i/none w/none | 0 x w/crlf
byte-identical to origin/main: 545 / 545  (differing: 0)
```

CONTROL obtained this result and the independent reviewer **reproduced it exactly** in its own clone.

## 7. Residual items and explicit non-verification

**Residual risk recorded, not actioned.** `.gitattributes` uses `* -text`, which unsets only the `text` attribute. Content changes remain visible in diffs, but git will never again normalise or warn about line endings, so a future contributor could commit CRLF blobs silently. The guard protects the existing LF blobs against checkout conversion; it does not prevent future drift. `* text=auto eol=lf` would have provided normalisation in addition to checkout fidelity. This warrants a future governance decision.

**Not verified, and why:**

1. **The Project Owner directive of 2026-10-10.** Asserted by CONTROL in `TO-GOV-010` §12.1, `BR-GOV-010` §9 and the Change Ledger. No repository artifact records it. It is not verifiable from the repository, by construction.
2. **Authorial intent** behind the seven literal-escape lines and the three `tests.yaml` values. No authoring record exists; the determination rests on convention evidence and is stated as such.
3. **The execution engine described in `BR-GOV-010` §2.** Every changed line's outcome was verified, but the engine was not reconstructed or re-executed.
4. **Whether `* -text` prevents future CRLF drift.** Not testable without a future commit round-trip.
5. **`BR-GOV-010` §1's baseline claim** that the start working tree was clean and byte-identical for 543 files. Retrospectively unevidenced; the figure is explained but not independently provable from the commit.

**Disclosed difference between the verified revisions and the final commit.** The second verification round was tied to explicit blob hashes. After it returned, CONTROL applied exactly two wording corrections that the reviewer had itself prescribed — the `BR-GOV-010` §10 preservation sentence and the `TO-GOV-010` §14.4 characterisation of §13.2. The final committed revision therefore differs from the verified blobs only by those two prescribed sentences; no status, count, finding or conclusion differs.

## 8. Lifecycle disposition

- `TO-GOV-010` → **`VERIFIED / COMPLETE`**
- `BR-GOV-010` → **`VERIFIED`**
- `AR-GOV-010` → **`APPROVED / VERIFIED`**
- `AR-GOV-005`, `BR-GOV-008`, `BR-GOV-009` registered as a traceability completion for Stable IDs that already existed
- `TO-GOV-010` §13.1's finding stands: **42 artifacts still have no registry record** — 39 of them P0/P1/P2 artifacts that `ADR-GOVERNANCE-012` §4 excludes from retroactive action, plus `BR-P5-003` (PH-P5) and `TO-P2-016` (PH-P2), which are **not** covered by that exclusion and require a bounded future reconciliation

## 9. `ADR-GOVERNANCE-012` Mandatory Peripheral Synchronization Checklist

Confirmed individually:

| # | Item | Result |
|---|---|---|
| 1 | `README.md` matches `CURRENT_CHECKPOINT.json` | **CONFIRMED** — phase, step, registry status, active and last-approved Task Order all agree; no stale `TO-P2-018` claim remains |
| 2 | `artifacts.yaml` records do not retain stale pre-activation status | **CONFIRMED** — 331 records, 331 unique; duplicates, the mislabel and both stale statuses reconciled |
| 3 | Specialized registries checked | **CONFIRMED** — all thirteen `docs/registry/` YAML files parse; record counts verified |
| 4 | Standalone status-bearing documents checked | **CONFIRMED** — `BR-P5-008.md` corrected with its body byte-identical; `PH-P5.md`, `TO-P2-018.md`, `TO-P2-019.md` and `AR-P2-AUDIT-020.md` re-read and already current |
| 5 | Supplemental / staging registries retired when absorbed | **CONFIRMED** — `phase2-artifacts.yaml` records `RETIRED / SUPERSEDED` and was not touched |

## 10. Non-claims

- This report does not reopen, re-verify or re-close any Phase or Step. `PH-P5` remains `ACTIVE / AUTHORIZED`, `STEP-P5-006` remains `COMPLETE / VERIFIED`, `TO-P2-019` remains the active phase Task Order, and `STEP-P5-007` remains `NOT ACTIVATED`.
- `BR-P2-019` and everything related to PRQ-3 were outside this verification and were not touched.
- The verification is by a separate AI reviewer context, not by external audit. See §1.
- No provider/product was selected and no implementation was authorised.

---END---
