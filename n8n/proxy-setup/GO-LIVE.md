# کارهایی که شما باید انجام بدهید (نسخهٔ شخصی شما)

این فایل فقط برای اکانت فعلی شماست. کارها را **به همین ترتیب** انجام دهید. تا یک مرحله تمام نشده سراغ بعدی نروید.

## چیزهایی که از شما دارم

| مورد | مقدار |
|---|---|
| دامنه سایت | `aryaabdi13850325.pythonanywhere.com` |
| n8n | `https://aryashop.app.n8n.cloud` |
| جیمیل فرستنده | `bardiaabdi1393@gmail.com` |
| آپلود پروژه | Git |
| Cloudflare | هنوز اکانت ندارید — باید بسازید |
| ربات تلگرام | توکن را دارید |

## چیزهایی که هنوز لازم است (این‌ها را در چت نفرستید)

این‌ها را **خودتان** در سایت مربوطه وارد کنید، اینجا پیست نکنید:

1. **App Password جیمیل** — رمز عادی جیمیل نیست. در گوگل: تأیید دو مرحله‌ای روشن → [App Passwords](https://myaccount.google.com/apppasswords) → یک رمز ۱۶ کاراکتری برای Mail بسازید. فقط داخل n8n در Credential SMTP می‌گذارید.
2. **Chat ID تلگرام** — عدد حساب ادمین. ربات خودتان را در تلگرام باز کنید و Start بزنید. بعد `@userinfobot` را Start کنید تا Id را بدهد.
3. **رمز ورود n8n** و **رمز PythonAnywhere** — فقط برای ورود خودتان.
4. بعد از ساخت ورکر، **آدرس ورکر** مثل `https://xxxx.yyyy.workers.dev` را برایم بفرستید تا در Django ثبت کنم.

توکن ربات را هم بعد از این، در BotFather اگر خواستید عوض کنید؛ چون در چت آمده بهتر است عمومی نماند. در n8n همان توکن فعلی را یک‌بار وارد کنید کافی است.

---

## مرحله ۱ — اکانت Cloudflare بسازید

1. بروید: https://dash.cloudflare.com/sign-up
2. با ایمیل ثبت‌نام کنید و تأیید کنید.
3. لازم نیست دامنه بخرید. Workers رایگان است.

وقتم این مرحله تمام شد بگویید «کلادفلر ساختم».

---

## مرحله ۲ — ورکر را از کامپیوتر خودتان دیپلوی کنید

روی ویندوز PowerShell:

```bash
npm install -g wrangler
wrangler login
```

مرورگر باز می‌شود؛ با همان اکانت Cloudflare وارد شوید و Allow بزنید.

بعد:

```bash
cd C:\Users\Ario\Desktop\Ario_Shop\Ario\n8n\proxy-setup
wrangler deploy
```

خروجی یک آدرس می‌دهد، شبیه:

`https://something.something.workers.dev`

آن آدرس را کپی کنید و برایم بفرستید.

تست سریع:

```bash
curl https://ADRES-WORKER-SHOMAS/
```

باید چیزی شبیه `{"status":"ok"...}` بیاید.

در `worker.js` آدرس n8n شما از قبل روی `https://aryashop.app.n8n.cloud` تنظیم شده است.

---

## مرحله ۳ — n8n را آماده کنید

1. وارد شوید: https://aryashop.app.n8n.cloud
2. **Credentials → Add Credential → SMTP**

```
Host: smtp.gmail.com
Port: 465
User: bardiaabdi1393@gmail.com
Password: همان App Password
SSL: روشن
```

3. **Credentials → Add Credential → Telegram**  
   Access Token = توکن ربات شما.

4. **Workflows → Import from File**  
   فایل: `n8n/proxy-setup/Django n8n (3).json`

5. روی این ۳ نود ایمیل، SMTP را وصل کنید:
   - Send Verification Email
   - Send Password Reset Email
   - Send Order Confirmation Email

6. روی نود **ارسال پیام تلگرام**: Credential تلگرام + **Chat ID** ادمین.

7. سوییچ بالای صفحه را **Active** کنید.

8. اگر ورکفلوی قدیمی با همین webhookها دارید، آن را خاموش کنید.

---

## مرحله ۴ — Django را روی PythonAnywhere ببرید

1. وارد https://www.pythonanywhere.com شوید.
2. تب **Web → Add a new web app**
   - دامنه: `aryaabdi13850325.pythonanywhere.com`
   - Manual configuration
   - Python **3.12** یا **3.13** (نه ۳.۱۰)

3. تب **Consoles → Bash**:

```bash
cd ~
git clone آدرس-ریپوی-گیت‌هاب Ario
cd ~/Ario
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install argon2-cffi
```

اگر ریپو خصوصی است، از PythonAnywhere با توکن GitHub کلون کنید.

**مهم:** `db.sqlite3` و پوشه `media` داخل Git نیستند. اگر محصول و عکس می‌خواهید، آن دو را جدا با تب Files در `~/Ario/` آپلود کنید.

4. ساخت `.env`:

```bash
cd ~/Ario
nano .env
```

```env
DEBUG=False
DJANGO_SECRET_KEY=اینجا-یک-کلید-تصادفی-بگذارید
ALLOWED_HOSTS=aryaabdi13850325.pythonanywhere.com
```

کلید تصادفی را روی کامپیوتر بسازید:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

nano: Ctrl+O ، Enter ، Ctrl+X

5. دیتابیس و فایل استاتیک:

```bash
cd ~/Ario
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

6. تب **Web**:
   - Virtualenv: `/home/Aryaabdi13850325/Ario/venv`  
     (اگر یوزرنیم در فایل‌سیستم حروف کوچک است همان را از مسیر home بردارید)
   - Working directory: `/home/YOURUSER/Ario`
   - فایل WSGI را این‌طور کنید (مسیر home را با یوزر واقعی عوض کنید):

```python
import sys
import os

path = '/home/YOURUSER/Ario'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ario_Shop.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

   - Static files:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOURUSER/Ario/staticfiles` |
| `/media/` | `/home/YOURUSER/Ario/media` |

7. **Reload**

---

## مرحله ۵ — آدرس ورکر را در Django بگذارید

بعد از مرحله ۲ که آدرس ورکر را برایم بفرستید، این سه خط در `Ario_Shop/settings.py` باید همان دامنه باشند:

- `N8N_WEBHOOK_URL`
- `N8N_ORDER_WEBHOOK_URL`
- `N8N_TELEGRAM_WEBHOOK_URL`

اگر خودتان می‌گذارید، فقط دامنهٔ ورکر را عوض کنید؛ انتهای مسیرها را دست نزنید:

```
.../webhook/django-auth-event
.../webhook/order-paid
.../webhook/new-order-notify
```

بعد روی PythonAnywhere `git pull` (یا فایل را آپلود) و **Reload**.

---

## مرحله ۶ — تست

از Bash خود PythonAnywhere (نه از کامپیوتر):

```bash
curl https://ADRES-WORKER-SHOMAS/
```

بعد روی سایت:

1. ثبت‌نام با ایمیل واقعی → باید کد تأیید بیاید
2. فراموشی رمز → باید ایمیل لینک بیاید
3. یک سفارش و پرداخت آزمایشی → ایمیل فاکتور + پیام تلگرام

---

## الان فقط همین را انجام دهید

**الان فقط مرحله ۱:** اکانت Cloudflare بسازید.

وقتی ساخته شد بنویسید: «کلادفلر ساختم»  
بعد مرحله ۲ (دیپلوی ورکر) را با هم می‌رویم.
