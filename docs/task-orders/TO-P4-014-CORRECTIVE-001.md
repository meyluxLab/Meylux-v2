# TO-P4-014-CORRECTIVE-001 — Complete S-03 Volume/RVOL Operational Integration

**Task Order SID:** `TO-P4-014-CORRECTIVE-001`  
**Parent:** `TO-P4-014`  
**Issuing Role:** CONTROL / REVIEWER — `ROL-V2-001`  
**Producer Role:** PRODUCER / ARCHITECT-BUILDER — `ROL-V2-002`  
**Boundary:** `PH-P4 / STEP-P4-006` — S-03 portion of Group-C upstream prerequisite resolution  
**Status:** AUTHORIZED TO EXECUTE  
**Governance Basis:** continuation under `ADR-GOVERNANCE-013 R1`; No-Drop under `ADR-GOVERNANCE-014`.

## 1. CONTROL correction finding

Independent CONTROL review confirms the Producer's causal findings for S-17, including the unresolved authoritative session-boundary/trade-population/input-path dependency.

However, the Producer stopped the parent Task Order before carrying the independently identifiable S-03 work to its legitimate boundary.

The existing P4 volume/RVOL mathematics is already authoritative and candle-based. The current orchestration path does not invoke the existing volume/RVOL calculation or persist its resulting facts through the governed runtime path.

Therefore S-03 is independently actionable inside the existing P4 boundary and must not be held indefinitely behind the S-17 semantic dependency.

## 2. Required outcome

Operationalize the existing authoritative Volume/RVOL capability for S-03 through the existing P4 quantitative path.

The resulting governed runtime path must expose and persist, for the applicable candle boundary:

- Volume SMA;
- RVOL;
- configured spike classification;
- configured climax classification;
- explicit calculation status/reason;
- provenance/venue context;
- deterministic identity/version;
- existing knowledge/event-time semantics;
- replay/idempotency behavior.

The implementation must use the already-ratified P4 mathematical authority. No new Volume/RVOL formula is authorized.

## 3. Implementation discretion

Producer retains implementation-level design authority.

The implementation may extend the existing quantitative result/persistence mapping only as required to make the already-existing S-03 mathematics operational.

Do not introduce a new P4 mathematical contract, duplicate truth source, hidden provider dependency, or unrelated refactoring.

If an architecture/canonical-contract/ownership conflict is discovered, stop only that conflicting portion and report the exact conflict to CONTROL.

## 4. Required verification evidence

At minimum:

1. direct mapping from existing volume/RVOL engine to P4 orchestration;
2. correct warm-up/insufficient-history behavior;
3. exact RVOL denominator semantics, excluding current candle from the baseline where required by ratified semantics;
4. spike/climax threshold semantics from configuration;
5. closed-candle/no-lookahead behavior;
6. malformed/non-finite/boundary input behavior;
7. provenance and venue preservation;
8. deterministic identity;
9. replay/idempotency;
10. append-only persistence/read-back;
11. regression of all existing quantitative families;
12. CI/test evidence;
13. real governed runtime/database evidence where required by the parent Task Order.

No synthetic or fabricated runtime evidence.

## 5. Scope protection

This corrective Task Order does **not** authorize:

- S-17 Volume Profile implementation;
- selecting or inventing a session calendar;
- populating `volume_profile_sessions`;
- fabricating canonical trades;
- P2/P3 provider expansion;
- P5 specialist implementation;
- changing P4 Volume Profile mathematics;
- changing frozen architecture;
- unrelated refactoring;
- trading/execution/capital/custody functionality.

The S-17 dependency remains open and traceable under the parent `TO-P4-014`.

## 6. Completion boundary

Successful Producer delivery establishes only:

**S-03 Volume/RVOL operational integration = IMPLEMENTED / TEST-EVIDENCED**

It does not establish:

- `PRQ-1 Group-C`;
- S-17;
- `STEP-P5-006`;
- `TO-P4-014` closure.

Producer must not declare VERIFIED/COMPLETE/CLOSED.

CONTROL will independently verify and then determine the remaining S-17 governance path.

## 7. Continuation / No-Drop

Producer shall carry S-03 work to the farthest legitimate point supported by existing authority and evidence.

The unresolved S-17 semantic dependency is not a reason to stop the independently separable S-03 work.

Any genuinely required additional prerequisite must be surfaced through the governed owning boundary rather than silently dropped or replaced.

## 8. Deliverable

Return a complete Build Report covering changed files, exact revision, tests/CI, runtime/database evidence, semantic mapping, persistence/read-back, replay/idempotency, deviations/open questions, and explicit statement that S-17 and P5-006 were not implemented or closed.
