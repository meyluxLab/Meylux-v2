# P5-003 — S-10 Runtime Semantics

Scope: STEP-P5-003 / TO-P5-003 only.

## Runtime boundary

The Stage-1 runtime path is:

authoritative InputSnapshot -> Redis Streams envelope -> worker-specialist -> S-10 -> append-only specialist_outputs -> deterministic read-back

The queue transport carries a canonical serialized InputSnapshot. The worker reconstructs and revalidates it before S-10 execution; it does not reconstruct facts from providers or from operational timestamps.

## S-10 semantics

S-10 is deterministic and consumes only the authoritative Snapshot.

Quality severity is ordered explicitly for worst-status classification:

VALID < PARTIAL/STALE < INSUFFICIENT_DATA < INVALID < CONTRADICTORY < UNAVAILABLE

The worst status is selected deterministically by severity and fact_id tie-break. Required non-VALID states are represented as explicit findings:

- STALE_INPUT
- INCOMPLETE_HISTORY
- CONTRADICTORY_INPUT
- UNAVAILABLE_INPUT
- INVALID_INPUT
- PARTIAL_INPUT

The specialist never fabricates a missing value or promotes event_time, observed_at_utc, persistence time, or wall-clock time to knowledge_time.

## Evidence resolution and lookahead

Before analysis:

1. every Snapshot fact must satisfy knowledge_time <= snapshot.as_of;
2. every EvidenceRef must resolve to the Snapshot provenance set;
3. resolved identity and record identifiers must match;
4. EvidenceRef knowledge_time must also satisfy the Snapshot as_of boundary.

Any violation is a non-retryable semantic/contract failure and is routed to DLQ.

## Queue semantics

The existing Redis Streams foundation is reused. The S-10 queue is specialist-stage1 with:

- FIFO enqueue/delivery ordering;
- configuration-driven maximum concurrency;
- configuration-driven timeout;
- bounded retry count and exponential backoff;
- atomic backlog limit / overload rejection;
- idempotency key derived from specialist, snapshot identity and configuration identity;
- consumer-group stale-message recovery;
- deterministic retry transition;
- DLQ after retry exhaustion;
- direct DLQ for explicitly classified semantic failures.

Transient database failures are explicitly classified as retryable. Semantic/contract failures are explicitly non-retryable. S-10 implementation failures are failed closed as semantic failures rather than retried indefinitely.

## Persistence

meylux.specialist_outputs remains the authoritative append-only store established by P5-001. Persistence now determines the insert result from PostgreSQL INSERT ... ON CONFLICT ... DO NOTHING RETURNING record_id rather than from a pre/post assumption.

Therefore:

- exactly one concurrent writer can report inserted=True for one identity;
- a duplicate/replay reports inserted=False;
- the existing row is subsequently read back by identity;
- no UPDATE/DELETE path is introduced.

No migration beyond the already-authorized P5-001 foundation is added by this Step.

## Configuration

config/specialists.yaml version 1.1.0 governs timeout, concurrency, retry attempts/backoff, backlog and retention, plus S-10 finding/evidence cardinality.

The configuration safety boundary remains read-only with private-provider access, trading, capital movement and custody disabled.

## Scope exclusions

No provider acquisition, new symbol, MEXC capability, Futures acquisition, PRQ-1/2/3, migration 0008_p4_knowledge_time_persistence.sql, P2/P3/P4 reopening, other specialist, cross-specialist synthesis, LLM, public API/UI, or trading/capital/custody/execution is introduced.
