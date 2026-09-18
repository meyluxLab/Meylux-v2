# EXEC-LOG-TO-P3-008 — Acquisition Operational Reassessment

**Task Order:** TO-P3-008 Revision 1.1
**Step:** STEP-P3-008
**Execution ID:** EXEC-LOG-TO-P3-008-ACQUISITION-DIAG-20260918
**Target:** server-l6rf / /srv/meylux-v2
**Executor:** ROL-V2-001 — CONTROL / REVIEWER
**Authorization:** TO-P3-008 Revision 1.1 / ADR-GOVERNANCE-011
**Repository:** meyluxLab/Meylux-v2
**Repository commit used:** 2f61be905259c7dc5ce5649b19931a83cc9591c2
**Start time:** NOT CAPTURED BY EXECUTION WRAPPER
**End time:** NOT CAPTURED BY EXECUTION WRAPPER

## Purpose
Operational reassessment of the prior zero-row condition under ADR-GOVERNANCE-013 Rule 1. The objective was to distinguish an empty raw table from absence of an authorized acquisition path and continue to the farthest reachable P3-008 boundary without fabricating data or bypassing the governed acquisition architecture.

## Actions and Results
1. Inspected the synchronized VPS runtime and repository state through SentinelX.
   - host: server-l6rf / host_3774c70bc3624713
   - checkout: /srv/meylux-v2
   - repository HEAD: 2f61be905259c7dc5ce5649b19931a83cc9591c2
   - six Compose services were running.
2. Inspected the collector runtime.
   - collector executes python -m meylux.runtime.service.
   - current src/meylux/runtime/service.py is a foundation long-running service boundary; it does not instantiate the Phase 2 acquisition adapters or persist acquisition events.
   - collector logs contained only the foundation startup message.
   - therefore no acquisition attempt had occurred through the running collector service at the prior zero-row boundary.
3. Independently inspected the repository acquisition implementation.
   - the existing BinanceAdapter is operationally reachable and provides public REST acquisition through the existing provider-neutral AcquisitionEnvelope boundary.
   - the current Binance adapter is a Spot acquisition path (https://api.binance.com); no Binance Futures adapter/path exists in the current repository.
4. Independently verified external Binance public acquisition from the deployed API image.
   - actual BinanceAdapter.fetch_trades(BTCUSDT, limit=1) returned AVAILABLE.
   - provider: binance
   - adapter: binance-acquisition
   - instrument: BINANCE:BTCUSDT
   - event type: TRADE
   - source sequence: 6692893843 on the first probe.
5. Independently verified that the public Binance Futures endpoint is network-reachable from the deployed runtime.
   - https://fapi.binance.com/fapi/v1/trades?symbol=BTCUSDT&limit=1
   - HTTP status: 200
   - response bytes: 132
   - this establishes external network/provider reachability only; it is not treated as governed acquisition evidence because the current repository has no Futures acquisition adapter/path.
6. Exercised the existing governed Binance Spot acquisition adapter and persisted one actual AVAILABLE envelope through the existing RawStagingRepository into the deployed PostgreSQL staging boundary.
   - ACQUISITION_STATE=AVAILABLE
   - provider: binance
   - adapter: binance-acquisition
   - instrument: BINANCE:BTCUSDT
   - event type: TRADE
   - source sequence: 6692896984
   - RAW_PERSIST_INSERTED=True
   - raw event id: f12b8c638b3a2e742c88bad720ca2f6b6a5f19df4f38ab3983cdcb251fbc7d7a
   - independent read-back from meylux.raw_acquisition_events succeeded for the inserted event.
   - no synthetic/fabricated/fallback data was used.
7. Re-ran the authorized P3-008 vertical-slice runner against the now non-empty governed raw boundary.
   - command: python -m meylux.runtime.p3_008_vertical_slice
   - runner no longer stopped at the zero-row guard.
   - execution failed while reconstructing the AcquisitionEnvelope from the PostgreSQL row.
   - actual traceback: TypeError: payload must be a mapping.
   - failure occurred in envelope_from_row() when passing row[payload_json] directly into AcquisitionEnvelope.
8. The observed failure establishes a new implementation-level runtime defect.
   - the database column meylux.raw_acquisition_events.payload_json is authoritative jsonb.
   - the deployed runner passes the driver-returned value directly as the envelope payload.
   - the actual runtime value supplied to the contract was not a mapping, and the contract rejected it before normalization/persistence/event processing.
   - this is distinct from the prior Docker contracts packaging defect and distinct from the prior zero-row condition.
9. No canonical persistence, event publication, rollback or partial P3-008 mutation was performed by the failed vertical-slice invocation after the raw acquisition insert.
10. The raw acquisition event is retained as real governed acquisition evidence; no destructive cleanup was performed because the staging boundary is append-only evidence.

## Diagnosis / Classification
The prior 0 rows observation was not a final external blocker.

- acquisition path reachable under current CONTROL authority: YES, for the existing Binance Spot adapter;
- acquisition path actually attempted before this reassessment: NO through the running collector service;
- authorized operational remediation of the empty raw boundary: YES, using the existing Binance Spot adapter and RawStagingRepository;
- governed AVAILABLE raw evidence after remediation: YES, one actual Binance Spot TRADE record;
- external Binance Futures network reachability: YES;
- existing governed Binance Futures acquisition capability in the repository: NO;
- controlled vertical-slice execution after raw evidence became available: REACHED, THEN FAILED;
- new blocker/defect: Producer-owned runtime reconstruction defect in src/meylux/runtime/p3_008_vertical_slice.py.

The current failure is a normal implementation/runtime defect requiring Producer correction, not an Owner A decision and not an authoritative conflict.

## Required Producer Correction
CONTROL returns only the newly established implementation defect to ROL-V2-002.

The correction must make the deployed vertical-slice runner reconstruct the existing PostgreSQL jsonb payload into the mapping type required by AcquisitionEnvelope, without weakening contract validation or changing the persistence schema merely to accommodate the runner.

The correction must:
1. preserve the existing jsonb storage contract;
2. decode the driver-returned JSON representation at the runtime boundary before constructing AcquisitionEnvelope;
3. preserve malformed/non-mapping rejection rather than silently accepting invalid payloads;
4. add deterministic automated regression coverage for the actual row-to-envelope boundary;
5. rerun the applicable P3-008 tests and full regression;
6. produce fresh Docker/runtime CI evidence;
7. update BR-P3-008 with the actual correction/evidence;
8. stop at the Producer-to-CONTROL lifecycle boundary after delivering the corrected evidence package.

No new Task Order or architecture change is requested. The Producer must not modify Production, EXEC-LOG, Checkpoint closure state, G-3 status, or CONTROL verification state.

## Current P3-008 Boundary
The step remains:
STEP-P3-008 = ACTIVE / CORRECTION REQUIRED

The controlled real-data path has advanced beyond the previous empty-data boundary, but canonical persistence read-back, event receipt, failure/recovery verification and G-3 remain unestablished because the current vertical-slice runner fails during raw-row envelope reconstruction.

Phase 4 remains unauthorized.

## Evidence Integrity
No secret values were recorded.
No synthetic or fabricated market data was used.
No manual/ungoverned VPS access was used.
All VPS operations were executed through SentinelX.