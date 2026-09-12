بله. این بار بررسی را صرفاً برای «تأیید شش Step موجود» انجام ندادم؛ سعی کردم ببینم اگر هدف نهایی Meylux V2 این است که در پایان پروژه یک موتور Market Intelligence واقعاً قابل اعتماد، قابل بازپخش، قابل توضیح و قابل استفاده بسازیم، آیا شش Step فعلی دقیقاً بهترین مرزبندی هستند یا باید درون آنها اصلاحات مهمی انجام شود.
اسناد را دوباره در چند سطح cross-check کردم: Master Architecture، نقشه جامع اختصاصی Phase 4، جزئیات artifact/contract/database/test، invariantهای V2، Vertical Slice، G-4، و حتی شواهد مربوط به Stepهای قبلی Phase 4. نتایج نشان می‌دهد شش Step اساساً درست هستند، اما برای اینکه roadmap واقعاً «نقشه راه نهایی و حداکثری» باشد، باید محتوای درونی آنها بسیار دقیق‌تر از نسخه CONTROL تعریف شود.
یک نکته هم از همین ابتدا مهم است: بعضی اسناد File Library، Stepهای 1 تا 5 را در مقاطعی COMPLETE یا DONE گزارش کرده‌اند، در حالی که اسناد دیگری صراحتاً می‌گویند G-4 هنوز با evidence عملیاتی بسته نشده است. بنابراین من وضعیت فعلی اجرا را از roadmap جدا نگه می‌دارم و هیچ‌کدام از آن گزارش‌های تاریخی را به‌عنوان مجوز اجرای امروز تلقی نمی‌کنم. خود اسناد نیز برای Step 5 تأکید کرده‌اند که وضعیت live باید مجدداً بررسی شود. 

---

# نتیجه نهایی من
من شش Step Phase 4 را حفظ می‌کنم، اما با یک اصلاح اساسی:
شش Step فعلی تعداد و مرزبندی مناسبی دارند؛ مشکل در خود Stepها نیست، بلکه در این است که نسخه قبلی آنها بعضی مسئولیت‌های بسیار مهم را بیش از حد فشرده کرده بود.
بنابراین پیشنهاد نهایی من:
text
PH-P4
│
├── STEP 1
│   Quantitative Foundation,
│   Contracts, Numeric Policy & Golden Vector Freeze
│
├── STEP 2
│   Technical Indicators,
│   Statistical & Volatility Engine
│
├── STEP 3
│   Deterministic Market Structure Engine
│
├── STEP 4
│   Volume Profile,
│   Order Flow & Derivatives Engine
│
├── STEP 5
│   Deterministic Market Regime Engine
│   + Venue-Aware Quantitative Track
│
└── STEP 6
    Quant Orchestration,
    Multi-Timeframe Runtime,
    Persistence, API,
    Replay & G-4 Closure

اما اجازه بدهید هرکدام را با دقت بسیار بیشتری باز کنیم.

---

# PHASE 4 — مأموریت واقعی
Phase 4 نباید صرفاً یک «Indicator Library» باشد.
ماموریت واقعی آن این است:
تبدیل Canonical, Quality-Aware Market Data به مجموعه‌ای از Facts کمی، آماری و ساختاری که deterministic، reproducible، provenance-aware و قابل استفاده توسط تمام لایه‌های بعدی Meylux باشند.
این تعریف با معماری کاملاً منطبق است: ورودی Phase 4 داده Canonical Phase 3 است و خروجی آن indicator vectors، structural states، Volume Profile، Order Flow و Market Regime است. 
در نتیجه:
text
P3 = Is this data trustworthy?

P4 = What deterministic facts can be extracted
     from this trustworthy data?

P5 = What does the collection of those facts imply?

P6 = What should the intelligence system conclude?

این separation یکی از مهم‌ترین نقاط موفقیت Meylux است.

---

# اصول غیرقابل مذاکره Phase 4
چهار اصل موجود در نقشه جامع باید به‌عنوان ستون فقرات تمام شش Step حفظ شوند:
1. Determinism
همان input باید همان output را تولید کند.
2. Purity
هسته محاسباتی نباید به:
• network
• database
• filesystem
• wall clock
• mutable global state
وابسته باشد.
3. Zero NaN / Inf
کمبود داده نباید به:
text
NaN
Inf
0 مصنوعی

تبدیل شود.
بلکه باید explicit باشد.
4. Golden Vector Freeze
هر تابع عمومی ریاضی باید reference input/output داشته باشد و تغییر عددی آن تحت change control قرار گیرد.
این چهار اصل صریحاً در نقشه Phase 4 آمده‌اند. 
و INV-V2-002 نیز deterministic baseline را الزام می‌کند. 

---

## STEP 1
Quantitative Foundation, Contracts, Numeric Policy & Golden Vector Freeze
این Step در نسخه قبلی با عنوان:
Feature Contracts + DB Models + Golden Vectors
بیان شده بود.
من این عنوان را کمی دقیق‌تر می‌کنم، چون Numeric Policy آن‌قدر مهم است که نباید در متن Step گم شود.

---

# هدف Step 1
ساخت «زمین بازی ریاضی» Phase 4.
قبل از اینکه حتی یک indicator پیچیده ساخته شود، باید مشخص باشد:
• ورودی معتبر چیست؟
• خروجی معتبر چیست؟
• precision چگونه مدیریت می‌شود؟
• insufficient history چگونه نمایش داده می‌شود؟
• rounding چگونه انجام می‌شود؟
• golden vector دقیقاً چه چیزی را freeze می‌کند؟
• feature چگونه provenance خود را حفظ می‌کند؟
• خروجی چگونه version می‌شود؟

---

### 1. Quantitative Contracts
حداقل contract domains موجود در معماری:
• Indicator
• Market Structure
• Volume Profile
• Order Flow
• Regime
هستند. نقشه جامع نیز همین contractها را در Step 1 قرار داده است. 
Contract باید فقط type definition نباشد؛ باید semantics را نیز تثبیت کند.
مثلاً:
text
value
status
reason
source_ref
timestamp
timeframe
symbol
venue/context
version

البته هر فیلد فقط در صورت پشتیبانی توسط قرارداد حاکم باید اضافه شود؛ اینجا نباید SID جدید اختراع کنیم.

---

### 2. Numeric Policy
این یکی از مهم‌ترین نقاط کل Phase 4 است.
اسناد Phase 4 صراحتاً یک Open Decision برای numeric policy دارند:
Hybrid internals + Decimal boundary
و Golden Vector باید مقدار quantized را referee قرار دهد. 
پس در formalization باید این موارد تعیین و ثبت شوند:
• internal numeric representation
• boundary representation
• precision
• rounding
• quantization
• comparison tolerance در جایی که مجاز است
• serialization
این بخش نباید implementation preference مخفی باشد.

---

### 3. Mathematical Primitives
قبل از indicatorها باید primitiveهای مشترک قابل اعتماد باشند:
• rolling calculations
• averages
• weighted calculations
• smoothing
• standard deviation
• percentile/ranking
• accumulation
• normalization
این کار باعث می‌شود هر indicator مجدداً منطق پایه را به شکل متفاوت پیاده نکند.

---

### 4. Insufficient History
این موضوع باید در foundation حل شود، نه اینکه هر indicator جداگانه تصمیم بگیرد.
مثلاً:
text
NOT ENOUGH HISTORY
        ↓
explicit status
        +
reason
        +
no numeric fabrication

نقشه Phase 4 صراحتاً None + reason را برای insufficient history مقرر کرده است. 

---

### 5. Golden Vector System
Golden Vector فقط چند تست عددی نیست.
باید تبدیل شود به:
text
Input fixture
      ↓
Function
      ↓
Expected output
      ↓
Exact comparison
      ↓
Regression protection

و برای public mathematical functions قابل توسعه باشد.
در سند موجود، حتی 8 vector اولیه و runner برای Step 1 مشخص شده‌اند. 

---

### 6. Golden Vector Freeze
این باید یکی از مهم‌ترین governance boundaries کل P4 باشد:
text
Math changed
     ↓
ACR/change control
     ↓
new reference calculation
     ↓
golden vector review
     ↓
approval

نه اینکه Producer صرفاً expected value را برای سبز کردن تست تغییر دهد.

---

### 7. Database Model Foundation
Step 1 باید مدل‌های persistence را نیز تعریف کند، ولی نباید orchestration runtime را هنوز وارد کند.
Architecture پنج DB object اصلی دارد:
text
DB-P4-001 calculated_indicator_vectors
DB-P4-002 market_structure_events
DB-P4-003 market_structure_zones
DB-P4-004 volume_profile_sessions
DB-P4-005 market_regime_states

این objects در معماری به‌عنوان authoritative outputs تعریف شده‌اند. 

---

# خروجی واقعی Step 1
در پایان Step 1 باید داشته باشیم:
text
Quantitative contracts
+
Numeric policy
+
Mathematical foundation
+
Golden vector infrastructure
+
Persistence model foundation
+
Deterministic output semantics

اما هنوز:
Indicator production pipeline کامل نداریم.

---

## STEP 2
Technical Indicators, Statistical & Volatility Engine
این Step باید تمام quantitative features مبتنی بر price/time/volume را تکمیل کند.
نسخه قبلی آن را فقط «Technical Indicators» نامیده بود. من Statistical & Volatility را عمداً به نام آن اضافه می‌کنم، چون در اسناد Phase 4 این بخش‌ها واقعاً جزو همین engine هستند.

---

### A. Moving Averages
طبق معماری:
• EMA 9
• EMA 21
• EMA 50
• EMA 200
• SMA
• WMA
• HMA
این موارد در architecture صریحاً آمده‌اند. 

---

### B. Momentum
• RSI 14
• MACD 12/26/9

---

### C. Trend / Volatility
• ATR 14
• ADX 14
• Bollinger Bands 20/2
• Supertrend

---

### D. Volatility / Statistical Features
از roadmap تفصیلی:
• Historical Volatility
• Realized/related volatility calculations
• ATR percentile
• volatility expansion/compression inputs

---

### E. Volume / Activity
• Volume SMA
• RVOL
• volume spike
• volume climax
اینها در Step 2 roadmap تفصیلی صراحتاً آمده‌اند. 

---

### F. VWAP
• VWAP
• Anchored VWAP
Anchored VWAP باید anchor را explicit input بگیرد؛ نباید وابسته به clock پنهان سیستم باشد.

---

### G. مهم‌تر از خود Indicatorها: رفتار آنها
برای هر indicator باید:
Warm-up behavior
مشخص باشد.
Missing input behavior
مشخص باشد.
Zero-volume behavior
مشخص باشد.
Invalid input behavior
مشخص باشد.
Length alignment
مشخص باشد.
Lookahead
صفر باشد.
Reproducibility
قطعی باشد.
Golden vector
وجود داشته باشد.

---

# خروجی Step 2
یک library کامل از quantitative price/volume/volatility facts:
text
Canonical candles
      ↓
Technical / Statistical Engine
      ↓
IndicatorVector

که هنوز وارد Market Structure یا AI interpretation نشده است.

---

## STEP 3
Deterministic Market Structure Engine
این Step از نظر من حساس‌ترین Step محاسباتی Phase 4 است.
چون indicators معمولاً formula-driven هستند، اما market structure دارای semantic ambiguity بیشتری است.

---

### 1. Swing Detection
معماری برای swingها نیازمند:
text
HH
HL
LH
LL

است.
Roadmap فعلی نیز 5/5 fractal swing detection را مشخص کرده است. 
اما نکته مهم:
تشخیص swing نباید باعث lookahead پنهان شود.
اگر الگوریتم برای تأیید یک swing به candleهای آینده نیاز دارد، باید semantics آن explicitly تعریف شود.
نباید یک swing تاریخی را طوری نمایش دهیم که گویی در همان لحظه قابل مشاهده بوده است.
این مسئله مستقیماً با INV-V2-009 ZERO LOOKAHEAD مرتبط است. 

---

### 2. Structure State
سپس:
text
HH / HL / LH / LL
        ↓
Trend / Range interpretation

اما این interpretation هنوز باید deterministic باشد.

---

### 3. BOS
Break of Structure.
باید دقیقاً مشخص باشد:
• چه levelی شکسته شده؟
• close یا wick؟
• چه timestampی event محسوب می‌شود؟
• duplicate event چگونه جلوگیری می‌شود؟
• invalidation چگونه رخ می‌دهد؟

---

### 4. CHOCH
همان discipline.

---

### 5. MSS
Market Structure Shift نیز باید با state machine مشخص شود.

---

### 6. Total State Machine
یکی از بهترین تصمیم‌های موجود در roadmap:
هر bar باید یک state مشخص داشته باشد و ambiguity نباید با حدس حل شود.
در صورت ambiguity:
text
UNCONFIRMED

این موضوع در roadmap اختصاصی Phase 4 صریحاً آمده است. 
این را من حتماً حفظ می‌کنم.

---

### 7. Fair Value Gap
FVG باید lifecycle داشته باشد:
text
ACTIVE
   ↓
PARTIALLY_MITIGATED
   ↓
FULLY_MITIGATED

و transitionها deterministic باشند.

---

### 8. Order Blocks
• detection
• lifecycle
• invalidation
• breaker transition

---

### 9. Breakers
Breaker باید نتیجه deterministic transition از structure/zone state باشد، نه یک interpretation AI.

---

### 10. Liquidity Pools
Liquidity zones/pools نیز باید به‌عنوان structural facts ثبت شوند، نه opportunity signals.

---

# آزمون بسیار مهم Step 3
دو سناریوی pinned در roadmap موجود است:
text
60-candle trend-with-BOS
60-candle reversal-with-CHOCH

و باید event-by-event بازتولید شوند. 
من پیشنهاد می‌کنم این نوع scenario test برای تمام stateful structure logic به یک اصل عمومی تبدیل شود:
text
input scenario
→ every event
→ every state transition
→ exact expected result

این برای جلوگیری از «درست بودن خروجی نهایی ولی غلط بودن مسیر» بسیار ارزشمند است.

---

## STEP 4
Volume Profile, Order Flow & Derivatives Engine
این Step در roadmap فعلی کاملاً درست است و من آن را حفظ می‌کنم؛ ولی باید سه engine واقعاً مستقل داشته باشد.
text
## STEP 4
│
├── Volume Profile
├── Order Flow
└── Derivatives


---

### A. Volume Profile
Architecture تأکید می‌کند:
Phase 4 sole owner of Volume Profile mathematics.
بنابراین نباید همان math بعداً در P5 یا P6 دوباره محاسبه شود. 
محاسبات:
• POC
• VAH
• VAL
• HVN
• LVN
و:
• session profile
• composite profile
در صورت وجود در contract.

---

Value Area
یکی از نقاطی که باید بسیار دقیق freeze شود:
text
70% value area

و algorithm انتخاب bins / expansion / tie-breaking باید deterministic باشد.
Roadmap صراحتاً golden test برای یک session با 200 trade و exact POC/VAH/VAL دارد. 
این بسیار خوب است و باید حفظ شود.

---

### B. Order Flow
حداقل:
• Bar Delta
• CVD
• Imbalance
• Absorption
Architecture این موارد را صریحاً تعریف کرده است. 

---

### CVD
CVD باید:
• deterministic
• monotonicity-aware
• replay-safe
باشد.
برای آن pinned trade set وجود دارد و property test نیز باید حفظ شود. 

---

### Imbalance
Threshold باید configuration-driven و governed باشد.
نباید Producer هنگام implementation آن را به‌صورت سلیقه‌ای انتخاب کند.

---

### Absorption
باید دقیقاً مشخص شود:
text
What constitutes absorption?

و چه داده‌ای برای آن لازم است.
اگر trade-level data کافی نباشد:
text
UNAVAILABLE / LIMITED_DATA

نه fabrication.

---

### D. Derivatives
محاسبات شامل:
• funding
• funding velocity/acceleration
• Open Interest
• OI delta
• basis
• mark/index relationship
است. معماری نیز funding velocity، OI delta و basis divergence را صریحاً آورده است. 
نکته بسیار مهم:
Phase 4 نباید خودش داده derivatives را invent یا reconstruct کند اگر input canonical آن موجود نیست.

---

# Step 4 خروجی
سه خانواده مستقل از evidence:
text
Volume Evidence
Order Flow Evidence
Derivatives Evidence

که بعداً P5 آنها را با سایر evidenceها ترکیب خواهد کرد.

---

## STEP 5
Deterministic Market Regime Engine + Venue-Aware Quantitative Track
اینجا یک اصلاح مهم نسبت به پیشنهاد قبلی CONTROL لازم است.
در roadmap رسمی، Step 5 با:
Market Regime Classifier & Cross-Venue Quantitative Engine
تعریف شده است. 
اما ACR-0008 هم‌زمان یک Venue Intelligence Track مستقل تعریف کرده که قرار است از P4 جدا بماند. سند ACR صریحاً می‌گوید این track در P4 ادغام نشود. 
بنابراین باید این دو را تفکیک مفهومی کنیم.

---

# بخش A — Market Regime
Regime engine باید deterministic باشد.
Roadmap فعلی 8 state را تعریف کرده:
text
TRENDING
RANGING
EXPANSION
COMPRESSION
HIGH_VOL
LOW_VOL
TRANSITION
ABNORMAL

و عوامل:
text
EMA 50/200
ATR percentile
BB width
structure bias

را ذکر کرده است. 

---

Hysteresis
این بخش برای من mandatory است.
بدون hysteresis:
text
A
B
A
B
A

با کوچک‌ترین تغییر رخ می‌دهد.
بنابراین:
text
candidate state
       ↓
confirmation
       ↓
official state

باید deterministic باشد.
و transient candidate باید قابل اثبات باشد؛ حتی در Build Report مربوط به Step 5، برای این مسئله vectorهای اضافی برای transient hysteresis ثبت شده‌اند. 

---

Regime نباید Forecast باشد
این بسیار مهم است.
Regime Engine نمی‌گوید:
بازار بالا خواهد رفت.
بلکه می‌گوید:
بر اساس قوانین مصوب، وضعیت فعلی بازار در این state قرار دارد.
این separation برای P5 و P6 حیاتی است.

---

# بخش B — Cross-Venue
اینجا باید بین دو مفهوم فرق بگذاریم:
Cross-Venue Quantitative Evidence
که می‌تواند در P4 برای evidence comparison وجود داشته باشد.
اما:
Venue Intelligence / Opportunity Engine
موضوع ACR-0008 است و به‌عنوان track مستقل تعریف شده است.
بنابراین:
text
P4 Step 5
=
venue-aware quantitative evidence

NOT

full arbitrage/opportunity engine

این distinction جلوی scope creep را می‌گیرد.
ACR-0008 نیز صراحتاً Venue Track را parallel و خارج از PH-P4 تعریف کرده است. 

---

## STEP 6
Quant Orchestration, Multi-Timeframe Runtime, Persistence, API, Replay & G-4
به نظر من این Step مهم‌ترین جایی است که نسخه CONTROL قبلی کمی بیش از حد فشرده بود.
چون Step 6 صرفاً:
Persistence + Worker + API
نیست.
بلکه اثبات operational integrity کل Phase 4 است.

---

# بخش A — Quant Engine Facade
تمام engineهای Step 2 تا 5 باید از یک execution boundary قابل کنترل استفاده کنند.
مثلاً:
text
Canonical Input
      ↓
Quant Engine Facade
      ↓
Technical
Structure
VP
Order Flow
Derivatives
Regime
      ↓
Quantitative Evidence

این facade نباید خودش منطق جدید ریاضی ایجاد کند.

---

# بخش B — Candle-Close Trigger
یکی از الزامات بسیار مهم:
فقط is_closed=True وارد محاسبات authoritative شود.
این در roadmap اختصاصی Phase 4 صریحاً آمده است. 
این موضوع باید هم:
• unit test
• integration test
• runtime test
داشته باشد.

---

# بخش C — Multi-Timeframe
Architecture و roadmap:
text
1M
5M
15M
1H
4H
1D

را برای worker و quantitative calculations مشخص کرده‌اند. 
اما Controlled Vertical Slice در معماری نهایی:
text
15M primary
1H
4H HTF

است. 
پس باید این دو را قاطی نکنیم:
• engine capability: چند timeframe
• acceptance slice: BTCUSDT 15M + 1H + 4H

---

# بخش D — Persistence
پنج authoritative object باید operationally وصل شوند:
text
calculated_indicator_vectors
market_structure_events
market_structure_zones
volume_profile_sessions
market_regime_states

معماری اینها را authoritative می‌داند. 
و باید:
• provenance
• identity
• idempotency
• timestamp
• symbol/timeframe context
• source linkage
را حفظ کنند.

---

# بخش E — Append-Only Boundary
یکی از architecture invariants مهم:
text
UPDATE/DELETE
     ↓
not permitted for authoritative canonical/quantitative truth

در معماری برای canonical data و Phase 4 persistence، append-oriented behavior و revoke UPDATE/DELETE برای application role ذکر شده است. 

---

# بخش F — Redis
Redis نباید تبدیل به durable truth شود.
معماری:
text
PostgreSQL / TimescaleDB
      = authoritative persistence

Redis
      = queue / stream / coordination / cache

این distinction باید در Step 6 verification نیز آزمایش شود.

---

# بخش G — Worker
Worker باید:
text
canonical closed candle event
        ↓
quant computation
        ↓
persistence
        ↓
feature event

را انجام دهد.
در roadmap queue و stream نیز مشخص شده‌اند:
text
stream:canonical:market_events
arq:queue:quant_heavy
stream:features:computed

و worker باید candle-close event را مصرف کند. 

---

# بخش H — API
API باید:
• read-only
• DB-backed
• provenance-aware
• quantitative-only
باشد.
حداقل خانواده endpointهای موجود در roadmap:
text
quant features
quant structure

است. 

---

# بخش I — Replay
من Replay را از Step 6 حذف نمی‌کنم.
چرا؟
چون purity Phase 4 عملاً برای Replay آینده P9 ساخته می‌شود.
باید بتوانیم:
text
Historical Input
      ↓
P4
      ↓
Output A

same Historical Input
      ↓
P4
      ↓
Output B

و:
text
A == B

داشته باشیم.
بدون:
• wall clock
• network
• database state
• mutable global state
• nondeterministic ordering

---

# بخش J — Zero Lookahead Harness
Replay باید مشخصاً ثابت کند که:
text
T

به:
text
T+1
T+2
...

دسترسی ندارد.
این موضوع برای:
• indicators
• swing detection
• BOS
• CHOCH
• MSS
• FVG
• regime
حیاتی است.
INV-V2-009 صراحتاً historical evaluation را از future information منع می‌کند. 

---

# بخش K — Performance
Performance باید measured باشد، نه ادعا.
Roadmap فعلی:
text
<5ms / indicator / 1000 bars

<50ms / full multi-timeframe vector

را به‌عنوان target تعریف کرده است. 
و این distinction بسیار مهم است:
text
TARGET
≠
GUARANTEE

تا وقتی evidence واقعی تولید نشده است.

---

# بخش L — Failure Testing
Phase 4 باید فقط happy path نداشته باشد.
حداقل:
text
short history
zero volume
unsorted input
missing data
invalid values
duplicate input
boundary values
large values
tiny values

باید آزمایش شوند.
Test architecture موجود نیز unit + golden + property + replay + failure + regression را مقرر کرده است. 

---

# بخش M — Security Boundary
نکته جالبی که در نقشه جامع آمده و به نظرم باید حتماً حفظ شود:
Quant computation باید:
• zero network egress
• zero subprocess
• no dynamic imports
• no secrets
داشته باشد و trade-probe coverage روی meylux/quant/** اعمال شود. 
این برای پروژه‌ای که باید strictly read-only باشد بسیار ارزشمند است.

---

# بخش N — G-4
G-4 نباید فقط:
unit tests green
باشد.
Architecture می‌گوید transition P4→P5 نیازمند math test suite کامل و zero deviation از math benchmarks است. 
Roadmap تفصیلی نیز G-4 را با مجموعه‌ای بسیار قوی‌تر تعریف می‌کند:
text
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

و در نسخه detailed حتی 167+N regression را به‌عنوان baseline evidence target ذکر کرده است. 
البته عدد test count باید به‌عنوان evidence واقعی ثبت شود، نه اینکه از roadmap به‌صورت پیشاپیش guarantee شود.

---

# یک نکته مهم درباره Step 5 و ACR-0008
این مورد را عمداً جدا می‌کنم چون ممکن است در آینده باعث confusion شود.
در یک سند، Cross-Venue Quantitative Engine داخل Step 5 آمده است؛ در ACR-0008، Venue Intelligence Track به‌صورت یک مسیر مستقل تعریف شده است.
بنابراین تفسیر صحیح من:
text
PH-P4
│
└── Step 5
      └── venue-aware quantitative evidence

در کنار:
text
PH-V1
│
└── Cross-Venue Opportunity Intelligence

و این دو نباید به یک engine تبدیل شوند.
ACR-0008 صراحتاً می‌گوید Venue Track در P4 fold نشود و parallel باشد. 
این separation از نظر معماری بسیار مهم است.

---

# حالا یک لایه مهم‌تر: Traceability
اگر بخواهیم در پایان پروژه واقعاً مطمئن باشیم P4 چیزی را جا نگذاشته، هر capability باید دقیقاً در یکی از Stepها قابل ردیابی باشد.

Capability
Step

Quant contracts
1

Numeric policy
1

Mathematical primitives
1

Golden vectors
1

DB model foundation
1

Moving averages
2

Momentum
2

ATR / ADX
2

Bollinger
2

Supertrend
2

HV / volatility
2

RVOL / volume activity
2

VWAP / Anchored VWAP
2

Swing points
3

HH/HL/LH/LL
3

BOS
3

CHOCH
3

MSS
3

FVG
3

Order Blocks
3

Breakers
3

Liquidity Pools
3

POC
4

VAH / VAL
4

HVN / LVN
4

Delta
4

### CVD
4

### Imbalance
4

### Absorption
4

Funding analytics
4

OI analytics
4

Basis
4

Regime classifier
5

Hysteresis
5

Regime provenance
5

Venue-aware quantitative evidence
5

Quant facade
6

Candle-close execution
6

Multi-timeframe worker
6

Persistence
6

Redis event boundary
6

Read-only API
6

Replay
6

Zero-lookahead harness
6

Performance measurement
6

Regression
6

G-4 evidence
6


این جدول از نظر من یکی از مهم‌ترین خروجی‌های این بازبینی است.

---

# وابستگی دقیق Stepها
من ترتیب خطی زیر را حفظ می‌کنم:
text
## STEP 1
   │
   ▼
## STEP 2
   │
   ▼
## STEP 3
   │
   ▼
## STEP 4
   │
   ▼
## STEP 5
   │
   ▼
## STEP 6
   │
   ▼
G-4
   │
   ▼
PHASE 5

اما این به معنی آن نیست که هر فایل در repository باید کاملاً sequential ساخته شود.
معنی آن این است که governance dependency این ترتیب را دارد.
مثلاً:
• test fixture preparation می‌تواند زودتر انجام شود؛
• documentation می‌تواند parallel باشد؛
• بعضی unit testها می‌توانند parallel توسعه یابند؛
• اما Step بعدی نباید روی contract یا behavior تأییدنشده Step قبلی بنا شود.
خود roadmap اختصاصی نیز همین execution order خطی را تعیین کرده است. 

---

# Vertical Slice را هم باید داخل P4 جدی بگیریم
Controlled Vertical Slice نهایی:
text
Binance Futures BTCUSDT
15M primary
1H
4H

است.
و مسیر:
text
P2 ingestion
→ P3 normalization
→ P4 quantitative/structure
→ P5 specialists
→ P6 AI
→ P8 presentation

تعریف شده است. 
پس P4 باید قبل از بسته‌شدن خود Phase ثابت کند که همین engine روی داده واقعی کار می‌کند، نه فقط روی fixture مصنوعی.
این یکی از تفاوت‌های مهم بین:
«کتابخانه ریاضی خوب»
و
«Quantitative Engine واقعی Meylux»
است.

---

# بنابراین Definition of Done واقعی Phase 4
من DoD را به 6 دسته تقسیم می‌کنم.
1. Mathematical Integrity
• فرمول‌ها درست
• golden vectors pinned
• regression protected
• numeric policy مشخص
• no silent math drift
2. Data Integrity
• canonical-only input
• provenance
• explicit insufficient data
• no fabrication
• no NaN/Inf
3. Temporal Integrity
• candle-close semantics
• zero lookahead
• replay determinism
• chronological correctness
4. Structural Integrity
• total state machines
• explicit UNCONFIRMED
• deterministic lifecycle
• event-by-event reproducibility
5. Operational Integrity
• persistence
• worker
• queues
• API
• idempotency
• read-only boundary
• failure isolation
6. Evidence Integrity
• unit
• golden
• property
• failure
• replay
• regression
• performance
• real-data vertical slice
• G-4 evidence bundle

---

# چیزی که نباید در Phase 4 اتفاق بیفتد
این‌ها را به‌عنوان hard scope boundary در roadmap نهایی نگه می‌دارم:
خارج از P4:
• AI reasoning
• LLM calls
• specialist interpretation
• contradiction analysis
• scenario synthesis
• Opportunity Score
• Analytical Confidence synthesis
• final decision support
• trade signals as intelligence decisions
• order execution
• portfolio management
Phase 4 فقط:
FACT GENERATION
است.
این دقیقاً همان separationای است که معماری V2 برای جلوگیری از واگذاری mathematical truth به AI ایجاد کرده است. 

---

# نسخه نهایی پیشنهادی من
اگر بخواهم این بررسی را در یک roadmap رسمی و فشرده خلاصه کنم، این نسخه را به‌عنوان بهترین candidate برای Formal Phase 4 Specification پیشنهاد می‌کنم:

Step
عنوان نهایی پیشنهادی
محور اصلی

1
Quantitative Foundation, Contracts, Numeric Policy & Golden Vector Freeze
قرارداد، precision، primitives، vectors، مدل‌های پایه

2
Technical Indicators, Statistical & Volatility Engine
MA، momentum، volatility، volume، VWAP

3
Deterministic Market Structure Engine
Swings، BOS، CHOCH، MSS، FVG، OB، Breakers، Liquidity

4
Volume Profile, Order Flow & Derivatives Engine
POC/VAH/VAL، HVN/LVN، Delta/CVD، Imbalance، Absorption، Funding/OI/Basis

5
Deterministic Market Regime Engine & Venue-Aware Quantitative Evidence
Regime، hysteresis، multi-factor state، venue-aware evidence

6
Quant Orchestration, Multi-Timeframe Runtime, Persistence, API, Replay & G-4 Closure
Worker، persistence، stream، API، replay، performance، regression، G-4



---

و یک حکم مهم Reviewer
بعد از این بازبینی، من توصیه نمی‌کنم Phase 4 را به 8، 10 یا 11 Step تبدیل کنیم.
دلیلش این است که شش Step موجود از نظر architectural boundaries بسیار خوب عمل می‌کنند.
اگر بیشتر خرد کنیم، احتمالاً همان مشکلی ایجاد می‌شود که در P2 دیدیم: capabilityها به Stepهای بیش از حد ریز تبدیل می‌شوند و governance سنگین می‌شود.
در مقابل، اگر کمتر از شش Step کنیم، مرزهای بسیار مهمی مثل:
text
Mathematics
vs
Indicators
vs
Structure
vs
Advanced Market Evidence
vs
Regime
vs
Operational Integration

از بین می‌روند.
بنابراین ۶ Step بهترین نقطه تعادل است.

---

# اما یک تفاوت مهم با Roadmap قبلی CONTROL
Roadmap قبلی CONTROL را رد نمی‌کنم؛ اتفاقاً ساختار اصلی آن درست است.
اصلاح من این است که:
شش Step همان شش Step باقی بمانند، اما Specification هر Step باید با عمق بالا و با acceptance boundary مستقل نوشته شود.
به‌خصوص:
Step 1 نباید فقط «contracts + DB + vectors» باشد؛ Numeric Policy و deterministic foundation باید explicit باشند.
Step 2 نباید فقط indicator list باشد؛ warm-up، precision، missing data، lookahead و golden behavior باید داخل آن باشد.
Step 3 باید یک state-machine discipline بسیار جدی داشته باشد.
Step 4 باید سه engine مستقل ولی یک Step governed باشد.
Step 5 باید Regime را از Venue Intelligence Opportunity Engine جدا نگه دارد.
Step 6 باید صرفاً integration نباشد؛ بلکه محل اثبات operational/replay/performance/G-4 کل Phase باشد.

---

# و در نهایت، مهم‌ترین خروجی این بازبینی
اگر این roadmap درست formalize و سپس واقعاً با evidence اجرا شود، Phase 4 در پایان نباید فقط بگوید:
«Meylux اندیکاتورهای EMA، RSI، MACD و ... دارد.»
بلکه باید بتوانیم بگوییم:
text
CANONICAL DATA
                          │
                          ▼
              ┌─────────────────────┐
              │ PHASE 4              │
              │                     │
              │ Mathematical Facts  │
              │ Technical Facts     │
              │ Structure Facts     │
              │ Volume Facts        │
              │ Flow Facts          │
              │ Derivatives Facts   │
              │ Regime Facts        │
              └──────────┬──────────┘
                         │
                         ▼
              DETERMINISTIC EVIDENCE
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       P5              P6              P9
   Specialists     AI Intelligence    Replay/
                                   Evaluation

و مهم‌تر از خود featureها:
هر Fact باید قابل محاسبه مجدد، قابل آزمون، قابل ردیابی به داده Canonical، فاقد future leakage و مقاوم در برابر silent mathematical drift باشد.
این دقیقاً همان چیزی است که Phase 4 را از یک technical-analysis library ساده به هسته کمی قابل اعتماد Meylux V2 تبدیل می‌کند.
اسناد معماری نیز همین جایگاه را برای P4 تعیین کرده‌اند: P4 باید quantitative features و structure را به‌صورت deterministic تولید کند و این خروجی‌ها ورودی لایه Specialist بعدی باشند. 
بنابراین verdict نهایی من:
ساختار ۶ گانه Phase 4 تأیید می‌شود؛ اما نسخه‌ای که در بالا ارائه کردم، از نظر من نسخه دقیق‌تر و کامل‌ترِ مناسب برای Formal Phase Establishment است.
این هنوز Phase Specification یا authorization اجرایی نیست؛ صرفاً بهترین execution roadmap پیشنهادی است. Stable IDهای جدید، Task Orderها، Artifactهای جدید، تغییر Contractها یا تغییر architecture باید در مرحله formal governance ایجاد/تأیید شوند.