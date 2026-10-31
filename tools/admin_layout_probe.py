"""Measure admin layout boxes in a real browser to diagnose width issues."""
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

User = get_user_model()
EMAIL, PASSWORD = "qa.layout@example.com", "Qa!Layout12345"


def main():
    User.objects.filter(username=EMAIL).delete()
    u = User.objects.create_superuser(username=EMAIL, email=EMAIL, password=PASSWORD)
    u.is_active = True
    u.save()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
            page = ctx.new_page()
            page.goto("http://127.0.0.1:8001/admin/login/", wait_until="networkidle")
            page.fill("#id_username", EMAIL)
            page.fill("#id_password", PASSWORD)
            page.click("input[type=submit]")
            page.wait_for_load_state("networkidle")
            info = page.evaluate("""() => {
                const pick = (sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    const cs = getComputedStyle(el);
                    return {w: Math.round(r.width), x: Math.round(r.x), disp: cs.display,
                            float: cs.float, flex: cs.flex, pos: cs.position, dir: cs.direction};
                };
                const sels = ['body','#header','#container','#nav-sidebar','#content','#content-main',
                              '.dashboard-stats-grid','.stat-card','.dashboard-card','.quick-actions',
                              '.dashboard-apps-grid'];
                const out = {};
                sels.forEach(s => out[s] = pick(s));
                return out;
            }""")
            for k, v in info.items():
                print(f"{k:26s} {v}")

            # what paints the white table header?
            probe = page.evaluate("""() => {
                const th = document.querySelector('.dashboard-table thead th');
                if (!th) return 'no th';
                const cs = getComputedStyle(th);
                return {bg: cs.backgroundColor, color: cs.color, cls: th.className};
            }""")
            print("dashboard-table th:", probe)

            td = page.evaluate("""() => {
                const t = document.querySelector('.dashboard-table tbody td');
                if (!t) return 'no td';
                const cs = getComputedStyle(t);
                return {bg: cs.backgroundColor, color: cs.color, text: t.textContent.trim().slice(0,20)};
            }""")
            print("dashboard-table td:", td)
            b.close()
    finally:
        User.objects.filter(username=EMAIL).delete()


if __name__ == "__main__":
    main()
