# 🚀 دليل التثبيت الكامل — ربط AutoShortsAI بـ Dashboard

> **الموضوع كله في 3 مراحل:** نشر الـ Dashboard على الإنترنت → تعديل مشروعك → ربطهم ببعض.

---

## 📋 قبل ما تبدأ — احتياجاتك

| الحاجة | ليه محتاجها |
|--------|-------------|
| حساب GitHub | عندك بالفعل (عندك مشروع عليه) |
| حساب Render.com | للنشر المجاني للـ Dashboard |
| مشروع AutoShortsAI | عندك بالفعل |
| صبر 30 دقيقة | الموضوع كله مش هياخد أكتر من كده |

---

## 🎯 المرحلة الأولى: نشر الـ Dashboard على Render.com

### الخطوة 1: ارفع الـ Dashboard على GitHub

1. **افتح موقع GitHub** واعمل repo جديد:
   - اسم الـ repo: `autoshortsai-dashboard`
   - **Private** (مش public — عشان الكود بتاعك)
   - متحدّش `README` ولا `.gitignore` (إحنا عندنا)

2. **نزّل ملف الـ ZIP** اللي بعتهولك قبل كده (`autoshortsai-dashboard.zip`) وفكّه.

3. **داخل المجلد اللي فكّيته**، افتح Terminal واكتب:

```bash
cd autoshortsai-dashboard

# تهيئة Git
git init
git add .
git commit -m "Initial commit: AutoShortsAI Dashboard"

# اربط الـ repo بتاعك (غيّر اليوزر نيم)
git remote add origin https://github.com/YOUR_USERNAME/autoshortsai-dashboard.git
git branch -M main
git push -u origin main
```

### الخطوة 2: اعمل حساب على Render.com

1. روح على **https://render.com**
2. اضغط **Get Started** واعمل حساب بـ GitHub
3. authorize Render عشان يقدر يوصل لـ repos بتاعتك

### الخطوة 3: أنشئ Web Service جديد

1. من لوحة Render، اضغط **New +** → **Web Service**
2. اختار الـ repo: `autoshortsai-dashboard`
3. املأ الإعدادات:

| الحقل | القيمة |
|------|------|
| **Name** | `autoshortsai-dashboard` |
| **Region** | الأقرب ليك (مثلاً Frankfurt لو في أوروبا) |
| **Branch** | `main` |
| **Root** | `backend` (مهم!) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python run.py` |
| **Instance Type** | `Free` (كافي جداً للبداية) |

4. اضغط **Advanced** وضيف **Environment Variables**:

| Key | Value |
|-----|-------|
| `APP_ENV` | `production` |
| `APP_DEBUG` | `false` |
| `ASA_DATABASE_URL` | `sqlite+aiosqlite:///./data/autoshortsai.db` |
| `LOG_LEVEL` | `INFO` |
| `LOG_JSON` | `true` |
| `ENABLE_SEED` | `false` |
| `CORS_ORIGINS` | `["*"]` |
| `DASHBOARD_API_KEY` | (هنعمله في الخطوة الجاية) |

5. اعمل **Disk** للحفاظ على قاعدة البيانات:
   - اضغط **Add Disk**
   - **Name**: `dashboard-data`
   - **Mount Path**: `/opt/render/project/src/backend/data`
   - **Size**: `1 GB`

6. اضغط **Create Web Service** ←.Render ه يبدأ البناء (هياخد 2-3 دقايق).

### الخطوة 4: ولّد API Key سري

في الـ Terminal على جهازك، شغّل:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

هيطلعلك string طويل زي ده:
```
aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5
```

**انسخه** وارجع للوحة Render:

1. افتح الـ service بتاعك
2. روح على **Environment** → **Add Environment Variable**
3. **Key**: `DASHBOARD_API_KEY`
4. **Value**: الـ string اللي نسخته
5. **Save Changes**

Render هييعمل redeploy تلقائياً.

### الخطوة 5: اختبر الـ Dashboard

بعد ما الـ deploy يخلص (اللون يبقى أخضر):

1. Render هيدّيك لينك زي: `https://autoshortsai-dashboard-xxxx.onrender.com`
2. افتحه في المتصفح ←.هتلاقي الـ Dashboard فاضي (مفيش بيانات لسه)
3. **اختبار الـ API** — افتح Terminal:

```bash
# حفظ اللينك والـ key في متغيرات
export DASHBOARD_URL="https://autoshortsai-dashboard-xxxx.onrender.com"
export DASHBOARD_API_KEY="الـ key اللي عملته"

# اختبار الاتصال
curl -s "$DASHBOARD_URL/api/health"
# لازم يرجّع: {"status":"ok",...}

# اختبار الـ report endpoint
curl -s -X POST "$DASHBOARD_URL/api/v1/report/pipeline" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DASHBOARD_API_KEY" \
  -d '{
    "run_uid": "test-manual-001",
    "status": "completed",
    "target_videos": 5,
    "completed_videos": 5,
    "started_at": "2026-07-14T18:00:00Z",
    "finished_at": "2026-07-14T18:45:00Z",
    "execution_time_seconds": 2700,
    "stages": [
      {"stage_key": "content_engine", "stage_name": "Content Engine", "status": "completed", "progress": 100, "execution_time_seconds": 45.2}
    ],
    "videos": [
      {"title": "Test Video", "status": "published", "video_url": "https://youtube.com/watch?v=test", "category": "test"}
    ],
    "logs": [
      {"level": "INFO", "source": "system", "message": "Test report"}
    ]
  }'
```

لو رجّع `{"success": true, ...}` ←.**الـ Dashboard جاهز!** ✅

افتح اللينك في المتصفح تاني، هتلاقي البيانات ظهرت فيه.

---

## 🔧 المرحلة الثانية: تعديل مشروع AutoShortsAI

دلوقتي هتعدّل مشروعك الأصلي عشان يبعت تقارير للـ Dashboard.

### الخطوة 1: انسخ مجلد `dashboard/`

من ملف الـ ZIP اللي بعتهولك، فيه مجلد اسمه `integration/autoshortsai-main/dashboard/`.

1. **افتح مشروع AutoShortsAI** على جهازك
2. **انسخ مجلد `dashboard/`** كامل لمجلد المشروع الرئيسي:

```
autoshortsai-main/
├── ai/
├── brain/
├── database/
├── dashboard/        ← نسخة جديدة
│   ├── __init__.py
│   ├── reporter.py
│   ├── requirements.txt
│   └── generate_api_key.py
├── images/
├── ...
└── main.py
```

### الخطوة 2: استبدل `main.py` بتاعك

من ملف الـ ZIP، هتلاقي ملف `integration/autoshortsai-main/main.py`.

**استبدل الـ `main.py` الأصلي بالملف ده.**

> ⚠️ **مهم:** لو عملت تعديلات على `main.py` بتاعك، حطها في النسخة الجديدة. التعديلات اللي أنا عملتها مميزة بـ `# [DASHBOARD INTEGRATION]`.

### الخطوة 3: حدّث `requirements.txt`

افتح `requirements.txt` في مشروعك وأضف السطر ده في الآخر:

```
# Dashboard integration
requests>=2.28.0
```

### الخطوة 4: استبدل `daily_run.yml`

من ملف الـ ZIP، هتلاقي:
`integration/autoshortsai-main/.github/workflows/daily_run.yml`

**استبدل الملف الموجود عندك:**
`autoshortsai-main/.github/workflows/daily_run.yml`

### الخطوة 5: ارفع التعديلات على GitHub

```bash
cd autoshortsai-main

git add .
git commit -m "Add dashboard integration"
git push
```

---

## 🔗 المرحلة الثالثة: ربط GitHub Actions بالـ Dashboard

### الخطوة 1: ضيف Secrets لـ AutoShortsAI repo

1. افتح repo بتاع AutoShortsAI على GitHub
2. روح على **Settings** → **Secrets and variables** → **Actions**
3. اضغط **New repository secret** وضيف الـ secrets دي:

| Name | Value |
|------|-------|
| `DASHBOARD_URL` | اللينك بتاع الـ Dashboard من Render (مثلاً: `https://autoshortsai-dashboard-xxxx.onrender.com`) |
| `DASHBOARD_API_KEY` | نفس الـ API key اللي عملته في المرحلة الأولى |

> ✅ باقي الـ secrets (GEMINI_API_KEY, PEXELS_API_KEY, etc.) موجودة عندك بالفعل.

### الخطوة 2: اختبر الـ workflow يدوياً

1. على GitHub، روح على repo بتاع AutoShortsAI
2. اضغط **Actions** → **AutoShortsAI Daily Run**
3. اضغط **Run workflow** → **Run workflow**
4. استنى لحد ما الـ workflow يخلص (5-10 دقايق عادةً)

### الخطوة 3: شوف النتيجة في الـ Dashboard

بعد ما الـ workflow يخلص:

1. افتح لينك الـ Dashboard على Render
2. هتلاقي:
   - ✅ Pipeline Status: آخر run وكل مراحله
   - ✅ Today's Videos: الفيديوهات اللي اتعملت
   - ✅ Logs: كل اللي حصل أثناء الـ run
   - ✅ Charts: التحديثات اليومية

---

## 🎉 خلصت! إيه اللي بقى شغّال؟

| الحاجة | الوضع |
|--------|------|
| Dashboard على الإنترنت | ✅ متاح 24/7 من أي مكان |
| GitHub Actions بيبعت تقارير | ✅ تلقائياً بعد كل run |
| بيانات حقيقية (مش تجريبية) | ✅ كل فيديو في Dashboard موجود فعلاً |
| Logs حية | ✅ كل log في main.py بيظهر في الـ dashboard |
| Pipeline status | ✅ كل مرحلة وحالتها وزمنها |

---

## 🧪 اختبار سريع (لو حابب تتأكد قبل ما تشغل الـ workflow كامل)

في الـ Terminal على جهازك (لو عندك Python):

```bash
# في مجلد مشروع AutoShortsAI
export DASHBOARD_URL="https://autoshortsai-dashboard-xxxx.onrender.com"
export DASHBOARD_API_KEY="your-api-key"

python -c "
from dashboard import get_reporter

reporter = get_reporter()
print('Reporter enabled:', reporter.is_enabled())
print('Run UID:', reporter.run_uid)

# محاكاة run بسيط
reporter.stage_start('content_engine', 'Content Engine', 'Generating ideas')
reporter.stage_end('content_engine', status='completed', message='Done!')
reporter.add_video(
    title='Test Video from Local',
    status='published',
    video_url='https://youtube.com/watch?v=test',
    external_video_id='test-local-001',
    category='Test',
)
reporter.finish_run(status='completed')
reporter.send()
"
```

لو رجّع `Report sent successfully` ←.كل حاجة شغّالة صح! 🎉

افتح الـ Dashboard وشوف البيانات الجديدة ظهرت.

---

## 🚨 مشاكل شائعة وحلولها

### مشكلة 1: "Failed to send report" في GitHub Actions

**السبب المحتمل:**
- الـ `DASHBOARD_URL` أو `DASHBOARD_API_KEY` مش متظبطين في GitHub Secrets

**الحل:**
1. تأكد إن الـ secrets مكتوبة صح في GitHub (بدون مسافات في الآخر)
2. تأكد إن `DASHBOARD_URL` بدون `/` في الآخر (مظبوطة: `https://xxx.onrender.com` — غلط: `https://xxx.onrender.com/`)
3. شوف logs الـ GitHub Action فيه تفاصيل أكتر

### مشكلة 2: الـ Dashboard بيفتح بس فاضي

**السبب:** الـ reporter في `main.py` مش بيتبعت، أو الـ GitHub Action فشل.

**الحل:**
1. روح على GitHub Actions وشوف logs الـ workflow
2. دور على `[Dashboard]` في الـ logs — لازم تلاقي رسائل من الـ reporter
3. لو مفيش، تأكد إن `dashboard/__init__.py` و `dashboard/reporter.py` موجودين في مشروعك

### مشكلة 3: Render service بيقول "Build failed"

**السبب:** مشاكل في dependencies.

**الحل:**
1. شوف logs الـ build على Render
2. لو في خطأ `module not found`، اتأكد إن كل حاجة في `requirements.txt`
3. جرّب تشغيل `pip install -r requirements.txt` محلياً قبل ما ترفع

### مشكلة 4: الـ Dashboard بطيء

**السبب:** Render free tier بياخد وقت عشان "يصحى" لو مفيش traffic.

**الحل:**
- استنى 30 ثانية لأول request (ده طبيعي في free tier)
- لو عايز أداء أعلى، ارتقِ لـ **Starter plan** ($7/شهر)

---

## 📞 لو احتجت مساعدة

لو وقفت في أي خطوة، ابعتلي:
1. screenshot للخطأ
2. الـ logs (من GitHub Actions أو Render)
3. الخطوة اللي وصلتها

وأنا هساعدك تكمّل. 🚀

---

## 🎁 تحسينات مستقبلية (اختيارية)

بعد ما كل حاجة تشتغل، تقدر تضيف:

1. **YouTube Stats Fetcher** — يجلب views/CTR/retention حقيقية كل ساعة
2. **Telegram Notifications** — يبعتلك رسالة لو الـ pipeline فشل
3. **Manual Trigger Button** — زرار في الـ Dashboard يشغّل الـ GitHub Action
4. **Multi-channel Support** — لو عندك أكتر من قناة يوتيوب

بس الأول، خلّي الأساسيات تشتغل! 😊
