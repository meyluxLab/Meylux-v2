# PHASE 5 ROADMAP — Specialist Market Intelligence Layer

**نوع سند:** Blueprint / Execution Roadmap — ورودی رسمی‌سازی فاز (Formal Phase Establishment). **Reference Only.**
**Phase SID (پیشنهادی):** `PH-P5` | **پیش‌نیاز:** `PH-P4` (`CLOSED / VERIFIED`، `G-4 ESTABLISHED / VERIFIED`) | **فاز بعدی:** `PH-P6`
**مبنای معماری:** `DOC-V2-ARCH-001` (`RATIFIED / FROZEN`) — §2.1، §8.4، §9، §12، §14، §16 (Phase P5)، §17، §22–§24، §26، §28–§34، §37، §42، §43، §46، §49. (نام P5 در §9 «Specialist analytical layer» و در §16 «Specialist Market Intelligence Layer» است؛ SID یکی است.)
**مبنای حاکمیتی:** `ADR-GOVERNANCE-012`، `ADR-GOVERNANCE-013` (Rule 1 تا Rule 5 و Footer)، `GOV-BOUNDARY-001`
**مبنای واقعیت‌سنجی:** مخزن `meyluxLab/Meylux-v2`، شاخهٔ `main`، HEAD = `c6f9f4e6b08dc8a905ae04667911b6c75c7aa5f5` (۲۰۲۶-۰۹-۲۰). موارد راستی‌آزمایی‌شده و تأییدنشده در پیوست A آمده است. هر «واقعیت مخزن» باید هنگام رسمی‌سازی توسط CONTROL دوباره تأیید شود.

---

## 0. وضعیت حاکمیتی این سند و برچسب‌ها

- این سند **Blueprint مرجع (Reference Only)** است، هم‌سطح `PHASE3_ROADMAP.md` و `PHASE4_ROADMAP.md` در `docs/blueprint/`.
- هیچ Stable ID، Task Order، Phase Definition یا authorization اجرایی از این سند صادر نمی‌شود. همهٔ شناسه‌های `STEP-P5-*`، `CTR-P5-*`، `DB-P5-*`، `WRK-P5-*`، `S-01..S-18`، `PD-*`، `PRE-*`، `PRQ-*`، `USR-*`، `BND-*`، `PROC-*` **پیشنهادی یا برچسب محلی** هستند. Stable ID را فقط CONTROL/Registry اختصاص می‌دهد.
- **برچسب منبع** در سراسر سند:
  - `[REPO]` = واقعیتی که در مخزن دیده شده؛
  - `[ARCH]` = الزام یا مرز در معماری فریزشده؛
  - `[PROP]` = پیشنهاد این Blueprint؛ **هیچ authority مستقلی ندارد** و فقط با ثبت رسمی معتبر می‌شود؛
  - `[UNVERIFIED]` = تأییدنشده.
- **وضعیت Checkpoint:** `CURRENT_CHECKPOINT.json` فقط می‌گوید «Phase 5 remains NOT AUTHORIZED» `[REPO]`. مجموعهٔ `PRE/PD/PRQ/USR` در این سند **پیشنهاد شرایط ورود به Formal Phase Establishment** است `[PROP]` و شرط ثبت‌شدهٔ Checkpoint نیست.

## 1. جایگاه و مأموریت

```text
PHASE 4 — «واقعیت ریاضی چیست؟»        (Facts: indicators, structure, volume profile, regime)
PHASE 5 — «هر دامنهٔ تخصصی، مستقل، چه برداشتی دارد؟»   (Independent findings + evidence + confidence + risk flags)
PHASE 6 — «با کنار هم گذاشتن برداشت‌ها، تصویر نهایی چیست؟»   (Synthesis, contradiction, scenarios, scores)
```

Phase 5 هجده دامنهٔ §16.2 را روی یک **Input Snapshot** مشترک و تغییرناپذیر اجرا می‌کند و برای هر دامنه خروجی ساختاریافته، نسخه‌دار، قابل‌ردیابی و append-only تولید می‌کند. Phase 5 تصمیم معاملاتی، امتیاز نهایی، سناریو یا روایت زبان طبیعی تولید نمی‌کند (`INV-V2-001`، §17).

**اصل مرزی این نسخه:** P5 **مصرف‌کنندهٔ** facts و داده است، نه مالک تولید آن‌ها (بند ۴).

## 2. اصول غیرقابل‌مذاکره

| اصل | معنا و مبنا |
|---|---|
| Determinism-Where-Possible | `INV-V2-002`، §16.1 `[ARCH]`. §16.1 می‌گوید «همهٔ specialistها LLM نیستند»؛ P5 در این Blueprint **هیچ فراخوانی LLM** ندارد (مرز `BND-1`، بند ۶) |
| Informational Independence | `INV-V2-005`، §16.3 `[ARCH]`: شواهد همبسته نباید رأی مستقل شمرده شوند. **مدل پایهٔ این Blueprint Stage-1 Only** است: هر specialist فقط Input Snapshot را می‌بیند. این مدل `[PROP]` و **تابع `PD-4`** است (`USR-14` مشروط) |
| No Fabrication | `INV-V2-003`. نبود داده = وضعیت صریح (`INSUFFICIENT_DATA` / `UNAVAILABLE_INPUT`)، نه عدد ساختگی و نه `confidence: 0` |
| Provenance | `INV-V2-004`. هر finding حداقل یک `evidence_ref` معتبر به رکورد واقعی (`record_id` / `identity_hash`) دارد |
| Zero Lookahead | `INV-V2-009`. فقط facts با `knowledge_time <= snapshot.as_of` وارد Snapshot می‌شوند |
| Single Authoritative Persistence | `INV-V2-007`. خروجی specialistها فقط در جدول‌های append-only دیتابیس رسمی |
| Confidence ≠ Data Quality | دو محور جدا؛ هرگز در یک عدد ادغام نمی‌شوند |
| No Cross-Phase Leakage | هیچ منطق Opportunity Score، Scenario، Contradiction Resolution یا Venue Opportunity (`CMP-V2-VENUE-001`) در P5 نیست |
| Ownership Respect | P5 هیچ قابلیت acquisition، normalization یا محاسبهٔ ریاضی P2/P3/P4 را نمی‌سازد؛ کمبودها از مسیر مالک همان مرز رفع می‌شوند (بند ۴) |
| Versioned Contract | تغییر منطق یا قرارداد بدون version bump صریح ممنوع است |
| Failure Isolation | §16.4. شکست یا timeout یک specialist فقط وضعیت صریح همان specialist است |

## 3. Scope و Non-Scope

**در Scope:** Specialist Contract و Evidence Model؛ Input Snapshot Builder؛ Runtime Harness؛ ۱۸ specialist؛ Independence Clustering (Registry-based)؛ Persistence append-only برای خروجی specialistها؛ Config؛ Observability؛ Handoff به P6؛ و اجرای همهٔ این‌ها روی VPS در همان گامی که ساخته می‌شوند (بند ۱۰).

**Non-Scope:**

| قابلیت | مالک |
|---|---|
| محاسبهٔ اندیکاتور/رویداد ساختار/Volume Profile/Order Flow/Derivatives/Regime، **و عملیاتی‌کردن و persist آن‌ها در runtime** (`PRQ-1`) | P4 (مرز مالکیت) |
| فعال‌سازی جمع‌آوری trade/depth، دادهٔ MEXC/نماد دوم (`PRQ-2`)، قابلیت‌های جدید Provider مثل funding/OI (`PRQ-3`) | P2 (مرز مالکیت) |
| کمبود شواهد کیفیت داده در لایهٔ persisted (`PRQ-4`) | P3 (مرز مالکیت) |
| تجمیع نظرات، تشخیص تناقض، سناریو، امتیازها، روایت، NO TRADE، هر LLM | P6 |
| Scanner | P7 |
| API/UI عمومی | P8 |
| ارزیابی صحت تاریخی، آمار نتیجه (outcome statistics)، Calibration | P9 |
| Venue Opportunity، executable spread، fee | `CMP-V2-VENUE-001` |
| Provider خبری | خارج از P5 مگر با ADR/ACR |

## 4. مرز مالکیت و بسته‌های پیش‌نیاز (PRQ)

### 4.1 چرا

- `[ARCH]` §12: P2 مالک acquisition است (candles، trades، order book، funding، open interest، liquidations، provider health). §14: P4 مالک facts ریاضی و ساختاری است. `PH-P4.md`: «Phase 4 owns mathematical truth and deterministic fact generation».
- `[REPO]` `TO-P4-007` §3.3 صریحاً «engine capability» را از «demonstrated runtime coverage» جدا کرده و `AR-P4-015` G-4 را با slice `BTCUSDT 15M+1H+4H` و پوشش `EMA/RSI/ATR + Structure + Regime` بسته است. بنابراین کمبودهای زیر **نقص P4 نیستند و G-4 را باطل نمی‌کنند**؛ فقط پوششی هستند که G-4 آن را نشان نداده است.
- اگر P5 این کمبودها را داخل Stepهای خودش بسازد، شکست بعدی (مثلاً در `S-01`) قابل‌تفکیک نیست: نقص fact-generation است یا نقص specialist؟ این همان الگوی «فاز جدید، کمبود فاز قبل را جبران می‌کند» است.

### 4.2 بسته‌های پیش‌نیاز `[PROP]`

| کد | موضوع | مرز مالکیت | نیاز P5 | محدودیت‌ها |
|---|---|---|---|---|
| `PRQ-1` | عملیاتی‌کردن و persist facts P4: اتصال موتورهای تأییدشدهٔ موجود (MACD، ADX، Bollinger، Supertrend، VWAP، RVOL/volume، Volume Profile، Order Flow، Derivatives) به orchestrator؛ persist رویدادها/zoneها/جلسات VP؛ facts **به‌ازای هر timeframe**؛ اجرای per-candle-close برای ساخت series تاریخی | P4 | S-01..S-06، S-08، S-09، S-11، S-12، S-14، S-16، S-17 | فقط additive؛ بدون ریاضی جدید؛ golden vectorها و Decimal policy بدون تغییر؛ engine بازگشایی نشود؛ migration رو به جلو (بعد از `0006`)؛ شواهد G-4 (`156` و `3/1/1`) دست‌نخورده یا re-baseline صریح توسط CONTROL؛ اگر شواهد G-4 متأثر شود ⇒ توقف و گزارش (الگوی `TO-P4-009`) |
| `PRQ-2` | فعال‌سازی governed جمع‌آوری trade/depth (سرویس `collector` که اکنون stub است)، داده MEXC برای همان instrument، نماد دوم، عمق کافی warm-up | P2 | S-05، S-07، S-12 (اختیاری)، S-17 | نیازمند Runtime Authorization صریح (manifest: `no_provider_runtime_activity_without_explicit_authorization`)؛ فقط داده عمومی؛ rate-budget و bounded resource |
| `PRQ-3` | قابلیت Derivatives (funding/OI/basis) در لایهٔ acquisition | P2 با ADR/ACR/change-control | S-04 | adapterهای فعلی Spot هستند؛ MEXC Futures سرویس جداست. اگر انجام نشود ⇒ `UNAVAILABLE_INPUT` با شواهد واقعی + OQ/DD |
| `PRQ-4` | شواهد کیفیت داده برای غیر-`VALID` و `unsupported` در لایهٔ persisted | P3 | S-10 | تعیین نیاز واقعی با FRM (گام ۰۰۲ و PRE-2)؛ گزینه: پذیرش محدودیت + ثبت Known Limitation |

### 4.3 قاعدهٔ گیت

هر Step از P5 که به یک `PRQ` وابسته است **فعال نمی‌شود** مگر (الف) آن `PRQ` تحویل و توسط CONTROL مستقل verified شده باشد، یا (ب) یک **disposition صریح `UNAVAILABLE`** توسط Owner/CONTROL ثبت شده باشد (با OQ/DD، مالک و trigger). P5 هرگز بی‌صدا کمبود را جذب نمی‌کند و «Feed Capability Step» داخل P5 وجود ندارد.

**VPS در هر تحویل PRQ:** Task Order هر `PRQ` نیز همان پروتکل VPS بند ۱۰ (VPS-1..VPS-12 متناسب با دامنهٔ آن تحویل) را دارد و `PRQ_DELIVERED` فقط با شواهد VPS واقعی و Audit مستقل CONTROL معتبر است؛ شاهد سطح کد یا تست به‌تنهایی کافی نیست.

### 4.4 مسیر اجرا (برای تصمیم `PD-1`/`PD-2`)

`[REPO]` دو سابقه وجود دارد: `TO-P4-008` (اصلاح adapter تحت Owner Directive) و `TO-P4-009` (سخت‌سازی post-closure با حفظ closure). اینکه `PRQ-1` که **افزودنی** است (نه سخت‌سازی) با همین مسیر سازگار است یا نیاز به change-control رسمی دارد، تصمیم Owner/CONTROL است `[PROP]`، نه فرض این Blueprint.

## 5. پیش‌شرط‌های رسمی‌سازی (PRE) `[PROP]`

| # | پیش‌شرط | وضعیت در HEAD `c6f9f4e` |
|---|---|---|
| PRE-1 | بستهٔ Handoff رسمی P4→P5 طبق §46. **Known Limitations باید شامل باشد:** محدودیت پوشش runtime (`EMA(20)/RSI(14)/ATR(14)` + Structure(شمارش/state) + Regime)، `DD-V2-P4-006-PERFORMANCE-TARGET`، `OQ-P4-006-MEXC-RESOURCEWARNING`، `OQ-GOV-CONSTITUTION-STABLE-ID`، محدودیت‌های شواهد کیفیت (`PRQ-4`)، عقب‌بودن source mount روی VPS | `[REPO]` موجود نیست |
| PRE-2 | Baseline فقط‌خواندنی روی VPS توسط CONTROL (SentinelX) شامل سلامت سرویس‌ها، migration head، موجودی داده به‌تفکیک جدول و feed، منابع، اقلام باقی‌مانده **به‌علاوهٔ نسخهٔ اولیهٔ Fact Requirements Matrix** | انجام نشده |
| PRE-3 | ثبت این Blueprint به‌صورت `REGISTERED / REFERENCE ONLY` در `docs/blueprint/` (الگوی `DOC-P3-001`/`DOC-P4-001`) | انجام نشده |
| PRE-4 | تصمیم Owner برای `PD-1` تا `PD-5` و ثبت **verbatim**؛ ثبت `BND-1` و `PROC-1` توسط CONTROL به‌صورت رکورد governance که در PRE-6 به `PH-P5.md` منتقل می‌شود | باز |
| PRE-5 | disposition هر `PRQ` (تحویل مصوب یا `UNAVAILABLE` صریح) | باز |
| PRE-6 | `PH-P5.md` رسمی، ثبت Registry و Checkpoint (الگوی PH-P4)، Owner Directive | انجام نشده |
| PRE-7 | شفاف‌سازی migration head: `[REPO]` فایل‌های `0001`–`0006` در مخزن‌اند؛ طبق Ledger مهاجرت `0006` مستقیماً با SQL از راه SentinelX روی دیتابیس اعمال شده ولی **mount مهاجرت/سورس روی VPS از مخزن عقب است** (`revision` مستقر = `fb7d984`). همگام‌سازی پیش از اولین migration جدید لازم است و شماره‌گذاری migrationهای `PRQ-1` و P5 توسط CONTROL هماهنگ می‌شود | باز |

## 6. تصمیم‌ها: چه کسی باید تصمیم بگیرد؟

**دسته‌بندی** `[PROP]`: **Owner** = تصمیم محصول/Scope/اختیار؛ **Owner یا CONTROL با تفویض صریح** = تصمیم semantic در حد اختیار معماری (سابقه: `ADR-QUANTITATIVE-001` با تفویض Owner)؛ **CONTROL-procedural** = رویهٔ اجرایی طبق معماری؛ **Arch-derived** = مرز مشتق از معماری که CONTROL ثبت می‌کند و فقط انحراف از آن نیاز به Owner دارد.

| کد | موضوع | دسته |
|---|---|---|
| PD-1 | مسیر اجرای `PRQ-1` (عملیاتی‌کردن و persist facts P4) | Owner |
| PD-2 | (2a) فعال‌سازی trade/depth و MEXC/نماد دوم (`PRQ-2`)؛ (2b) قابلیت Derivatives (`PRQ-3`) | Owner |
| PD-3 | Venue، محصول slice و نمادها | Owner |
| PD-4 | مدل استقلال (Stage-1 Only یا Stage-2 رسمی) | Owner یا CONTROL با تفویض صریح |
| PD-5 | مرز «ریاضی جدید» و معنای Historical Pattern | Owner یا CONTROL با تفویض صریح |
| BND-1 | صفر LLM در P5 | Arch-derived |
| PROC-1 | فرآیند تعریف هدف عملکرد | CONTROL-procedural |

### PD-1 — مسیر `PRQ-1`
واقعیت: بند ۷. گزینه‌ها:
- **A — کار محدود، افزودنی و governed تحت مرز P4** با Task Order(های) مجزا و Owner Directive، مطابق سابقهٔ `TO-P4-009` با حفظ closure؛ توقف اگر شواهد G-4 متأثر شود. *(پیشنهاد Blueprint)*
- **B — change-control رسمی** (ADR/ACR یا بازگشایی کنترل‌شده) اگر CONTROL تشخیص دهد A برای کار افزودنی کافی نیست یا شواهد G-4 را متأثر می‌کند.
- **C — محدودکردن specialistها به facts موجود** (اکثر specialistها `UNAVAILABLE_INPUT` می‌شوند و G-5 به‌شدت محدود می‌ماند).
- **گزینه‌های ارائه‌نشده:** (۱) انجام این کار داخل Stepهای P5، چون مرز مالکیت را نقض می‌کند (بند ۴.۱)؛ (۲) محاسبهٔ درون‌فرایندی بدون persist، چون `INV-V2-007` و Replay/Provenance را نقض می‌کند.

### PD-2 — داده واقعی
- **2a (trade/depth، MEXC، نماد دوم):** A — فعال‌سازی governed توسط مرز P2 با Runtime Authorization *(پیشنهاد Blueprint)*؛ B — `UNAVAILABLE_INPUT` با شواهد واقعی + OQ/DD.
- **2b (Derivatives):** A — افزودن قابلیت از مسیر ADR/ACR/change-control P2 (هزینه: سرویس Futures جدا از adapter Spot)؛ B — `UNAVAILABLE_INPUT` + DD با trigger. Blueprint توصیه‌ای ندارد؛ تصمیم Owner است.

### PD-3 — Venue، محصول و نمادها
واقعیت: slice فاز ۴ روی Binance Spot `BTCUSDT` اجرا شد؛ adapterهای فعلی Spot هستند و استفاده از Futures نیازمند قابلیت جدید است (`PRQ-3`). پیشنهاد `[PROP]`: Slice اصلی Binance Spot `BTCUSDT` + MEXC برای همان instrument + یک نماد دوم با پروفایل نقدشوندگی متفاوت. **CONTROL گزینه‌ها را از نظر فنی ارزیابی و پیشنهاد می‌کند؛ انتخاب نهایی دامنهٔ محصول/داده با Owner است.**

### PD-4 — مدل استقلال
معماری فقط خوشه‌بندی شواهد را می‌خواهد `[ARCH]` §16.3. گزینه‌ها: **A — Stage-1 Only** (هر specialist فقط Snapshot را می‌بیند) *(مدل پایهٔ این Blueprint)*؛ **B — Stage-2 «meta» رسمی و برچسب‌دار** برای تحلیل‌هایی که ذاتاً خروجی specialistها را می‌خوانند. `USR-14` هر دو مدل را پوشش می‌دهد (بند ۹). چون بر G-5 و P6 اثر دارد باید پیش از Task Order گام ۰۰۱ قطعی شود.

### PD-5 — مرز «ریاضی جدید»
پیشنهاد `[PROP]`: منطق P5 فقط **مقایسه، رتبه‌بندی، عضویت در مجموعه، طبقه‌بندی state و محاسبهٔ حسابی ساده (تفاضل/نسبت)** روی facts P4 و فیلدهای canonical با آستانه‌های Config؛ هر پنجرهٔ غلتان، تخمین‌گر آماری یا اندیکاتور جدید = ریاضی P4. بر این مبنا: الگوهای تک‌کندلی/دوکندلی به‌عنوان طبقه‌بندی مجازند؛ **Divergence اندیکاتور** در v1 خارج از دامنه (نیاز به series ثبت‌شده)؛ **Historical Pattern Reasoner** فقط تطبیق دقیق state tuple با شمارش رخداد و آخرین زمان، **بدون آمار نتیجه** (P9).

### BND-1 — صفر LLM در P5 (Arch-derived)
مبنا: `[ARCH]` §17 مالک provider abstraction، prompt isolation و budget را P6 می‌کند؛ §33 وابستگی معکوس ممنوع است؛ §42 provider را پشت adapter/config می‌خواهد؛ `[REPO]` manifest: `provider_or_market_credentials_allowed: false`. یک LLM-specialist در P5 یا وابستگی معکوس به P6 می‌سازد یا provider abstraction تکراری. **توجه:** معماری در §16.1 اشاره می‌کند «همهٔ specialistها LLM نیستند»، پس صفر LLM «الزام صریح» نیست بلکه نتیجهٔ dependency direction است. ۷ specialist با نام‌های Reasoner/Contrarian (`S-11`، `S-12`، `S-13`، `S-14`، `S-15`، `S-17`، `S-18`) در P5 **deterministic rule-based classifier** تفسیر می‌شوند؛ CONTROL این تفسیر را به‌صورت رکورد governance ثبت می‌کند (PRE-4) و در PRE-6 به `PH-P5.md` منتقل می‌کند. فقط انحراف (LLM در P5) نیاز به Owner/ACR دارد. ارتقا به AI در P6 مسیر رسمی جدا دارد.

### PROC-1 — هدف عملکرد (CONTROL-procedural)
مبنا: `[ARCH]` §2.1 (T6 = «Evidence-based tuning») و §34. هدف عددی از قبل حدس زده نمی‌شود (درس `DD-V2-P4-006-PERFORMANCE-TARGET`). رویه: workload و روش در Phase Definition تعریف؛ baseline در گام ۰۰۳ روی VPS اندازه‌گیری؛ CONTROL هدف‌ها را به‌صورت `TARGET` با فیلدهای §34 (`workload, environment, sample size, percentile, method, warm/cold, concurrency, threshold`) **پیش از** گام ۰۰۴ ثبت می‌کند؛ نتیجهٔ اندازه‌گیری هر گام حتی در صورت عدم تحقق ثبت می‌شود. Owner فقط اگر هدف جدیدِ ماهوی مخالف معماری پیشنهاد شود.

## 7. وضعیت شروع راستی‌آزمایی‌شده (Input Reality Baseline)

منبع هر ردیف در ستون آخر است. داده روی VPS از EXEC-LOG/AR-P4-015 آمده و `[UNVERIFIED]` است تا PRE-2.

| خانوادهٔ fact | موتور (کد) | در orchestrator | Persist شده | داده واقعی روی VPS | منبع |
|---|---|---|---|---|---|
| کندل canonical | P3 | — | جدول canonical | `156 = 116/31/9` (BTCUSDT Spot، snapshot لحظه‌ای؛ نماد دوم/MEXC ندارد) `[UNVERIFIED]` | AR-P4-015 §5 |
| Indicators | `indicators.py` (EMA/SMA/WMA/HMA، RSI، MACD، ATR، ADX، Bollinger، Supertrend، HV، ATR percentile، volume/RVOL، VWAP و …) | **فقط** `EMA(20 پیش‌فرض)`, `RSI(14)`, `ATR(14)` **روی سری primary** | فقط ۳ ردیف به‌ازای هر اجرای orchestration | ۳ ردیف | `orchestration/engine.py:9-11,48-50,90`؛ `persistence/quantitative.py:32-58` |
| Market Structure | `market_structure.py` | بله (اجرا) | فقط یک ردیف `ORCHESTRATION` با `event_count` و `state`؛ رویدادها و zoneها persist نمی‌شوند | ۱ ردیف | همان |
| Regime | `regime_venue.py` | بله | بله (payload شامل `htf`) | ۱ ردیف | همان |
| Multi-Timeframe | `align_higher_timeframe` | فقط alignment/zero-lookahead | HTF فقط داخل payload regime؛ بردار indicator/structure برای HTF ساخته نمی‌شود | — | `engine.py` |
| Volume Profile | `VolumeProfileEngine` (ورودی: `CanonicalTrade`) | خیر | جدول `volume_profile_sessions` هست (`0005`) ولی نوشته نمی‌شود | ردیفی نیست | `0005`؛ `TABLES` |
| Order Flow | `OrderFlowEngine` (ورودی: trade) | خیر | جدول ندارد | trade ندارد | migrationها |
| Derivatives | `DerivativesEngine` | خیر | جدول ندارد | مسیر acquisition ندارد | همان |
| Venue Evidence | `VenueEvidenceEngine` | خیر | خیر | داده MEXC ندارد | — |

**سایر واقعیت‌ها `[REPO]`:**
- **Series تاریخی:** هر اجرای orchestration فقط یک `as_of` را persist می‌کند؛ series تاریخی facts (لازم برای `S-14` و Divergence) وجود ندارد مگر اجرای per-candle-close/backfill (`PRQ-1`).
- **Acquisition:** adapterها Spot هستند؛ capabilityها `REST_BOOTSTRAP، LIVE_STREAM، INSTRUMENT_METADATA، ORDER_BOOK_SNAPSHOT، TRADES، CANDLES`؛ funding/OI/liquidations نیست؛ `fetch_trades` روی `/api/v3/trades` با `limit ≤ 1000` است (فقط trade های اخیر). MEXC صراحتاً Spot V3 است و Futures «خارج از این adapter» (`mexc.py:26-27`).
- **سرویس‌ها:** `collector` و `worker-ai` stub هستند (`runtime/service.py`).
- **Data Quality:** `DataQualityState` هفت مقدار دارد: `VALID/DEGRADED/STALE/INCOMPLETE/CONTRADICTORY/REJECTED/UNAVAILABLE`. `CapabilityState.UNSUPPORTED` در quality logic به `DataQualityState.UNAVAILABLE` با reason `provider_unsupported` نگاشت می‌شود (`contracts/quality.py:275-276`)؛ پس مفهوم «unsupported» **گم نشده** و افزودن enum لازم نیست.
- **اما:** `CanonicalRecord` فقط `VALID` را می‌پذیرد (`persistence/canonical.py`) و `data_quality_logs` (با `reason_codes`) فقط همراه درج موفق رکورد canonical نوشته می‌شود؛ در migrationها جدول quarantine/DLQ برای داده‌ٔ غیر-`VALID` نیست. یعنی reasonهای `unsupported/unavailable` در لایهٔ persisted فقط برای موارد `VALID` دیده می‌شوند و منبع این تمایز برای `S-10` باید در FRM مشخص شود (`PRQ-4`).
- **Migration:** فایل‌های `0001`–`0006` در مخزن؛ `0006` = `application_role_grant_hardening`.
- **Manifest:** `provider_or_market_credentials_allowed: false`؛ `no_provider_runtime_activity_without_explicit_authorization: true`.
- **عملکرد:** `DD-V2-P4-006-PERFORMANCE-TARGET` باز؛ diagnostic فاز ۴ (۱۰۰۰ کندل primary) ≈ `704.670 ms` با EMA `537.506 ms` و Market Structure `440.568 ms`.

## 8. فهرست ۱۸ Specialist (برچسب محلی، `[PROP]`)

همگی deterministic (`BND-1`) مگر ذکر دیگر. ستون «وابستگی» به `PRQ`ها ارجاع می‌دهد و ورودی را بر اساس **واقعیت بند ۷** می‌گوید.

| # | Specialist | گام | ورودی از Snapshot | وابستگی |
|---|---|---|---|---|
| S-10 | Data Quality Analyst | 003 | context کیفیت + capability declarations + `acquisition_state` (هرکدام که persisted است) | FRM؛ `PRQ-4` یا پذیرش محدودیت |
| S-01 | Technical Analyst | 004 | indicator facts به‌ازای timeframe | `PRQ-1` (اکنون فقط EMA20/RSI14/ATR14) |
| S-06 | Multi-Timeframe Analyst | 004 | facts هر timeframe | `PRQ-1` (facts HTF) |
| S-08 | Volatility Analyst | 004 | ATR/HV/percentile/bandwidth | `PRQ-1` (اکنون فقط ATR14 primary) |
| S-02 | Market Structure Analyst | 005 | events/zones | `PRQ-1` |
| S-11 | Price Action Reasoner | 005 | کندل‌های closed؛ zones برای `ZONE_REJECTION` | کندل موجود؛ zones: `PRQ-1` |
| S-12 | Liquidity Reasoner | 005 | liquidity zones؛ depth اختیاری | `PRQ-1` (+`PRQ-2` برای depth) |
| S-03 | Volume Analyst | 006 | volume facts | `PRQ-1` |
| S-17 | Volume Profile Reasoner | 006 | VP sessions | `PRQ-1` + `PRQ-2` (trade) |
| S-05 | Order Flow Analyst | 007 | delta/CVD/imbalance/absorption | `PRQ-1` + `PRQ-2` |
| S-04 | Derivatives Analyst | 007 | funding/OI/basis | `PRQ-3` (+ persist `PRQ-1`) |
| S-07 | Cross-Exchange Analyst | 008 | facts هر venue | `PRQ-2` (MEXC) + `PRQ-1` |
| S-09 | Risk Analyst | 008 | facts Snapshot (نه خروجی specialistهای دیگر) | `PRQ-1` (تدریجی؛ عوامل ناموجود = `UNAVAILABLE`) |
| S-18 | Market Regime Reasoner | 009 | regime persisted + `structure_state` (در payload) | **قابل‌اجرا با facts فعلی** `[REPO]` |
| S-14 | Historical Pattern Reasoner | 009 | series تاریخی state | `PRQ-1` (per-candle-close/backfill) |
| S-16 | Setup Validation | 009 | facts (چک‌لیست بولی) | `PRQ-1` |
| S-13 | Contrarian / Devil's Advocate | 010 | facts (طبق `PD-4`) | `PRQ-1` |
| S-15 | News / Event Reasoner | 010 | — | Contract-only: `SKIPPED` (`NO_NEWS_PROVIDER_CONFIGURED`) |

جمع = ۱۸؛ هر specialist دقیقاً یک بار.

**نکته:** با facts فعلی فقط `S-18`، بخشی از `S-10` و `S-15` (SKIPPED) کامل قابل‌اجرا هستند و `S-01` محدود؛ بقیه به `PRQ`ها یا disposition صریح وابسته‌اند (بند ۴.۳).

## 9. الزامات یکسان برای همهٔ گام‌ها (USR) `[PROP]`

هر Task Order باید صراحتاً به `USR-*` ارجاع دهد.

- **USR-01 (Rule 5):** هر Task Order «نیت حاکم» ADR-013 Rule 5 را به Producer می‌رساند: حداکثر استاندارد درستی، robustness، پوشش edge-case، عمق validation، مستندسازی و شواهد؛ نه حداقل لازم برای pass. CONTROL همین معیار را در Audit و Closure اعمال می‌کند؛ hedging نامحدود یا re-verification بدون شواهد جدید کوتاهی از این استاندارد است.
- **USR-02 (VPS در هر گام):** طبق بند ۱۰. هیچ گامی بدون شواهد VPS مربوط به دامنهٔ خودش `VERIFIED` نمی‌شود و کاری صرفاً برای «گام آخر» به VPS موکول نمی‌شود.
- **USR-03 (Data-first):** پیش از فعال‌سازی هر Step، هر ورودی مورد نیازش در Fact Requirements Matrix یکی از سه وضعیت را دارد: `AVAILABLE_PERSISTED` (روی VPS تأییدشده)، `PRQ_DELIVERED` (تحویل و verified توسط CONTROL)، `UNAVAILABLE_DISPOSITIONED` (تصمیم صریح + OQ/DD). وضعیت چهارم مجاز نیست؛ P5 هیچ ورودی را خودش نمی‌سازد.
- **USR-04 (Registry-first):** هر CTR/CMP/DB/WRK/QUE/CFG/TST/OBS/SEC/PERF/DEP در **همان گام** ساخته‌شدنش ثبت می‌شود، نه در پایان.
- **USR-05 (PostgreSQL واقعی):** هر جدول/grant با probe واقعی روی PostgreSQL اثبات شود (`has_table_privilege`, `has_column_privilege`، رد UPDATE/DELETE/TRUNCATE، trigger append-only). تست متنی SQL یا fake کافی نیست (درس `TO-P4-009`). هر جدول جدید صراحتاً `REVOKE` دارد.
- **USR-06 (مسیر runtime):** هر قابلیت از مسیر worker/queue تست شود، نه فقط فراخوانی مستقیم؛ کلید/timeframe/نماد نامعتبر رد شود؛ اگر HTTP دارد، تست wire-level.
- **USR-07 (Zero Lookahead):** Snapshot فقط facts با `knowledge_time <= as_of` دارد؛ تست property: تغییر داده‌های آینده خروجی را عوض نمی‌کند. الگوهای چندکندلی فقط پس از close کندل آخر (`pattern_time` = close؛ `confirmed_at` جدا از `detected_at`).
- **USR-08 (Determinism):** ورودی یکسان ⇒ خروجی بایت‌به‌بایت یکسان. Decimal، بدون float، canonical JSON، ترتیب پایدار. Golden vector برای هر specialist، تولیدشده از اجرای واقعی و freeze‌شده. زمان wall-clock (مدت اجرا) از `identity_hash` بیرون می‌ماند.
- **USR-09 (وضعیت صریح):** `SUCCESS/PARTIAL/INSUFFICIENT_DATA/UNAVAILABLE_INPUT/SKIPPED/DISABLED/FAILED/TIMEOUT` مجزا هستند؛ specialist غیرفعال با Config باز هم رکورد `DISABLED` تولید می‌کند. NaN/Inf ممنوع.
- **USR-10 (Config):** هر آستانه در `specialists.yaml` با رکورد کامل §26 (`SID, owner, source, default, allowed range, unit, environment scope, safety constraints, change procedure`)؛ Config نسخه دارد و در هر خروجی ثبت می‌شود؛ نمی‌تواند invariant را خاموش کند.
- **USR-11 (عملکرد):** هدف‌ها طبق `PROC-1` با فیلدهای §34 تعریف و روی VPS اندازه‌گیری می‌شوند؛ عدد بدون workload ممنوع است.
- **USR-12 (Observability):** طبق §28: معیارهای هر specialist، correlation id در لاگ‌ها، بدون secret؛ شواهد روی VPS.
- **USR-13 (امنیت):** read-only مطلق؛ بدون endpoint معاملاتی؛ بدون credential؛ secret هرگز در مخزن/چت/گزارش؛ Operational authority روی VPS فقط با CONTROL؛ Producer طبق `GOV-BOUNDARY-001` §1–§2.
- **USR-14 (اجبار استقلال) (مشروط به PD-4):**
  - اگر `PD-4 = A (Stage-1 Only)`: تست AST/import — ماژول هر specialist ماژول specialist دیگر را import نمی‌کند و به خروجی‌های ذخیره‌شدهٔ specialist دیگر دسترسی ندارد؛ کد مشترک فقط از کتابخانهٔ pure مشترک.
  - اگر `PD-4 = B (Stage-2)`: گراف وابستگی رسمی و برچسب‌دار مصوب؛ specialistهای Stage-2 فقط از فهرست مجاز Stage-1 می‌خوانند؛ چرخه ممنوع؛ همان تست AST برای اجرای گراف مصوب.
  - تا زمانی که `PD-4` ثبت نشده، **هیچ Task Order فعال نمی‌شود** که به این الزام وابسته باشد.
- **USR-15 (Worker/Queue):** هر worker و queue رکورد کامل §24.2 (`primary responsibility, inputs, outputs, queues, allowed dependencies, forbidden responsibilities, side effects, resource budget, retry policy, timeout, concurrency, failure isolation`) و §24.3 (`owner, producer, consumer, purpose, payload contract, ordering, retry, timeout, backlog limits, DLQ, idempotency, retention, drain/recovery`) دارد، با پاسخ صریح به overload.
- **USR-16 (استقلال Audit):** Producer فقط تا Build Report؛ CONTROL مستقل Audit می‌کند؛ اگر CONTROL کد Producer را اصلاح کند باید در Audit صریح افشا و مسیر بازبینی مستقل مشخص شود.
- **USR-17 (Closure Sync) (محدود به رکوردهای closure):** طبق ADR-012 به‌علاوهٔ machine read-back: parse همهٔ YAML/JSON حاکمیتی؛ اسکریپت تطبیق وضعیت‌ها **برای artifactها و رکوردهای مشمول closure همان Step/Phase** (`PH-P5`/Step/TO/BR/AR/رکوردهای registry تخصصی مرتبط/README/Checkpoint/`PH-P5.md`/هدر Task Order و Build Report)؛ برای آن رکوردها هیچ وضعیت lifecycle ناسازگار یا کهنه باقی نماند. (Stepهای بعدی `DEFINED / INACTIVE` و سایر رکوردهای نامرتبط مجازند ACTIVE/UNVERIFIED باشند.) Ledger فقط با append اصلاح شود. **این کار متعلق به CONTROL و در مرز closure است، نه بخشی از اجرای runtime.**
- **USR-18 (Migration):** شماره‌گذاری بعد از head (طبق PRE-7 و هماهنگی با `PRQ-1`)؛ `migrate.sh`، mount مهاجرت روی VPS و CI Docker harness در همان گام به‌روز شوند؛ همگام‌سازی سورس و migration mount روی VPS با revision گام جزو Boundary VPS است (درس `AR-P4-016`).
- **USR-19 (Stable ID):** شناسهٔ خودساخته ممنوع؛ فقط CONTROL/Registry.
- **USR-20 (ADR-013 R2 و Footer):** هر hand-off کامل و آمادهٔ ارسال در همان پاسخ (English → توضیح فارسی)؛ Footer در هر پاسخ اساسی.
- **USR-21 (کلاس‌های evidence):** هر ادعای verification با کلاس `E-*` (§32) مشخص شود؛ `E-LIVE` فقط با داده واقعی؛ داده synthetic هرگز به‌عنوان واقعی معرفی نشود.
- **USR-22 (Scope):** هیچ قابلیت P6+ و هیچ V1؛ ایده‌های خارج از scope فقط در OQ/DD.
- **USR-23 (Known Limitations):** پایان هر گام، فهرست محدودیت‌ها و مفروضات در Build Report/Audit (نسخهٔ کوچک §46).
- **USR-24 (چک‌لیست §49):** هر artifact مهم به ۲۴ پرسش §49 پاسخ دهد؛ در غیر این صورت `NOT READY FOR IMPLEMENTATION APPROVAL`.
- **USR-25 (جدید — availability ورودی):** هر Specialist Output تمایز زیر را با کدهای enumerated حفظ کند: `CAPABILITY_UNSUPPORTED` (Provider قابلیت ندارد)، `NOT_ACQUIRED` (قابلیت هست ولی داده جمع‌آوری نشده)، `PRQ_NOT_DELIVERED`، `DATA_QUALITY_<state>`. این کدها روی `DataQualityState.UNAVAILABLE + reason` نگاشت می‌شوند و **enum جدید در قرارداد P3/P4 ساخته نمی‌شود** (مگر با ACR جدا). منبع هر کد در Snapshot با provenance ثبت شود.

## 10. پروتکل VPS در هر گام

**اختیار:** فقط CONTROL، فقط با SentinelX (ADR-013 Rule 4، ADR-011)، و فقط در مرز صریح Task Order. **Operational authority** روی VPS (استقرار، اعمال migration روی runtime مستقر، تغییر سرویس، فعالیت Provider) فقط با CONTROL از طریق SentinelX است. Producer Development Workspace Access طبق `GOV-BOUNDARY-001` §1–§2 مجاز است و Operational Authority نیست؛ هر اقدام VPS-side Producer باید داخل محیط توسعهٔ مجازِ نام‌برده در Task Order باشد. `[REPO]` «توان فنی SentinelX» اجازه نیست؛ هر Task Order بخش «VPS Boundary» با فهرست عملیات مجاز دارد. هر Task Order که دسترسی شبکه‌ای به Provider لازم دارد **Runtime Authorization صریح** جدا دارد `[REPO]` (manifest).

**فهرست الزامی (VPS-1..VPS-12) برای هر گام، متناسب با دامنهٔ همان گام:**

| # | اقدام | شاهد |
|---|---|---|
| VPS-1 | همگام‌سازی سورس، migration mount، compose و image با revision گام؛ `git status` تمیز؛ hash فایل‌های runtime = revision | E-OPS |
| VPS-2 | اعمال migration(ها) به‌ترتیب؛ probe privilege/trigger به‌صورت assertion؛ اعمال مجدد idempotent | E-OPS، E-STRUCT |
| VPS-3 | استقرار/به‌روزرسانی سرویس‌ها؛ سلامت، restart count، اسکن ۶ ساعتهٔ لاگ | E-OPS |
| VPS-4 | اجرای **واقعی** با داده واقعی مسیر governed (بدون synthetic-as-real) روی slice و نماد دوم (از گام ۰۰۴ و بسته به disposition) | E-LIVE / E-REPLAY |
| VPS-5 | Replay قطعی روی VPS: ورودی یکسان ⇒ خروجی و `identity_hash` یکسان؛ درج دوم = ۰ | E-REPLAY |
| VPS-6 | سناریوی داده‌ناکافی **واقعی** (مثلاً ۴H با ۹ کندل برای EMA-200) ⇒ وضعیت صریح | E-FAILURE |
| VPS-7 | تزریق شکست/timeout کنترل‌شده و اثبات failure isolation | E-FAILURE |
| VPS-8 | restart/recovery worker با پیام pending؛ pending = 0، lag = 0 | E-FAILURE |
| VPS-9 | probe مسیر خواندن/API (اگر گام دارد) و رد mutation | E-INTEGRATION |
| VPS-10 | اندازه‌گیری عملکرد و منابع طبق workload تعریف‌شده (CPU/RAM/disk/queue) | E-OPS |
| VPS-11 | Hygiene: بدون container/فایل/probe باقی‌مانده؛ فهرست اقلام باقی‌مانده صریح | E-OPS |
| VPS-12 | **ثبت شواهد اجرا در EXEC-LOG** (اجباری). **هیچ تغییر lifecycle** (VERIFIED/COMPLETE/CLOSED)، بروزرسانی مجموعهٔ verified در Checkpoint یا ledger transition در این مرحله انجام نمی‌شود | E-OPS |

**مرز evidence در برابر closure `[PROP]`:**
- **اجازه‌شده حین Step (توسط CONTROL، فقط رکورد شواهد):** EXEC-LOG؛ رکورد evidence-addendum در Ledger که lifecycle را تغییر نمی‌دهد؛ transcription شواهد در registryهای تخصصی با وضعیت `TESTED / UNVERIFIED` و ارجاع مستقیم به شواهد (سابقه: `CHG-P4-STEP-006-CONTROL-CORRECTION-AND-RUNTIME-20260919` که Step را `ACTIVE` نگه داشت). به Checkpoint فقط در مرز activation/closure دست زده می‌شود.
- **فقط در مرز closure (CONTROL، پس از Audit مستقل):** انتقال lifecycle، Checkpoint، artifacts registry، README، registryهای تخصصی، اسناد status-bearing، registry موقت، Ledger و read-back نهایی (ADR-012 و `USR-17`). `VERIFIED` هرگز صرفاً به‌خاطر اجرای VPS ثبت نمی‌شود (`EXECUTED ≠ VERIFIED`).

**قاعدهٔ «عدم تعویق بی‌صدا»:** اگر داده واقعی برای یک خانواده در دسترس نباشد، گام باید (الف) وضعیت صریح `UNAVAILABLE` را روی VPS با شواهد واقعی نشان دهد، (ب) OQ/DD با trigger و مالک ثبت کند، و (ج) این محدودیت را در Audit و Handoff بیاورد. تعویق به «گام آخر» ممنوع است.

**Rollback/Recovery:** هر گام پیش از اعمال migration، نقطهٔ بازیابی (backup/dump) ثبت می‌کند؛ migrationها forward-only هستند و برگشت با بازیابی از backup یا migration اصلاحی جدید انجام می‌شود، نه ویرایش migration قدیمی.

## 11. تعریف‌های مشترک (Cross-Cutting) `[PROP]`

**Input Snapshot (`CTR-P5-INPUT-SNAPSHOT`).** تغییرناپذیر و hash‌دار؛ شامل `as_of`، instrument، venue(ها)، فهرست timeframeها (Config)، به‌ازای هر timeframe بستهٔ facts (هر fact با `record_id`, `identity_hash`, `knowledge_time`, `calculation_version`)، context کیفیت داده (از `DataQualityState` با منبع مشخص طبق `USR-25`)، `config_version`، `snapshot_hash`. فهرست خانواده‌های fact **Registry/Config-driven** است تا خانواده‌هایی که بعداً با `PRQ` می‌رسند بدون تغییر کد اضافه شوند. هیچ fact با `knowledge_time > as_of` وارد نمی‌شود.

**Specialist Output (`CTR-P5-SPECIALIST-OUTPUT`).** فیلدهای §16.5: `domain`, `findings` (`code`, `direction/state`, `severity`, `evidence_refs`), `evidence_refs`, `confidence` (Decimal در `[0,1]` + برچسب `LOW/MODERATE/HIGH` + `confidence_basis`)، `data_quality_status` (از `DataQualityState`؛ تمایز `unsupported` طبق `USR-25`)، `uncertainty`, `risk_flags`, `invalidation_evidence` (شرط‌های ماشین‌ارزیابی‌پذیر، نه متن آزاد)، `version_metadata` (منطق، قرارداد، Config، snapshot_hash)، و `input_availability` (فهرست کدهای `USR-25` به‌ازای ورودی‌های نایاب). `confidence` فقط در `SUCCESS/PARTIAL` مقدار دارد؛ در سایر وضعیت‌ها `null` و `confidence_impact` ∈ `NONE/REDUCED/EXCLUDED`.

**Taxonomy وضعیت:** `NOT_STARTED → RUNNING → {terminal} → REPORTED` با terminal ∈ `SUCCESS, PARTIAL, INSUFFICIENT_DATA, UNAVAILABLE_INPUT, SKIPPED, DISABLED, FAILED, TIMEOUT`؛ هر terminal کد دلیل enumerated دارد (مثل `NO_NEWS_PROVIDER_CONFIGURED`, `NO_BIAS_TO_CHALLENGE`, `HTF_HISTORY_INSUFFICIENT`, `CAPABILITY_UNSUPPORTED`, `PRQ_NOT_DELIVERED`).

**Evidence Ref (`CTR-P5-EVIDENCE-REF`).** `source_family`, `record_id`, `identity_hash`, `event_time`, `knowledge_time`, `timeframe`, `venue`. شناسهٔ خیالی ممنوع؛ هر `evidence_ref` روی DB واقعی resolve می‌شود.

**Immutability.** فقط INSERT؛ اصلاح = اجرای جدید. کلید هویت: `(specialist, snapshot_hash, config_version, code_version)`؛ اجرای تکراری بی‌اثر.

**DB.** `specialist_executions` (اجرا، وضعیت، دلیل، زمان‌بندی به‌عنوان telemetry خارج از identity) و `specialist_findings`، با ساختار مشابه جدول‌های P4 (`record_id`, `identity_hash UNIQUE`, `payload_json`) و trigger append-only الگوی migration `0003` و `REVOKE UPDATE, DELETE, TRUNCATE` برای `meylux_app`. سیاست رشد/نگهداری (§37) در Phase Definition.

**Independence Graph (`CTR-P5-INDEPENDENCE-GRAPH`).** نگاشت ثابت و Registry-based هر specialist به خوشهٔ اطلاعاتی (Price-derived, Volume/Trade-derived, Structure-derived, Derivatives-derived, Cross-Venue-derived, Quality-derived, History-derived) + `weight_hint` + سیگنال «تضاد درون‌خوشه‌ای». محاسبهٔ آماری همبستگی خارج از P5؛ وزن‌دهی نهایی مال P6.

**Worker/Queue.** `WRK-P5` specialist-orchestrator (Stage-1 موازی، یا مطابق گراف مصوب `PD-4`) و specialist-persistence؛ `QUE` برای snapshot-ready و DLQ؛ نام‌گذاری stream مطابق الگوی موجود. رکوردها طبق `USR-15`.

## 12. نمای کلی گام‌ها

| گام | عنوان | Specialistها | وابستگی به PRQ | VPS |
|---|---|---|---|---|
| 001 | Contract, Evidence Model, Config & Persistence Foundation | — | — | migration + probe |
| 002 | Input Snapshot Builder & Fact Availability Verification | — | مصرف خروجی PRQ (فقط‌خواندنی نسبت به P2/P3/P4) | خواندن داده واقعی + FRM |
| 003 | Runtime Harness & Reference Specialist | S-10 | FRM؛ `PRQ-4` یا پذیرش محدودیت | سرویس + E2E |
| 004 | Group A — Technical, MTF, Volatility | S-01, S-06, S-08 | `PRQ-1` | کامل |
| 005 | Group B — Structure, Price Action, Liquidity | S-02, S-11, S-12 | `PRQ-1` (+`PRQ-2` اختیاری) | کامل |
| 006 | Group C — Volume, Volume Profile | S-03, S-17 | `PRQ-1`, `PRQ-2` | کامل (یا UNAVAILABLE واقعی) |
| 007 | Group D — Order Flow, Derivatives | S-05, S-04 | `PRQ-1`, `PRQ-2`, `PRQ-3` | کامل (یا UNAVAILABLE واقعی) |
| 008 | Group E — Cross-Exchange, Risk | S-07, S-09 | `PRQ-2`, `PRQ-1` | کامل |
| 009 | Group F — Regime, Pattern, Setup | S-18, S-14, S-16 | `PRQ-1` (S-18: بدون وابستگی) | کامل |
| 010 | Group G — Contrarian, News/Event | S-13, S-15 | `PRQ-1` (طبق `PD-4`) | کامل |
| 011 | Evidence Independence Clustering | — | — | کامل |
| 012 | Integration, Multi-Symbol/Venue, Soak, Handoff & G-5 | همه | — | Verification یکپارچه + refresh زنده |

```text
PH-P4 (CLOSED) ──► [PRQ-1..4 در مرز مالک: P4/P2/P3، با Owner Directive]
                        │ (تحویل verified یا UNAVAILABLE صریح)
PRE-* ► 001 ► 002 ► 003 ► {004..010 هر Step پس از گیت PRQ خودش} ► 011 ► 012 ► G-5 ► PH-P6
```

گام‌های ۰۰۴ تا ۰۱۰ در **توسعه** می‌توانند موازی باشند، اما **استقرار و Verification روی VPS ترتیبی** است (یک تغییر runtime در هر زمان). **هیچ Step از نوع Feed Capability در P5 وجود ندارد.**

**ترتیب و سریال‌سازی:** Task Orderهای `PRQ` (مرز P4/P2/P3) و Stepهای P5 یک runtime مشترک روی VPS را تغییر می‌دهند. قاعدهٔ «یک تغییر runtime در هر زمان»، ترتیب استقرار همهٔ آن‌ها و شماره‌گذاری migrationها را CONTROL در Phase Definition تعیین می‌کند. Stepهای ۰۰۱ و ۰۰۲ به تحویل `PRQ`ها وابسته نیستند و در توسعه می‌توانند پیش یا همزمان با آن‌ها پیش بروند؛ گام ۰۰۳ نیز به «تحویل» PRQ وابسته نیست ولی به تصمیم دربارهٔ `PRQ-4` (تحویل یا پذیرش محدودیت) نیاز دارد. استقرار و Verification VPS همهٔ آن‌ها فقط طبق ترتیب مصوب انجام می‌شود.

## 13. جزئیات گام‌ها

### STEP-P5-001 — Contract, Evidence Model, Config & Persistence Foundation
**هدف:** زبان مشترک خروجی، پیش از هر specialist.
**تحویل:** قراردادها (بند ۱۱)؛ taxonomy؛ مدل confidence؛ اسکلت `specialists.yaml` و اعتبارسنجی Config؛ migration جدول‌های append-only؛ تست معماری استقلال طبق `USR-14`؛ زیرساخت golden vector؛ رکوردهای Registry برای همهٔ اقلام؛ رکوردهای CMP برای هجده specialist (`DESIGNED`).
**تست:** unit، contract، property (NaN/Inf)، PostgreSQL-محور برای grant/trigger.
**VPS:** VPS-1، 2، 11، 12 — migration روی دیتابیس واقعی، probe privilege و trigger، اعمال مجدد idempotent، موجودی صفر، نقطهٔ بازیابی.
**پذیرش:** جدول‌ها فقط INSERT می‌پذیرند؛ همهٔ قراردادها registered؛ هیچ specialist منطقی وجود ندارد.

### STEP-P5-002 — Input Snapshot Builder & Fact Availability Verification
**هدف:** ساخت Snapshot از **facts موجود و verified** و کشف زودهنگام شکاف‌ها؛ **بدون** تغییر در P2/P3/P4.
**تحویل:** (الف) Input Snapshot Builder؛ (ب) **Fact Requirements Matrix (FRM)** نهایی: به‌ازای هر specialist، هر fact با موتور P4، granularity، تعداد بار لازم (warm-up)، timeframe، اجباری/اختیاری، رفتار در نبود، و **منبع تمایز `unsupported/unavailable`**؛ (ج) تأیید FRM روی VPS: برای هر fact یکی از سه وضعیت `USR-03`؛ (د) سیاست رشد/نگهداری (§37).
**ممنوع:** اتصال موتور P4، فعال‌سازی acquisition، migration برای facts P4 (این‌ها `PRQ` هستند).
**VPS:** VPS-1، 3، 5، 6، 10، 11، 12 — فقط queryهای خواندنی و اندازه‌گیری؛ بدون دسترسی شبکه‌ای به Provider.
**پذیرش:** برای هر fact مورد نیاز وضعیت مستند؛ هیچ خانوادهٔ نامشخص باقی نماند؛ Snapshot روی داده واقعی موجود بازتولیدپذیر و hash پایدار.

### STEP-P5-003 — Runtime Harness & Reference Specialist (S-10)
**هدف:** مسیر End-to-End کامل از ابتدا (Walking Skeleton).
**تحویل:** اجراکنندهٔ Stage-1 (یا گراف مصوب) با bounded concurrency؛ timeout از Config؛ ایزوله‌سازی استثنا؛ ترتیب قطعی؛ idempotency؛ retry محدود (فقط خطای زیرساختی)؛ DLQ؛ پاسخ صریح به overload؛ writer append-only؛ مسیر خواندن؛ سرویس compose جدید (`worker-specialist`)؛ رکوردهای WRK/QUE/DEP/OBS/SEC؛ **S-10** با منابع تعریف‌شده در FRM: طبقهٔ کیفیت کلی (بدترین وضعیت)، فهرست ورودی‌های غیر-`VALID`، پرچم‌های `STALE_INPUT/INCOMPLETE_HISTORY/CONTRADICTORY_INPUT/UNAVAILABLE_INPUT`. اگر شواهد غیر-`VALID` در لایهٔ persisted نیست، S-10 همین را با `UNAVAILABLE_INPUT` و کد مربوط گزارش می‌کند و چیزی نمی‌سازد. fixtureهای تزریق شکست **فقط تست** (غیرفعال در Config تولیدی، برچسب `TEST_FIXTURE`، جزو پوشش نیست).
**VPS:** VPS-1 تا 12 کامل: Snapshot واقعی ⇒ پیام ⇒ worker ⇒ DB؛ restart با pending؛ DLQ؛ duplicate؛ overload؛ **baseline عملکرد/منابع** (ورودی `PROC-1`).
**پذیرش:** ردیف‌های S-10 با evidence ref قابل‌resolve؛ pending = 0؛ replay یکسان؛ baseline ثبت.

### STEP-P5-004 — Group A: Technical, Multi-Timeframe, Volatility
**گیت:** `PRQ-1` (facts به‌ازای هر timeframe).
**Facts لازم (طبق FRM):** EMA (دوره‌های Config؛ پیش‌فرض پیشنهادی 9/21/50/200 `[PROP]`)، RSI14، MACD 12/26/9، ADX14، Bollinger 20/2، bandwidth، ATR14، HV، ATR percentile، expansion ratio — به‌ازای هر timeframe (15M/1H/4H، بدون hard-code).
- **S-01:** `MA_ALIGNMENT`، `PRICE_VS_MA`، `MACD_STATE`، `RSI_ZONE`، `ADX_STRENGTH`، `BOLLINGER_POSITION` و squeeze با آستانهٔ bandwidth. Divergence: خارج از v1 (DD با trigger «series ثبت‌شدهٔ indicator»).
- **S-06:** همان قواعد pure از کتابخانهٔ مشترک (بدون import S-01) روی facts هر timeframe؛ خروجی `CONFLUENCE/CONFLICT/PARTIAL`؛ فقط HTF با `close_time <= primary.close_time`؛ نبود facts یک timeframe ⇒ آن timeframe `INSUFFICIENT_DATA` و کل `PARTIAL`.
- **S-08:** `LOW/NORMAL/HIGH` و `EXPANDING/CONTRACTING` با percentile و ratio؛ `HIGH_VOLATILITY` به‌عنوان risk flag.
**تست/VPS/پذیرش:** golden vector هر قاعده؛ مرزها (برابری آستانه)؛ property lookahead؛ تست مسیر worker؛ VPS-1..12؛ اجرای واقعی روی slice؛ سناریوی واقعی `INSUFFICIENT_DATA` (۴H با کندل ناکافی برای EMA-200)؛ resolve همهٔ evidence refها؛ replay یکسان؛ هیچ import بین specialistها (`USR-14`).

### STEP-P5-005 — Group B: Market Structure, Price Action, Liquidity
**گیت:** `PRQ-1` (events/zones persisted).
- **S-02:** state ساختاری غالب (حفظ `UNCONFIRMED`)، آخرین رویداد تأییدشده با `knowledge_time <= as_of`، رابطهٔ قیمت با سطح محافظت‌شده (تفاضل Decimal)، نزدیک‌ترین zoneهای mitigate‌نشده.
- **S-11:** `PIN_BAR`, `ENGULFING`, `INSIDE_BAR`, `ZONE_REJECTION` روی کندل‌های closed با آستانه‌های Config؛ `pattern_time` = close.
- **S-12:** نزدیک‌ترین liquidity zoneها، `SWEPT/UNSWEPT` از کندل‌های پس از تشکیل؛ تمرکز depth فقط اگر snapshot عمق موجود باشد؛ نبود آن ⇒ `PARTIAL`.
**VPS/تست/پذیرش:** مانند ۰۰۴ به‌علاوهٔ resolve هر `evidence_ref` به رویداد/zone واقعی persist‌شده و تست lookahead با `as_of` متفاوت.

### STEP-P5-006 — Group C: Volume, Volume Profile
**گیت:** `PRQ-1`، `PRQ-2` (trade).
- **S-03:** کلاس RVOL، پرچم spike/climax، تأیید حجمی حرکت آخرین کندل.
- **S-17:** موقعیت قیمت نسبت به Value Area (`INSIDE/ABOVE/BELOW`)، نزدیک‌ترین سطح POC/VAH/VAL/HVN/LVN و فاصله؛ بازگشت به POC جلسهٔ قبل فقط با ≥۲ session persist‌شده وگرنه `INSUFFICIENT_DATA`.
**VPS:** اجرای واقعی روی trade واقعی governed؛ اگر disposition = `UNAVAILABLE`، وضعیت `UNAVAILABLE_INPUT` واقعی + OQ/DD (بدون synthetic).

### STEP-P5-007 — Group D: Order Flow, Derivatives
**گیت:** `PRQ-1`، `PRQ-2` (S-05)؛ `PRQ-3` (S-04).
- **S-05:** تفسیر facts persist‌شدهٔ delta/CVD/imbalance/absorption؛ وضعیت `UNAVAILABLE/LIMITED_DATA` موتور P4 **بدون تغییر** منتقل می‌شود؛ مقایسهٔ علامت تغییر CVD با قیمت فقط با series ثبت‌شده.
- **S-04:** طبقهٔ funding (Config)، علامت velocity، ربع‌های OI-delta × price-change (برچسب کیفی)، وضعیت basis؛ نبود داده canonical ⇒ `UNAVAILABLE_INPUT` (هرگز حدس).
**VPS:** طبق disposition؛ حتی در `UNAVAILABLE` شواهد واقعی وضعیت صریح روی VPS الزامی است.

### STEP-P5-008 — Group E: Cross-Exchange, Risk
**گیت:** `PRQ-2` (MEXC) و `PRQ-1`.
- **S-07:** مقایسهٔ facts محاسبه‌شده جداگانه برای هر venue (state ساختار، regime، اختلاف close، نسبت‌ها) با خروجی `ALIGNED/DIVERGENT` و ارجاع شواهد؛ بدون spread قابل‌اجرا، fee یا مفهوم Opportunity.
- **S-09:** طبقهٔ ریسک ساختاری کیفی `LOW/ELEVATED/HIGH` از **facts Snapshot** (نه از خروجی S-06/S-08/S-04)؛ عوامل مؤثر با evidence ref و فهرست عوامل `UNAVAILABLE`؛ بدون امتیاز عددی تجمیعی.
**VPS:** داده MEXC واقعی برای همان instrument؛ اجرای دو venue؛ اثبات قطع‌نشدن مسیر با شکست یک venue (`INV-V2-008`).

### STEP-P5-009 — Group F: Regime, Historical Pattern, Setup Validation
- **S-18** (بدون وابستگی به PRQ): سازگاری `CONSISTENT/CONFLICTING` بین regime رسمی P4 و `structural_state` (هر دو از Snapshot)؛ هرگز پیش‌بینی regime بعدی.
- **S-14** (گیت `PRQ-1`): تطبیق **دقیق** state tuple در تاریخچهٔ همان instrument با `knowledge_time <= as_of`؛ خروجی: تعداد رخداد، زمان آخرین رخداد، عمق تاریخچه؛ **بدون آمار نتیجه**؛ `INSUFFICIENT_DATA` زیر حداقل تاریخچهٔ Config.
- **S-16** (گیت `PRQ-1`): چک‌لیست versioned در Config با معیارهای بولی روی facts (نه خروجی specialistهای دیگر)؛ هر معیار `PASS/FAIL/UNKNOWN` با شواهد؛ بدون تصمیم معاملاتی.
**VPS:** تاریخچهٔ کافی از داده واقعی؛ اگر ناکافی است، وضعیت واقعی ثبت شود.

### STEP-P5-010 — Group G: Contrarian, News/Event
- **S-13 (طبق `BND-1`/`PD-4`):** روی همان Snapshot، «bias» را با قاعدهٔ deterministic از facts می‌سازد (regime + structural_state + trend fact)، سپس facts مخالف را به‌صورت `counter_evidence` با evidence ref فهرست می‌کند؛ bias خنثی ⇒ `INSUFFICIENT_DATA` با `NO_BIAS_TO_CHALLENGE`. تحلیل تناقض بین specialistها = P6.
- **S-15:** Contract و Harness کامل؛ خروجی `SKIPPED` با `NO_NEWS_PROVIDER_CONFIGURED`؛ فعال‌سازی آینده فقط با Task Order/ADR جدا.
**VPS:** شواهد واقعی هر دو رفتار؛ معیار `SKIPPED` از `FAILED` متمایز.

### STEP-P5-011 — Evidence Independence Clustering
**تحویل:** `CTR-P5-INDEPENDENCE-GRAPH` ثبت‌شده؛ نگاشت هر ۱۸ specialist؛ `weight_hint`؛ سیگنال تضاد درون‌خوشه‌ای (سیگنال مستقل، نه finding جدید)؛ تست اینکه EMA/MACD/RSI (Technical/MTF/Volatility) یک خوشه‌اند و «اکثریت کاذب» تولید نمی‌شود.
**VPS:** اجرای واقعی روی خروجی‌های persist‌شدهٔ گام‌های قبل؛ replay.

### STEP-P5-012 — Integration, Multi-Symbol/Venue, Soak, Handoff & G-5
**نکتهٔ کلیدی:** اولین استقرار روی VPS نیست؛ **Verification یکپارچه** است.
**گیت:** «refresh زنده» به Runtime Authorization صریح و مسیر acquisition governed (طبق `PRQ-2` یا یک مسیر یک‌بارمصرف مصوب) نیاز دارد. در نبود آن، refresh به‌عنوان Known Limitation ثبت می‌شود و ادعای E-LIVE برای تازگی داده مطرح نمی‌شود.
**تحویل:** اجرای واقعی هر ۱۸ دامنه با وضعیت واقعی هرکدام؛ refresh زنده برای اثبات نبود وابستگی به fixture کهنه؛ replay قطعی سراسری؛ failure injection؛ سناریوی «داده ناکافی»؛ soak محدود با منابع (E-SOAK)؛ آزمون‌های استقلال؛ بازرسی نبود منطق P6؛ بستهٔ Handoff §46؛ closure sync توسط CONTROL با machine read-back.
**پذیرش:** بند ۱۴.

## 14. Definition of Done و شواهد G-5

### 14.1 معیار معماری `[ARCH]` §31 (G-5)
`specialist contracts` • `independence rules` • `failure isolation` • `evidence provenance`. هیچ gate صرفاً به‌خاطر وجود کد بسته نمی‌شود.

### 14.2 معیارهای پیشنهادی Blueprint `[PROP]` (فقط پس از ثبت در `PH-P5.md` الزام‌آورند)

1. Contract Integrity — قراردادها versioned و verified (E-CONTRACT).
2. Full Domain Coverage — هجده specialist در Registry؛ هرکدام با وضعیت واقعی روی VPS و دلیل مستند (E-LIVE، E-FAILURE). *(وضعیت `UNAVAILABLE_DISPOSITIONED` پذیرفته است، به شرط شواهد و OQ/DD.)*
3. Determinism — golden vector + replay روی VPS (E-UNIT، E-REPLAY).
4. Independence Enforcement — طبق `USR-14` (E-STRUCT، E-CONTRACT).
5. Failure Isolation — تزریق شکست/timeout روی VPS (E-FAILURE).
6. Evidence Traceability — هر finding حداقل یک ref قابل resolve روی DB (E-INTEGRATION).
7. Confidence/Quality Separation — بازرسی و تست schema.
8. Independence Clustering — گراف ثبت‌شده و هر ۱۸ نگاشت‌شده.
9. Immutable Persistence — UPDATE/DELETE/TRUNCATE رد می‌شود؛ probe روی PostgreSQL واقعی و VPS (E-OPS).
10. Observability — معیارها و لاگ‌ها روی VPS (E-OPS).
11. No Cross-Phase Leakage — بازرسی کد؛ **و بازرسی اینکه P5 هیچ منطق P2/P3/P4 نساخته است**.
12. Configuration-Driven Thresholds — هیچ آستانهٔ hard-code.
13. Multi-Symbol/Venue — طبق `PD-3`/`PD-2` (اگر disposition = `UNAVAILABLE`، شواهد واقعی همان وضعیت).
14. Performance — هدف‌ها طبق `PROC-1` تعریف، اندازه‌گیری و ثبت؛ عدم تحقق صریحاً گزارش (E-OPS).
15. Real-Data Vertical Slice — مسیر P3→P4→P5 با داده واقعی و بستهٔ P6-ready (E-LIVE).
16. VPS Completeness — برای هر گام شواهد VPS-1..12 مربوطه.
17. Closure Sync — ADR-012 + machine read-back (`USR-17`).
18. G-5 — با همهٔ شواهد بالا و بدون claim بی‌شواهد (§32).

**بستهٔ Handoff P5→P6 (§46):** source/destination phase، gate بسته، commit تأییدشده، artifactهای verified، open questions، known limitations، required assumptions، registry sync، evidence bundle، next permitted task.

## 15. ثبت ریسک‌ها

| ریسک | کاهش |
|---|---|
| ورودی‌های P4 در runtime ناقص است | `PRQ-1` در مرز P4 + FRM + گیت (بند ۴.۳) |
| کار افزودنیِ `PRQ-1` شواهد G-4 را عوض کند | محدودیت‌های `PRQ-1`؛ توقف و گزارش؛ re-baseline صریح توسط CONTROL |
| نبود trade/derivatives واقعی | `PRQ-2/3`؛ disposition `UNAVAILABLE` با شواهد؛ تعویق بی‌صدا ممنوع |
| شواهد کیفیت غیر-`VALID` در persisted نیست | `PRQ-4` یا محدودیت ثبت‌شدهٔ S-10 |
| کندی Decimal با ۱۸ specialist | baseline در ۰۰۳، `PROC-1`، اندازه‌گیری هر گام |
| نقض استقلال به‌خاطر ارتباط ضمنی | `USR-14` + `PD-4` |
| Drift بین مخزن و VPS | VPS-1 در هر گام؛ PRE-7 |
| تصادم شماره migration بین `PRQ-1` و P5 | هماهنگی CONTROL (PRE-7، `USR-18`) |
| privilege بیش‌ازحد جدول‌ها | `USR-05` |
| انتشار مسئولیت P6 در P5 | بند ۳ + بازرسی |
| داده کهنه (snapshot لحظه‌ای) | refresh زنده در ۰۱۲ (مشروط به Runtime Authorization)؛ برچسب as-of |
| تبدیل پیشنهاد Blueprint به «واقعیت Checkpoint» | برچسب‌های منبع (بند ۰)؛ ثبت رسمی قبل از هر authority |

## 16. مراحل بعدی حاکمیتی

1. ثبت این Blueprint (PRE-3) و تولید Handoff P4→P5 (PRE-1) و Baseline + FRM اولیه (PRE-2) توسط CONTROL.
2. تصمیم Owner برای `PD-1, 2, 3` و (`PD-4, 5` یا تفویض صریح به CONTROL)؛ ثبت verbatim (PRE-4). ثبت `BND-1` و `PROC-1` توسط CONTROL.
3. disposition هر `PRQ` (PRE-5)؛ در صورت تصویب، Task Order(های) مجزا در مرز مالک با Stable ID توسط CONTROL.
4. Phase Definition `PH-P5.md` با الگوی `PH-P0..P4`، Acceptance Criteria مستقل هر گام و ثبت Stable IDها (PRE-6).
5. صدور Task Order گام ۰۰۱ فقط پس از تصویب Owner. هر Task Order شامل: بند Rule 5، ارجاع به USR، «VPS Boundary» صریح، Required Pre-Implementation Evidence و Stop Conditions.

**شرایط توقف در هر گام:** ورودی لازم موجود نیست و disposition مصوب ندارد؛ تعارض میان منابع authoritative؛ نیاز به تغییر معماری/Decimal policy/engine تأییدشده/P6؛ نیاز به ساخت قابلیت P2/P3/P4 داخل P5؛ تغییر ناخواستهٔ موجودی داده یا شواهد G-4؛ تهدید یکپارچگی migration؛ نیاز به تصمیم Owner.

---

## پیوست A — شواهد راستی‌آزمایی و محدودیت‌ها

**مستقیماً روی HEAD `c6f9f4e` بررسی شد:** `docs/state/CURRENT_CHECKPOINT.json`؛ `docs/phases/PH-P4.md`؛ `docs/task-orders/TO-P4-007.md` (§3، scope)؛ `docs/audits/AR-P4-015.md` (کامل)؛ `docs/architecture/MASTER_ARCHITECTURE_V2.md` (کامل)؛ `docs/state/CHANGE_LEDGER.yaml` (ورودی‌های P4 و post-closure)؛ `docs/environment/ENVIRONMENT_MANIFEST.yaml` (کلیدهای credentials/runtime)؛ `src/meylux/orchestration/engine.py`؛ `src/meylux/persistence/quantitative.py`؛ `src/meylux/persistence/canonical.py`؛ `src/meylux/runtime/service.py`؛ `src/meylux/acquisition/binance.py` و `mexc.py` (capabilities/`fetch_trades`/توضیح Spot)؛ `contracts/quality.py`؛ `contracts/data_quality.py`؛ `contracts/acquisition.py` (`AcquisitionState`، `CapabilityState`)؛ `migrations/versions/0001`–`0006` (فهرست و جدول‌های `0002/0003/0005`).

**تأیید نشده `[UNVERIFIED]`:**
- وضعیت زندهٔ VPS (سرویس‌ها، migration head واقعی، تعداد ردیف‌ها). اعداد `156` و `3/1/1` از `AR-P4-015`/EXEC-LOG است.
- اینکه `RawStagingRepository` رکوردهای غیر-`AVAILABLE` را persist می‌کند یا نه (قرارداد `AcquisitionState` این حالت‌ها را دارد ولی رفتار persist بررسی نشد؛ در FRM تعیین شود).
- کفایت `collector` واقعی P2 برای پنجرهٔ طولانی trade.
- دوره‌های پیش‌فرض (مثل EMA 9/21/50/200) و آستانه‌های Config پیشنهادی‌اند و در Task Order تثبیت می‌شوند.
- گزارش‌های Build/Audit تک‌تک Stepهای P4 و رجیستری‌های تخصصی خوانده نشد.
