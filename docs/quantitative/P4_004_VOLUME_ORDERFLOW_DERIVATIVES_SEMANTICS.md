# DOC-P4-003 — Authoritative Volume Profile, Order Flow & Derivatives Semantics

Status: RATIFIED / AUTHORIZED
Stable Document ID: DOC-P4-003
Decision Authority: ROL-V2-001 — CONTROL / REVIEWER
Delegation Basis: Project Owner Directive — AUTHORIZE STEP-P4-004 / Volume Profile, Order Flow & Derivatives Engine, 2026-09-19
Phase / Step: PH-P4 / STEP-P4-004
Task Order: TO-P4-005

## 1. Governing rules
This is the authoritative deterministic semantic boundary for STEP-P4-004. It does not amend the frozen architecture or superior ADRs.
- Existing P4 Decimal policy governs authoritative arithmetic; reject binary floats and non-finite values.
- Missing/unavailable evidence is explicit; never fabricate zero, NaN, Infinity, or unrelated substitutes.
- Pure authoritative calculations have no hidden wall-clock, network, database, filesystem, mutable-global, or provider-runtime dependency.
- Identical governed input plus identical explicit configuration produces identical output and ordering.
- UTC-aware timestamps are required; no undocumented epsilon/tolerance.
- Preserve provenance and calculation version through existing quantitative result/context contracts.
- Outputs are facts only: no opportunity score, forecast, recommendation, trade signal, or execution instruction.

## 2. Volume Profile
Input is validated CanonicalTrade events for one instrument and one explicitly supplied profile interval. Hidden session/calendar discovery is forbidden.
Required configuration is positive Decimal price_bin_size. No hidden default or inferred provider tick size.
Binning is exact Decimal floor bucketing: bin_lower = floor(price / price_bin_size) * price_bin_size. Each trade contributes quantity to exactly one bin.
POC is the maximum-volume bin. Exact maximum ties select the lowest-price bin.
Value Area target is exactly 70% of total profile volume. Start at POC and expand to adjacent bins until accumulated volume is >= 70%. When both sides exist choose greater adjacent volume; exact ties choose the lower-price side first; if only one side exists choose it. Stop immediately at threshold. VAL is the lowest selected-bin lower bound; VAH is the highest selected-bin upper boundary. Empty profiles have no numeric POC/VAH/VAL.
HVN/LVN are configuration-driven, never Producer-invented. hvn_threshold and lvn_threshold are explicit finite Decimal ratios against POC-bin volume. HVN qualifies at >=; LVN qualifies at <=; equality qualifies. Missing thresholds return UNAVAILABLE. Zero-volume bins are not HVN.
Composite profiles may aggregate only explicitly supplied constituent intervals, deterministically ordered by interval.

## 3. Order Flow
Bar Delta: BUY aggressor quantity is positive; SELL quantity negative; Delta = BUY - SELL. Missing aggressor evidence for required trades returns UNAVAILABLE, never candle-direction guessing.
CVD is the cumulative sum of valid Bar Delta over explicitly ordered closed bars. First value is first valid Delta; each next value is prior CVD plus current Delta. Missing/invalid Delta is not zero and does not silently advance cumulative state. Same complete input must replay exactly.
Imbalance requires explicit imbalance_ratio_threshold > 1. For adjacent levels/buckets with non-zero opposing volume, ratio = dominant / opposing; qualify at ratio >= threshold. Zero opposing volume never becomes Infinity; return explicit unavailable/insufficient semantics. Tests cover below/equal/above threshold.
Absorption is a fact only with aggressive trade evidence plus contemporaneous order-book evidence. Explicit configuration must include absorption_volume_threshold and max_price_displacement. A qualifying observation requires aggressive volume >= threshold, opposite-side resting quantity at the observed price, and no traversal beyond configured displacement during the observation window. Missing evidence/configuration returns UNAVAILABLE; no motive is inferred.

## 4. Derivatives
Input is only CTR-V2-CANONICAL-DERIVATIVES. Missing derivatives evidence is never reconstructed from candles, trades, order books, providers, or other venues.
Funding rate/change are exposed exactly as canonical values. Derived funding velocity is (current funding - prior funding) / elapsed_seconds only with explicit ordered observations and elapsed_seconds > 0. Funding acceleration is (current velocity - prior velocity) / elapsed_seconds under the same rule.
Zero/negative elapsed time is INVALID_INPUT; absent history is INSUFFICIENT_HISTORY. If canonical funding_velocity is supplied it may be exposed as supplied rather than silently replaced.
Derived OI delta is current OI - prior OI; absent prior observation is INSUFFICIENT_HISTORY, not zero. Basis is exposed from canonical basis; mark/index prices are never invented.

## 5. Output boundary
Existing CalculationResult, VolumeProfileResult, OrderFlowResult, and canonical derivatives contracts remain the output foundation. Only minimal additive output fields strictly required here may be proposed through the governed contract-change process; no new canonical Stable ID is invented.
Every result distinguishes metric identity, numeric value versus status/reason, calculation version, provenance/context, and explicit profile/configuration identity where supported.

## 6. Mandatory Rule-5 evidence
Tests must directly cover: empty/one-trade profiles; exact POC tie; exact 70% boundary; value-area expansion tie; exact bin boundaries; missing/invalid bin size; HVN/LVN equality; missing aggressor side; CVD replay and missing evidence; imbalance below/equal/above threshold and zero opposing volume; absorption without required book evidence; missing derivatives fields; first-observation velocity/OI-delta; zero/negative elapsed time; large/small Decimal values; malformed/non-finite/contradictory inputs; repeated deterministic replay and no-lookahead temporal sequences.

## 7. Scope
Only STEP-P4-004 is covered. STEP-P4-005, STEP-P4-006, G-4 closure, Phase 5+, AI/LLM interpretation, Venue Intelligence/Opportunity Engine, trading/capital/execution, V1, and VPS/runtime remain outside this specification.

Ratification: CONTROL, under the explicit Project Owner delegation dated 2026-09-19, ratifies this specification as the semantic authority for TO-P4-005. A genuine superior-authority conflict is handled under ADR-GOVERNANCE-013 Rule 1(B).