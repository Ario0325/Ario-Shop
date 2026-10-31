"""Measure the new admin shell: grid columns, content widths, nav contents."""
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
EMAIL, PW = "qa.shell@example.com", "Qa!Shell12345"


def main():
    User.objects.filter(username=EMAIL).delete()
    u = User.objects.create_superuser(username=EMAIL, email=EMAIL, password=PW)
    u.is_active = True
    u.save()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
            pg = ctx.new_page()
            pg.goto("http://127.0.0.1:8001/admin/login/", wait_until="networkidle")
            pg.fill("#id_username", EMAIL)
            pg.fill("#id_password", PW)
            pg.click("#login-form input[type=submit]")
            pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(800)
            print(pg.evaluate("""() => {
                const m = (sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return 'MISSING';
                    const r = el.getBoundingClientRect();
                    const cs = getComputedStyle(el);
                    return {w: Math.round(r.width), x: Math.round(r.x), h: Math.round(r.height),
                            disp: cs.display, grid: cs.gridTemplateColumns, float: cs.float};
                };
                return {
                    app: m('.adm-app'),
                    rail: m('.adm-rail'),
                    body: m('.adm-body'),
                    header: m('#header'),
                    canvas: m('.adm-canvas'),
                    content: m('#content'),
                    main: m('#content-main'),
                    nav: m('#nav-sidebar'),
                    navApps: document.querySelectorAll('#nav-sidebar .module').length,
                    navLinks: document.querySelectorAll('#nav-sidebar tr th a').length,
                    availableApps: !!document.querySelector('#nav-sidebar .app-Products_Module'),
                };
            }"""))
            b.close()
    finally:
        User.objects.filter(username=EMAIL).delete()


if __name__ == "__main__":
    main()
