# P4-010 — Family-Specific Knowledge-Time Semantic Evidence

Task Order: TO-P4-010
Role: ROL-V2-002 — PRODUCER / ARCHITECT-BUILDER
Purpose: correction-cycle semantic evidence for the three audited persisted P4 families
Status: IMPLEMENTATION EVIDENCE — CONTROL INDEPENDENT AUDIT PENDING

## 1. Authority and method

This document does not create a new semantic rule.

It records the semantic rule already recoverable from the authoritative P4 architecture, contracts, and ratified semantic specifications, and explicitly refuses to generalize that rule across fact families where the authorities do not establish it.

The governing distinction is:

- implementation equality is not semantic equivalence;
- database materialization is not semantic authority;
- synthetic migration rows prove migration mechanics, not historical truth;
- event_time, provider/source timestamp, receipt/observation time, ingestion time, persistence time, logging time, wall-clock execution time, and knowledge_time remain distinct unless an existing authoritative semantic establishes equivalence.

Primary authorities inspected:

1. docs/quantitative/P4_002_INDICATOR_SEMANTICS.md
2. docs/quantitative/P4_003_MARKET_STRUCTURE_SEMANTICS.md (DOC-P4-002)
3. docs/decisions/ADR/ADR-QUANTITATIVE-001.md
4. contracts/quantitative/base.py
5. contracts/quantitative/structure.py
6. contracts/quantitative/regime.py
7. src/meylux/quantitative/regime_venue.py
8. src/meylux/quantitative/market_structure.py
9. src/meylux/orchestration/engine.py
10. src/meylux/persistence/quantitative.py
11. docs/registry/contracts.yaml
12. docs/requirements/P5_002_FACT_REQUIREMENTS_MATRIX.md
13. docs/task-orders/TO-P4-010.md
14. existing P4 closure/runtime evidence referenced by the Task Order.

## 2. Temporal vocabulary

### Authoritative source / evidence

The authoritative P4 input is the validated CanonicalCandle sequence. Its close_time is part of the immutable canonical contract and its provenance_id identifies upstream evidence lineage.

### Closed-candle boundary

P4 quantitative execution requires closed canonical candles. The quantitative worker contract is explicitly a candle-close runtime boundary, and the indicator/regime engines reject incomplete candles.

### Orchestration as_of

QuantitativeOrchestrator.process() derives as_of from the last accepted primary candle's close_time.

Therefore as_of is not receipt time, persistence time, logging time, or wall-clock execution time. It is the closed-primary-candle reference boundary of the orchestration result.

### Provider/source timestamp

Provider/source timestamps belong to acquisition/canonical evidence and are preserved through canonical candle fields/provenance. They are not substituted for knowledge_time.

### Observation / receipt / ingestion time

These are operational observations about when data was received or processed. The P4 deterministic calculation authorities prohibit hidden wall-clock dependencies and do not use receipt time to establish mathematical output.

### Persistence time

Database persisted_at, where present, records persistence timing. P5 explicitly prohibits using it as a substitute for authoritative knowledge time.

### Logging time

logged_at is evidence/logging metadata. It is not the knowledge boundary.

### Wall-clock execution time

P4 pure engines do not read wall-clock time. Replaying the same closed input must reproduce the same result.

### Knowledge time

For the families below, knowledge_time means the earliest legitimate time at which the specific fact can be authoritatively exposed from the permitted evidence.

## 3. Family 1 — meylux.calculated_indicator_vectors

### 3.1 What the persisted fact is

The persisted indicator row is the final indicator calculation produced by the P4 orchestration for the primary candle sequence. The currently persisted implementation covers EMA, RSI and ATR vectors.

### 3.2 Authoritative source

CanonicalCandle is the only canonical market-data input to the P4 indicator engine.

P4_002_INDICATOR_SEMANTICS.md states that every candle-derived result carries QuantitativeContext containing the candle provenance and close timestamp, timeframe, instrument identity and calculation version.

The indicator engine is pure: no provider, database, filesystem, clock, receipt-time or persistence-time dependency participates in calculation.

### 3.3 Closed-candle boundary

The orchestration accepts only closed primary candles and rejects incomplete input.

The final indicator calculation is taken from the final element of the accepted closed sequence.

The final candle's close_time is therefore the latest input boundary used by that fact.

### 3.4 Orchestration as_of

QuantitativeOrchestrator.process() assigns as_of = xs[-1].close_time.

This is the same close timestamp already carried by the final candle-derived calculation context.

### 3.5 Fact construction

The indicator values are deterministic functions of the permitted closed sequence through the final primary candle.

The P4-002 temporal rule requires that an already-emitted observation depends only on observations up to that point. Future extension cannot alter the authoritative result for the existing prefix.

Therefore the earliest legitimate knowledge boundary for the final indicator vector is the final accepted primary candle close.

### 3.6 Event-time assignment

The existing authoritative P4 persistence adapter constructs indicator identity material with event_time = result.as_of and persists the same result.as_of into the table's event_time.

This is not a substitution of a convenient operational timestamp: the existing fact's event/reference boundary is the closed primary-candle boundary from which the indicator result is constructed.

### 3.7 Knowledge-time equivalence

Conclusion: CLASS-B — deterministically reconstructible.

For this family, the preserved authoritative chain establishes:

CanonicalCandle.close_time
→ closed primary boundary
→ QuantOrchestrationResult.as_of
→ final indicator calculation/context timestamp
→ persisted event_time
→ earliest legitimate knowledge boundary.

Therefore:

knowledge_time == event_time == final primary candle close_time

is an existing semantic consequence of the P4 candle-derived result model, not a new database-derived rule.

The equality is not inferred from persisted_at, receipt time, logging time, or wall-clock execution.

### 3.8 Historical rows

Existing historical indicator rows may be classified CLASS-B when their preserved event_time and governing calculation semantics identify them as outputs of the same closed-candle orchestration model.

No historical timestamp is rewritten. Migration materializes the deterministic value without UPDATE.

## 4. Family 2 — meylux.market_regime_states

### 4.1 What the persisted fact is

The persisted regime row is the deterministic regime state produced by MarketRegimeEngine for the accepted primary closed-candle sequence.

### 4.2 Authoritative source

MarketRegimeEngine consumes CanonicalCandle input only.

The engine validates every candle is closed, one instrument, one timeframe, strictly increasing open times, and non-overlapping intervals.

Its deterministic context derivation uses the maximum candle close_time, the final timeframe and symbol, plus canonical provenance.

### 4.3 Closed-candle boundary

The regime state uses the final candle's close and prior closed candles.

The trend factor compares the current close with the mean of preceding closes.

The momentum factor compares the current close with the close at the configured lookback.

Hysteresis is applied deterministically to the candidate state.

No receipt time, persistence time, logging time or wall clock participates.

Therefore the regime state cannot be authoritatively known before the close of the final candle whose value participates in the state calculation.

### 4.4 Orchestration as_of

The orchestration assigns as_of = xs[-1].close_time.

The regime engine's derived QuantitativeContext.timestamp is the maximum closed-candle close, which is the same final primary boundary for the orchestration.

### 4.5 Fact construction

The state is constructed from the final closed sequence and the explicitly supplied previous regime state.

The previous state is an input to the deterministic transition, not an independently timed observation.

No future candle is inspected.

### 4.6 Event-time assignment

The existing P4 persistence adapter assigns event_time = result.as_of for the persisted regime state.

The persisted row therefore represents the regime state at the final closed primary-candle reference boundary.

### 4.7 Knowledge-time equivalence

Conclusion: CLASS-B — deterministically reconstructible.

The authoritative chain is:

CanonicalCandle.close_time
→ closed primary boundary
→ regime factor/state construction
→ derived quantitative context timestamp
→ QuantOrchestrationResult.as_of
→ persisted regime event_time
→ earliest legitimate knowledge boundary.

Therefore:

knowledge_time == event_time == final primary candle close_time

for this persisted regime-state family.

This conclusion is independent of the indicator-family conclusion: it follows from the regime engine's own validation, factor construction, deterministic context and state semantics.

### 4.8 Historical rows

Existing historical regime rows may be classified CLASS-B where their preserved event_time and calculation provenance place them within the same governed closed-candle regime model.

No historical timestamp is fabricated or substituted.

## 5. Family 3 — meylux.market_structure_events, event_type = ORCHESTRATION

### 5.1 What the persisted fact actually is

The persisted row is not an individual StructuralEvent.

The persistence adapter creates a summary record with event_type = ORCHESTRATION, event_count, final structure_state, and source provenance.

The actual structural engine separately produces StructuralEvent records with explicit event_location, confirmation_time and knowledge_time.

### 5.2 Applicable authoritative semantic

DOC-P4-002 is the ratified authority for deterministic structural facts.

It explicitly defines event location, confirmation time, knowledge time, zero-lookahead, closed-candle confirmation and immutable structural facts.

It also explicitly states that event location is not knowledge time.

For a genuine confirmed structural event, confirmation_time and knowledge_time are equal because only closed canonical candles are authoritative.

### 5.3 Semantic gap for the persisted ORCHESTRATION summary

The persisted ORCHESTRATION row is not itself one of those governed structural event objects.

It is an orchestration snapshot summary.

The ratified market-structure authority does not define a knowledge-time semantic for this summary record.

The repository therefore contains evidence for structural-event knowledge_time but not an authoritative semantic rule for ORCHESTRATION summary knowledge_time.

The fact that the implementation currently uses event_time = result.as_of does not create the missing semantic authority.

### 5.4 Knowledge-time conclusion

Conclusion: UNAVAILABLE / NOT AUTHORITATIVELY ESTABLISHED.

This family is deliberately not Class-B.

The correct evidence classification is:

- historical ORCHESTRATION summary: CLASS-C — insufficient authoritative semantic evidence;
- unsupported equality inference: CLASS-D — prohibited and not performed.

No generated-column equality is permitted to manufacture the missing semantic.

### 5.5 Consequence

The persistence migration keeps market_structure_events.knowledge_time nullable.

The persistence adapter does not claim or insert a structure-summary knowledge time.

The existing event_time remains the orchestration summary's persisted reference time, but it is not treated as authoritative knowledge_time.

The actual individual structural events retain their existing DOC-P4-002 knowledge-time semantics in the in-memory deterministic structure engine; this correction does not redesign their persistence model.

## 6. Per-family semantic matrix

| Family | Authoritative source | Event/reference boundary | Knowledge-time basis | Historical classification | knowledge_time == event_time |
|---|---|---|---|---|---|
| calculated_indicator_vectors | closed canonical candles + P4-002 indicator semantics | final primary candle close / orchestration as_of | final candle close is earliest legitimate exposure boundary | CLASS-B | Established |
| market_regime_states | closed canonical candles + P4-005 regime semantics | final primary candle close / orchestration as_of | final candle close is earliest legitimate exposure boundary | CLASS-B | Established |
| market_structure_events / ORCHESTRATION | orchestration summary of structure result | orchestration as_of | no ratified summary-fact knowledge-time rule | CLASS-C | Not established |

## 7. Historical evidence classification

Only two families have an evidence-backed deterministic reconstruction:

### CLASS-B
- indicator vectors;
- regime states.

Their authoritative value is reconstructible from the preserved event/reference boundary and the already-ratified closed-candle calculation semantics.

### CLASS-C
- persisted ORCHESTRATION structure summary.

The repository preserves its event_time and summary payload but does not preserve a ratified semantic authority establishing that its knowledge boundary is identical to its event/reference boundary.

### CLASS-D
No Class-D timestamp is created.

No value is reconstructed from persisted_at, logged_at, receipt time, database commit time, process wall clock, migration execution time, provider receipt latency, or arbitrary event-time substitution.

## 8. P5 boundary

This correction does not modify P5-002.

Even for the two CLASS-B families, the semantic result does not by itself establish AVAILABLE_PERSISTED.

P5 still independently requires knowledge_time <= snapshot.as_of plus complete EvidenceRef provenance, identity, timeframe, venue, and CONTROL-owned runtime availability evidence.

The structure summary remains unavailable for authoritative P5 knowledge-time purposes.

## 9. Migration compatibility

Migration 0008 uses STORED generated knowledge_time = event_time only for:

- calculated_indicator_vectors;
- market_regime_states.

market_structure_events.knowledge_time remains nullable.

This is compatible with the proven semantic model:

- deterministic materialization for Class-B families;
- explicit unavailable representation for the Class-C family;
- no historical UPDATE;
- no DELETE;
- append-only preservation;
- no privilege expansion;
- no competing truth store.

## 10. No new semantic rule

No new semantic rule was introduced.

The two CLASS-B conclusions recover existing P4 temporal semantics from:

CanonicalCandle
→ closed-candle calculation semantics
→ family-specific deterministic engine
→ orchestration boundary
→ existing persisted event/reference boundary.

The structure-summary non-equivalence is equally important: absence of authoritative semantic evidence is preserved as absence rather than repaired by declaration.

## 11. Evidence boundary

This document is a Producer evidence artifact.

It does not:

- modify P5-002;
- activate P5-003;
- reopen PH-P4;
- reopen STEP-P4-006;
- change G-4;
- perform VPS mutation;
- modify CONTROL closure artifacts;
- declare VERIFIED/CLOSED.

CONTROL must independently determine whether the semantic chain and classifications are sufficient for verification.
