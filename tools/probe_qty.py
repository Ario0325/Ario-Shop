"""Probe the cart quantity stepper in a real browser (login + inspect + zoom shot)."""
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
EMAIL, PASSWORD = "qa.probe@example.com", "Probe!12345"
OUT = ROOT / "_shots"


def main():
    User.objects.filter(username=EMAIL).delete()
    u = User.objects.create_user(username=EMAIL, email=EMAIL, password=PASSWORD)
    u.is_active = True
    u.save(update_fields=["is_active"])
    p = Product.objects.filter(is_active=True).first()
    CartItem.objects.create(user=u, product=p, quantity=2)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR",
                                device_scale_factor=3)
            page = ctx.new_page()
            page.goto("http://127.0.0.1:8001/accounts/login/", wait_until="networkidle")
            page.fill("#singin-email-2", EMAIL)
            page.fill("#singin-password-2", PASSWORD)
            page.click("#panel-login button[type=submit]")
            page.wait_for_load_state("networkidle")
            page.goto("http://127.0.0.1:8001/cart/", wait_until="networkidle")
            page.wait_for_timeout(700)
            info = page.evaluate("""() => {
                const boxes = document.querySelectorAll('.ar-qty');
                if (!boxes.length) return {count: 0};
                const q = boxes[0];
                return {
                    count: boxes.length,
                    buttons: q.querySelectorAll('button').length,
                    inputs: q.querySelectorAll('input').length,
                    html: q.innerHTML.replace(/\\s+/g,' ').slice(0, 300),
                    innerWidth: q.getBoundingClientRect().width
                };
            }""")
            print(info)
            page.locator(".ar-qty").first.screenshot(path=str(OUT / "qty-zoom.png"))
            print("shot qty-zoom")
            b.close()
    finally:
        CartItem.objects.filter(user=u).delete()
        u.delete()


if __name__ == "__main__":
    main()
