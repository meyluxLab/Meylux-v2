# P4-003 — Authoritative Market Structure Semantics Specification

**Stable Document ID:** `DOC-P4-002`
**Step:** `STEP-P4-003`
**Task Order:** `TO-P4-004`
**Status:** RATIFIED / AUTHORIZED
**Decision Authority:** `ROL-V2-001 — CONTROL / REVIEWER`
**Delegation Basis:** Project Owner Directive — `STEP-P4-003 / TO-P4-004 — Full Authority Delegated to CONTROL for Market-Structure Semantics`, 2026-09-19
**Governing ADR:** `ADR-QUANTITATIVE-001`
**Architecture:** `DOC-V2-ARCH-001` — RATIFIED / FROZEN
**Reference Roadmap:** `DOC-P4-001` — reference input only; adopted proposals are expressly ratified below

## 1. Authority and Scope

This document is the authoritative deterministic semantic specification for the Market Structure Engine in `STEP-P4-003`.

It was established and ratified by CONTROL under explicit Project Owner delegation. It resolves the semantic Open Question `OQ-P4-003-STRUCTURE-SEMANTICS` and is the semantic authority referenced by `TO-P4-004`.

This specification governs only deterministic structural fact generation and state evolution over trusted canonical Phase-3 candle input. It does not authorize AI/LLM interpretation, opportunity scoring, Venue Intelligence, trading, execution, capital behavior, future Phase-4 Steps, V1 work, VPS/runtime work, or unrelated redesign.

Higher-order architecture, constitutional invariants, ratified ADRs, existing canonical contracts, and the P4-001 numeric policy always prevail over this specification.

## 2. Core Invariants

1. **Zero-lookahead is primary.** No future candle, future state, future aggregate, or future-derived value may affect an earlier authoritative state.
2. **Closed canonical input only.** Structural facts are authoritative only from `is_closed=True` candles.
3. **Event location is not knowledge time.** A historical event may belong to an earlier candle while becoming observable only on a later closed candle.
4. **Determinism.** Identical canonical input, configuration, and semantic version produce identical events, states, identities, and lifecycle transitions.
5. **Exact numeric equality.** Decimal comparisons are exact. No epsilon/tolerance substitution is permitted unless this specification explicitly defines one; this specification defines none.
6. **No silent repair.** Missing, malformed, contradictory, non-finite, or discontinuous evidence is detected and classified; it is never fabricated or silently repaired.
7. **Ambiguity is explicit.** Where the available evidence cannot deterministically establish a state, the state is `UNCONFIRMED`.
8. **Append-only structural truth.** Historical structural facts are not retroactively rewritten. Later contradictory evidence creates a new invalidation/state-transition fact rather than mutating the old fact.
9. **Pure computation.** No wall clock, network, database, filesystem, randomness, or mutable global state participates in authoritative calculation.
10. **P4-001 numeric policy applies.** Decimal arithmetic, finite values, explicit quantization where required by an output boundary, exact comparisons, and no float/bool numeric substitution remain mandatory.

## 3. Temporal Model

Every structural fact that is observable in the public semantic result has:

- `event_location`: the candle `open_time` to which the event belongs;
- `confirmation_time`: the earliest closed-candle `close_time` at which the event itself is confirmed;
- `knowledge_time`: the earliest time the engine can authoritatively expose the fact.

For this Step, `confirmation_time` and `knowledge_time` are equal for confirmed events because only closed canonical candles are authoritative. They remain separate fields because event location may precede both.

A fact must never be emitted as confirmed at its event location when its confirmation requires later candles.

## 4. Canonical Sequence and Continuity

Input candles must be strictly increasing by `open_time`, with a stable instrument and timeframe. The engine must not sort, deduplicate, interpolate, backfill, or repair input.

For supported fixed candle intervals (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`), the expected interval is deterministic from the timeframe. A continuity break exists when the next canonical `open_time` is later than the immediately expected slot.

If the timeframe has no governed fixed-duration mapping, the engine must not infer continuity from observed spacing. Continuity is then `UNCONFIRMED` rather than guessed.

At a continuity break:

- no swing confirmation may use candles across the break;
- no BOS/CHOCH/MSS may use a structural level whose required evidence crosses the break;
- no FVG/OB/Breaker/Liquidity lifecycle transition may infer an unobserved path across the break;
- the official per-bar structure state becomes `UNCONFIRMED` until a new valid evidence window establishes a state;
- previously confirmed facts remain immutable;
- resumption requires fresh valid evidence and does not retroactively reconstruct missing bars.

A quarantined/rejected canonical bar is equivalent to unavailable evidence for continuity purposes.

## 5. 5/5 Swing Semantics

A candidate candle at index `i` is a **Swing High** exactly when:

`high[i] > high[j]` for every `j in {i-5,...,i-1,i+1,...,i+5}`.

A candidate candle at index `i` is a **Swing Low** exactly when:

`low[i] < low[j]` for every `j in {i-5,...,i-1,i+1,...,i+5}`.

Equality with any comparison candle disqualifies the candidate. There is no tie-breaking by index, tolerance, tick size, or preference.

The candidate itself is the event location. The earliest confirmation/knowledge time is the `close_time` of candle `i+5`, provided every candle in the required eleven-candle window is valid, canonical, closed, and continuous.

If fewer than five valid future candles or fewer than five valid prior candles are available, the candidate is not a confirmed swing. No provisional swing is exposed as authoritative.

A candle cannot simultaneously be confirmed as both Swing High and Swing Low under these strict inequalities.

## 6. HH / HL / LH / LL Classification

Classification is performed only when a new swing of the same type is confirmed.

For Swing High:
- current high > previous confirmed Swing High high → `HH`;
- current high < previous confirmed Swing High high → `LH`;
- exact equality → `UNCONFIRMED` for classification; no HH/LH label is emitted.

For Swing Low:
- current low > previous confirmed Swing Low low → `HL`;
- current low < previous confirmed Swing Low low → `LL`;
- exact equality → `UNCONFIRMED` for classification; no HL/LL label is emitted.

The previous reference is the immediately preceding confirmed swing of the same type after all continuity boundaries. A reference from before a canonical gap cannot be used after the gap.

The first confirmed swing of either type has no comparative classification and is represented as an unclassified swing fact. It does not establish a directional structure state.

## 7. Structure State Machine

The official per-bar structure state is one of:

`TRENDING_UP`, `TRENDING_DOWN`, `RANGE`, `NEUTRAL`, `UNCONFIRMED`.

State is evaluated after processing all evidence that becomes knowable on the current closed candle.

### 7.1 TRENDING_UP

Requires the latest confirmed classified Swing High to be `HH` and the latest confirmed classified Swing Low to be `HL`, with both references occurring after the most recent continuity boundary and no unresolved CHOCH waiting for MSS confirmation.

### 7.2 TRENDING_DOWN

Requires the latest confirmed classified Swing High to be `LH` and the latest confirmed classified Swing Low to be `LL`, with both references occurring after the most recent continuity boundary and no unresolved CHOCH waiting for MSS confirmation.

### 7.3 RANGE

A valid continuous structure exists with at least one confirmed high and one confirmed low, but the latest classified high/low pair does not satisfy either directional rule and there is no unresolved ambiguity.

### 7.4 NEUTRAL

Insufficient confirmed structure exists to establish a directional or range state, but there is no active continuity break and no contradictory evidence.

### 7.5 UNCONFIRMED

Used when:
- a canonical continuity boundary has just occurred;
- an equality prevents deterministic classification;
- a CHOCH has placed the structure in transition pending MSS;
- a required structural reference is unavailable or contradictory;
- available evidence is insufficient to distinguish competing states.

`UNCONFIRMED` is never replaced by a guessed directional state merely to avoid an incomplete output.

## 8. BOS

BOS is a **close-confirmed** structural break. Wick-only penetration is not a BOS.

### Bullish BOS

A bullish BOS occurs when a closed candle has:

`close > latest confirmed structural Swing High level`

and the level belongs to a confirmed structure that is not separated from the current candle by a continuity boundary.

### Bearish BOS

A bearish BOS occurs when:

`close < latest confirmed structural Swing Low level`.

Equality is not a break.

The reference level is the most recent confirmed opposing structural swing relevant to the current state. A level that was already broken in the same direction cannot generate a duplicate BOS.

For each BOS:
- event location = triggering candle `open_time`;
- confirmation_time = triggering candle `close_time`;
- knowledge_time = triggering candle `close_time`;
- level = exact Decimal reference level;
- direction = bullish/bearish.

A BOS fact is immutable. If later evidence makes the resulting structure obsolete or invalid, the engine emits a distinct invalidation/state-transition fact referencing the original identity; it does not delete or mutate the original BOS.

## 9. CHOCH

CHOCH is the first confirmed break against the current directional structure.

From `TRENDING_UP`, a bearish close through the latest protected Swing Low produces bearish CHOCH.

From `TRENDING_DOWN`, a bullish close through the latest protected Swing High produces bullish CHOCH.

CHOCH uses the same close-only break rule as BOS.

A CHOCH transitions the official structure state to `UNCONFIRMED`. It does not by itself declare the opposite trend confirmed.

The CHOCH fact records its protected reference level, direction, event location, confirmation/knowledge time, and prior structural state.

## 10. MSS

MSS is the **confirmed state transition following CHOCH**, not an alternative name for BOS.

After a bullish CHOCH from a downtrend, the engine waits for a new valid bullish structural sequence and a bullish break of the newly established protected high. That event confirms `TRENDING_UP` and is recorded as bullish MSS.

After a bearish CHOCH from an uptrend, the engine waits for a new valid bearish structural sequence and a bearish break of the newly established protected low. That event confirms `TRENDING_DOWN` and is recorded as bearish MSS.

Thus:

`old trend → CHOCH → UNCONFIRMED transition state → qualifying opposite structure → MSS → new trend`.

A CHOCH without the required subsequent evidence never becomes MSS merely because additional candles exist.

MSS uses close-only breaks, exact Decimal comparisons, event/knowledge timing rules, and immutable event identity.

## 11. Fair Value Gap

FVG detection uses a three-candle sequence ending at current closed candle `i`.

Bullish FVG exists when:

`low[i] > high[i-2]`.

Its zone is:

`lower_bound = high[i-2]`
`upper_bound = low[i]`.

Bearish FVG exists when:

`high[i] < low[i-2]`.

Its zone is:

`lower_bound = high[i]`
`upper_bound = low[i-2]`.

Equality produces no FVG.

The event location is the third candle `open_time`; confirmation/knowledge time is its `close_time`.

Lifecycle is exactly:

`ACTIVE → PARTIALLY_MITIGATED → FULLY_MITIGATED`.

For a bullish FVG:
- no overlap with the zone → remains `ACTIVE`;
- price low enters the zone but remains above `lower_bound` → `PARTIALLY_MITIGATED`;
- price low reaches or crosses `lower_bound` → `FULLY_MITIGATED`.

For a bearish FVG:
- no overlap → `ACTIVE`;
- price high enters the zone but remains below `upper_bound` → `PARTIALLY_MITIGATED`;
- price high reaches or crosses `upper_bound` → `FULLY_MITIGATED`.

Mitigation uses observed candle wick ranges because mitigation is a zone-intersection fact, not a structural break rule.

A fully mitigated FVG is terminal. No revival is permitted. Across a continuity gap, the engine must not infer an unseen partial/full transition.

## 12. Order Blocks

An Order Block is created only from a structural displacement that is already confirmed by a BOS, CHOCH, or MSS event.

For a bullish displacement, the source Order Block is the nearest preceding **bearish-body** closed candle before the triggering displacement candle. For a bearish displacement, it is the nearest preceding **bullish-body** closed candle.

A candle has a bullish body when `close > open`, bearish body when `close < open`. A doji is not an Order Block source.

The source search stops at the most recent continuity boundary and never crosses it.

The zone boundaries are exactly the source candle's `low` and `high`. No ATR, percentage, volume, or discretionary strength filter is introduced.

If no qualifying opposite-body source candle exists, no Order Block is emitted.

An Order Block becomes `ACTIVE` when the associated structural displacement becomes known. Its identity includes source candle identity, direction, zone bounds, and originating structural event identity.

## 13. Order Block Invalidation and Breakers

An active bullish Order Block is invalidated when a closed candle closes strictly below its lower bound.

An active bearish Order Block is invalidated when a closed candle closes strictly above its upper bound.

Wick-only penetration does not invalidate an Order Block.

Invalidation is immutable and emits a distinct lifecycle transition.

A bullish Order Block invalidated by a bearish close becomes a **bearish Breaker**.

A bearish Order Block invalidated by a bullish close becomes a **bullish Breaker**.

Breaker boundaries remain the original Order Block boundaries. A Breaker inherits the source identity and records the invalidating event.

A Breaker is not retroactively treated as an Order Block again. It remains a distinct structural zone state.

A Breaker is invalidated only by a closed candle closing through its opposite boundary:
- bearish Breaker invalidated by close above upper bound;
- bullish Breaker invalidated by close below lower bound.

No wick-only breaker transition is recognized.

## 14. Liquidity Pools

Liquidity pools are structural facts formed from repeated confirmed same-side swing levels.

A bullish-side liquidity pool consists of at least two confirmed Swing High levels that are **exactly equal** as Decimal values.

A bearish-side liquidity pool consists of at least two confirmed Swing Low levels that are exactly equal.

No percentage, tick, epsilon, or proximity tolerance is used. P4-001 exact equality governs.

The pool is created when the second matching swing becomes confirmed. Its identity is derived from instrument, timeframe, side, exact level, and the ordered identities of its member swings.

A pool remains active until a closed candle closes strictly beyond the pool level in the direction that consumes the level. That event is recorded as a structural pool-sweep/invalidation fact. No opportunity, probability, or trading interpretation is attached.

A continuity gap prevents new members from being matched with pre-gap members.

## 15. Structural Event Identity and Duplicate Prevention

Every structural event has a deterministic identity derived from:
- instrument;
- timeframe;
- semantic specification version;
- event type;
- event location;
- confirmation/knowledge time;
- direction where applicable;
- reference level or zone bounds where applicable;
- source structural identity where applicable.

Identity serialization uses canonical deterministic field ordering and exact Decimal serialization consistent with P4-001.

The same canonical input cannot emit two identities for the same semantic event.

A later recalculation must reproduce the same identity. Duplicate prevention must be semantic, not based on process-local mutable state.

## 16. Invalidation Rules

Invalidation is additive and append-only.

A previously emitted structural fact is never deleted or rewritten because later candles change its interpretation.

Each invalidation event references the original structural identity and records:
- invalidated object identity;
- invalidation event location;
- confirmation/knowledge time;
- exact trigger;
- resulting lifecycle/state.

No invalidated object may silently return to an earlier lifecycle state.

## 17. Per-Bar State Evolution

For each closed input candle, the engine must deterministically process in this order:

1. validate sequence continuity and canonical eligibility;
2. establish continuity boundary state if applicable;
3. confirm any newly eligible 5/5 swings;
4. classify newly confirmed swings;
5. update structural state;
6. evaluate structural breaks (BOS/CHOCH/MSS) against the state that existed immediately before the break;
7. create/transition Order Blocks and Breakers from already-confirmed structural events;
8. create/transition FVGs;
9. update liquidity pools;
10. emit the official post-bar structure state and all newly known events.

Events caused by the current candle may depend only on information available through that candle's close.

The implementation must expose enough evidence to reconstruct:

`canonical bars → confirmed swings → classifications → structural events → lifecycle transitions → per-bar state`.

## 18. Insufficient History and Ambiguity

The engine must not manufacture a first swing classification, directional state, BOS reference, CHOCH reference, MSS confirmation, FVG mitigation path, OB source, Breaker transition, or liquidity pool when the required evidence is absent.

Use:
- `INSUFFICIENT_HISTORY` for required history that does not yet exist;
- `UNCONFIRMED` for an otherwise structurally relevant state that cannot be deterministically resolved from available evidence.

These are distinct from `INVALID_INPUT`, which applies to malformed/contradictory contract input.

## 19. Pinned Worked Scenario A — 60-Candle Trend with BOS

Use candles indexed `0..59`. All candles not explicitly identified below must be constructed so that they do not create competing 5/5 swings, gaps, or breaks.

Required confirmed structural pivots:

| Candidate | Type | Exact level | Classification |
|---:|---|---:|---|
| 7 | Low | 95 | first low |
| 12 | High | 105 | first high |
| 17 | Low | 100 | HL |
| 22 | High | 112 | HH |
| 27 | Low | 107 | HL |
| 32 | High | 118 | HH |

The 32 high becomes confirmed only at candle 37 close because of the 5/5 rule.

Expected state evolution:
- before sufficient paired structure: `NEUTRAL`;
- after 17/22 become confirmed and paired: `TRENDING_UP`;
- after 27/32 become confirmed and paired: `TRENDING_UP`;
- candle 38 close at 117 or below 118: no BOS;
- candle 39 close at 121: bullish BOS of level 118;
- BOS event location = candle 39 open_time;
- BOS confirmation/knowledge time = candle 39 close_time;
- post-event state remains `TRENDING_UP`.

The scenario must prove that a hypothetical candle 33–36 close above 118 cannot produce BOS because the level at 32 was not yet confirmed until candle 37.

## 20. Pinned Worked Scenario B — 60-Candle Reversal with CHOCH

Use a continuous 60-candle sequence sharing the same initial uptrend through confirmed swings 7/12/17/22/27/32.

After the 32 high is confirmed at candle 37:
- candle 40 closes strictly below the protected Swing Low at 107;
- this produces bearish CHOCH;
- event location = candle 40;
- knowledge time = candle 40 close;
- official state becomes `UNCONFIRMED`.

The sequence must then contain:
- a newly confirmed lower low derived from post-CHOCH evidence;
- a newly confirmed lower high;
- a later closed candle that breaks the newly established protected low.

That later qualifying break produces bearish MSS and changes the official state to `TRENDING_DOWN`.

The scenario must prove that CHOCH alone does not immediately produce `TRENDING_DOWN`, and that MSS cannot be emitted until the required post-CHOCH evidence exists.

## 21. Pinned Worked Scenario C — Canonical Gap

Use a continuous pre-gap structure, then omit at least one expected canonical candle.

Expected behavior:
- no swing confirmation may bridge the gap;
- no BOS/CHOCH/MSS may consume a reference whose required evidence crosses the gap;
- active lifecycle objects cannot infer unseen mitigation/invalidation across the gap;
- official structure state becomes `UNCONFIRMED`;
- after continuity resumes, the engine requires fresh valid evidence before establishing a directional state;
- replaying the exact same gapped sequence reproduces the exact same event/state sequence.

## 22. Deterministic Replay Requirement

Replay of an identical canonical sequence must reproduce:
- event identities;
- event locations;
- confirmation/knowledge times;
- exact Decimal levels/bounds;
- lifecycle transitions;
- per-bar structure states;
- invalidation references.

Appending future candles to a previously evaluated prefix must not change any already-authoritative knowledge-time output for that prefix.

This property is a mandatory zero-lookahead regression condition.

## 23. Alternative Decisions Considered

### BOS: close vs wick
- **Wick:** more sensitive to transient intrabar excursions and would make break confirmation dependent on extremes.
- **Close:** aligns break confirmation with a completed canonical candle and provides a deterministic structural confirmation boundary.
- **Selected:** **close**.

### Swing equality
- **Tie-break by latest/earliest candle:** deterministic but would manufacture a pivot from equal evidence.
- **Exact equality = no pivot:** preserves evidence-backed state and P4-001 exact comparison policy.
- **Selected:** **equality disqualifies the swing**.

### Liquidity tolerance
- **Configurable epsilon/tick tolerance:** introduces an additional parameter and instrument-specific interpretation not established by the current contract.
- **Exact Decimal equality:** uses existing P4-001 policy without inventing tolerance.
- **Selected:** **exact equality only**.

### CHOCH vs MSS
- **Treat them as synonyms:** simpler but fails to provide a distinct state-machine transition.
- **CHOCH = counter-trend break; MSS = confirmed new-trend transition after additional structure:** preserves the roadmap's requirement that MSS be state-machine behavior.
- **Selected:** **distinct two-stage transition**.

### OB source
- **Discretionary displacement strength / ATR / volume threshold:** requires additional semantics and parameters.
- **Nearest preceding opposite-body candle tied to a confirmed structural displacement:** deterministic and uses only existing candle evidence.
- **Selected:** **nearest preceding opposite-body source candle**.

## 24. Versioning

Semantic version for this specification starts at `1.0.0`.

Any change to a rule affecting event identity, state transition, lifecycle, timing, equality, or output semantics is a governed semantic change and requires a new revision and corresponding change-control record.

Implementation must expose its calculation/semantic version so replay results remain attributable to the governing specification.

## 25. Implementation Boundary

Producer may now implement `TO-P4-004` against this specification.

The implementation must not:
- reinterpret any selected rule;
- add an alternative BOS/CHOCH/MSS definition;
- introduce hidden tolerances;
- introduce future-step functionality;
- use AI/LLM interpretation;
- create trading or opportunity behavior;
- silently alter canonical contracts;
- bypass the P4-001 numeric policy.

Any implementation discovery that conflicts with this specification or a higher-order authority must stop only the affected portion and return the exact conflict to CONTROL.
