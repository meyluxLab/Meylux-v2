# PHASE 3 ROADMAP — Validation, Normalization & Data Quality Engine

**Document type:** Blueprint / Execution Roadmap (planning input for formal Phase Establishment)
**Phase SID (proposed):** `PH-P3`
**Predecessor:** `PH-P2` — CLOSED / VERIFIED
**Successor:** `PH-P4` — Deterministic Quantitative & Market Structure Engine
**Architectural basis:** `DOC-V2-ARCH-001` (RATIFIED / FROZEN), §7–8 (Canonical Data & Quality), §13 (PHASE P3)
**Governance status:** این سند یک **Roadmap/Blueprint** است، نه یک `PH-P3.md` رسمی. هیچ Stable ID، Task Order یا authorization اجرایی از طریق این سند صادر نمی‌شود. تبدیل این نقشه به Phase Definition رسمی، ثبت در Registry، و صدور Task Order باید از طریق فرآیند Governance موجود (ADR/ACR + Project Owner ratification) انجام شود.

---

## 1. جایگاه Phase 3 در زنجیره پروژه

```text
PHASE 2 — "می‌توانیم داده را جمع‌آوری کنیم؟"
   Provider Raw / Staging Data (Binance, MEXC)
        │
        ▼
PHASE 3 — "می‌توانیم به این داده اعتماد کنیم؟"
   Validate → Normalize → Classify Quality → Quarantine Invalid → Persist Canonical Truth
        │
        ▼
PHASE 4 — "این داده از نظر ریاضی چه می‌گوید؟"
   Deterministic Quantitative / Structure Engine
```

- **Phase 2** مالک Acquisition است.
- **Phase 3** مالک Trust / Canonicalization / Quality است.
- **Phase 4** مالک Mathematical Truth / Structure است.

این تفکیک یک اصل معماری صریح V2 است (§8.3، §8.4) و نباید در حین اجرا نقض شود.

## 2. مأموریت Phase 3

Phase 3 مرز اعتماد داده Meylux را می‌سازد: داده خام/staging تحویل‌شده از Phase 2 را validate، normalize، quality-classify و در صورت نیاز quarantine می‌کند، و فقط داده validated semantic را به‌صورت canonical و authoritative در اختیار Phase 4 قرار می‌دهد.

**قاعده بنیادین (Canonical Data Rule — §8.3):** Canonical contracts فقط شامل validated semantic data هستند. فیلدهای خاص provider (aliasها، event ID، جزئیات sequence، wire-format fields) در سطح provider adapter باقی می‌مانند مگر آنکه یک domain requirement صریح آن‌ها را semantic کند.

**قاعده کیفیت داده (Data-Quality Rule — §8.4):** هر مصرف‌کننده downstream باید بتواند بین حالت‌های زیر تمایز قائل شود: کامل و تازه، ناقص، stale، degraded، متناقض، در دسترس نبودن، و پشتیبانی‌نشده.

## 3. اصول غیرقابل‌مذاکره Phase 3

| اصل | توضیح |
|---|---|
| **No Silent Fixing** | `Bad Data → Detect → Classify → Route` — نه `Bad Data → Guess → Silently Fix` |
| **No Fabrication** | هیچ مقدار missing یا invalid با مقدار ساختگی پر نمی‌شود |
| **Explicit Degradation** | هر رکورد باید وضعیت کیفیت صریح داشته باشد؛ ابهام هرگز silent نیست |
| **Provider Isolation → Canonical Purity** | فرمت خاص provider هرگز وارد canonical نمی‌شود مگر با توجیه صریح domain |
| **Quarantine, not Delete, not Promote** | داده خراب نه حذف می‌شود، نه canonical می‌شود؛ isolate می‌شود |
| **Lineage** | هر رکورد canonical باید تا منبع و تاریخچه validation آن قابل ردیابی باشد |

## 4. Scope و Non-Scope

### در Scope
Schema validation، semantic validation، timestamp/sequence validation، price/spread integrity، tick/lot precision، duplicate detection، cross-venue equivalence، data-quality scoring، quarantine/DLQ، canonical persistence، normalized event handoff به Phase 4.

### خارج از Scope (به‌صراحت متعلق به فازهای بعدی)

| قابلیت | فاز مالک |
|---|---|
| Technical Indicators (EMA, RSI, MACD, ATR, ADX, Bollinger) | P4 |
| Market Structure (BOS, CHOCH, MSS, FVG, Order Blocks, Liquidity Pools) | P4 |
| Volume Profile، Order Flow Analytics | P4 |
| Regime Classification | P4 |
| Specialist Intelligence | P5 |
| AI Interpretation، Opportunity Score، Trade Idea Generation | P6 |
| Natural Language Summary | P6 |
| Arbitrage / Opportunity Analysis (فراتر از Cross-Venue Validation) | خارج از scope P3 |

Cross-Venue Validation در P3 مجاز است؛ Opportunity Detection مجاز نیست.

## 5. ساختار پیشنهادی Step — نمای کلی

تحلیل سه گزینه (۶ Step درشت، ۱۴ Step ریز، و نسخه بینابین) نشان می‌دهد که **۸ Step** بهترین تعادل بین dependency boundaries، قابلیت تست مستقل، traceability، و جلوگیری از Scope Creep را ایجاد می‌کند. هیچ capability‌ای نسبت به تحلیل تفصیلی‌تر (۱۴ مورد) حذف نشده؛ صرفاً به مرزهای اجرایی منطقی‌تری منتقل شده است (جدول تطبیق در بخش ۱۴).

| # | Step SID (proposed) | عنوان | محور اصلی |
|---|---|---|---|
| 1 | `STEP-P3-001` | Canonical Contracts, Identity & Validation Foundation | تعریف داده معتبر |
| 2 | `STEP-P3-002` | Structural, Schema & Identity Validation | ساختار داده |
| 3 | `STEP-P3-003` | Temporal, Sequence & Completeness Validation | زمان و ترتیب |
| 4 | `STEP-P3-004` | Market Semantic, Price, Spread & Precision Validation | معنای بازار و اعداد |
| 5 | `STEP-P3-005` | Canonical Normalization & Provider Mapping | تبدیل به زبان مشترک |
| 6 | `STEP-P3-006` | Cross-Venue Consistency & Equivalence | مقایسه‌پذیری بین Venue |
| 7 | `STEP-P3-007` | Data Quality, Quarantine, DLQ & Lineage | کیفیت و اعتمادپذیری |
| 8 | `STEP-P3-008` | Authoritative Persistence, Event Handoff & G-3 Verification | تحویل نهایی به P4 |

**وابستگی خطی:** هر Step روی contract/behavior تأییدشده Step قبلی بنا می‌شود؛ Step بعدی نباید روی رفتار تأییدنشده Step قبل اجرا شود. (آماده‌سازی fixture، مستندسازی، و برخی unit testها می‌توانند موازی توسعه یابند.)

```text
PH-P2 (RAW/STAGING)
        │
        ▼
 STEP-P3-001  Contracts / Identity / Validation Foundation
        │
        ▼
 STEP-P3-002  Structural / Schema Validation
        │
        ▼
 STEP-P3-003  Temporal / Sequence / Completeness
        │
        ▼
 STEP-P3-004  Semantic / Price / Spread / Precision
        │
        ▼
 STEP-P3-005  Canonical Normalization (Binance + MEXC)
        │
        ▼
 STEP-P3-006  Cross-Venue Consistency
        │
   ┌────┴────┐
   ▼         ▼
 VALID   INVALID / DEGRADED
   │         │
   ▼         ▼
 STEP-P3-007  Quality Scoring + Lineage   /   Quarantine + DLQ
        │
        ▼
 STEP-P3-008  Authoritative Persistence + Event Handoff + API + E2E Verification
        │
        ▼
       G-3
        │
        ▼
      PH-P4
```

---

## 6. STEP-P3-001 — Canonical Contracts, Identity & Validation Foundation

**هدف:** پیش از هر validation، باید دقیقاً مشخص باشد «داده معتبر» یعنی چه.

**مسئولیت‌ها:**
- تثبیت Canonical Data Contracts: Canonical Instrument Identity، Canonical Candle، Canonical Trade، Canonical Order Book، Canonical Derivatives
- تعریف: venue identity، symbol identity، market type، contract type، timeframe، timestamp semantics، فیلدهای required/optional، null semantics، نمایش Decimal، سیاست precision/scale، taxonomy نتیجه validation، الزامات provenance، قواعد deterministic identity
- تثبیت ارتباط با دو component معماری مرتبط: `CMP-P3-001` (Normalization & Data Quality Subsystem) و `CMP-P3-002` (Canonical Contract Registry)

**چرا ضروری است:** بدون یک Canonical Contract دقیق قبل از Validation، مصرف‌کنندگان بعدی (Validator، Normalizer، Database، Quant Engine، Specialists) ممکن است برداشت‌های متفاوتی از «داده معتبر» داشته باشند. هدف این Step دقیقاً جلوگیری از این ناهمخوانی است.

**خروجی:** یک Canonical Data Boundary Definition که کل Phase 3 بر اساس آن کار می‌کند.

---

## 7. STEP-P3-002 — Structural, Schema & Identity Validation

**هدف:** بررسی پذیرش ساختاری داده ورودی، پیش از هر بررسی معنایی.

**پوشش:** required fields، field types، nullability، enum values، schema compliance، payloadهای malformed، صحت syntax نماد (symbol)، اعتبار timeframe، venue identity، market type، contract type، شناسایی identity اولیه، duplicate identity candidates.

نمونه موارد ردشدنی: `price = "ABC"`، `timestamp = null`، `unknown market_type`.

**اصل حاکم:**

```text
Bad Data → Detect → Classify → Route      (درست)
Bad Data → Guess → Silently Fix           (ممنوع)
```

این اصل برای هدف نهایی Meylux حیاتی است و در تمام Stepهای بعدی نیز اعمال می‌شود.

---

## 8. STEP-P3-003 — Temporal, Sequence & Completeness Validation

**هدف:** زمان یک مفهوم بنیادین در market intelligence است؛ این Step به‌صورت مستقل به آن می‌پردازد.

**پوشش:**
- **Timestamp:** اعتبار timestamp، معنای timezone، event timestamp در برابر receive timestamp، timestamp آینده، clock skew (مقدار پیشنهادی معماری: **5000ms**، که باید به‌صورت configuration parameter مورد governed validation قرار گیرد، نه یک عدد hard-coded)
- **Ordering:** monotonicity، رویدادهای out-of-order، timestampهای تکراری، سازگاری sequence
- **Candle continuity:** پیوستگی interval، کندل‌های گمشده، gapهای غیرمنتظره، sequence ناقص
- **Event sequence:** در صورت وجود sequence در منبع (`n, n+1, n+2, ...`)، الگوی `n, n+2` نباید به‌عنوان sequence سالم تلقی شود

**خروجی:** هر رکورد باید یکی از وضعیت‌های صریح زیر را داشته باشد: `valid`، `gap`، `out-of-order`، `duplicate`، `stale`، `incomplete`. این خروجی مستقیماً با Semantic & Monotonicity Validator تعریف‌شده در معماری P3 منطبق است.

---

## 9. STEP-P3-004 — Market Semantic, Price, Spread & Precision Validation

**هدف:** قلب market-data correctness در Phase 3. سازگاری schema به‌تنهایی کافی نیست؛ معنای بازار نیز باید صحیح باشد.

**OHLC integrity:**
```text
high >= open, high >= close, high >= low
low  <= open, low  <= close, low  <= high
```

**Price:** قیمت منفی، قیمت غیرممکن، صفر نامعتبر در جایی که از نظر معنایی غیرممکن است، مقادیر عددی malformed.

**Quantity / Volume:** مقدار/حجم منفی یا نامعتبر، ناسازگاری معنایی.

**Spread:** سلامت bid/ask، spread منفی یا غیرممکن، spread بیش از حد — معماری صراحتاً **Price & Spread Integrity Validator** را تعریف کرده و **حداکثر spread مجاز: ۵٫۰٪** را به‌عنوان configuration parameter مشخص کرده است.

**Precision:** tick size، lot size، دقت instrument، دقت مقدار و قیمت، سیاست rounding، دقت نامعتبر — این بخش با **Tick & Lot Size Precision Validator** تعریف‌شده در معماری منطبق است.

**اصل حیاتی:** Phase 3 نباید قیمت را «به‌زور» قابل‌قبول کند. اگر مقدار با قواعد instrument سازگار نیست، باید `Reject / Quarantine / Quality Degradation` رخ دهد — نه rounding خاموش، مگر آنکه قاعده rounding خودش به‌صورت صریح و governed تعریف شده باشد.

---

## 10. STEP-P3-005 — Canonical Normalization & Provider Mapping

**هدف:** تبدیل داده validated به زبان مشترک (canonical) Meylux.

```text
Binance → Provider Representation → Canonical Mapping
MEXC    → Provider Representation → Canonical Mapping
```

**حوزه‌های mapping:** instrument، candle، trade، order book، derivatives، venue، market type، contract type، timeframe، timestamp، price، quantity، volume، side semantics، provenance.

**آرتیفکت‌های معماری مرتبط:** `ART-P3-013` (Binance to Canonical Transformer)، `ART-P3-014` (MEXC to Canonical Transformer). معماری صراحتاً Canonical Mappers برای Binance و MEXC را الزامی کرده است.

**اصل حیاتی:** فرمت خاص wire هر provider نباید وارد Domain Canonical شود. V2 صراحتاً مقرر کرده که aliasهای خاص provider، event IDها، جزئیات sequence و فیلدهای wire-format در مرز provider باقی بمانند، مگر آنکه یک domain requirement مشخص آن‌ها را semantic کند.

---

## 11. STEP-P3-006 — Cross-Venue Consistency & Equivalence

**هدف:** در پروژه‌ای که Binance و MEXC هر دو first-class provider هستند، مقایسه بین venue صرفاً یک جزئیات کوچک Validator نیست؛ پایه‌ای برای Market Intelligence آینده (Cross-Exchange Analyst، Venue Intelligence، Opportunity Analysis) است — بدون آنکه خودش وارد تحلیل فرصت یا arbitrage شود.

**پوشش (Cross-Venue Rider — §13):**
- **Identity:** یکسانی base asset، quote asset، معنای symbol
- **Market type:** Spot ≠ Futures
- **Contract type:** Perpetual ≠ Delivery
- **Unit semantics:** واحد volume/quantity بین دو provider بدون اثبات نباید معادل فرض شود
- **Timestamp alignment:** قابل‌مقایسه بودن داده دو venue از نظر زمانی
- **Freshness:** مقایسه Binance تازه در برابر MEXC stale نباید به‌عنوان divergence معتبر ثبت شود
- **Bid/Ask sanity:** هر دو سمت باید از نظر market integrity معتبر باشند
- **Impossible values:** اختلاف ناشی از corruption نباید به‌عنوان market dislocation ثبت شود

**قاعده حیاتی:** mapping نامطمئن هرگز نباید به‌صورت silent فعال شود.

---

## 12. STEP-P3-007 — Data Quality, Quarantine, DLQ & Lineage

**هدف:** قلب اعتمادپذیری Meylux. Validation نباید فقط `PASS/FAIL` بگوید؛ باید مشخص کند کیفیت داده برای مصرف‌کننده بعدی چقدر و چرا قابل اعتماد است.

### 12.1 Data Quality Score
خروجی: `Data Quality Score: 0.00 – 1.00` + `Explanation Vector`، با مؤلفه‌های: freshness، completeness، consistency، feed health، validation status، provider capability.

### 12.2 وضعیت‌های کیفیت (سطح رکورد — معماری، §8.2)
```text
VALID · DEGRADED · STALE · INCOMPLETE · CONTRADICTORY · REJECTED · UNAVAILABLE
```

### 12.3 وضعیت‌های data-flow (سطح pipeline)
```text
RAW · STAGED · VALIDATING · NORMALIZED · CANONICAL
QUALITY_DEGRADED · REJECTED · QUARANTINED · EXPIRED · ARCHIVED
```

### 12.4 Quarantine / DLQ
```text
Invalid → Quarantine / DLQ     (درست)
Invalid → Delete                (ممنوع)
Invalid → Canonical             (ممنوع)
```
معماری صراحتاً `normalization_dlq` را برای داده corrupt تعریف کرده و الزام کرده که این جداسازی بدون crash کردن worker انجام شود.

### 12.5 Lineage
برای هر رکورد canonical باید مسیر زیر قابل ردیابی باشد:
```text
Provider → Raw/Staging record → Validation result → Normalization → Quality result → Canonical record
```
این موضوع برای debugging، replay، audit، ارزیابی آینده و AI evidence provenance حیاتی است.

---

## 13. STEP-P3-008 — Authoritative Persistence, Event Handoff & G-3 Verification

**هدف:** تحویل واقعی و end-to-end فاز به Phase 4.

### 13.1 Canonical persistence — شش object اصلی معماری

| DB SID | نام | Append-only |
|---|---|---|
| `DB-P3-001` | `canonical_instruments` | بله |
| `DB-P3-002` | `canonical_candles` | بله |
| `DB-P3-003` | `canonical_trades` | بله |
| `DB-P3-004` | `canonical_orderbook_depth` | بله |
| `DB-P3-005` | `canonical_derivatives` | بله |
| `DB-P3-006` | `data_quality_logs` | بله |

جداول canonical باید authoritative boundary باشند و برای application، دسترسی `UPDATE`/`DELETE` نداشته باشند — این الزام در معماری صریح است.

### 13.2 Normalized Event Stream
```text
Canonical Data → stream:canonical:market_events → Phase 4
```

### 13.3 Workers
- `WRK-P3-001` — normalization-stream-worker
- `WRK-P3-002` — data-quality-auditor

### 13.4 Quality API (Observability)
- `GET /api/v1/quality/{exchange}/{symbol}`
- `GET /api/v1/quality/summary`

این APIها بخشی از مرز observable data-quality هستند، نه UI نهایی؛ باید در همین Step یا در مرز integration آن قرار گیرند.

### 13.5 معیار خروج (G-3)
Phase 3 با «تست‌ها pass شدند» تمام نمی‌شود. باید ثابت شود که مسیر کامل زیر به‌صورت end-to-end کار می‌کند:
```text
P2 staging → Validation → Normalization → Quality → Quarantine → Canonical persistence → Canonical event stream → P4-ready data
```

**معیار رسمی معماری برای G-3:**
```text
Normalization pipeline pass
100% canonical schema pass
DLQ active
```

---

## 14. جدول تطبیق: از تحلیل تفصیلی (۱۴ Capability) به ساختار نهایی (۸ Step)

| Capability | Step نهایی |
|---|---|
| Schema / Contract Validation | P3-001 / P3-002 |
| Semantic Validation | P3-003 / P3-004 |
| Temporal Validation | P3-003 |
| Sequence Validation | P3-003 |
| Price / Quantity Integrity | P3-004 |
| Precision | P3-004 |
| Duplicate / Identity | P3-001 / P3-002 / P3-003 |
| Missing / Stale / Incomplete | P3-003 / P3-007 |
| Canonical Mapping | P3-005 |
| Cross-Venue Consistency | P3-006 |
| Data Quality Scoring | P3-007 |
| Quarantine / DLQ | P3-007 |
| Canonical Persistence | P3-008 |
| Normalized Event Stream | P3-008 |
| G-3 Verification | P3-008 |

هیچ capability مهمی از تحلیل قبلی حذف نشده؛ فقط به مرزهای اجرایی منطقی‌تری منتقل شده است.

---

## 15. Definition of Done — معیار خروج نهایی Phase 3

Phase 3 فقط زمانی کامل تلقی می‌شود که همه موارد زیر با evidence واقعی اثبات شده باشند:

1. **Contract Integrity** — Canonical contracts مشخص، versioned و verified هستند.
2. **Structural Integrity** — داده malformed هرگز وارد canonical نمی‌شود.
3. **Temporal Integrity** — semantics مربوط به timestamp/sequence/gap اثبات شده‌اند.
4. **Market Integrity** — OHLC، price، quantity، volume، spread و precision کنترل می‌شوند.
5. **Provider Mapping** — Binance و MEXC هر دو به یک canonical semantic representation می‌رسند.
6. **Cross-Venue Integrity** — مقایسه venueها فقط پس از اثبات semantic equivalence انجام می‌شود.
7. **Quality Awareness** — هر مصرف‌کننده downstream می‌تواند بفهمد داده fresh، complete، degraded، stale، contradictory، unavailable یا unsupported است.
8. **No Fabrication** — هیچ داده missing/invalid با مقدار ساختگی پر نمی‌شود.
9. **Quarantine** — داده خراب isolate می‌شود و canonical را آلوده نمی‌کند.
10. **Lineage** — هر رکورد canonical تا source و تاریخچه validation قابل ردیابی است.
11. **Authoritative Persistence** — جداول canonical مرجع authoritative و append-only هستند.
12. **Event Handoff** — Phase 4 می‌تواند رویدادهای canonical را دریافت کند.
13. **Real-Time Quality** — quality scoring فقط batch تاریخی نیست؛ در جریان عملیاتی فعال است.
14. **Replay / Determinism** — ورودی یکسان، خروجی validation/normalization قابل تکرار تولید می‌کند.
15. **Performance** — هدف معماری برای batch normalization: **بیش از ۵٬۰۰۰ رویداد بر ثانیه به ازای هر core**؛ این هدف باید با evidence سنجیده شود، نه صرفاً «achieved» فرض شود.
16. **G-3** — با evidence واقعی: `100% staging → canonical processing`، `DLQ active`، `zero canonical corruption`، `real-time quality scoring`.

---

## 16. الزام Vertical Slice

Phase 3 نباید صرفاً با چند fixture مصنوعی بسته شود. مسیر Controlled Vertical Slice نهایی معماری:

```text
Binance Futures BTCUSDT — 15M Primary / 1H & 4H HTF
P2 Ingestion → P3 Normalization → P4 Quantitative/Structure → P5 Specialists → P6 AI → P8 Persistence/API
```

بنابراین Phase 3 باید حداقل یک مسیر evidence مبتنی بر داده واقعی (real-data vertical-slice) داشته باشد که نشان دهد داده واقعی Phase 2 می‌تواند بدون corruption از مرز Phase 3 عبور کرده و به ورودی معتبر Phase 4 تبدیل شود.

---

## 17. نکات تکمیلی — شکاف‌های اجرایی که باید صریح شوند

بازبینی مجدد این Roadmap چهار نقطه را شناسایی کرد که در ساختار ۸ Step فعلی به‌صورت ضمنی حل شده‌اند اما باید پیش از تبدیل به Phase Definition رسمی، **صریح** و به یکی از Stepهای مربوطه ضمیمه شوند.

### 17.1 Backfill تاریخی در برابر Stream زنده (مرتبط با `STEP-P3-002` تا `STEP-P3-005`)

Stepهای فعلی صراحتاً بین دو مسیر ورودی تمایز قائل نمی‌شوند:

```text
مسیر A — Live Stream:      Provider WS/REST → Raw/Staging → Validation → Normalization  (کندل به کندل)
مسیر B — Historical Backfill: Bulk Provider Export/REST → Raw/Staging (حجم بالا) → Validation → Normalization  (batch)
```

هر دو مسیر باید از **همان Canonical Contracts** (`STEP-P3-001`) و **همان قواعد Validation** (`STEP-P3-002` تا `STEP-P3-004`) عبور کنند تا خروجی canonical دچار دوگانگی معنایی نشود. اما تفاوت‌های عملیاتی زیر باید صریحاً در سطح Step (ترجیحاً `STEP-P3-005` یا به‌عنوان یک rider مستقل) مشخص شوند:

- **Throughput profile متفاوت:** batch backfill معمولاً چند مرتبه حجیم‌تر از نرخ ورودی stream زنده است و نباید صف/normalization stream زنده را گرسنه (starve) کند — باید یا اولویت‌بندی صف مجزا داشته باشد، یا worker مستقل.
- **Idempotency در تلاقی دو مسیر:** اگر بازه زمانی backfill با داده‌ای که از stream زنده قبلاً canonical شده هم‌پوشانی داشته باشد، قاعده باید صریح باشد: رکورد stream زنده برنده است یا رکورد backfill (بر اساس provenance و completeness)، و این تصمیم نباید silent باشد.
- **Gap Recovery در برابر Cold Backfill:** وقتی Phase 2 یک gap شناسایی‌شده را با backfill پر می‌کند، Phase 3 باید بتواند این رکوردها را از نظر lineage به‌عنوان `SOURCE: BACKFILL` علامت‌گذاری کند تا از رکوردهای `SOURCE: LIVE` قابل تفکیک باشند (بدون تغییر در نتیجه validation).

**پیشنهاد الحاق:** یک زیربخش صریح با عنوان «Backfill Ingestion Mode» در `STEP-P3-005` (Canonical Normalization & Provider Mapping) اضافه شود که provenance field موجود در `STEP-P3-001` را برای این تمایز استفاده کند — بدون نیاز به Contract جدید.

### 17.2 Schema Versioning / Migration برای Canonical Contracts (مرتبط با `STEP-P3-001` و `STEP-P3-008`)

`STEP-P3-001` صرفاً **freeze** اولیه Canonical Contracts را پوشش می‌دهد؛ مسیر **تکامل** بعدی این contracts (وقتی نیاز به افزودن/تغییر فیلد در آینده پیش بیاید) صریح نیست. پیشنهاد می‌شود این قاعده به‌عنوان یک بند مستقل در `STEP-P3-001` یا `STEP-P3-008` اضافه شود:

```text
تغییر Canonical Contract:
  Additive field (backward-compatible)  →  version bump جزئی + مستندسازی، بدون migration اجباری داده قدیمی
  Breaking change (تغییر معنایی/حذف)     →  ACR/change control + Contract SID جدید یا versioned schema
                                            + قاعده صریح migration/backfill برای رکوردهای canonical قبلی
```

این با اصل `Golden Vector Freeze` در Phase 4 هم‌راستا است: تغییر contract نباید silent باشد و باید همان انضباط change-control را داشته باشد.

### 17.3 Alerting روی Quarantine/DLQ Rate (مرتبط با `STEP-P3-007`)

`STEP-P3-007` مکانیزم Quarantine/DLQ را تعریف می‌کند اما آستانه یا رفتار عملیاتی برای **نرخ غیرعادی quarantine** را مشخص نمی‌کند. پیشنهاد الحاق به `STEP-P3-007`:

- یک **Quarantine Rate Baseline** به ازای هر `(venue, symbol, feed type)` باید در طول زمان قابل مشاهده باشد (از طریق `data_quality_logs` / Quality API موجود).
- عبور نرخ quarantine از یک آستانه پیکربندی‌شده (configuration-driven، نه hard-coded) باید یک سیگنال عملیاتی صریح تولید کند — نه اینکه صرفاً در DLQ انباشته شود و کسی متوجه نشود.
- این سیگنال می‌تواند از همان Observability Foundation (`CMP-P1-005`) تعریف‌شده در Phase 1 استفاده کند؛ نیازی به component جدید نیست.

### 17.4 مقیاس چندنمادی/چندبازاری (مرتبط با معیار خروج G-3)

معیار خروج فعلی صرفاً حول یک Vertical Slice تک‌نمادی (`Binance Futures BTCUSDT`) شده است. پیشنهاد می‌شود یک بند کوتاه به بخش ۱۵ (Definition of Done) اضافه شود:

> G-3 علاوه بر اثبات Vertical Slice تک‌نمادی، باید حداقل یک شاهد (evidence) از صحت pipeline روی **بیش از یک نماد هم‌زمان** (مثلاً یک جفت نماد با نرخ رویداد متفاوت) ارائه دهد تا اطمینان حاصل شود منطق validation/normalization به‌صورت implicit به یک نماد خاص وابسته نشده است. این شاهد نباید به‌معنای گسترش رسمی scope Phase 3 به پشتیبانی کامل چند-نماد باشد؛ صرفاً یک non-regression check است.

---

## 18. یادداشت حاکمیتی

این سند **Final Proposed Execution Structure** برای Phase 3 است — نه یک Phase Definition رسمی، نه Registry entry، و نه authorization اجرایی. Stable IDهای `STEP-P3-*` در این سند صرفاً **پیشنهادی** هستند و بدون ثبت رسمی در `docs/registry/artifacts.yaml` معتبر شناخته نمی‌شوند.

مرحله بعدی governance که باید توسط CONTROL/Project Owner از طریق فرآیند موجود انجام شود:

1. تبدیل این ساختار به `docs/phases/PH-P3.md` رسمی (با همان قالب `PH-P0.md`/`PH-P1.md`/`PH-P2.md`).
2. ثبت Stable IDهای `STEP-P3-001` تا `STEP-P3-008` در Registry.
3. تعریف Acceptance Criteria مستقل برای هر Step.
4. صدور Task Order رسمی برای اولین Step (`STEP-P3-001`) فقط پس از تصویب Owner.

تا پیش از انجام این مراحل، طبق `docs/state/CURRENT_CHECKPOINT.json`، **هیچ اجرای Phase 3 مجاز نیست.**
