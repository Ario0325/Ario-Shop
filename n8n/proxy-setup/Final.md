# راهنمای کامل ستاپ و تست — آریو شاپ + n8n + Cloudflare Worker

## مشکل چیست؟

هاست PythonAnywhere (پلن رایگان) اجازه ارسال درخواست HTTP مستقیم به سرویس‌های خارجی مثل n8n.cloud را نمی‌دهد. در نتیجه Django نمی‌تواند webhook بفرستد.

## راه‌حل چیست؟

یک Cloudflare Worker به عنوان واسط (proxy) بین Django و n8n قرار می‌گیرد:

```
Django (PythonAnywhere)  →  Cloudflare Worker  →  n8n Cloud  →  ارسال ایمیل
```

Worker درخواست را بدون تغییر به n8n فوروارد می‌کند و پاسخ را برمی‌گرداند.

---

## معماری نهایی

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌──────────────┐
│  Django App         │────▶│  Cloudflare Worker       │────▶│  n8n Cloud   │
│  PythonAnywhere     │     │  quiet-field-a090.       │     │  (workflows) │
│                     │◀────│  mimoomim456.workers.dev │◀────│              │
└─────────────────────┘     └──────────────────────────┘     └──────┬───────┘
                                                                     │ SMTP
                                                                     ▼
                                                              ایمیل به کاربر
```

---

## فایل‌های تغییر یافته / ساخته شده

### فایل‌های جدید (پوشه `n8n/proxy-setup/`)

| فایل | توضیح |
|------|-------|
| `worker.js` | کد Cloudflare Worker — پروکسی شفاف |
| `wrangler.toml` | تنظیمات deploy کردن Worker |
| `n8n-project-context.md` | توضیحات پروژه برای هوش مصنوعی n8n |
| `Final.md` | این فایل — راهنمای کامل |

### فایل‌های تغییر یافته

| فایل | تغییر |
|------|-------|
| `Ario_Shop/settings.py` | آدرس‌های webhook به Cloudflare Worker تغییر کرد |
| `Accounts_Module/services.py` | `secret_token` به payload اضافه شد (برای تطبیق با workflow) |

---

## مرحله ۱: آپلود کد Worker در Cloudflare

### ۱.۱ نصب Wrangler (روی کامپیوتر محلی)

```bash
npm install -g wrangler
```

### ۱.۲ ورود به Cloudflare

```bash
wrangler login
```

مرورگر باز می‌شود → وارد اکانت Cloudflare شوید → اجازه دهید.

### ۱.۳ Deploy کردن Worker

```bash
cd n8n/proxy-setup/
wrangler deploy
```

بعد از deploy، آدرس Worker شما:
```
https://quiet-field-a090.mimoomim456.workers.dev/
```

### ۱.۴ تست سلامت Worker

```bash
curl https://quiet-field-a090.mimoomim456.workers.dev/
```

باید برگرداند:
```json
{"status":"ok","timestamp":"2026-06-15T..."}
```

---

## مرحله ۲: تنظیمات n8n

### ۲.۱ ورود به n8n

به آدرس `https://tjnryhbtgvrfdcs.app.n8n.cloud` بروید و وارد شوید.

### ۲.۲ ساخت SMTP Credential

1. از منوی چپ روی **Credentials** کلیک کنید
2. روی **Add Credential** کلیک کنید
3. **SMTP** را انتخاب کنید
4. اطلاعات زیر را وارد کنید:

```
Name:     Gmail SMTP
Host:     smtp.gmail.com
Port:     465
User:     bardiaabdi1393@gmail.com
Password: wokw kyci lswj uqqd
SSL/TLS:  true
```

5. روی **Save** کلیک کنید

### ۲.۳ ایمپورت Workflow

1. از منوی چپ روی **Workflows** کلیک کنید
2. روی **Import from File** کلیک کنید
3. فایل `n8n/proxy-setup/Django n8n (1).json` را انتخاب کنید
4. Workflow ایمپورت می‌شود

### ۲.۴ تنظیم SMTP در Workflow

روی هر ۳ نود ایمیل کلیک کنید و Credential را روی **Gmail SMTP** تنظیم کنید:

- **Send Verification Email** → Credential: Gmail SMTP
- **Send Password Reset Email** → Credential: Gmail SMTP
- **Send Order Confirmation Email** → Credential: Gmail SMTP

### ۲.۵ فعال‌سازی Workflow

 toggle بالای صفحه را روی **Active** قرار دهید.

### ۲.۶ غیرفعال کردن Workflow قدیمی

اگر workflow قبلی به نام «آریو شاپ - ایمیل احراز هویت» دارید، آن را **غیرفعال** کنید تا conflict ایجاد نشود.

---

## مرحله ۳: آپلود کد Django در PythonAnywhere

### ۳.۱ ورود به PythonAnywhere

به `https://www.pythonanywhere.com` بروید و وارد شوید.

### ۳.۲ آپلود فایل‌ها

فایل‌های زیر را آپلود کنید (جایگزین فایل‌های قبلی):

- `Ario_Shop/settings.py` — آدرس‌های webhook به Worker تغییر کرده
- `Accounts_Module/services.py` — `secret_token` اضافه شده

### ۳.۳ ریلود وب‌اپ

1. به تب **Web** بروید
2. روی دکمه **Reload** کلیک کنید

---

## مرحله ۴: تست کامل سیستم

### ۴.۱ تست Worker (مستقیم با curl)

**تست webhook احراز هویت:**
```bash
curl -X POST https://quiet-field-a090.mimoomim456.workers.dev/webhook/django-auth-event \
  -H "Content-Type: application/json" \
  -d '{"event":"register","email":"test@example.com","username":"test","code":"123456","secret_token":"ario-shop-secret-token","sender_email":"bardiaabdi1393@gmail.com"}'
```

پاسخ موفق: `{"status":"ok","message":"email sent"}`

**تست webhook سفارش:**
```bash
curl -X POST https://quiet-field-a090.mimoomim456.workers.dev/webhook/order-paid \
  -H "Content-Type: application/json" \
  -d '{"secret_token":"ario-shop-secret-token","order_id":1,"order_number":"TEST-001","customer_name":"test","customer_email":"test@example.com","payment_status":"paid","total_price":100000,"shipping_cost":0,"discount":0,"created_at":"2026-06-15T10:00:00","shipping_address":"test","items":[{"name":"محصول تست","quantity":1,"unit_price":100000,"total_price":100000}],"sender_email":"bardiaabdi1393@gmail.com"}'
```

پاسخ موفق: `{"status":"success","message":"Email sent successfully"}`

### ۴.۲ تست از طریق وب‌سایت

1. **ثبت‌نام کاربر جدید:**
   - به صفحه ثبت‌نام بروید
   - ایمیل وارد کنید و ثبت‌نام کنید
   - باید ایمیل کد تأیید بیاید

2. **بازیابی رمز عبور:**
   - روی «فراموشی رمز عبور» کلیک کنید
   - ایمیل خود را وارد کنید
   - باید ایمیل بازیابی بیاید

3. **تأیید سفارش:**
   - یک سفارش با پرداخت موفق ثبت کنید
   - باید ایمیل فاکتور بیاید

---

## عیب‌یابی

### Worker پاسخ نمی‌دهد
- مطمئن شوید `wrangler deploy` با موفقیت انجام شده
- با `curl https://quiet-field-a090.mimoomim456.workers.dev/` تست کنید

### n8n خطای 404 برمی‌گرداند
- مطمئن شوید Workflow در n8n **Active** است
- مطمئن شوید مسیر webhook دقیقاً `/webhook/django-auth-event` است

### n8n خطای 401 برمی‌گرداند (Unauthorized)
- مطمئن شوید `secret_token` در payload وجود دارد
- مقدار آن باید `ario-shop-secret-token` باشد

### ایمیل نمی‌آید
- تب **Executions** در n8n را چک کنید — آیا webhook دریافت شده؟
- SMTP Credential در n8n درست تنظیم شده؟
- پوشه Spam را چک کنید

### خطای timeout از Django
- Worker ممکن است timeout خورده باشد (n8n free tier بعد از بی‌فعالیتی sleep می‌کند)
- اولین درخواست بعد از sleep ممکن است ۱۰-۳۰ ثانیه طول بکشد

---

## ساختار فایل‌های پروژه

```
Ario/
├── Ario_Shop/
│   └── settings.py              ← آدرس‌های webhook به Worker تغییر کرد
├── Accounts_Module/
│   └── services.py              ← secret_token اضافه شد
├── Cart_Module/
│   └── services.py              ← بدون تغییر (قبلاً secret_token داشت)
├── n8n/
│   └── proxy-setup/
│       ├── worker.js            ← کد Cloudflare Worker
│       ├── wrangler.toml        ← تنظیمات deploy
│       ├── n8n-project-context.md ← توضیحات پروژه برای AI
│       ├── Django n8n (1).json  ← Workflow واقعی شما
│       └── Final.md             ← این فایل
└── env.example                  ← نمونه تنظیمات
```

---

## جریان داده (هر درخواست)

```
1. کاربر ثبت‌نام می‌کند
2. Django payload می‌سازد:
   {
     "event": "register",
     "email": "user@example.com",
     "username": "ali",
     "code": "847291",
     "secret_token": "ario-shop-secret-token",
     "sender_email": "bardiaabdi1393@gmail.com"
   }
3. Django requests.post() به Cloudflare Worker
4. Worker درخواست را به n8n.cloud فوروارد می‌کند
5. n8n:
   - secret_token را validate می‌کند
   - event را چک می‌کند → "register"
   - ایمیل تأیید با کد OTP ارسال می‌کند
   - پاسخ 200 برمی‌گرداند
6. Worker پاسخ را به Django برمی‌گرداند
7. Django موفقیت را لاگ می‌کند
```

---

## هزینه‌ها

| سرویس | پلن | هزینه |
|--------|------|-------|
| Cloudflare Workers | رایگان | ۱۰۰,۰۰۰ درخواست/روز |
| n8n Cloud | رایگان | محدود به تعداد اجرا |
| PythonAnywhere | رایگان | HTTP خروجی بلاک (با proxy حل می‌شود) |

---

## نکات امنیتی

- `secret_token` در هر دو webhook (auth + order) بررسی می‌شود
- Cloudflare Worker فقط مسیرهای مشخص را قبول می‌کند
- درخواست‌های GET به webhookها برگردانده نمی‌شوند (فقط POST)
