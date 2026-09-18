# P4-001 — Deterministic Numeric Policy

Status: IMPLEMENTED / PRODUCER EVIDENCE ONLY
Scope: TO-P4-001 / STEP-P4-001
Authority: TO-P4-001, PH-P4, DOC-V2-ARCH-001; roadmap proposal used only as implementation input.

## Policy

1. Decimal is used at the public quantitative boundary and throughout the P4-001 primitive implementation. This implementation choice prevents binary floating-point drift and preserves exact decimal inputs.
2. Python float and bool are rejected by numeric conversion helpers. No implicit binary-float conversion is permitted.
3. NaN, positive infinity and negative infinity are rejected.
4. No implicit rounding occurs. Explicit quantization uses ROUND_HALF_EVEN.
5. Quantization requires an explicit positive Decimal quantum.
6. Deterministic serialization uses plain decimal notation without exponent notation, removing insignificant fractional trailing zeros.
7. Golden vectors use exact canonical value/status/reason equality. No epsilon tolerance is used.
8. Primitive operations use Decimal arithmetic. Square-root operations use at least 50 significant digits.
9. Insufficient history returns status INSUFFICIENT_HISTORY, a deterministic reason, and value=None.
10. Invalid or mathematically undefined inputs return INVALID_INPUT where they can be classified safely; type/shape contract violations raise explicit TypeError/ValueError rather than being silently repaired.
11. Primitive functions are pure: no network, database, filesystem, wall-clock or mutable-global dependency.
12. Identical inputs produce identical results across repeated executions in the supported Python/Decimal environment.

## Semantic choices

- standard_deviation default ddof=0 is population standard deviation; ddof=1 is sample standard deviation.
- percentile uses sorted values and linear interpolation over the inclusive 0..100 percentile domain.
- exponential_smoothing seeds from the first observation and then applies S_t = alpha*x_t + (1-alpha)*S_(t-1).
- normalize_min_max maps minimum to 0 and maximum to 1; zero range is INVALID_INPUT.
- rolling_mean emits explicit insufficient-history results through warm-up and valid results for complete windows.
- weighted_average rejects zero total weight.

## Golden-reference governance

The JSON vectors under tests/golden_vectors are controlled mathematical references. Changing an expected numeric value requires governed change control; it is not a routine fixture edit. This Producer document does not declare project-level freeze or verification.

## Non-goals

No technical indicator library, market-structure engine, volume profile engine, order-flow engine, derivatives engine, regime runtime, orchestration, API, replay, or AI interpretation is implemented here.
