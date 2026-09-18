# P4-002 Technical Indicator, Statistical & Volatility Semantics

**Step:** STEP-P4-002  
**Task Order:** TO-P4-002  
**Status:** IMPLEMENTATION DOCUMENTATION — NOT PROJECT VERIFICATION

## Design boundary

The engine is pure and provider-neutral. Its only canonical market-data input is CanonicalCandle; numeric moving-average functions also accept explicit finite Decimal/int/string numeric series. No provider, network, database, filesystem, clock, randomness, mutable global state, or trading capability is used.

Every candle result carries QuantitativeContext containing the candle provenance, close timestamp, timeframe, instrument identity, and calculation version. Candle sequences must be strictly increasing by open_time, with constant instrument/timeframe. The engine never sorts or repairs an input sequence.

By default, indicators require is_closed=True. Passing allow_incomplete=True explicitly permits provisional calculation and makes that choice part of the caller's deterministic configuration.

## Moving averages

- SMA: arithmetic mean of the last window observations; first window-1 results are INSUFFICIENT_HISTORY.
- WMA: linear weights 1..window, newest observation receiving the largest weight.
- EMA: seeded with the SMA of the first window observations, then alpha = 2/(window+1); no library-default seed is used.
- HMA: WMA(2*WMA(x,floor(n/2))-WMA(x,n), floor(sqrt(n))); periods below 2 are rejected.

## Momentum

- RSI: Wilder-style smoothing of gains/losses. Requires period+1 closes. A zero average loss with positive gain yields 100; zero gain and zero loss yields 50.
- MACD: fast EMA minus slow EMA, followed by an EMA signal line and MACD-signal histogram. Default configuration is 12/26/9. Signal warm-up begins only after the slow EMA becomes valid.

## Trend / volatility

- ATR: True Range is max(high-low, abs(high-previous_close), abs(low-previous_close)); the first TR is high-low. ATR is seeded from the first period TR values and then Wilder-smoothed.
- ADX: Wilder-smoothed TR and directional movement produce +DI/-DI, DX, then a Wilder-smoothed ADX. The first ADX requires 2*period-1 observations.
- Bollinger Bands: SMA middle band plus/minus deviations * population standard deviation.
- Supertrend: uses Wilder ATR, midpoint (high+low)/2, explicit multiplier, deterministic initial UP direction at the first valid ATR, and deterministic final-band recurrence.
- Historical Volatility: sample standard deviation (ddof=1) of rolling natural-log close returns, annualized by sqrt(periods_per_year). It requires window+1 closes.
- ATR percentile: current ATR's percentile rank among the current and preceding lookback-1 valid ATR observations, with rank normalized to 0–100.
- Volatility expansion ratio: current ATR divided by the rolling mean of the last baseline_window valid ATR values.
- Bollinger bandwidth: (upper-lower)/middle; zero middle is explicit INVALID_INPUT.

## Volume / activity

- Volume SMA: SMA over candle volume.
- RVOL: current volume divided by the mean of the immediately preceding window volumes. The current candle is intentionally excluded from its baseline.
- Volume spike: RVOL flag encoded as Decimal 1/0 using an explicit threshold, default 2.
- Volume climax: RVOL flag encoded as Decimal 1/0 using an explicit threshold, default 4.
- Zero prior-volume baseline is INVALID_INPUT; no substitution is made.

## VWAP

VWAP uses typical price (high+low+close)/3 and cumulative price-volume divided by cumulative volume.

Anchored VWAP requires an explicit anchor_index. Values before the anchor are INSUFFICIENT_HISTORY; zero cumulative volume is INVALID_INPUT. No system time, implicit session boundary, global state, or hidden anchor inference is used.

## Invalid and insufficient input policy

Detect → Classify → Route is applied as follows:

- malformed/non-numeric values at the public numeric boundary raise the established P4-001 TypeError/ValueError;
- invalid mathematical states produce CalculationStatus.INVALID_INPUT;
- insufficient history produces CalculationStatus.INSUFFICIENT_HISTORY;
- non-finite values are rejected;
- zero denominators are never silently replaced;
- contradictory temporal ordering is rejected;
- duplicate observations are not silently de-duplicated;
- missing required OHLCV fields cannot be substituted because CanonicalCandle validates the canonical boundary.

## Determinism and temporal integrity

The implementation uses Decimal arithmetic and explicit local precision contexts for numerically sensitive operations. It never reads wall-clock time. Results for an already-emitted observation depend only on observations up to that point. Tests explicitly compare base and future-extended sequences to detect lookahead.

Controlled vectors are stored in tests/golden_vectors/p4_002_indicators.json and are compared by exact canonical Decimal serialization.

## Scope discipline

This document covers only STEP-P4-002. Market structure, volume profile/order flow/derivatives, regime/venue intelligence, orchestration/MTF/API/replay runtime, AI/LLM interpretation, Opportunity Score, trading/capital functionality, V1 integration, and unrelated refactoring remain outside this implementation boundary.
