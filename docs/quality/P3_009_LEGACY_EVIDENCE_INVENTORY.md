# P3-009 — Historical / Legacy Evidence Inventory

**Task Order:** TO-P3-009  
**Purpose:** Direct evidence inventory for the legacy population relevant to PRQ-4.  
**Status:** EVIDENCE INVENTORY — NO HISTORICAL PROMOTION PERFORMED.

## 1. Authoritative evidence sources inspected

The repository contains the following direct historical evidence references:

- docs/operations/sentinelx/EXEC-LOG-P5-CORRECTIVE-VPS-RECON-20260924.md
- docs/audits/AR-P4-017.md
- docs/build-reports/BR-P4-010.md
- preserved dump identifier: meylux-data-pre-corrective.sql
- preserved dump SHA-256: c2a0ee9f6756170fcb0c980afe2a35c2d61b87d0407ac7362659a2fb252adaa0

The preserved dump is explicitly recorded as a pre-correction data preservation artifact. Its raw SQL contents are not part of the current repository tree, so this document does not pretend to have performed row-level reconstruction from bytes that are not available in the repository Source of Truth.

## 2. Population inventory

The CONTROL execution record reports the following pre-correction governed population:

| Population | Observed population | Direct evidence | Current P5 treatment |
|---|---:|---|---|
| meylux.raw_acquisition_events | 2995 | EXEC-LOG-P5-CORRECTIVE-VPS-RECON-20260924 | Not automatically promoted; row-level reconstruction required |
| meylux.data_quality_logs | 157 | EXEC-LOG-P5-CORRECTIVE-VPS-RECON-20260924 | Semantically incomplete for direct P5 promotion |
| meylux.canonical_event_outbox | 157 | same execution record | Operational downstream evidence; not itself a quality-evidence source |
| meylux.canonical_candles | 156 | same execution record | Canonical analytical truth; not automatically converted into P3 quality evidence |

These counts are preserved as observed historical evidence. They are not inferred from the new quality_evidence table.

## 3. Legacy data_quality_logs

The 157 legacy quality-log rows are physically present in the preserved historical population, but the legacy schema does not contain the dedicated authoritative knowledge_time required by PRQ-4.

logged_at is an operational persistence timestamp and is not a valid substitute.

Therefore the population cannot become P5-authoritative merely because migration 0009 now provides a table capable of storing knowledge_time.

The correct classification for the legacy data_quality_logs population is:

**Class 3 — physically present but semantically incomplete for direct P5 eligibility.**

A row may become Class-B only if its originating authoritative acquisition evidence and deterministic P3 classification can be demonstrated record-by-record. The existence of a corresponding legacy quality-log row is not sufficient proof.

No legacy quality-log row was backfilled or promoted by TO-P3-009.

## 4. Legacy raw acquisition population

The preserved historical source population contains 2995 raw_acquisition_events.

The raw acquisition contract itself preserves:

- source/event identity;
- provider/adapter identity;
- event type;
- event time;
- receipt time;
- acquisition state;
- provenance;
- payload/canonical bytes;
- identity hash.

For rows whose preserved envelope is complete, P3 quality classification is deterministic and does not require wall-clock or persistence-time lookup. Such rows are candidates for Class-B deterministic reconstruction, but the current repository does not contain the preserved dump bytes needed to establish the classification row-by-row.

Accordingly, TO-P3-009 does not claim that all 2995 rows are Class-B.

Current population-level disposition:

**Class 2 candidate — deterministic reconstruction is architecturally possible where the preserved authoritative envelope is complete, but individual rows remain unpromoted until their source bytes are directly available and reconstructed.**

Any row whose preserved source envelope is incomplete remains Class 3/4 and cannot be promoted.

## 5. Historical reconstruction boundary

A historical record may be promoted to authoritative P3 quality evidence only when all of the following can be reconstructed from preserved authoritative material:

1. immutable AcquisitionEnvelope identity;
2. provider/adapter identity;
3. source event identity;
4. event time;
5. receipt time;
6. acquisition state;
7. provenance;
8. payload/canonical bytes;
9. deterministic P3 validation inputs;
10. deterministic quality classification;
11. deterministic evidence identity;
12. authoritative knowledge_time = received_at.

No database persistence time, migration execution time, logging time, or current wall-clock value may enter the reconstruction.

## 6. Why schema introduction cannot promote history

Migration 0009 creates a new authoritative persistence capability; it does not retroactively establish facts that the legacy population did not preserve.

In particular:

- a new nullable context field cannot manufacture timeframe/venue;
- a new knowledge-time column cannot manufacture historical knowledge semantics;
- persisted_at cannot become historical knowledge_time;
- a legacy data_quality_logs row cannot become authoritative merely because its source_record_id exists;
- a canonical row cannot be silently reclassified as a P3 quality-evidence fact.

The new schema therefore creates a valid destination for future evidence without silently changing the semantic status of historical records.

## 7. Direct conclusion

The relevant legacy population has been inventoried from repository-backed execution evidence.

The correction deliberately performs no blind historical backfill.

The only historical records eligible for eventual Class-B promotion are those for which the preserved authoritative source material permits deterministic, record-by-record reconstruction. The current repository evidence does not establish that row-level result for the full 2995-row population, so no population-wide promotion claim is made.

This classification is an evidence boundary, not an UNAVAILABLE / ACCEPTED LIMITATION for new runtime evidence. New P3 quality/acquisition outcomes now have the authoritative persistence path implemented by TO-P3-009.
