"""Capture authenticated pages (cart, dashboard, orders, comments).

Creates a throw-away QA user + cart rows, screenshots the pages, then removes
everything it created so the dev database is left untouched.

Usage: python tools/authed_shots.py
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

from Cart_Module.models import CartItem  # noqa: E402
from Products_Module.models import Product  # noqa: E402

User = get_user_model()
EMAIL = "qa.screenshots@example.com"
PASSWORD = "Qa!Screen12345"
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8001"

PAGES = [
    ("cart-authed", "/cart/", 1440, 1100),
    ("cart-authed-mobile", "/cart/", 390, 900),
    ("dashboard-authed", "/accounts/dashboard/", 1440, 1000),
    ("orders-authed", "/accounts/orders/", 1440, 1000),
    ("comments-authed", "/accounts/comments/", 1440, 1000),
]


def setup():
    User.objects.filter(username=EMAIL).delete()
    user = User.objects.create_user(username=EMAIL, email=EMAIL, password=PASSWORD)
    user.is_active = True
    user.save(update_fields=["is_active"])
    products = list(Product.objects.filter(is_active=True)[:2])
    for p in products:
        CartItem.objects.create(user=user, product=p, quantity=2 if p == products[0] else 1)
    return user, products


def teardown(user):
    CartItem.objects.filter(user=user).delete()
    user.delete()


def main():
    user, products = setup()
    print(f"qa user={user.username} products={[p.name for p in products]}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, path, w, h in PAGES:
                ctx = browser.new_context(viewport={"width": w, "height": h}, locale="fa-IR")
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(BASE + "/accounts/login/", wait_until="networkidle", timeout=45000)
                page.fill("#singin-email-2", EMAIL)
                page.fill("#singin-password-2", PASSWORD)
                page.click("#panel-login button[type=submit]")
                page.wait_for_load_state("networkidle", timeout=45000)
                page.goto(BASE + path, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(900)
                page.evaluate("""() => {
                    const m = document.querySelector('[data-ar-modal]');
                    if (m) { m.classList.remove('is-open'); m.setAttribute('aria-hidden','true'); }
                    document.querySelectorAll('[data-ar-reveal]').forEach(e => e.classList.add('is-revealed'));
                }""")
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=(name == "cart-authed"))
                print(f"shot {name:22s} errors={len(errors)}")
                for e in errors[:4]:
                    print("   ", e)
                ctx.close()
            browser.close()
    finally:
        teardown(user)
        print("qa data removed")


if __name__ == "__main__":
    main()
