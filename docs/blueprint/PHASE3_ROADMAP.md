هدف P3 باید دقیقاً جلوگیری از همین مشکل باشد.

### خروجی

یک **Canonical Data Boundary Definition** که تمام P3 بر اساس آن کار کند.

---

# STEP-P3-002

## Structural, Schema & Identity Validation

حالا باید بررسی کنیم که داده‌ی ورودی از نظر ساختاری اصلاً قابل پذیرش هست یا نه.

### Validation

* required fields
* field types
* nullability
* enum values
* schema compliance
* malformed payloads
* symbol syntax
* timeframe validity
* venue identity
* market type
* contract type
* basic deterministic identity
* duplicate identity candidates

مثلاً:

```text
price = "ABC"
```

یا:

```text
timestamp = null
```

یا:

```text
unknown market_type
```

نباید وارد canonical analytical data شوند.

### اصل مهم

این Step **اصلاح‌کننده خاموش داده نیست**.

یعنی:

```text
Bad Data
   ↓
Detect
   ↓
Classify
   ↓
Route
```

نه:

```text
Bad Data
   ↓
Guess
   ↓
Silently Fix
```

این اصل برای هدف نهایی Meylux حیاتی است.

---

# STEP-P3-003

## Temporal, Sequence & Completeness Validation

این Step باید مستقل باشد، چون زمان در market intelligence یک مفهوم بنیادی است.

### مسئولیت‌ها

#### Timestamp

* valid timestamp
* timezone semantics
* event timestamp
* receive timestamp
* future timestamp
* clock skew

معماری موجود برای P3 مقدار `5000ms` را به‌عنوان clock-skew configuration parameter در نظر گرفته است؛ این مقدار باید به‌عنوان config مورد governed validation قرار گیرد، نه یک عدد hard-coded و غیرقابل تغییر.

#### Ordering

* monotonicity
* out-of-order events
* duplicate timestamps
* sequence consistency

#### Candle continuity

* interval continuity
* missing candles
* unexpected gaps
* incomplete sequence

#### Event sequence

در مواردی که source sequence دارد:

```text
n
n+1
n+2
```

نباید:

```text
n
n+2
```

به‌عنوان sequence سالم تلقی شود.

### خروجی

هر داده باید بتواند به‌طور explicit یکی از وضعیت‌های:

```text
valid
gap
out-of-order
duplicate
stale
incomplete
```

را داشته باشد.

این موضوع مستقیماً با `Semantic & Monotonicity Validator` موجود در معماری P3 منطبق است.

---

# STEP-P3-004

## Market Semantic, Price, Spread & Precision Validation

این Step قلب **market-data correctness** در P3 است.

Schema درست به‌تنهایی کافی نیست.

ممکن است تمام فیلدها datatype صحیح داشته باشند ولی معنای بازار اشتباه باشد.

### OHLC

باید روابط منطقی بازار بررسی شوند:

```text
high >= open
high >= close
high >= low

low <= open
low <= close
low <= high
```

و موارد غیرممکن detect شوند.

### Price

* negative price
* impossible price
* invalid zero where semantically impossible
* malformed numeric values

### Quantity

* negative quantity
* invalid quantity
* impossible quantity semantics

### Volume

* negative volume
* invalid volume
* semantic inconsistency

### Spread

* bid/ask sanity
* negative spread
* impossible spread
* excessive spread

Architecture برای P3 صراحتاً `Price & Spread Integrity Validator` را تعریف کرده و حتی `Max allowable price spread: 5.0%` را به‌عنوان configuration parameter مشخص کرده است.

### Precision

* tick size
* lot size
* instrument precision
* quantity precision
* price precision
* rounding policy
* invalid precision

این بخش نیز صراحتاً با `Tick & Lot Size Precision Validator` منطبق است.

### نکته بسیار مهم

P3 نباید price را «به زور» قابل‌قبول کند.

اگر مقدار با instrument rules سازگار نیست:

```text
Reject / Quarantine / Quality Degradation
```

باید اتفاق بیفتد، نه silent rounding مگر اینکه **قانون rounding خودش به‌صورت صریح و governed تعریف شده باشد.**

---

# STEP-P3-005

## Canonical Normalization & Provider Mapping

حالا داده‌ای که از validationهای لازم عبور کرده، باید به زبان مشترک Meylux تبدیل شود.

### وظایف

```text
Binance
   ↓
Provider Representation
   ↓
Canonical Mapping
```

و:

```text
MEXC
   ↓
Provider Representation
   ↓
Canonical Mapping
```

### Mapping areas

* instrument
* candle
* trade
* order book
* derivatives
* venue
* market type
* contract type
* timeframe
* timestamp
* price
* quantity
* volume
* side semantics
* provenance

Architecture صراحتاً `Canonical Mappers for Binance & MEXC` را به‌عنوان requirement P3 تعریف کرده است.

و source تفصیلی حتی mapperهای زیر را مشخص کرده:

* `ART-P3-013` — Binance to Canonical Transformer
* `ART-P3-014` — MEXC to Canonical Transformer.

### اصل بسیار مهم

Provider-specific wire format نباید وارد Domain Canonical شود.

V2 صراحتاً مقرر کرده provider-specific aliases، event IDs، sequence details و wire-format fields در provider boundary باقی بمانند مگر اینکه domain requirement مشخصی آن‌ها را semantic کند.

---

# STEP-P3-006

## Cross-Venue Consistency & Equivalence

این Step را عمداً مستقل کرده‌ام.

در پروژه‌ای که Binance و MEXC هر دو **first-class providers** هستند، Cross-Venue فقط یک جزئیات کوچک Validator نیست.

بلکه پایه مهمی برای Market Intelligence آینده است.

### باید بررسی شود:

#### Identity

```text
same base asset?
same quote asset?
same symbol meaning?
```

#### Market type

```text
Spot ≠ Futures
```

#### Contract type

```text
Perpetual ≠ Delivery
```

#### Unit semantics

واحد volume یا quantity در دو provider نباید بدون اثبات معادل فرض شود.

#### Timestamp alignment

داده دو venue باید از نظر زمانی قابل مقایسه باشد.

#### Freshness

مقایسه:

```text
fresh Binance
vs
stale MEXC
```

نباید به‌عنوان divergence معتبر تلقی شود.

#### Bid/Ask sanity

هر دو سمت باید از نظر market integrity معتبر باشند.

#### Impossible values

اختلاف ناشی از corruption نباید به‌عنوان market dislocation ثبت شود.

Architecture V2 دقیقاً یک **Cross-Venue Rider** برای این موضوع تعریف کرده و instrument identity، base/quote، market type، contract type، unit semantics، timestamp، freshness و bid/ask sanity را mandatory می‌داند. همچنین می‌گوید mapping نامطمئن هرگز نباید silently فعال شود.

### اهمیت برای آینده

این Step مستقیماً به قابلیت‌های آینده:

```text
Cross-Exchange Analyst
Venue Intelligence
Opportunity Analysis
```

کمک می‌کند.

اما خودش **نباید وارد تحلیل فرصت یا arbitrage شود**.

---

# STEP-P3-007

## Data Quality, Quarantine, DLQ & Lineage

این Step را می‌توان قلب «اعتمادپذیری» Meylux دانست.

Validation فقط نباید بگوید:

```text
PASS / FAIL
```

بلکه باید مشخص کند **کیفیت داده برای مصرف‌کننده بعدی چقدر و چرا قابل اعتماد است.**

---

## Data Quality

معماری P3 خروجی:

```text
Data Quality Score: 0.00 – 1.00
```

با:

```text
Explanation Vector
```

را تعریف کرده است.

مولفه‌های اصلی:

* freshness
* completeness
* consistency
* feed health
* validation status
* provider capability

---

## Stateهای کیفیت

باید حداقل وضعیت‌های معماری حفظ شوند:

```text
VALID
DEGRADED
STALE
INCOMPLETE
CONTRADICTORY
REJECTED
UNAVAILABLE
```

اینها در Master Architecture V2 صراحتاً تعریف شده‌اند.

و در سطح data-flow نیز stateهای:

```text
RAW
STAGED
VALIDATING
NORMALIZED
CANONICAL
QUALITY_DEGRADED
REJECTED
QUARANTINED
EXPIRED
ARCHIVED
```

وجود دارند.

---

# Quarantine / DLQ

اگر داده خراب باشد:

```text
Invalid
   ↓
Quarantine / DLQ
```

نه:

```text
Invalid
   ↓
Delete
```

و نه:

```text
Invalid
   ↓
Canonical
```

Architecture صراحتاً `normalization_dlq` را برای داده corrupt تعریف کرده و الزام کرده که این جداسازی بدون crash کردن worker انجام شود.

---

# Lineage

برای هر canonical record باید بتوانیم مسیر را دنبال کنیم:

```text
Provider
   ↓
Raw/Staging record
   ↓
Validation result
   ↓
Normalization
   ↓
Quality result
   ↓
Canonical record
```

این موضوع برای:

* debugging
* replay
* audit
* future evaluation
* AI evidence provenance

بسیار مهم است.

---

# STEP-P3-008

## Authoritative Persistence, Event Handoff & G-3 Verification

این Step باید Phase را به شکل واقعی به Phase 4 تحویل دهد.

### Canonical persistence

Architecture شش object اصلی P3 را مشخص می‌کند:

```text
DB-P3-001 canonical_instruments
DB-P3-002 canonical_candles
DB-P3-003 canonical_trades
DB-P3-004 canonical_orderbook_depth
DB-P3-005 canonical_derivatives
DB-P3-006 data_quality_logs
```

این‌ها باید **authoritative boundary** شوند.

### Append-only

Canonical tables باید append-only باشند و برای application، UPDATE/DELETE privilege نداشته باشند. این الزام در architecture صریح است.

---

## Normalized Event Stream

P3 فقط database writer نیست.

باید downstream event handoff نیز داشته باشد:

```text
Canonical Data
      ↓
stream:canonical:market_events
      ↓
Phase 4
```

این queue/stream نیز در source architecture مشخص شده است.

---

## Workers

معماری این دو worker را تعریف کرده:

```text
WRK-P3-001 normalization-stream-worker

WRK-P3-002 data-quality-auditor
```

---

## Quality API

برای مشاهده وضعیت کیفیت:

```text
GET /api/v1/quality/{exchange}/{symbol}

GET /api/v1/quality/summary
```

نیز در architecture آمده است.

این APIها را باید در همین Step یا در مرز integration آن قرار داد، چون بخشی از **observable data-quality boundary** هستند، نه UI نهایی.

---

# G-3 — مهم‌ترین بخش Step 8

Phase 3 زمانی تمام نشده که:

```text
tests pass
```

تنها.

باید ثابت شود:

```text
P2 staging
      ↓
Validation
      ↓
Normalization
      ↓
Quality
      ↓
Quarantine
      ↓
Canonical persistence
      ↓
Canonical event stream
      ↓
P4-ready data
```

به‌صورت end-to-end کار می‌کند.

Gate رسمی:

```text
G-3
Phase 3 → Phase 4
```

و معیار architecture:

```text
Normalization pipeline pass
100% canonical schema pass
DLQ active
```

است.

---

# حالا مهم‌ترین قسمت: چه چیزهایی در P3 نباید باشند؟

برای اینکه Phase 3 بیشترین بازده را داشته باشد، Scope آن باید **به‌شدت محافظت شود**.

## P3 نباید انجام دهد:

### ❌ Technical Indicators

مثل:

```text
EMA
RSI
MACD
ATR
ADX
Bollinger
```

اینها P4 هستند.

### ❌ Market Structure

```text
BOS
CHOCH
MSS
FVG
Order Blocks
Liquidity Pools
```

P4.

### ❌ Volume Profile

P4.

### ❌ Order Flow Analytics

P4.

### ❌ Regime Classification

P4.

### ❌ Specialist Intelligence

P5.

### ❌ AI Interpretation

P6.

### ❌ Opportunity Score

P6.

### ❌ Trade Idea Generation

صراحتاً non-goal است.

### ❌ Natural Language Summary

P3 نباید وارد این حوزه شود.

### ❌ Arbitrage / Opportunity Analysis

Cross-venue validation بله؛ opportunity detection خیر.

---

# رابطه دقیق P2 → P3 → P4

این سه Phase باید مثل یک زنجیره کاملاً تمیز باشند:

```text
              PHASE 2
       "Can we acquire it?"
               │
               ▼
        Raw / Staging Data
               │
               ▼
              PHASE 3
        "Can we trust it?"
               │
       ┌───────┴────────┐
       │                │
    Valid            Invalid
       │                │
       ▼                ▼
 Normalize          Quarantine
       │
       ▼
 Canonical
 + Quality
 + Provenance
       │
       ▼
              PHASE 4
        "What does the data
          mathematically say?"
```

این تفکیک برای کل موفقیت Meylux بسیار مهم است.

Phase 2 مالک **Acquisition** است.

Phase 3 مالک **Trust / Canonicalization / Quality** است.

Phase 4 مالک **Mathematical Truth / Structure** است.

---

# یک اصلاح مهم نسبت به نقشه ۶-Step قبلی

من با بررسی مجدد sourceها، یک تغییر مهم نسبت به پیشنهاد قبلی CONTROL می‌دهم.

در نقشه ۶-Step قبلی:

> `Canonical Normalization & Decimal Boundary`

به‌صورت یک Step واحد آمده بود.

اما برای Meylux، این کافی نیست.

چون معماری موجود **چهار خانواده‌ی validation مشخص** دارد:

* Semantic & Monotonicity
* Price & Spread Integrity
* Tick & Lot Precision
* Cross-Venue Consistency

و همچنین mapperهای Binance/MEXC و Quality Engine جدا هستند.

اگر همه را در ۶ Step فشرده کنیم، Stepها بیش از حد سنگین می‌شوند و مرز verification مبهم خواهد شد.

از طرف دیگر، ۱۴ Step اولیه نیز هر validation کوچک را تبدیل به یک execution Step می‌کرد که برای governance پروژه بیش از حد خرد است.

بنابراین **۸ Step نقطه تعادل بهتری است.**

---

# Mapping کامل ۱۴ capability قبلی به ۸ Step نهایی

| Capability استخراج‌شده       | Step نهایی               |
| ---------------------------- | ------------------------ |
| Schema / Contract Validation | P3-001 / P3-002          |
| Semantic Validation          | P3-003 / P3-004          |
| Temporal Validation          | P3-003                   |
| Sequence Validation          | P3-003                   |
| Price / Quantity Integrity   | P3-004                   |
| Precision                    | P3-004                   |
| Duplicate / Identity         | P3-001 / P3-002 / P3-003 |
| Missing / Stale / Incomplete | P3-003 / P3-007          |
| Canonical Mapping            | P3-005                   |
| Cross-Venue Consistency      | P3-006                   |
| Data Quality Scoring         | P3-007                   |
| Quarantine / DLQ             | P3-007                   |
| Canonical Persistence        | P3-008                   |
| Normalized Event Stream      | P3-008                   |
| G-3 Verification             | P3-008                   |

در نتیجه **هیچ capability مهمی از roadmap قبلی حذف نشده است.**

فقط به execution boundaries منطقی‌تر منتقل شده است.

---

# تمام اجزای P3 در یک نقشه واحد

```text
                         PH-P2
                    RAW / STAGING
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-001                 │
              │ Contracts / Identity   │
              │ Validation Foundation  │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-002                 │
              │ Schema / Structural    │
              │ Validation             │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-003                 │
              │ Temporal / Sequence    │
              │ Completeness           │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-004                 │
              │ Semantic / Price /     │
              │ Spread / Precision     │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-005                 │
              │ Canonical Normalization│
              │ Binance + MEXC         │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ P3-006                 │
              │ Cross-Venue Consistency│
              └────────────┬───────────┘
                           │
                           ▼
                  ┌────────┴────────┐
                  │                 │
                VALID           INVALID/DEGRADED
                  │                 │
                  ▼                 ▼
             P3-007 QUALITY    QUARANTINE / DLQ
                  │                 │
                  ├────────┬────────┘
                  │        │
                  ▼        ▼
             Score +     Lineage
             Explanation
                  │
                  ▼
              P3-008
       Authoritative Persistence
          + Event Handoff
          + API/Observability
          + E2E Verification
                  │
                  ▼
                 G-3
                  │
                  ▼
                 PH-P4
```

---

# معیار خروج نهایی Phase 3

به نظر من این قسمت باید حتی از Stepها مهم‌تر باشد.

P3 نباید با «کد نوشته شد» تمام شود.

باید بتوانیم در پایان بگوییم:

### 1. Contract Integrity

Canonical contracts مشخص، versioned و verified هستند.

### 2. Structural Integrity

داده malformed وارد canonical نمی‌شود.

### 3. Temporal Integrity

timestamp/sequence/gap semantics اثبات شده‌اند.

### 4. Market Integrity

OHLC، price، quantity، volume، spread و precision کنترل می‌شوند.

### 5. Provider Mapping

Binance و MEXC هر دو به یک canonical semantic representation می‌رسند.

### 6. Cross-Venue Integrity

مقایسه venueها فقط وقتی انجام می‌شود که semantic equivalence ثابت شده باشد.

### 7. Quality Awareness

هر downstream consumer می‌تواند بفهمد:

```text
fresh?
complete?
degraded?
stale?
contradictory?
unavailable?
unsupported?
```

### 8. No Fabrication

هیچ داده‌ی missing یا invalid با مقدار ساختگی پر نمی‌شود.

### 9. Quarantine

داده خراب isolated می‌شود و canonical را آلوده نمی‌کند.

### 10. Lineage

canonical record به source و validation history قابل trace است.

### 11. Authoritative Persistence

canonical tables مرجع authoritative می‌شوند و append-only باقی می‌مانند.

### 12. Event Handoff

Phase 4 می‌تواند canonical events را دریافت کند.

### 13. Real-Time Quality

Quality scoring فقط batch تاریخی نیست؛ باید در operational flow فعال باشد.

### 14. Replay / Determinism

ورودی یکسان، normalization و validation قابل تکرار تولید کند.

### 15. Performance

معماری موجود برای batch normalization هدف `>5,000 events/sec per core` را مشخص کرده است. این باید به‌عنوان performance target ارزیابی شود، نه اینکه بدون evidence «achieved» فرض شود.

### 16. G-3

در نهایت:

```text
100% staging → canonical processing
DLQ active
zero canonical corruption
real-time quality scoring
```

باید با evidence واقعی اثبات شود.

---

# یک نکته بسیار مهم درباره Vertical Slice

P3 نباید صرفاً با چند fixture مصنوعی بسته شود.

Controlled Vertical Slice معماری نهایی مشخص می‌کند:

```text
Binance Futures BTCUSDT
15M Primary
1H / 4H HTF
```

و مسیر:

```text
P2 Ingestion
→ P3 Normalization
→ P4 Quantitative/Structure
→ P5 Specialists
→ P6 AI
→ P8 persistence/API
```

است.

بنابراین در P3 باید حداقل یک **real-data vertical-slice evidence path** داشته باشیم که نشان دهد داده واقعی P2 می‌تواند بدون corruption از مرز P3 عبور کند و ورودی معتبر P4 شود.

---

# نتیجه نهایی من

بعد از این بررسی مجدد، من این را **نسخه نهایی پیشنهادی roadmap Phase 3** می‌دانم:

```text
PH-P3
Validation, Normalization & Data Quality Engine

│
├── STEP-P3-001
│   Canonical Contracts, Identity & Validation Foundation
│
├── STEP-P3-002
│   Structural, Schema & Identity Validation
│
├── STEP-P3-003
│   Temporal, Sequence & Completeness Validation
│
├── STEP-P3-004
│   Market Semantic, Price, Spread & Precision Validation
│
├── STEP-P3-005
│   Canonical Normalization & Provider Mapping
│
├── STEP-P3-006
│   Cross-Venue Consistency & Equivalence
│
├── STEP-P3-007
│   Data Quality, Quarantine, DLQ & Lineage
│
└── STEP-P3-008
    Authoritative Persistence, Event Handoff
    & G-3 Verification
```

### و منطق آن:

**P3-001** تعیین می‌کند «داده معتبر چیست».

**P3-002** می‌گوید «ساختار داده درست است یا نه».

**P3-003** می‌گوید «زمان و sequence درست است یا نه».

**P3-004** می‌گوید «معنای بازار و اعداد درست هستند یا نه».

**P3-005** داده معتبر را به زبان مشترک Meylux تبدیل می‌کند.

**P3-006** اطمینان می‌دهد دو venue را واقعاً می‌توان با هم مقایسه کرد.

**P3-007** کیفیت، عدم قطعیت، خطا، quarantine و lineage را مدیریت می‌کند.

**P3-008** خروجی را authoritative می‌کند، به downstream تحویل می‌دهد و کل Phase را با G-3 اثبات می‌کند.

و این ساختار از نظر من از هر دو نسخه قبلی بهتر است، چون **نه capability مهمی را حذف می‌کند و نه Stepها را بی‌دلیل خرد می‌کند.**

در عین حال با معماری V2، dependency رسمی P2→P3→P4، componentهای `CMP-P3-001/002`، artifactهای P3، canonical DB objects، worker/queue/APIهای تعریف‌شده و G-3 هم‌راستا باقی می‌ماند.

**نکته حاکمیتی نهایی:** این ۸ مورد در این لحظه **Final Proposed Execution Structure** هستند، نه اینکه من Stable IDهای `STEP-P3-*` را بدون ثبت رسمی در Registry به پروژه تحمیل کرده باشم. مرحله بعدی governance باید همین ساختار را به `PH-P3.md`، Registry، artifact traceability، acceptance criteria و سپس Task Orderهای رسمی تبدیل کند. GitHub نیز در جست‌وجوی فعلی هنوز نتیجه‌ای برای `PH-P3` ندارد؛ بنابراین این distinction همچنان لازم است.
