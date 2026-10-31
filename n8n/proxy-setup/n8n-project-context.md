# Ario Shop — توضیحات پروژه برای هوش مصنوعی n8n

## خلاصه پروژه

**آریو شاپ** یک فروشگاه آنلاین با Django 6.0 و رابط کاربری فارسی (راست‌به‌چپ) است. از n8n Cloud برای ارسال ایمیل‌های تراکنشی (کد تأیید، بازیابی رمز، فاکتور سفارش) استفاده می‌کند.

## معماری

```
Django (PythonAnywhere) → Cloudflare Worker (proxy) → n8n Cloud → SMTP → ایمیل کاربر
```

هاست PythonAnywhere اجازه اتصال مستقیم به n8n.cloud را نمی‌دهد. Cloudflare Worker به عنوان واسط عمل می‌کند.

## Webhook ها

### ۱. Auth Webhook — `/webhook/django-auth-event`

رویدادهای احراز هویت (ثبت‌نام و بازیابی رمز) را مدیریت می‌کند.

**ورودی:**
```json
{
  "event": "register یا password_reset",
  "email": "user@example.com",
  "username": "نام کاربر",
  "code": "123456",
  "reset_link": "https://...",
  "sender_email": "shop@example.com",
  "secret_token": "ario-shop-secret-token"
}
```

**جریان:**
1. Auth Webhook → دریافت POST
2. Validate Auth Secret → بررسی `secret_token` برابر با `ario-shop-secret-token`
3. Normalize Auth Payload → استخراج فیلدها
4. Route Auth Event → مسیردهی بر اساس `event`:
   - `register` → ارسال ایمیل کد تأیید → پاسخ 200
   - `password_reset` → ارسال ایمیل بازیابی → پاسخ 200

**خروجی موفق:** `{"status":"ok","message":"email sent"}`
**خروجی خطا:** `{"status":"error","message":"Unauthorized"}` (کد 401)

### ۲. Order Webhook — `/webhook/order-paid`

تأیید سفارش و ارسال ایمیل فاکتور.

**ورودی:**
```json
{
  "secret_token": "ario-shop-secret-token",
  "order_id": 42,
  "order_number": "ORD-20260615-0042",
  "customer_name": "نام مشتری",
  "customer_email": "customer@example.com",
  "payment_status": "paid",
  "total_price": 850000,
  "shipping_cost": 50000,
  "discount": 0,
  "created_at": "2026-06-15T10:30:00+03:30",
  "shipping_address": "آدرس پستی",
  "items": [
    {
      "name": "نام محصول",
      "quantity": 2,
      "unit_price": 400000,
      "total_price": 800000
    }
  ],
  "sender_email": "bardiaabdi1393@gmail.com"
}
```

**جریان:**
1. Order Paid Webhook → دریافت POST
2. Validate Secret Token → بررسی `secret_token`
3. Build Invoice Email HTML → ساخت HTML فاکتور (Code node)
4. Send Order Confirmation Email → ارسال ایمیل
5. Respond Success → پاسخ 200

**خروجی موفق:** `{"status":"success","message":"Email sent successfully"}`
**خروجی خطا:** `{"status":"error","message":"Unauthorized"}` (کد 401)

## نکات مهم

### امنیت
- هر دو webhook با `secret_token` محافظت می‌شوند
- مقدار توکن: `ario-shop-secret-token`
- Cloudflare Worker فقط مسیرهای `/webhook/django-auth-event` و `/webhook/order-paid` را قبول می‌کند

### قالب‌بندی اعداد
- قیمت‌ها با `Intl.NumberFormat('fa-IR')` فرمت می‌شوند
- واحد: تومان

### ایمیل‌ها
- همه ایمیل‌ها RTL هستند (dir="rtl")
- فونت: Vazir, Tahoma, sans-serif
- کد تأیید: ۶ رقمی، ۱۵ دقیقه معتبر
- لینک بازیابی: ۳۰ دقیقه معتبر
- فاکتور: شامل جدول اقلام، جمع کل، هزینه ارسال، تخفیف

### SMTP
- Credential مورد نیاز: SMTP (در بخش Credentials n8n)
- سرور: smtp.gmail.com:465 (SSL)
- ایمیل فرستنده: bardiaabdi1393@gmail.com
