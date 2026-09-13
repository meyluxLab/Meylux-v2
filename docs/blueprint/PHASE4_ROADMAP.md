# PHASE 4 ROADMAP — Deterministic Quantitative & Market Structure Engine

**Document type:** Blueprint / Execution Roadmap (planning input for formal Phase Establishment)
**Phase SID (proposed):** `PH-P4`
**Predecessor:** `PH-P3` — Validation, Normalization & Data Quality
**Successor:** `PH-P5` — Specialist Analytical Layer
**Architectural basis:** `DOC-V2-ARCH-001` (RATIFIED / FROZEN), §14 (PHASE P4), `INV-V2-002`, `INV-V2-009`, §15 (Venue Intelligence Track / `CMP-V2-VENUE-001`)
**Governance status:** این سند یک **Roadmap/Blueprint** است، نه یک `PH-P4.md` رسمی. هیچ Stable ID جدید، Task Order یا authorization اجرایی از طریق این سند صادر نمی‌شود. تبدیل این نقشه به Phase Definition رسمی و صدور Task Order باید از طریق فرآیند Governance موجود انجام شود.

---

## 1. مأموریت واقعی Phase 4

Phase 4 نباید صرفاً یک «Indicator Library» باشد. مأموریت واقعی آن:

> تبدیل داده Canonical و Quality-Aware دریافتی از Phase 3 به مجموعه‌ای از **Facts** کمّی، آماری و ساختاری که deterministic، reproducible، provenance-aware باشند و توسط تمام لایه‌های بعدی Meylux قابل استفاده باشند.

```text
P3 = این داده قابل اعتماد است؟
P4 = از این داده قابل‌اعتماد چه واقعیت‌های deterministic استخراج می‌شود؟
P5 = مجموعه این واقعیت‌ها چه چیزی دلالت دارد؟
P6 = سیستم intelligence باید چه نتیجه‌ای بگیرد؟
```

این تفکیک یکی از مهم‌ترین نقاط موفقیت معماری V2 است و نباید در اجرا نقض شود.

## 2. اصول غیرقابل‌مذاکره Phase 4

این چهار اصل ستون فقرات تمام Stepهای Phase 4 هستند:

| اصل | توضیح |
|---|---|
| **1. Determinism** (`INV-V2-002`) | همان ورودی باید همان خروجی را تولید کند؛ arithmetic/structure authoritative باید deterministic باشد |
| **2. Purity** | هسته محاسباتی نباید به network، database، filesystem، wall clock یا mutable global state وابسته باشد |
| **3. Zero NaN / Inf** | کمبود داده هرگز به `NaN`، `Inf` یا صفر مصنوعی تبدیل نمی‌شود؛ باید explicit باشد |
| **4. Golden Vector Freeze** | هر تابع عمومی ریاضی باید reference input/output داشته باشد و تغییر عددی آن تحت change control باشد |

## 3. Scope و Non-Scope

### در Scope
Technical Indicators، Statistical/Volatility Engine، Deterministic Market Structure، Volume Profile، Order Flow، Derivatives Analytics، Market Regime Classification، Quant Orchestration/Persistence/API/Replay.

### خارج از Scope (Hard Boundary)

| خارج از P4 | متعلق به |
|---|---|
| AI reasoning، LLM calls، specialist interpretation | P5 / P6 |
| Contradiction analysis، Scenario synthesis | P6 |
| Opportunity Score، Analytical Confidence synthesis | P6 |
| Final decision support، Trade signals as intelligence decisions | P6 و بعد از آن |
| Order execution، Portfolio management | خارج از scope کل پلتفرم (Read-only) |
| Venue Intelligence / Opportunity Engine کامل (فراتر از venue-aware evidence) | `CMP-V2-VENUE-001` — track مستقل cross-cutting، نه بخشی از P4 |

Phase 4 فقط **Fact Generation** است — این دقیقاً همان separation است که معماری V2 برای جلوگیری از واگذاری mathematical truth به AI ایجاد کرده است.

## 4. ساختار پیشنهادی Step — نمای کلی

بررسی مجدد نشان می‌دهد شش Step اصلی از نظر مرزهای معماری کاملاً مناسب هستند و نیازی به تجزیه بیشتر (که governance را سنگین می‌کند) یا ادغام بیشتر (که مرزهای حیاتی Mathematics / Indicators / Structure / Advanced Market Evidence / Regime / Operational Integration را از بین می‌برد) نیست. آنچه باید تغییر کند **عمق specification** هر Step است، نه تعداد آن‌ها.

| # | Step SID (proposed) | عنوان | محور اصلی |
|---|---|---|---|
| 1 | `STEP-P4-001` | Quantitative Foundation, Contracts, Numeric Policy & Golden Vector Freeze | قرارداد، precision، primitives، vectors، مدل پایه |
| 2 | `STEP-P4-002` | Technical Indicators, Statistical & Volatility Engine | MA، momentum، volatility، volume، VWAP |
| 3 | `STEP-P4-003` | Deterministic Market Structure Engine | Swings، BOS، CHOCH، MSS، FVG، OB، Breakers، Liquidity |
| 4 | `STEP-P4-004` | Volume Profile, Order Flow & Derivatives Engine | POC/VAH/VAL، HVN/LVN، Delta/CVD، Imbalance، Absorption، Funding/OI/Basis |
| 5 | `STEP-P4-005` | Deterministic Market Regime Engine & Venue-Aware Quantitative Evidence | Regime، hysteresis، multi-factor state، venue-aware evidence |
| 6 | `STEP-P4-006` | Quant Orchestration, Multi-Timeframe Runtime, Persistence, API, Replay & G-4 Closure | Worker، persistence، stream، API، replay، performance، regression، G-4 |

**وابستگی خطی حاکمیتی:**
```text
STEP-P4-001 → STEP-P4-002 → STEP-P4-003 → STEP-P4-004 → STEP-P4-005 → STEP-P4-006 → G-4 → PH-P5
```
این ترتیب governance dependency است، نه اینکه هر فایل باید کاملاً sequential ساخته شود: آماده‌سازی fixture، مستندسازی، و برخی unit testها می‌توانند موازی توسعه یابند؛ اما هیچ Step نباید روی contract یا رفتار تأییدنشده Step قبلی بنا شود.

---

## 5. STEP-P4-001 — Quantitative Foundation, Contracts, Numeric Policy & Golden Vector Freeze

**هدف:** ساخت «زمین بازی ریاضی» Phase 4. پیش از ساخت هر indicator، باید مشخص باشد: ورودی معتبر چیست، خروجی معتبر چیست، precision چگونه مدیریت می‌شود، insufficient history چگونه نمایش داده می‌شود، rounding چگونه انجام می‌شود، golden vector دقیقاً چه چیزی را freeze می‌کند، feature چگونه provenance خود را حفظ می‌کند، و خروجی چگونه version می‌شود.

### 5.1 Quantitative Contracts
حداقل contract domainها: **Indicator، Market Structure، Volume Profile، Order Flow، Regime**. Contract باید فقط type definition نباشد؛ باید semantics هر فیلد را نیز تثبیت کند: `value`، `status`، `reason`، `source_ref`، `timestamp`، `timeframe`، `symbol`، `venue/context`، `version`. هر فیلد فقط در صورت پشتیبانی قرارداد حاکم باید اضافه شود؛ در این مرحله SID جدید اختراع نمی‌شود.

### 5.2 Numeric Policy
یکی از مهم‌ترین نقاط کل Phase 4. سیاست پایه پیشنهادی: **Hybrid internals + Decimal boundary**، با Golden Vector به‌عنوان referee مقدار quantized. باید در formalization تعیین و ثبت شوند:
- نمایش عددی داخلی
- نمایش در مرز (boundary representation)
- precision
- rounding
- quantization
- comparison tolerance در جایی که مجاز است
- serialization

این بخش نباید implementation preference پنهان باشد.

### 5.3 Mathematical Primitives
پیش از indicatorها باید primitiveهای مشترک قابل اعتماد باشند: rolling calculations، averages، weighted calculations، smoothing، standard deviation، percentile/ranking، accumulation، normalization. این کار مانع از پیاده‌سازی متفاوت منطق پایه در هر indicator می‌شود.

### 5.4 Insufficient History
باید در foundation حل شود، نه در هر indicator جداگانه:
```text
NOT ENOUGH HISTORY → explicit status + reason + no numeric fabrication
```
سیاست پایه: `None + reason`، بدون fabrication عددی.

### 5.5 Golden Vector System
```text
Input fixture → Function → Expected output → Exact comparison → Regression protection
```
باید برای توابع ریاضی عمومی قابل توسعه باشد؛ حداقل مجموعه اولیه vector و runner برای این Step باید مشخص شود.

### 5.6 Golden Vector Freeze (Governance Boundary)
```text
تغییر ریاضی → ACR/change control → محاسبه reference جدید → بازبینی golden vector → تأیید
```
نه اینکه Producer صرفاً مقدار expected را برای سبز کردن تست تغییر دهد.

### 5.7 Database Model Foundation
مدل‌های persistence در این Step تعریف می‌شوند (بدون ورود به orchestration runtime، که در Step 6 است):

| DB SID | نام |
|---|---|
| `DB-P4-001` | `calculated_indicator_vectors` |
| `DB-P4-002` | `market_structure_events` |
| `DB-P4-003` | `market_structure_zones` |
| `DB-P4-004` | `volume_profile_sessions` |
| `DB-P4-005` | `market_regime_states` |

این آبجکت‌ها در معماری به‌عنوان authoritative outputs تعریف شده‌اند.

### 5.8 خروجی نهایی Step 1
Quantitative contracts + Numeric policy + Mathematical foundation + Golden vector infrastructure + Persistence model foundation + Deterministic output semantics. **در این مرحله هنوز pipeline کامل تولید indicator وجود ندارد.**

---

## 6. STEP-P4-002 — Technical Indicators, Statistical & Volatility Engine

**هدف:** تکمیل تمام quantitative features مبتنی بر price/time/volume.

| دسته | موارد |
|---|---|
| **Moving Averages** | EMA 9, EMA 21, EMA 50, EMA 200, SMA, WMA, HMA |
| **Momentum** | RSI 14, MACD 12/26/9 |
| **Trend / Volatility** | ATR 14, ADX 14, Bollinger Bands 20/2, Supertrend |
| **Volatility / Statistical** | Historical Volatility، محاسبات realized/related volatility، ATR percentile، ورودی‌های expansion/compression |
| **Volume / Activity** | Volume SMA, RVOL, volume spike, volume climax |
| **VWAP** | VWAP, Anchored VWAP (anchor باید ورودی صریح باشد؛ وابسته به clock پنهان سیستم نیست) |

### الزامات رفتاری برای هر Indicator
هر indicator باید موارد زیر را به‌صراحت تعریف کند:

- Warm-up behavior
- Missing input behavior
- Zero-volume behavior
- Invalid input behavior
- Length alignment
- Lookahead = صفر
- Reproducibility قطعی
- Golden vector موجود

### خروجی Step 2
```text
Canonical candles → Technical / Statistical Engine → IndicatorVector
```
هنوز وارد Market Structure یا AI interpretation نشده است.

---

## 7. STEP-P4-003 — Deterministic Market Structure Engine

**هدف:** حساس‌ترین Step محاسباتی Phase 4. برخلاف indicators که عمدتاً formula-driven هستند، market structure ابهام معنایی بیشتری دارد و به state-machine discipline جدی نیاز دارد.

### 7.1 Swing Detection
`HH / HL / LH / LL` با تشخیص fractal ۵/۵. **قاعده حیاتی:** تشخیص swing نباید باعث lookahead پنهان شود. اگر الگوریتم برای تأیید یک swing به کندل‌های آینده نیاز دارد، semantics آن باید صریحاً تعریف شود؛ یک swing تاریخی نباید طوری نمایش داده شود که گویی در همان لحظه قابل مشاهده بوده است. این مستقیماً به `INV-V2-009` (ZERO LOOKAHEAD) مرتبط است.

### 7.2 Structure State
```text
HH / HL / LH / LL → تفسیر Trend / Range (باید deterministic باشد)
```

### 7.3 BOS (Break of Structure)
باید دقیقاً مشخص شود: کدام level شکسته شده، close یا wick، چه timestampی رویداد محسوب می‌شود، جلوگیری از duplicate event، و نحوه invalidation.

### 7.4 CHOCH
همان discipline رفتاری BOS.

### 7.5 MSS (Market Structure Shift)
باید با state machine مشخص تعریف شود.

### 7.6 Total State Machine
هر bar باید یک state مشخص داشته باشد؛ ابهام نباید با حدس حل شود. در صورت ابهام:
```text
state = UNCONFIRMED
```
این یکی از تصمیمات کلیدی است که باید حفظ شود.

### 7.7 Fair Value Gap
Lifecycle: `ACTIVE → PARTIALLY_MITIGATED → FULLY_MITIGATED`، با transitionهای deterministic.

### 7.8 Order Blocks
Detection، lifecycle، invalidation، breaker transition.

### 7.9 Breakers
باید نتیجه deterministic transition از structure/zone state باشد، نه interpretation AI.

### 7.10 Liquidity Pools
باید به‌عنوان structural facts ثبت شوند، نه opportunity signals.

### 7.11 آزمون الزامی Step 3
دو سناریوی pinned:
```text
60-candle trend-with-BOS
60-candle reversal-with-CHOCH
```
که باید event-by-event بازتولید شوند. این نوع scenario test باید به یک اصل عمومی برای تمام stateful structure logic تبدیل شود:
```text
input scenario → every event → every state transition → exact expected result
```
این برای جلوگیری از «خروجی نهایی درست، اما مسیر غلط» حیاتی است.

---

## 8. STEP-P4-004 — Volume Profile, Order Flow & Derivatives Engine

**هدف:** سه engine مستقل ولی یک Step governed.

```text
STEP-P4-004
├── Volume Profile
├── Order Flow
└── Derivatives
```

### 8.A Volume Profile
معماری تأکید می‌کند Phase 4 مالک انحصاری ریاضیات Volume Profile است؛ این محاسبات نباید بعداً در P5/P6 تکرار شوند.

محاسبات: POC، VAH، VAL، HVN، LVN، session profile، composite profile (در صورت وجود در contract).

**Value Area:** باید **۷۰٪** value area دقیقاً freeze شود؛ الگوریتم انتخاب bins، expansion و tie-breaking باید deterministic باشد. الزام تست: golden test برای یک session با ۲۰۰ trade با POC/VAH/VAL دقیق.

### 8.B Order Flow
حداقل: Bar Delta، CVD، Imbalance، Absorption.

- **CVD** باید deterministic، monotonicity-aware و replay-safe باشد؛ نیازمند pinned trade set و property test.
- **Imbalance:** threshold باید configuration-driven و governed باشد، نه انتخاب سلیقه‌ای Producer.
- **Absorption:** باید دقیقاً مشخص شود «absorption» یعنی چه و چه داده‌ای لازم است. اگر داده سطح trade کافی نیست: `UNAVAILABLE / LIMITED_DATA`، نه fabrication.

### 8.C Derivatives
funding، funding velocity/acceleration، Open Interest، OI delta، Basis؛ رابطه mark/index. **قاعده حیاتی:** Phase 4 نباید داده derivatives را در نبود ورودی canonical آن، invent یا reconstruct کند.

### خروجی Step 4
سه خانواده مستقل evidence: Volume Evidence، Order Flow Evidence، Derivatives Evidence — که بعداً در P5 با سایر evidenceها ترکیب می‌شوند.

---

## 9. STEP-P4-005 — Deterministic Market Regime Engine & Venue-Aware Quantitative Evidence

### 9.A بخش Market Regime
باید deterministic باشد. هشت state:
```text
TRENDING · RANGING · EXPANSION · COMPRESSION
HIGH_VOL · LOW_VOL · TRANSITION · ABNORMAL
```
عوامل ورودی: `EMA 50/200`، `ATR percentile`، `BB width`، `structure bias`.

**Hysteresis (الزامی):** بدون hysteresis، دنباله `A B A B A` با کوچک‌ترین نوسان رخ می‌دهد. باید:
```text
candidate state → confirmation → official state
```
به‌صورت deterministic اعمال شود؛ حالت transient candidate باید قابل اثبات باشد (پوشش golden vector برای hysteresis گذرا).

**Regime ≠ Forecast:** Regime Engine نمی‌گوید «بازار بالا خواهد رفت»؛ می‌گوید «بر اساس قوانین مصوب، وضعیت فعلی بازار در این state قرار دارد». این تفکیک برای P5 و P6 حیاتی است.

### 9.B بخش Cross-Venue — تفکیک حیاتی از ACR-0008
باید بین دو مفهوم فرق گذاشت:

| مفهوم | جایگاه |
|---|---|
| **Venue-Aware Quantitative Evidence** | بخشی از `STEP-P4-005`؛ صرفاً evidence comparison بین venue |
| **Venue Intelligence / Opportunity Engine** | موضوع `CMP-V2-VENUE-001` (ACR-0008)؛ **track مستقل، cross-cutting به‌عنوان rider روی P2/P3/P4/P5/P6/P9** — نه بخشی از PH-P4 |

```text
STEP-P4-005 = venue-aware quantitative evidence
             NOT
             full arbitrage / opportunity engine
```
این تفکیک مانع scope creep می‌شود. طبق معماری (§15)، Venue Intelligence Track دارای state model مستقل (`S0 OBSERVED_SPREAD` تا `S8 NO_OPPORTUNITY`) است و نباید در P4 ادغام شود.

---

## 10. STEP-P4-006 — Quant Orchestration, Multi-Timeframe Runtime, Persistence, API, Replay & G-4 Closure

این Step صرفاً `Persistence + Worker + API` نیست؛ محل **اثبات operational integrity** کل Phase 4 است.

### 10.A Quant Engine Facade
تمام engineهای Stepهای ۲ تا ۵ باید از یک execution boundary قابل کنترل استفاده کنند:
```text
Canonical Input → Quant Engine Facade → (Technical, Structure, VP, Order Flow, Derivatives, Regime) → Quantitative Evidence
```
این facade نباید خودش منطق جدید ریاضی ایجاد کند.

### 10.B Candle-Close Trigger
فقط رکوردهای `is_closed = True` وارد محاسبات authoritative می‌شوند. این باید هم unit test، هم integration test، هم runtime test داشته باشد.

### 10.C Multi-Timeframe
Engine capability: `1M / 5M / 15M / 1H / 4H / 1D`. **Controlled Vertical Slice** پذیرشی: `BTCUSDT — 15M primary + 1H + 4H`. این دو (قابلیت engine در برابر slice پذیرش) نباید با هم اشتباه شوند.

### 10.D Persistence
پنج object authoritative Step 1 باید operationally وصل شوند و provenance، identity، idempotency، timestamp، symbol/timeframe context، و source linkage را حفظ کنند.

### 10.E Append-Only Boundary
برای canonical/quantitative truth authoritative: `UPDATE/DELETE` برای application role مجاز نیست (revoke شده).

### 10.F Redis Boundary
```text
PostgreSQL / TimescaleDB = authoritative persistence
Redis                    = queue / stream / coordination / cache
```
Redis هرگز نباید durable truth شود؛ این تفکیک باید در verification این Step آزمایش شود.

### 10.G Worker
```text
canonical closed candle event → quant computation → persistence → feature event
```
Queue/stream مرتبط: `stream:canonical:market_events`، `arq:queue:quant_heavy`، `stream:features:computed`. Worker باید مصرف‌کننده رویداد candle-close باشد.

### 10.H API
باید read-only، DB-backed، provenance-aware و صرفاً quantitative باشد. حداقل خانواده endpoint: `quant features`، `quant structure`.

### 10.I Replay
Purity Phase 4 عملاً برای Replay آینده (P9) ساخته می‌شود:
```text
Historical Input → P4 → Output A
same Historical Input → P4 → Output B
A == B
```
بدون وابستگی به wall clock، network، database state، mutable global state یا nondeterministic ordering.

### 10.J Zero Lookahead Harness
Replay باید ثابت کند که زمان `T` به `T+1, T+2, ...` دسترسی ندارد — برای indicators، swing detection، BOS، CHOCH، MSS، FVG و regime حیاتی است. `INV-V2-009` صراحتاً historical evaluation از future information را منع می‌کند.

### 10.K Performance
Targetهای پیشنهادی (باید با evidence اندازه‌گیری شوند، نه ادعا):
```text
< 5ms  / indicator / 1000 bars
< 50ms / full multi-timeframe vector
```
```text
TARGET ≠ GUARANTEE   (تا زمانی که evidence واقعی تولید نشده)
```

### 10.L Failure Testing
حداقل سناریوهای الزامی: short history، zero volume، unsorted input، missing data، invalid values، duplicate input، boundary values، large values، tiny values. استراتژی تست: `unit + golden + property + replay + failure + regression`.

### 10.M Security Boundary
Quant computation باید: zero network egress، zero subprocess، no dynamic imports، no secrets — با پوشش trade-probe روی `meylux/quant/**`. این الزام برای پلتفرمی که باید strictly read-only باشد بسیار حیاتی است.

### 10.N معیار G-4
G-4 صرفاً «تست‌های واحد سبز» نیست. طبق معماری، گذار P4→P5 نیازمند math test suite کامل و صفر انحراف از math benchmarks است. مجموعه evidence الزامی پیشنهادی:
```text
100% math suite
0 deviation
0 NaN/Inf
measured performance
1-day BTCUSDT 15M replay
zero-lookahead
persistence
API
full regression
evidence bundle
```
عدد دقیق regression count باید به‌عنوان evidence واقعی هنگام اجرا ثبت شود، نه اینکه از پیش در roadmap تضمین گردد.

---

## 11. جدول Traceability — از Capability به Step

| Capability | Step |
|---|---|
| Quant contracts، Numeric policy، Mathematical primitives، Golden vectors، DB model foundation | 1 |
| Moving averages، Momentum، ATR/ADX، Bollinger، Supertrend، HV/volatility، RVOL/volume activity، VWAP/Anchored VWAP | 2 |
| Swing points، HH/HL/LH/LL، BOS، CHOCH، MSS، FVG، Order Blocks، Breakers، Liquidity Pools | 3 |
| POC، VAH/VAL، HVN/LVN، Delta، CVD، Imbalance، Absorption، Funding analytics، OI analytics، Basis | 4 |
| Regime classifier، Hysteresis، Regime provenance، Venue-aware quantitative evidence | 5 |
| Quant facade، Candle-close execution، Multi-timeframe worker، Persistence، Redis event boundary، Read-only API، Replay، Zero-lookahead harness، Performance measurement، Regression، G-4 evidence | 6 |

---

## 12. Definition of Done — شش دسته

1. **Mathematical Integrity** — فرمول‌ها صحیح؛ golden vectors pinned؛ regression protected؛ numeric policy مشخص؛ بدون silent math drift.
2. **Data Integrity** — ورودی فقط canonical؛ provenance حفظ‌شده؛ insufficient data صریح؛ بدون fabrication؛ بدون NaN/Inf.
3. **Temporal Integrity** — semantics candle-close؛ zero lookahead؛ replay deterministic؛ صحت زمانی.
4. **Structural Integrity** — state machineهای کامل؛ `UNCONFIRMED` صریح؛ lifecycle deterministic؛ بازتولیدپذیری رویداد-به-رویداد.
5. **Operational Integrity** — persistence؛ worker؛ queueها؛ API؛ idempotency؛ مرز read-only؛ ایزوله‌سازی خطا.
6. **Evidence Integrity** — unit، golden، property، failure، replay، regression، performance، real-data vertical slice، evidence bundle G-4.

## 13. الزام Vertical Slice

مسیر Controlled Vertical Slice نهایی معماری:
```text
Binance Futures BTCUSDT — 15M primary / 1H / 4H
P2 Ingestion → P3 Normalization → P4 Quantitative/Structure → P5 Specialists → P6 AI → P8 Presentation
```
Phase 4 باید پیش از بستن خود اثبات کند که همین engine روی داده واقعی کار می‌کند، نه فقط روی fixtureهای مصنوعی. تفاوت بین «یک کتابخانه ریاضی خوب» و «Quantitative Engine واقعی Meylux» دقیقاً همین‌جاست.

---

## 14. نکات تکمیلی — شکاف‌های اجرایی که باید صریح شوند

بازبینی مجدد این Roadmap سه نقطه را شناسایی کرد که باید پیش از تبدیل به Phase Definition رسمی، به یکی از Stepهای مربوطه ضمیمه شوند.

### 14.1 رفتار Market Structure Engine در برابر Gap‌های Quarantine‌شده (مرتبط با `STEP-P4-003`)

اگر یک یا چند کندل در `Phase 3` به دلیل نقض validation، quarantine شده باشند، ورودی `STEP-P4-003` (Swing/BOS/CHOCH/MSS/FVG) با یک **gap واقعی در داده canonical** مواجه می‌شود — نه صرفاً یک کندل معمولی. رفتار دقیق در این حالت باید صریح باشد؛ در حال حاضر مشخص نیست:

```text
گزینه A — Explicit Gap Halt:
  Gap شناسایی شده → state engine برای بازه مربوطه = UNCONFIRMED (نه محاسبه با فرض تداوم)
  → با بازگشت داده معتبر، engine از سر گرفته می‌شود، بدون آنکه گذشته را بازنویسی (backfill silent) کند

گزینه B — Explicit Gap Skip با Provenance:
  Gap شناسایی شده → آن بازه به‌طور کامل از محاسبه ساختار حذف می‌شود
  → رویداد ساختاری بعدی، gap را در provenance خودش (source_ref/lineage) صریحاً ثبت می‌کند
```

**پیشنهاد:** گزینه A با اصل `UNCONFIRMED` که خود `STEP-P4-003` (بخش ۷.۶) از قبل برای ابهام state تعریف کرده هم‌راستاتر است — یعنی همان مکانیزم موجود Total State Machine برای این حالت هم استفاده شود، بدون معرفی حالت جدید. این باید به‌عنوان یک بند صریح («Behavior under Canonical Data Gaps») در `STEP-P4-003` اضافه و با یک Golden Vector اختصاصی (سناریوی gap در وسط دنباله BOS) پوشش داده شود — مشابه دو سناریوی pinned موجود در بخش ۷.۱۱.

این نکته به `STEP-P4-002` (Indicators) نیز به‌طور محدودتر مرتبط است: رفتار indicatorهای rolling (مثل EMA/ATR) در برابر gap باید طبق همان الزام «Missing input behavior» بخش ۶ صریح باشد؛ اما دامنه اصلی تصمیم در `STEP-P4-003` است چون structure engine به تداوم توالی حساس‌تر است.

### 14.2 Schema / Contract Versioning برای Quantitative Contracts (مرتبط با `STEP-P4-001`)

مشابه نکته معادل در Phase 3، `STEP-P4-001` صرفاً **freeze** اولیه Quantitative Contracts (`Indicator`, `Market Structure`, `Volume Profile`, `Order Flow`, `Regime`) و Golden Vectorها را پوشش می‌دهد. مسیر تکامل بعدی این contracts صریح نیست. پیشنهاد الحاق به `STEP-P4-001`:

```text
تغییر Quantitative Contract یا فرمول مرجع:
  Additive field غیرشکننده        →  version bump جزئی، بدون invalidation golden vectors موجود
  تغییر در فرمول/منطق محاسباتی      →  الزاماً از مسیر Golden Vector Freeze (بخش ۵.۶) عبور می‌کند
                                       (ACR/change control → محاسبه reference جدید → بازبینی → تأیید)
  Breaking change در ساختار خروجی  →  Contract SID جدید یا versioned schema + قاعده migration دیتای persist‌شده
                                       (`DB-P4-001` تا `DB-P4-005`)
```

این بند صرفاً تصریح چیزی است که بخش ۵.۶ (Golden Vector Freeze) از قبل به‌صورت ضمنی الزام کرده؛ افزودن آن جلوی این برداشت اشتباه را می‌گیرد که «freeze» یعنی «هرگز تغییر نمی‌کند» به‌جای «تغییر فقط از مسیر governed ممکن است».

### 14.3 مقیاس چندنمادی/چندبازاری (مرتبط با معیار G-4)

معیار G-4 فعلی (بخش ۱۰.N) صرفاً حول یک Vertical Slice تک‌نمادی (`BTCUSDT`) تعریف شده است. پیشنهاد می‌شود بند زیر به الزامات G-4 اضافه شود:

> G-4 علاوه بر اثبات Vertical Slice تک‌نمادی روی `15M/1H/4H`، باید حداقل یک شاهد replay روی **یک نماد دوم با پروفایل نوسان/حجم متفاوت** ارائه دهد تا اطمینان حاصل شود Golden Vectorها و منطق determinism به‌صورت implicit برای یک نماد خاص tune نشده‌اند. این شاهد صرفاً یک non-regression check است و به‌معنای گسترش رسمی scope Phase 4 به پشتیبانی کامل چند-نماد/چند-بازار نیست؛ آن گسترش موضوع فازهای بعدی و تصمیم جداگانه Owner است.

---

## 15. یادداشت حاکمیتی

ساختار ۶ Step این سند به‌عنوان **Final Proposed Execution Structure** پیشنهاد می‌شود — نه یک Phase Definition رسمی، نه Registry entry، و نه authorization اجرایی. Stable IDهای `STEP-P4-*` در این سند **پیشنهادی** هستند.

مرحله بعدی governance:

1. تبدیل این ساختار به `docs/phases/PH-P4.md` رسمی، با همان قالب `PH-P0.md`/`PH-P1.md`/`PH-P2.md`.
2. ثبت Stable IDهای `STEP-P4-001` تا `STEP-P4-006` در Registry.
3. تعریف Acceptance Criteria مستقل برای هر Step.
4. تثبیت رسمی تفکیک `STEP-P4-005` (venue-aware evidence) از `CMP-V2-VENUE-001` (Venue Intelligence Track، ACR-0008) در سطح Registry/ADR تا از خلط این دو در اجرا جلوگیری شود.
5. صدور Task Order رسمی برای اولین Step فقط پس از تصویب Owner **و** پس از تکمیل و بستن رسمی Phase 3.

تا پیش از انجام این مراحل، طبق `docs/state/CURRENT_CHECKPOINT.json`، **هیچ اجرای Phase 3 یا Phase 4 مجاز نیست.**
