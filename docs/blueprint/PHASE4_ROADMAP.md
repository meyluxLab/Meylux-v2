=====================================================================================
MEYLUX PHASE 4 MASTER ROADMAP
Deterministic Quantitative & Market Structure Engine (PH-P4)
Authority: Master Blueprint v5.1.1 (Section 4 PH-P4, Section 5 DB-P4-*, Section
12 TST-P4-*, Section 23 ACR-0008, Golden Vector Freeze E6)
Version: 1.0-DRAFT -> pending operator ratification
Storage upon ratification: docs/blueprint/PHASE4_ROADMAP.md
Supersedes: nothing (pure elaboration of ratified PH-P4; zero conflicts)
=====================================================================================

SECTION 1 - MISSION & PRINCIPLES
1.1 Mission: transform canonical market data into deterministic, reproducible,
    mathematically-verified FACTS. AI reasons OVER these outputs; it NEVER
    computes them [INV-2].
1.2 Prime directives:
    - PURITY: quant functions have no clock, no I/O, no network, no DB.
    - DETERMINISM: same inputs -> byte-identical outputs, forever.
    - GOLDEN VECTOR FREEZE [E6]: every public math function is pinned by
      input->output vectors; any math change requires ACR + vector update.
    - ZERO NaN/Inf [INV-3]: insufficient history -> explicit None + reason.
    - Candle-Close Trigger: only is_closed=True candles enter computation.
1.3 Input: List[CanonicalCandle] sorted ascending. Outputs: Decimal(10dp)
    quantized at the boundary (see Section 10 Numeric Policy).

SECTION 2 - SIX-STEP DECOMPOSITION
STEP 1 - QUANT CORE + GOLDEN VECTOR FREEZE
  (already commissioned: TO-P4-STEP1-001)
  Engine facade, EMA/SMA/WMA/HMA, RSI(Wilder), MACD(12/26/9); golden_vectors.py
  with 8 pinned cases + runner; generator script (audit-only).
  SIDs: ART-P4-005/006/007/024, TST-P4-001, SCR-P4-001.
  DoD: golden runner failed==0 (REAL sandbox output); suite green.
STEP 2 - TECHNICAL COMPLETION
  ATR14, Bollinger(20,2), HV; VolumeSMA/RVOL/Climax; VWAP + Anchored VWAP
  (session anchors as explicit params). Contract CTR-P4-001 IndicatorVector.
  New golden cases: ATR w/ gap-open, BB squeeze, RVOL 2x spike, VWAP 2 sessions.
  SIDs: ART-P4-008/009. Tests: TST-P4-001 extended.
STEP 3 - MARKET STRUCTURE ENGINE [CMP-P4-002]
  Fractal swing detection (5/5), trend/range state, BOS/CHOCH/MSS state
  machine, Order Blocks + Breakers, FVG with 3-stage mitigation lifecycle
  (ACTIVE / PARTIALLY_MITIGATED / FULLY_MITIGATED), liquidity pools.
  Contract CTR-P4-002 MarketStructure. Two pinned 60-candle scenarios
  (trend-with-BOS; reversal-with-CHOCH) reproduced event-by-event. State
  machine MUST be total: every bar maps to exactly one state; ambiguous ->
  explicit UNCONFIRMED (never guessed).
  SIDs: ART-P4-010..013. Tests: TST-P4-002/003 + totality property test.
STEP 4 - VOLUME PROFILE + ORDER FLOW + DERIVATIVES
  POC/VAH/VAL (70% value area), HVN/LVN; Delta/CVD/Imbalance/Absorption;
  funding acceleration, OI delta, Basis.
  SIDs: ART-P4-014/015/016/017/018/019; CTR-P4-003/004.
STEP 5 - MARKET REGIME + CROSS-VENUE QUANTITATIVE ENGINE
  8-state regime classifier with hysteresis and quantitative cross-venue
  capability per Section 23 / ACR-0008.
  SIDs: ART-P4-020/021; CTR-P4-005.
STEP 6 - PERSISTENCE + WORKER + API + G-4
  Quantitative persistence, computation worker on candle close, six timeframes
  (1m/5m/15m/1h/4h/1d), read-only APIs, Redis stream/queue integration and
  complete G-4 evidence.
  SIDs: ART-P4-022/023/029, DB-P4-001..005, API-P4-001/002,
  QUE-P4-001/002, WRK-P4-001.

SECTION 3 - FILE / ARTIFACT MAP
  meylux/quant/engine.py                         [ART-P4-005]
  meylux/quant/technical/                       [ART-P4-006..009]
  meylux/quant/structure/                       [ART-P4-010..013]
  meylux/quant/volume_profile/                  [ART-P4-014..015]
  meylux/quant/derivatives/                     [ART-P4-016..017]
  meylux/quant/order_flow/                      [ART-P4-018..019]
  meylux/quant/regime/                          [ART-P4-020..021]
  meylux/database/models/quantitative.py        [ART-P4-022]
  meylux/workers/tasks/computation.py           [ART-P4-023]
  meylux/quant/golden_vectors.py                [ART-P4-024]
  alembic/versions/0005_quant_persistence.py   [ART-P4-029 PROPOSED]
  contracts/quantitative/{indicators,structure,
    volume_profile,order_flow,regime}.py        [CTR-P4-001..005]
  config/quantitative.yaml                      [ART-P4-030 PROPOSED]
  scripts/generate_golden_vectors.py            [SCR-P4-001 PROPOSED, audit-only]
  tests/unit/test_quantitative/                 [TST-P4-001..004]
  DB: DB-P4-001..005 | QUE: QUE-P4-001/002 | API: API-P4-001/002
  Worker: WRK-P4-001

SECTION 4 - CONFIG MATRIX
  swing_left=5, swing_right=5, fvg_min_threshold_pct=0.1, rvol_spike=2.0,
  bb_period=20, bb_std=2.0, atr_period=14, rsi_period=14,
  macd_fast=12/slow=26/signal=9, regime_ema_fast=50, regime_ema_slow=200,
  regime_hysteresis_factor=0.5, vwap_session_anchor=UTC-midnight,
  value_area_pct=70.0.

SECTION 5 - PERFORMANCE TARGETS [PERF-P4-001]
  HARD: zero NaN/Inf; byte-identical reruns.
  TARGET: <5ms per indicator per 1000 bars; <50ms full multi-TF vector
  (1M/5M/15M/1H/4H/1D) on VPS-class core.
  OPTIMIZATION (non-blocking): vectorized internals, per-TF caching.

SECTION 6 - SECURITY
  Pure computation: zero network egress, zero subprocess, no dynamic imports;
  DB INSERT/SELECT only; no secrets; AST trade-probe coverage extended to
  meylux/quant/**.

SECTION 7 - TEST ARCHITECTURE
  Unit (hand-computed micro) + Golden Vectors (pinned macro) + Property
  (state-machine totality, CVD monotonicity, length alignment) + Replay
  (1-day window, zero-lookahead) + Failure (short history, zero-volume,
  unsorted input) + Regression.

SECTION 8 - GATE ALIGNMENT (G-4)
  G-4 closes when: math suite 100% (0 deviation); <5ms measured; 0 NaN/Inf
  across 1M-bar synthetic soak; STEP-6 evidence bundle verified; P3-debt
  items R1/R2 (API wiring, worker registrations) closed here or explicitly
  re-ratified as P5-entry items.

SECTION 9 - RISK REGISTER
  R1 numeric policy (Section 10) - RESOLVE AT ENTRY.
  R2 TA-Lib availability (Open Decision #2) - deferred per Section 10.
  R3 structure ambiguity - UNCONFIRMED labels + property tests.
  R4 cross-architecture determinism - Decimal boundary + pinned vectors.
  R5 dual worker package - superseded at STEP-6 rebuild.

SECTION 10 - NUMERIC POLICY
  OD-A [CRITICAL, RECOMMENDED = Option H "Hybrid with Decimal boundary"]:
  internals may use float64 (pure Python or NumPy; TA-Lib only if the
  <5ms target is missed and measured), BUT every public function quantizes
  output to Decimal(30,10) at the boundary, and Golden Vectors pin the
  QUANTIZED values. Residual float error (<1e-12 relative) is documented
  and acceptable for analytic features. Money-grade precision remains
  enforced where money actually moves (canonical data, DB).
  OD-B: TA-Lib DEFERRED - pure-Decimal baseline first; introduce only as a
  measured optimization with golden vectors as referee.
  OD-C: Regime thresholds ratified as starting defaults; tuned post-P9.

SECTION 11 - PARALLEL TRACK (VENUE, per ACR-0008 / Section 23)
  V1-0 readiness matrix (evidence-only) runs parallel to STEPS 1-3.
  V1-M1+ (venue engine: spread math, book walk, 8 gates, persistence)
  starts after V1-0 sign-off, parallel to STEPS 4-6. Venue math is NOT
  folded into PH-P4 (track separation is normative).

SECTION 12 - EXECUTION ORDER
  STEP-1 -> 2 -> 3 -> 4 -> 5 -> 6 (linear; each step golden-frozen before
  the next builds on it). Parallel: V1-0 (with 1-3); P3-debt R1/R2 (into 6).

SECTION 13 - DEFINITION OF DONE (PHASE-LEVEL)
  All 6 steps closed; all golden vectors frozen & passing; DB-P4-001..005
  live; computation worker scheduled; APIs serving; SLO measured; registry
  rows activated; G-4 verdict recorded in checkpoint.
=====================================================================================
END OF PHASE 4 ROADMAP v1.0-DRAFT
=====================================================================================
