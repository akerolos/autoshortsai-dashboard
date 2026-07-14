# 🚀 الدليل البسيط — تشغيل الـ Dashboard على GitHub Pages (بدون فيزا)

> ✅ الطريقة دي **مجانية 100%** ومش محتاجة أي كارت دفع.

---

## 🎯 الفكرة باختصار

```
GitHub Action (مشروع AutoShortsAI)
  ↓ يشغّل الـ pipeline يومياً
  ↓ يحدّث videos.db
  ↓ يبعت DB للـ dashboard repo
Dashboard repo (autoshortsai-dashboard)
  ↓ يستقبل الـ DB
  ↓ يولّد ملفات JSON
  ↓ ينشرهم على GitHub Pages
أنت تفتح اللينك → تشوف كل حاجة محدّثة ✨
```

---

## 📋 اللي هتعمله (5 خطوات بس)

### الخطوة 1: نزّل الـ ZIP الجديد

نزّل `autoshortsai-dashboard.zip` وفكّه على جهازك.

---

### الخطوة 2: ارفع الـ Dashboard على GitHub (لو عملته قبل كده، تجاوز)

لو رفعت الـ dashboard repo قبل كده، امسحه وارفع النسخة الجديدة:

```powershell
cd autoshortsai-dashboard
git init
git add .
git commit -m "Static dashboard"
git branch -M main
git remote add origin https://github.com/akerolos/autoshortsai-dashboard.git
git push -u origin main --force
```

> `--force` عشان ياستبدل القديم.

---

### الخطوة 3: فعّل GitHub Pages على الـ dashboard repo

1. افتح https://github.com/akerolos/autoshortsai-dashboard
2. روح على **Settings** → **Pages** (من القائمة الجانبية اللي على اليسار)
3. تحت **Build and deployment**:
   - **Source**: اختار **GitHub Actions** (مش Deploy from a branch)
4. ✅ خلاص! الـ GitHub Actions هتتبني تلقائياً وتنشر الـ dashboard.

**استنى 2-3 دقايق**، وبعدها هتلاقي لينك أخضر فوق الصفحة:
`https://akerolos.github.io/autoshortsai-dashboard/`

افتح اللينك — هتلاقي الـ Dashboard شغّال (ببيانات فاضية لحد ما الـ pipeline يشتغل).

---

### الخطوة 4: اعمل Personal Access Token لـ AutoShortsAI

عشان AutoShortsAI repo يقدر يبعت الـ DB للـ dashboard repo:

1. روح على https://github.com/settings/tokens?type=beta
2. اضغط **Generate new token**
3. الإعدادات:
   - **Token name**: `Dashboard Sync`
   - **Expiration**: `90 days`
   - **Repository access**: اختار **"Only select repositories"** → اختار `autoshortsai-dashboard`
   - **Permissions** → **Repository permissions** → **Contents** → **Read and write**
4. اضغط **Generate token**
5. **انسخ الـ token** (يبدأ بـ `github_pat_...`)

---

### الخطوة 5: ضيف Secrets لـ AutoShortsAI repo

1. افتح https://github.com/YOUR_USERNAME/autoshortsai-main (أو اسم مشروعك)
2. روح على **Settings** → **Secrets and variables** → **Actions**
3. اضغط **New repository secret** وضيف 2 secrets:

| Name | Value |
|------|-------|
| `DASHBOARD_REPO_TOKEN` | الـ token اللي نسخته في الخطوة 4 |
| `DASHBOARD_REPO` | `akerolos/autoshortsai-dashboard` (غيّر `akerolos` ليوزر نيمك) |

---

### الخطوة 6: انسخ ملفات الـ integration لمشروع AutoShortsAI

من الـ ZIP، هتلاقي مجلد `integration/autoshortsai-main/` فيه:
- `main.py` (معدّل)
- `.github/workflows/daily_run.yml` (معدّل)

**استبدل نفس الملفات في مشروعك:**

```
autoshortsai-main/
├── main.py                              ← استبدل ده
└── .github/workflows/daily_run.yml      ← استبدل ده
```

ارفع التعديلات:
```powershell
cd autoshortsai-main
git add .
git commit -m "Add dashboard sync"
git push
```

---

### الخطوة 7: شغّل الـ workflow!

1. روح على https://github.com/YOUR_USERNAME/autoshortsai-main/actions
2. اختار **AutoShortsAI Daily Run**
3. اضغط **Run workflow** → **Run workflow**
4. استنى 5-10 دقايق لحد ما يخلص

بعد ما يخلص:
- ✅ الـ DB هتتبعت تلقائياً للـ dashboard repo
- ✅ الـ dashboard repo هيبني الـ JSON تلقائياً
- ✅ GitHub Pages هيتحدّث تلقائياً

افتح اللينك: `https://akerolos.github.io/autoshortsai-dashboard/`

🎉 **هتلاقي كل بياناتك ظاهرة!** الفيديوهات، الـ logs، الـ charts، كل حاجة.

---

## 🔄 إيه اللي بيحصل كل يوم تلقائياً؟

| الوقت | الحدث |
|------|------|
| (اللي أنت محدده) | Cloudflare يطلب من GitHub Actions يشغّل AutoShortsAI |
| + 5-10 دقايق | الـ pipeline يشغّل، ينتج 5 فيديوهات، يرفعهم على YouTube |
| + 1 دقيقة | الـ DB تتبعت للـ dashboard repo |
| + 1-2 دقيقة | الـ dashboard repo يبني الـ JSON وينشرهم على GitHub Pages |
| بعدها | تفتح اللينك وتشوف كل حاجة محدّثة |

---

## 🚨 مشاكل محتملة وحلولها

### مشكلة: الـ dashboard بيفتح بس فاضي
- تأكد إن الـ GitHub Action على AutoShortsAI اشتغل بنجاح (Actions tab)
- شوف logs الـ Action — لازم تلاقي `Dashboard update triggered!`
- استنى دقيقة كاملة عشان الـ dashboard repo يبني

### مشكلة: GitHub Pages مش شغّال
- روح على Settings → Pages على dashboard repo
- تأكد إن Source = **GitHub Actions**
- شوف Actions tab — لازم تلاقي workflow اسمه "Build Static Dashboard" اشتغل

### مشكلة: "Resource not accessible" في GitHub Action
- الـ token مش عنده صلاحيات كافية
- اتأكد إنك اخترت `Contents: Read and write` لما عملت الـ token
- اتأكد إنك اختارت `autoshortsai-dashboard` repo في `Repository access`

### مشكلة: الـ dashboard بيظهر فيها "0" لكل الإحصائيات
- ده طبيعي في أول مرة (مفيش فيديوهات لسه)
- شغّل الـ workflow مرة واحدة وانتظر
- بعد ما يخلص، حدّث الصفحة

---

## 📞 لو وقفت في أي خطوة

ابعتلي:
1. اسم الخطوة اللي وقفت فيها
2. screenshot للخطأ (لو فيه)
3. الـ logs من GitHub Actions (Actions tab → اضغط على الـ run الفاشل)

وأنا هساعدك فوراً! 🚀
