"""Screenshot the admin panel with a throw-away superuser.

Creates (then removes) a temporary superuser so the panel can be captured at a
known password. Writes PNGs into ./_shots/.

Usage: python tools/admin_shots.py [--suffix before|after]
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DEBUG"] = "True"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ario_Shop.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from Products_Module.models import Product  # noqa: E402

User = get_user_model()
EMAIL = "qa.admin@example.com"
PASSWORD = "Qa!Admin12345"
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8001"

suffix = ""
for i, a in enumerate(sys.argv):
    if a == "--suffix" and i + 1 < len(sys.argv):
        suffix = "-" + sys.argv[i + 1]


def main():
    User.objects.filter(username=EMAIL).delete()
    admin = User.objects.create_superuser(username=EMAIL, email=EMAIL, password=PASSWORD)
    admin.first_name = "QA"
    admin.save()

    product = Product.objects.first()
    pages = [
        ("admin-login" + suffix, "/admin/login/", 1440, 900, False),
        ("admin-dash" + suffix, "/admin/", 1440, 1400, True),
        ("admin-list" + suffix, "/admin/Products_Module/product/", 1440, 1000, False),
        ("admin-form" + suffix, f"/admin/Products_Module/product/{product.id}/change/" if product else "/admin/", 1440, 1100, False),
        ("admin-orders" + suffix, "/admin/Cart_Module/order/", 1440, 1000, False),
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # logged-out login page
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="fa-IR")
            page = ctx.new_page()
            page.goto(BASE + "/admin/login/", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(700)
            page.screenshot(path=str(OUT / f"admin-login{suffix}.png"))
            print("shot admin-login")
            ctx.close()

            ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE + "/admin/login/", wait_until="networkidle", timeout=45000)
            page.fill("#id_username", EMAIL)
            page.fill("#id_password", PASSWORD)
            page.click("input[type=submit]")
            page.wait_for_load_state("networkidle", timeout=45000)

            for name, path, w, h, full in pages[1:]:
                page.set_viewport_size({"width": w, "height": h})
                page.goto(BASE + path, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1200)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
                print(f"shot {name}  errors={len(errors)}")
                for e in errors[:3]:
                    print("   ", e)
            ctx.close()
            browser.close()
    finally:
        User.objects.filter(username=EMAIL).delete()
        print("temp superuser removed")


if __name__ == "__main__":
    main()
