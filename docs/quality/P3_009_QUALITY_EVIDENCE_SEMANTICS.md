# P3-009 — Quality / Acquisition Evidence Semantic Contract

## Status

Implementation-level semantic contract for TO-P3-009; pending independent CONTROL verification.

## 1. Evidence family

The authoritative P3 quality-evidence fact is the deterministic quality classification of one immutable P2 AcquisitionEnvelope, together with the preserved acquisition, validation, provenance and lineage inputs used to reach that classification.

It is distinct from canonical market truth. VALID quality evidence may accompany canonical truth; non-VALID evidence remains evidence and is never promoted to canonical persistence.

## 2. Time model

The following remain distinct fields:

- event_time: source/provider event timestamp carried by the acquisition envelope;
- received_at: acquisition observation/receipt timestamp;
- knowledge_time: authoritative earliest boundary at which the quality-evidence fact is knowable from the immutable acquisition evidence;
- persisted_at: database persistence timestamp.

For this evidence family:

knowledge_time == received_at

This equality is explicit semantic contract, not a substitution from database or wall-clock time. The reason is that P3 quality classification is a deterministic, side-effect-free function of the immutable acquisition envelope and its explicit validation evidence; all information needed to reconstruct the classification is present at the acquisition receipt boundary. Validation does not introduce a new source fact or later external observation. Therefore received_at is the earliest legitimate evidence-knowledge boundary.

event_time is never copied merely because it is available. A late-arriving event therefore has knowledge_time > event_time, preserving the event/knowledge distinction.

## 3. Provenance and identity

The source identity is the P2 acquisition identity hash, which is the SHA-256 identity of the governed acquisition identity bytes.

Quality-evidence identity is a separate SHA-256 over the logical fact key, source identity, quality state/lifecycle, quality score, reason codes, validation result, provenance/lineage, payload fingerprint, event/receipt/knowledge times, and explicit timeframe/venue context.

A retry of identical evidence therefore produces the same evidence_id.

A different quality result for the same logical fact produces a different evidence identity and is retained as an explicit contradiction rather than silently replacing the prior fact.

## 4. Context

timeframe and venue are accepted only from explicit payload context (timeframe/interval and venue/venue_context). Provider identity is preserved separately and is never silently promoted to venue.

Missing context remains missing. Such a record is persisted as evidence but is not P5-resolvable until the required context exists authoritatively.

## 5. Historical evidence

Legacy data_quality_logs rows are preserved unchanged. They are not promoted automatically because they lack an authoritative knowledge-time field and complete P5 context.

Historical raw acquisition observations can be reconstructed into the new evidence family only when the preserved raw envelope is complete and the deterministic P3 validation/quality path can be rerun without external or wall-clock inputs. Such rows are Class-B / deterministically reconstructible evidence. Rows lacking those inputs remain Class-C / semantically incomplete. No migration performs a blind timestamp backfill.

## 6. Contradiction semantics

Multiple distinct evidence identities for one logical_fact_key are retained. Read-back resolution refuses silent selection and raises ContradictoryQualityEvidence.

This preserves both evidence and ambiguity instead of overwriting history.

## 7. P5 resolution boundary

A persisted record can be represented as a structured P5 EvidenceRef only when the persisted record exists, knowledge_time is authoritative and non-null, source identity and record identity are present, event_time is present, and required timeframe/venue context is explicit where the S-10 consumer requires it.

No P5-002 code or contract is modified by P3-009.

## 8. Append-only / security

The new table has an UPDATE/DELETE trigger and application-role UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER privileges are revoked. persisted_at is operational only and is never used as knowledge time.

## 9. Historical closure

PH-P3 and its completed historical Steps remain closed. This document records the post-closure corrective semantic needed for PRQ-4 and does not reopen historical P3 closure.
