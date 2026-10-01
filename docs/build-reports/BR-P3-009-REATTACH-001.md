# BR-P3-009-REATTACH-001 — Controlled Reattachment of P3-009 into Current SoT

**Task Order:** `TO-P3-009-REATTACH-001`  
**Role:** `ROL-V2-002` — PRODUCER / ARCHITECT-BUILDER  
**Boundary:** `PH-P5 / STEP-P5-003` prerequisite correction  
**Status:** VERIFIED by independent CONTROL audit  
**Producer lifecycle statement:** This report does not declare VERIFIED, COMPLETE, CLOSED, or PRQ-4 independently resolved.

## 1. Producer conclusion

The controlled reattachment has reached the natural Producer boundary:

`current main @ 2b5dc4f` → current authoritative mainline reconciliation → fresh implementation/tests → Build Report → CONTROL independent audit.

The resulting implementation is based on current `main`, not a merge of historical PR #51. Historical PR #51 remains open and unmerged.

Final implementation revision delivered for independent audit:

`008f7f3bfc554077ea9ca87bc39ee00b337a59c4`

Fresh current-mainline CI evidence for this exact revision:

- CI Core Run #1546 / GitHub Actions Run ID `36825055079` — SUCCESS.
- CI Docker Foundation Run #483 / GitHub Actions Run ID `36825054935` — SUCCESS.
- Dedicated PostgreSQL P3-009 evidence: 6 tests, all successful in 5.790s, inside CI Core #1546.

## 2. Historical boundary

Historical evidence remains distinct:

- PR #51: OPEN / UNMERGED.
- Historical PR head: `11e3063d77d817fdb60e0199d5cef4fc1d4d3119`.
- Historical functional revision: `021030f921b5f7ecc498ebe3e93b7b1bcd849764`.
- Historical Build Report: `BR-P3-009`.
- Historical Audit Report: `AR-P3-009`.
- Historical CI/test evidence is not counted as fresh reattachment evidence.

The new implementation was created from current `main` and reconciled against the current surrounding contracts, migration sequence, persistence boundary and CI workflows.

## 3. Current-mainline starting point and reconciliation

CONTROL's authorized starting point was current main `2b5dc4fc227c157cc00c97cde35287605a8c89c4`. Current `main` subsequently contains only the authorized governance lineage additions for this Task Order, and the reattachment branch was based directly on the current authoritative `main` at `115f7abdd9003ec7b976cf730a66db96045a4a76`.

The controlled reconciliation established:

1. Current `contracts/quality.py` remains the authoritative deterministic quality classifier; no quality-state precedence redesign was introduced.
2. Current `src/meylux/runtime/p3_008_vertical_slice.py` was extended rather than replaced conceptually:
   - raw rows are no longer restricted to `AVAILABLE`;
   - authoritative `canonical_bytes` are used to reconstruct an existing `ProviderError` when present;
   - non-AVAILABLE acquisition outcomes are persisted as quality evidence without validation/normalization of fabricated market payloads;
   - quality evidence is persisted before canonical eligibility gating;
   - VALID canonical persistence remains behind the existing canonical eligibility boundary.
3. Current raw acquisition schema already preserves `canonical_bytes`, `event_time`, `received_at`, acquisition state, provenance and identity hash; no P2 schema change was required.
4. Current migration sequence ends at 0008 before this reattachment. Migration 0008 was inspected and was not modified.
5. Migration orchestration now executes 0009 strictly after 0008.
6. Current CI workflows were reconciled so P3-009 unit and PostgreSQL evidence execute against the reattached implementation.
7. P5-002 contracts/implementation were not modified.

## 4. Changed-file inventory

The reattachment implementation surface is:

1. `contracts/quality_evidence.py` — deterministic authoritative P3 quality/acquisition evidence contract.
2. `src/meylux/persistence/quality_evidence.py` — transactional append-only persistence, deterministic read-back, logical-fact resolution and EvidenceRef mapping.
3. `migrations/versions/0009_quality_evidence_persistence.sql` — authoritative evidence schema, semantic constraints, indexes, append-only trigger and application privileges.
4. `infrastructure/postgres/migrate.sh` — executes migration 0009 after migration 0008.
5. `src/meylux/runtime/p3_008_vertical_slice.py` — P3 evidence persistence and unavailable-acquisition integration before canonical gating.
6. `tests/test_p3_009_quality_evidence.py` — deterministic semantic and persistence behavior tests.
7. `tests/test_p3_009_postgresql.py` — actual PostgreSQL behavioral/integration evidence.
8. `.github/workflows/ci-core.yml` — dedicated PostgreSQL P3-009 evidence step.
9. `.github/workflows/ci-docker.yml` — current CI trigger coverage for P3-009 evidence tests.
10. `docs/quality/P3_009_QUALITY_EVIDENCE_SEMANTICS.md` — semantic authority.
11. `docs/quality/P3_009_LEGACY_EVIDENCE_INVENTORY.md` — historical evidence boundary.

No change was made to `migrations/versions/0008_p4_knowledge_time_persistence.sql`.

## 5. Contract and semantic implementation

The authoritative contract is `QualityEvidenceRecord`.

It preserves:

- source record identity;
- source identity hash;
- provider/adapter identity;
- canonical/provider instrument identity;
- event type;
- event time;
- received_at;
- knowledge_time;
- acquisition state;
- all governed quality states;
- lifecycle state;
- deterministic quality score when available;
- deterministic reason codes;
- validation result;
- provenance;
- lineage parent;
- payload fingerprint;
- explicit timeframe/venue context.

The mandatory semantic is enforced in both contract and database:

`knowledge_time = received_at`

The implementation never substitutes:

- `persisted_at`;
- `logged_at`;
- wall-clock time;
- migration time;
- synthetic fixture time;
- `event_time`.

Event time and knowledge time remain independently represented. A late-arriving observation therefore preserves `knowledge_time > event_time` where applicable.

## 6. Identity, provenance and lineage

The source identity is the existing immutable P2 acquisition event identity.

A separate deterministic quality-evidence identity is derived from the logical fact and its semantic inputs, including quality/lifecycle classification, reason codes, validation result, provenance/lineage, payload fingerprint and time/context fields.

Consequences established by implementation and tests:

- identical replay produces the same `logical_fact_key`;
- identical replay produces the same `evidence_id`;
- duplicate persistence is idempotent;
- different evidence identity for one logical fact is retained rather than silently overwritten;
- logical-fact resolution detects multiple identities as contradiction;
- provenance and lineage remain explicit;
- no missing timeframe or venue is fabricated.

## 7. Quality-state semantics

The reattached evidence path preserves the complete governed quality-state set:

`VALID`, `DEGRADED`, `STALE`, `INCOMPLETE`, `CONTRADICTORY`, `REJECTED`, `UNAVAILABLE`.

Evidence persistence is independent of canonical promotion.

VALID evidence may proceed through the existing canonical eligibility path.

Non-VALID evidence is persisted as evidence and is never promoted to canonical analytical truth by this implementation.

For an unavailable acquisition outcome, the runtime uses the authoritative P2 acquisition state and ProviderError already preserved in the raw acquisition envelope. It does not invent market values, validation inputs or replacement timestamps.

## 8. Persistence implementation

Migration 0009 creates:

`meylux.quality_evidence`

with:

- deterministic primary evidence identity;
- logical-fact key;
- source identity and provenance fields;
- event/receipt/knowledge timestamps;
- quality and lifecycle state;
- reason codes;
- validation result;
- lineage;
- payload fingerprint;
- optional timeframe and venue;
- operational `persisted_at`.

Database protections include:

- `CHECK (knowledge_time = received_at)`;
- governed quality-state vocabulary;
- bounded quality score;
- logical-fact/source indexes;
- append-only UPDATE/DELETE trigger;
- application SELECT/INSERT grant;
- application UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER revocation;
- backup SELECT grant;
- idempotent schema-migration registration.

Persistence uses PostgreSQL `INSERT ... ON CONFLICT (evidence_id) DO NOTHING RETURNING evidence_id`, so the returned insertion result reflects the actual database outcome rather than a race-sensitive pre-check.

## 9. EvidenceRef resolution

The persistence resolver maps an authoritative persisted record to the structured P5 EvidenceRef surface:

- `source_family`;
- `record_id`;
- `identity_hash`;
- `event_time`;
- `knowledge_time`;
- `timeframe`;
- `venue`.

Required timeframe/venue context is resolved only when explicitly present in authoritative payload context.

Missing required context returns unavailable rather than manufacturing a value.

No P5-002 implementation or contract was modified.

## 10. Migration ordering and idempotency

The migration runner now executes:

`0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009`

Migration 0008 was not modified or reapplied by Producer.

Fresh Docker Foundation evidence confirms the migration harness completed successfully.

Fresh PostgreSQL evidence explicitly re-executed migration 0009 and confirmed the migration registration remains singular/idempotent.

The Docker Foundation legacy knowledge-time verification also re-executed migration 0008 against a separate legacy database; that is existing 0008 behavior verification and not a modification or redesign of 0008.

## 11. Fresh test evidence

### CI Core #1546 — Run ID 36825055079

Result: SUCCESS.

Observed fresh evidence on implementation head `008f7f3bfc554077ea9ca87bc39ee00b337a59c4`:

- foundation suite: 573 tests, OK;
- dedicated PostgreSQL P3-009 evidence: 6 tests, OK;
- P3-009 PostgreSQL evidence duration: 5.790s.

The six real PostgreSQL tests proved:

1. actual unavailable provider outcome reaches persisted quality evidence;
2. persisted evidence resolves to the P5 Snapshot boundary and enforces temporal lookahead;
3. append-only privileges and migration rerun behavior;
4. transaction rollback after a failed knowledge-boundary insert;
5. concurrent duplicate persistence has deterministic one-insert/one-no-insert behavior;
6. duplicate/idempotent persistence and contradictory logical-fact behavior on real PostgreSQL.

The final PostgreSQL log records all six tests as `ok` and concludes `OK`.

### CI Docker Foundation #483 — Run ID 36825054935

Result: SUCCESS.

Fresh Docker evidence includes:

- full foundation self-checks;
- P3-009 quality-evidence tests;
- migration harness success;
- migration 0009 execution;
- current database foundation checks;
- existing 0008 legacy idempotency verification;
- UTC database verification;
- knowledge-time schema observation.

The Docker foundation log records all 12 dedicated P3-009 semantic unit tests as successful, including:

- receipt-boundary knowledge time;
- deterministic replay identity;
- all quality states;
- unavailable evidence without fabrication;
- missing/conflicting context;
- idempotent persistence;
- contradiction semantics;
- P5 context-gated resolution;
- migration/harness/runtime integration.

## 12. Current-mainline regression evidence

The final Core run records:

- Binance acquisition tests: success;
- P2-004 acquisition tests: success;
- P2-005 operational hardening tests: success;
- P3-007 quality tests: success;
- P3-008 persistence/event tests: success;
- full foundation suite: 573 tests, OK;
- dedicated P3-009 PostgreSQL suite: 6 tests, OK.

Docker Foundation Run #483 completed successfully.

## 13. Corrective test-harness cycle

An earlier fresh Docker run on the same implementation family exposed two unit-test harness failures because the historical in-memory test double still modeled the previous insert API.

The persistence implementation uses PostgreSQL `INSERT ... RETURNING`; the fake connection was corrected to model that actual behavior.

A subsequent fresh CI cycle on final head `008f7f3bfc554077ea9ca87bc39ee00b337a59c4` passed both Core and Docker Foundation.

The PostgreSQL test connection was additionally bounded with explicit connection/command timeouts so network-level CI failures cannot become indefinite execution.

The earlier failed run is retained as historical corrective-cycle evidence and is not counted as acceptance evidence.

## 14. Architecture and scope preservation

No frozen architecture was redesigned.

No new provider acquisition was introduced.

No MEXC expansion, order-book/depth, derivatives, Futures, Forex, new symbol, P4 mathematical implementation, PRQ-1/2/3, TO-P2-013, P5-003 implementation, LLM, synthesis, trading, capital, custody or execution capability was introduced.

PH-P3 historical closure was not reopened.

STEP-P5-003 implementation was not performed.

P5-002 source/contract implementation was not modified.

No VPS/SentinelX operation was performed by Producer.

## 15. Historical evidence and legacy data boundary

No historical data backfill or blind promotion was performed.

Legacy `data_quality_logs` remain semantically distinct from the new authoritative quality-evidence family.

Historical raw acquisition records remain candidates for deterministic reconstruction only where the authoritative envelope is directly available and complete.

No `logged_at`, `persisted_at`, migration time or current wall-clock value is used to manufacture historical knowledge time.

The legacy inventory document records the historical population boundary without relabeling historical evidence as fresh current-mainline evidence.

## 16. Deviations and open questions

### Deviations

No architectural deviation was taken.

The implementation mechanism was selected at Producer implementation level as permitted by the Task Order.

The only corrective implementation iteration was test-harness alignment with the actual `INSERT ... RETURNING` persistence contract and bounded PostgreSQL test connection timeout.

### Evidence limitations

- No governed VPS runtime/deployment/migration execution was performed by Producer; VPS evidence remains CONTROL-owned.
- Historical population-wide promotion remains intentionally unperformed.
- PR #51 remains historical and open/unmerged.

These are evidence-boundary statements, not substitutions for required current-mainline evidence.

## 17. Exact implementation revision

`008f7f3bfc554077ea9ca87bc39ee00b337a59c4`

Base current-mainline revision:

`115f7abdd9003ec7b976cf730a66db96045a4a76`

CONTROL-authorized historical reference revision:

`2b5dc4fc227c157cc00c97cde35287605a8c89c4`

Historical functional P3-009 revision:

`021030f921b5f7ecc498ebe3e93b7b1bcd849764`

Historical PR #51 head:

`11e3063d77d817fdb60e0199d5cef4fc1d4d3119`

## 18. Producer handoff boundary

The Producer has completed the authorized implementation/test/build-report cycle.

The current state is:

- P3-009 current-mainline implementation: IMPLEMENTED / FRESH CI TESTED.
- PRQ-4 current reproducible basis: PRODUCER EVIDENCE RE-ESTABLISHED / AWAITING INDEPENDENT CONTROL VERIFICATION.
- STEP-P5-003: NOT VERIFIED / NOT COMPLETE / NOT CLOSED.
- Historical PH-P3 closure: unchanged.

Next governed action is independent CONTROL audit of this exact revision and evidence set.

--- END BUILD REPORT ---
