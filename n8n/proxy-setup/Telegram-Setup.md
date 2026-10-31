# راهنمای ستاپ اطلاع‌رسانی سفارش از طریق تلگرام

## معماری

`
Django (PythonAnywhere) → Cloudflare Worker → n8n Cloud → Telegram Bot → پیام به ادمین
`

## مراحل پیاده‌سازی

### مرحله ۱: ساخت ربات تلگرام

1. وارد تلگرام شوید و @BotFather را باز کنید
2. دستور /newbot را بزنید
3. نام ربات را وارد کنید: Ario Shop Bot
4. یوزرنیم ربات را وارد کنید: rio_shop_notify_bot (یا هر اسم دلخواه)
5. BotFather یک توکن می‌دهد مثل: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
6. این توکن را ذخیره کنید

### مرحله ۲: دریافت Chat ID

1. ربات @userinfobot را در تلگرام باز کنید
2. روی Start بزنید
3. Chat ID شما را نشان می‌دهد (یک عدد مثل 123456789)
4. این عدد را ذخیره کنید

### مرحله ۳: تنظیم Telegram Credential در n8n

1. وارد n8n شوید: https://tjnryhbtgvrfdcs.app.n8n.cloud
2. از منوی چپ روی **Credentials** کلیک کنید
3. روی **Add Credential** کلیک کنید
4. **Telegram** را انتخاب کنید
5. **Access Token** را وارد کنید (توکن ربات از مرحله ۱)
6. روی **Save** کلیک کنید

### مرحله ۴: ایمپورت Workflow

1. از منوی چپ روی **Workflows** کلیک کنید
2. روی **Import from File** کلیک کنید
3. فایل 
8n/proxy-setup/Django n8n (3).json را انتخاب کنید
4. نود **ارسال پیام تلگرام** را باز کنید
5. **Credential** را روی Telegram credential تنظیم کنید
6. **Chat ID** را وارد کنید (عدد از مرحله ۲)
7. Workflow را **Active** کنید

### مرحله ۵: Deploy کردن Cloudflare Worker

`ash
cd n8n/proxy-setup/
wrangler deploy
`

### مرحله ۶: آپدیت کد Django در PythonAnywhere

`ash
cd ~/Ario
git pull origin main
`

سپس به تب **Web** بروید و **Reload** بزنید.

### مرحله ۷: تست

**تست مستقیم با curl:**
`ash
curl -X POST https://quiet-field-a090.mimoomim456.workers.dev/webhook/new-order-notify \
  -H "Content-Type: application/json" \
  -d '{"secret_token":"ario-shop-secret-token","order_id":1,"order_number":"TEST-001","customer_name":"تست","customer_email":"test@test.com","customer_phone":"09123456789","total_price":100000,"shipping_cost":0,"discount":0,"payment_method":"آنلاین","shipping_address":"تهران","items":[{"name":"محصول تست","quantity":1,"unit_price":100000,"total_price":100000}],"created_at":"2026-06-15","status":"paid"}'
`

**تست از طریق سایت:**
1. یک سفارش با پرداخت موفق ثبت کنید
2. باید پیام تلگرام دریافت کنید

## ساختار Payload ارسالی

`json
{
  "secret_token": "ario-shop-secret-token",
  "order_id": 142,
  "order_number": "ORD-000142",
  "customer_name": "علی محمدی",
  "customer_email": "ali@example.com",
  "customer_phone": "09123456789",
  "total_price": 450000,
  "shipping_cost": 30000,
  "discount": 0,
  "payment_method": "آنلاین",
  "shipping_address": "تهران، خیابان ولیعصر",
  "items": [
    {
      "name": "کفش اسپرت",
      "quantity": 1,
      "unit_price": 350000,
      "total_price": 350000
    }
  ],
  "created_at": "2026-06-15T14:30:00Z",
  "status": "paid"
}
`

## فایل‌های تغییر یافته

| فایل | تغییر |
|------|-------|
| 
8n/proxy-setup/worker.js | اضافه شدن مسیر /webhook/new-order-notify |
| Ario_Shop/settings.py | اضافه شدن N8N_TELEGRAM_WEBHOOK_URL |
| Cart_Module/services.py | اضافه شدن متد send_telegram_notification |
| Cart_Module/views.py | فراخوانی اطلاع‌رسانی تلگرام بعد از پرداخت |
