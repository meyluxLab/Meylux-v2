# TO-P5-003-CORRECTIVE-001 — Authoritative Evidence-Context Resolution for Stage-1 Input Snapshot

**Task Order SID:** `TO-P5-003-CORRECTIVE-001`
**Parent Step:** `STEP-P5-003`
**Parent Task Order:** `TO-P5-003`
**Project:** MEYLUX V2
**Phase:** `PH-P5`
**Issuing Role:** `ROL-V2-001` — CONTROL / REVIEWER
**Producer Role:** `ROL-V2-002` — PRODUCER / ARCHITECT-BUILDER
**Status:** VERIFIED / COMPLETE
**Owner Authorization:** Project Owner directive — corrective continuation of STEP-P5-003 — 2026-10-01
**Completion:** CONTROL independently verified the corrective outcome under `AR-P5-003`; the implementation/verification distinction is preserved and the corrective Task Order is now VERIFIED / COMPLETE.
**Governance Basis:** `ADR-GOVERNANCE-012`, `ADR-GOVERNANCE-013`, `ARTIFACT_PROTOCOL_V2.md`

## 1. Authority and Objective

This corrective Task Order authorizes the Producer to resolve the established P3/P5 evidence-context defect preventing authoritative P5 Input Snapshot construction.

The established finding is concrete:

- authoritative Binance envelope data contains interval information at `payload["k"]["i"]`;
- the current quality-evidence context extraction does not obtain that nested interval;
- `provider_id` and `venue` are distinct contract concepts;
- provider identity MUST NOT be silently promoted to venue without authoritative venue evidence;
- the resulting incomplete EvidenceRef prevents the P5-003 authoritative Input Snapshot boundary from being satisfied.

The required outcome is **complete root-cause resolution**, not merely adding a field, copying a nested value into a convenient column, changing a test fixture, weakening validation, or making the current runtime pass.

The Producer retains implementation-level design authority within this Task Order. CONTROL retains governance, scope, independent verification, VPS execution/verification, and closure authority.

## 2. Required Outcome

The corrective implementation must establish a durable, provider-neutral evidence-context path such that authoritative P5 EvidenceRefs can be resolved from genuinely authoritative persisted evidence when the underlying source data actually contains the required context.

The completed work must, as applicable to the actual repository architecture:

1. Trace the authoritative context from acquisition envelope through persistence/quality-evidence extraction to the P5 EvidenceRef boundary.
2. Correct the root extraction/propagation defect for Binance nested interval data (`payload["k"]["i"]`) without hard-coding Binance-specific semantics into a provider-neutral contract unless the existing architecture explicitly requires such specialization.
3. Preserve the distinction between:
   - provider identity;
   - venue;
   - symbol/instrument identity;
   - interval/timeframe;
   - event time;
   - receipt/knowledge time;
   - persistence/logging time.
4. Populate `timeframe` only from authoritative source evidence or an explicitly authoritative existing contract mapping.
5. Populate `venue` only when authoritative venue evidence exists. Do NOT infer `venue = provider_id`.
6. Preserve `knowledge_time = received_at` and the existing temporal/zero-lookahead semantics.
7. Preserve identity, provenance, lineage, EvidenceRef and append-only semantics.
8. Preserve unavailable/invalid/contradictory evidence semantics. Missing authoritative context MUST remain explicitly unavailable rather than being fabricated.
9. Ensure the corrected context survives the complete path required by P5-003: authoritative persisted evidence → EvidenceRef resolution → Input Snapshot → S-10.
10. Address all directly relevant provider/envelope shapes and edge cases discovered during implementation where doing so remains within the existing architecture and this bounded objective.
11. Preserve backward compatibility for valid existing records unless a genuine contract/data correction requires governed handling.
12. Prevent silent corruption where malformed, ambiguous, contradictory, or incomplete envelope context reaches the P5 authoritative boundary.
13. Provide deterministic behavior for equivalent evidence.
14. Demonstrate that the corrected path works with real persisted evidence, not only synthetic fixtures.

## 3. Technical Freedom / Non-Prescriptive Boundary

This Task Order defines the required outcome and semantic constraints, not a prescribed patch.

The Producer may determine the technically correct mechanism, including whether the resolution requires changes to extraction helpers, normalization, persistence mapping, contracts, migrations, tests, provider-specific adapters, or bounded documentation.

Do not implement a superficial one-field patch merely because `payload["k"]["i"]` is the observed symptom.

If investigation demonstrates that a contract, schema, migration, architecture rule, or stable semantic identifier genuinely must change, stop that affected portion and report the exact conflict and proposed governance/change-control route to CONTROL. Do not silently alter frozen architecture or canonical contracts.

## 4. In Scope

- Root-cause resolution of authoritative evidence-context extraction/propagation for the P5-003 Input Snapshot boundary.
- Binance envelope interval extraction where the authoritative source actually provides it.
- Correct provider/venue semantic separation.
- Existing P3 quality-evidence and EvidenceRef path directly required to make the P5 boundary authoritative.
- Necessary bounded persistence/schema/contract changes if technically required and governance-compatible.
- Regression and compatibility tests.
- Real PostgreSQL/integration tests where required to prove persistence semantics.
- P5-003 Input Snapshot construction and S-10 acceptance tests using real authoritative evidence.
- Relevant failure/edge cases: missing nested interval, malformed envelope, missing venue, contradictory context, unavailable context, duplicate evidence, replay/idempotency and temporal-boundary checks where affected.
- Build Report with actual implementation/test evidence.

## 5. Explicitly Out of Scope

This Task Order does NOT authorize:

- redesign of `DOC-V2-ARCH-001`;
- changing `knowledge_time` semantics;
- treating `persisted_at`, `logged_at`, wall-clock time or synthetic timestamps as `knowledge_time`;
- equating provider identity with venue;
- new market-data provider acquisition;
- MEXC implementation or acquisition changes;
- new symbols/instruments merely to obtain a passing fixture;
- Futures/Forex acquisition;
- P4 mathematical-engine changes;
- PRQ-1/PRQ-2/PRQ-3 implementation;
- `TO-P2-013);
- migration `0008_p4_knowledge_time_persistence.sql) rework unless CONTROL separately authorizes it because a demonstrated dependency cannot otherwise be resolved;
- other specialists beyond S-10;
- cross-specialist synthesis;
- Phase 6;
- trading, capital, custody, execution or decision authority;
- provider credentialing;
- unrelated cleanup or refactoring.

## 6. Semantic Invariants

The implementation MUST preserve:

- `provider_id != venue` unless an authoritative contract explicitly establishes equality for a specific evidence source.
- `timeframe) is not inferred from an unrelated field.
- `knowledge_time = received_at) remains authoritative.
- `event_time) remains distinct from `knowledge_time).
- No future knowledge relative to `snapshot.as_of) may enter the Input Snapshot.
- Evidence identity remains deterministic and provider-neutral.
- EvidenceRef remains resolvable to its authoritative source record.
- Append-only semantics remain intact.
- Existing unavailable/invalid/contradictory states remain explicit.
- No fabricated market facts or context are introduced.

## 7. Required Evidence

The Producer Build Report must provide actual evidence for:

1. The original failing path and the corrected path.
2. Binance nested interval extraction from a real authoritative envelope.
3. Correct provider/venue separation, including a case where venue is unavailable.
4. A valid EvidenceRef containing authoritative `timeframe) and `venue) when both are genuinely available.
5. A case where venue remains unavailable and is NOT synthesized from `provider_id`.
6. `knowledge_time = received_at) and event/knowledge-time separation.
7. Evidence identity/provenance/lineage preservation.
8. Real PostgreSQL persistence/read-back where persistence is affected.
9. P5 Input Snapshot construction from real persisted evidence.
10. S-10 end-to-end processing using the corrected authoritative snapshot.
11. Missing/malformed/contradictory context behavior.
12. Duplicate/idempotency behavior where affected.
13. Regression against existing P3/P5 contracts and tests.
14. CI results for the complete applicable suite.
15. Runtime evidence sufficient for CONTROL to independently repeat the acceptance path.

Fixtures may be used for unit-level edge cases, but fixtures MUST NOT be the sole proof of authoritative context resolution.

## 8. Continuation Duty

Under ADR-GOVERNANCE-013 R1/R5, the Producer must carry this authorized correction through the farthest legitimate implementation/build-report boundary in the same cycle.

Do not stop after extracting the nested interval if downstream persistence, EvidenceRef construction, Snapshot resolution, or S-10 acceptance remains broken.

Normal test failures, additional bounded analysis, and implementation difficulty are not blockers.

Stop and escalate only for:

- genuine Owner decision requirement;
- unresolved authoritative architectural/contract conflict;
- a dependency that cannot be resolved within this Task Order's authorized boundary.

## 9. Producer / CONTROL Boundary

Producer responsibilities:

- implementation;
- tests;
- applicable CI/build evidence;
- Build Report;
- explicit unresolved questions/deviations.

CONTROL responsibilities:

- independent repository audit;
- independent runtime/functional verification through SentinelX where required;
- determination of VERIFIED / COMPLETE / CLOSED;
- ADR-GOVERNANCE-012 closure synchronization;
- Checkpoint, README, registry and Change Ledger synchronization.

Producer MUST NOT declare its work VERIFIED, COMPLETE or CLOSED and MUST NOT modify closure registries/checkpoint/README/Change Ledger as a substitute for CONTROL closure.

## 10. Build Report

Producer must deliver a Build Report using the next valid Producer-allocated BR identity under the Artifact Protocol.

It must include:

- implementation revision;
- changed-file inventory;
- root-cause statement;
- exact corrective mechanism;
- semantic/provider/venue decision evidence;
- migration/schema impact, if any;
- tests and exact results;
- CI evidence;
- real-data/runtime evidence;
- regression results;
- limitations/open questions;
- scope compliance.

The Build Report must distinguish IMPLEMENTED, EXECUTED and TESTED evidence from any claim requiring later CONTROL verification.

## 11. Completion Boundary

This corrective Task Order reaches its Producer boundary only when the implementation and Build Report establish enough real evidence for CONTROL to independently test whether:

`authoritative persisted evidence → EvidenceRef → Input Snapshot → S-10 → append-only persistence → deterministic read-back`

is now genuinely satisfiable without inferred or fabricated context.

Successful unit tests alone are insufficient.

CONTROL will then proceed directly into independent verification of the corrected path without restarting the original diagnostic investigation.

## 12. Governance and Closure

This Task Order is a corrective continuation under `STEP-P5-003); it does not itself close or re-verify `STEP-P5-003).

The existing implementation/verification distinction remains intact.

If the corrective work succeeds, CONTROL will determine whether the parent Step can advance to independent verification and subsequently perform the full `ADR-GOVERNANCE-012) closure cycle at the genuine Step boundary, including:

- README;
- `CURRENT_CHECKPOINT.json);
- `artifacts.yaml);
- applicable tests/database/runtime/security/config/requirements registries;
- standalone status-bearing records;
- Change Ledger;
- machine read-back.

Historical P3-009 evidence and PR #51 remain preserved. No historical closure record is rewritten to manufacture a new implementation lineage.

## 13. Final Scope Statement

This is an outcome-driven corrective Task Order. It authorizes the Producer to determine and implement the technically correct bounded solution to the established evidence-context defect, including directly necessary supporting changes, while preserving frozen architecture, semantic contracts, evidence discipline and phase boundaries.

**Status:** AUTHORIZED TO EXECUTE


## 14. CONTROL Closure Disposition

CONTROL independently verified the corrected authoritative evidence-context and Snapshot transport path on deployed main. `TO-P5-003-CORRECTIVE-001` is **VERIFIED / COMPLETE**. Closure synchronization is recorded in `CL-P5-003-CLOSURE-20261001`.
