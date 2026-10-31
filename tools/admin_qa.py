"""Admin QA: screenshot desktop + mobile across every admin screen type.

Creates a throw-away superuser, logs in with the real login form, walks the
admin, records console/page errors, then removes the user.

Usage: python tools/admin_qa.py [--suffix name]
Writes PNGs to ./_shots/
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
EMAIL = "qa.admin.qa@example.com"
PASSWORD = "Qa!Admin12345"
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8001"

suffix = ""
for i, a in enumerate(sys.argv):
    if a == "--suffix" and i + 1 < len(sys.argv):
        suffix = "-" + sys.argv[i + 1]

DESKTOP = (1440, 1000)
MOBILE = (390, 844)


def pages(product):
    return [
        ("dash", "/admin/", True),
        ("list", "/admin/Products_Module/product/", False),
        ("form", f"/admin/Products_Module/product/{product.id}/change/" if product else "/admin/", False),
        ("appindex", "/admin/Products_Module/", False),
        ("orders", "/admin/Cart_Module/order/", False),
        ("history", f"/admin/Products_Module/product/{product.id}/history/" if product else "/admin/", False),
    ]


def main():
    User.objects.filter(username=EMAIL).delete()
    admin = User.objects.create_superuser(username=EMAIL, email=EMAIL, password=PASSWORD)
    admin.is_active = True
    admin.save()
    product = Product.objects.first()
    failures = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # logged-out login page (desktop + mobile)
            for label, size in (("login", DESKTOP), ("login-m", MOBILE)):
                ctx = browser.new_context(viewport={"width": size[0], "height": size[1]}, locale="fa-IR")
                pg = ctx.new_page()
                pg.goto(BASE + "/admin/login/", wait_until="networkidle", timeout=45000)
                pg.wait_for_timeout(500)
                pg.screenshot(path=str(OUT / f"adm-{label}{suffix}.png"))
                print(f"shot adm-{label}{suffix}")
                ctx.close()

            for label, size, mobile in (("", DESKTOP, False), ("-m", MOBILE, True)):
                ctx = browser.new_context(
                    viewport={"width": size[0], "height": size[1]},
                    locale="fa-IR",
                    is_mobile=mobile,
                    has_touch=mobile,
                )
                pg = ctx.new_page()
                errors = []
                pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
                pg.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)

                pg.goto(BASE + "/admin/login/", wait_until="networkidle", timeout=45000)
                pg.fill("#id_username", EMAIL)
                pg.fill("#id_password", PASSWORD)
                pg.click("#login-form input[type=submit]")
                pg.wait_for_load_state("networkidle", timeout=45000)

                for name, path, full in pages(product):
                    pg.goto(BASE + path, wait_until="networkidle", timeout=45000)
                    pg.wait_for_timeout(900)
                    shot = f"adm-{name}{label}{suffix}"
                    pg.screenshot(path=str(OUT / f"{shot}.png"), full_page=full)
                    errs = [e for e in errors if e]
                    print(f"shot {shot:26s} errors={len(errs)}")
                    if errs:
                        failures.append((shot, errs[:3]))
                        for e in errs[:3]:
                            print("     ", e)
                        errors.clear()

                # mobile: open the nav drawer once to prove it works
                if mobile:
                    pg.goto(BASE + "/admin/", wait_until="networkidle")
                    pg.wait_for_timeout(500)
                    pg.click("#adm-burger")
                    pg.wait_for_timeout(450)
                    opened = pg.evaluate("() => document.body.classList.contains('adm-nav-open')")
                    pg.screenshot(path=str(OUT / f"adm-drawer{suffix}.png"))
                    print(f"drawer opens: {opened}")
                    if not opened:
                        failures.append(("drawer", ["did not open"]))

                ctx.close()
            browser.close()
    finally:
        User.objects.filter(username=EMAIL).delete()
        print("temp superuser removed")

    if failures:
        print("\nFAILURES:", failures)
        return 1
    print("\nall admin screens captured with no errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
