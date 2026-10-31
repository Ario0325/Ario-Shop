"""Render the admin pages as the existing superuser and report status + markers."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DEBUG"] = "True"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ario_Shop.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver", "localhost", "127.0.0.1"]

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()
print("superuser:", admin)
if not admin:
    raise SystemExit("no superuser to test with")

c = Client()
c.force_login(admin)

for url in ("/admin/", "/admin/login/", "/admin/Products_Module/product/", "/admin/Cart_Module/order/",
            "/admin/Core_Module/sitesetting/"):
    try:
        r = c.get(url, follow=True)
        body = r.content.decode("utf-8", "replace")
        print(f"{r.status_code}  {len(body):>7}  {url}  {'(redirected)' if r.redirect_chain else ''}")
        for marker in ("dashboard-stats-grid", "theme-selector-wrapper", "custom_admin.css", "stat-card"):
            if marker in body:
                print(f"        marker: {marker}")
    except Exception as exc:  # noqa: BLE001
        print(f"ERR  {url}  {type(exc).__name__}: {exc}")
