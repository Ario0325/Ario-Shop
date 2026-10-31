import os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
os.environ["DEBUG"]="True"; os.environ.setdefault("DJANGO_SETTINGS_MODULE","Ario_Shop.settings")
import django; django.setup()
from django.contrib.auth import get_user_model
from playwright.sync_api import sync_playwright
U=get_user_model(); E,P="qa.err@example.com","Qa!Err12345"
U.objects.filter(username=E).delete(); u=U.objects.create_superuser(username=E,email=E,password=P); u.is_active=True; u.save()
try:
  with sync_playwright() as pw:
    b=pw.chromium.launch(); ctx=b.new_context(viewport={"width":1440,"height":1000},locale="fa-IR")
    pg=ctx.new_page()
    pg.on("pageerror", lambda e: print("PAGEERROR:", e, "\nSTACK:", getattr(e, "stack", "n/a")))
    pg.goto("http://127.0.0.1:8001/admin/login/",wait_until="networkidle")
    pg.fill("#id_username",E); pg.fill("#id_password",P); pg.click("#login-form input[type=submit]")
    pg.wait_for_load_state("networkidle")
    pg.goto("http://127.0.0.1:8001/admin/Products_Module/product/",wait_until="networkidle")
    pg.wait_for_timeout(1200)
    b.close()
finally:
  U.objects.filter(username=E).delete()
