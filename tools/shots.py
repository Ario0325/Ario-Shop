"""Screenshot pages / elements with Playwright for visual QA.

Usage:
    python tools/shots.py                       # default desktop+mobile set
    python tools/shots.py --only home-full
    python tools/shots.py --elem "#arHeader" --name header
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)

PAGES = [
    ("home-view", "/", 1440, 1000, False),
    ("home-full", "/", 1440, 1000, True),
    ("home-mobile", "/", 390, 844, True),
    ("shop-desktop", "/shop/", 1440, 1000, False),
    ("shop-full", "/shop/", 1440, 1000, True),
    ("login-desktop", "/accounts/login/", 1440, 1000, False),
    ("login-mobile", "/accounts/login/", 390, 844, False),
    ("cart-desktop", "/cart/", 1440, 900, False),
    ("product-desktop", "/shop/womens-scarf/", 1440, 1000, False),
    ("product-full", "/shop/womens-scarf/", 1440, 1000, True),
    ("dashboard", "/accounts/dashboard/", 1440, 1000, False),
    ("about", "/About_us/", 1440, 1000, False),
    ("contact", "/Contact_us/", 1440, 1000, False),
]


def main():
    base = "http://127.0.0.1:8001"
    only = None
    elem = None
    name = "element"
    dpr = 1
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--only":
            only = set(args[i + 1].split(","))
            i += 2
            continue
        if a == "--elem":
            elem = args[i + 1]
            i += 2
            continue
        if a == "--name":
            name = args[i + 1]
            i += 2
            continue
        if a == "--dpr":
            dpr = float(args[i + 1])
            i += 2
            continue
        if a.startswith("http"):
            base = a
        i += 1

    with sync_playwright() as p:
        browser = p.chromium.launch()

        if elem:
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                      locale="fa-IR", device_scale_factor=dpr)
            page = ctx.new_page()
            page.goto(base, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(900)
            page.evaluate("""() => {
                const m = document.querySelector('[data-ar-modal]');
                if (m) { m.classList.remove('is-open'); m.setAttribute('aria-hidden','true'); }
                document.querySelectorAll('[data-ar-reveal]').forEach(e => e.classList.add('is-revealed'));
            }""")
            page.locator(elem).first.screenshot(path=str(OUT / f"{name}.png"))
            print("shot", name)
            ctx.close()
            browser.close()
            return

        for pg_name, path, w, h, full in PAGES:
            if only and pg_name not in only:
                continue
            ctx = browser.new_context(viewport={"width": w, "height": h}, locale="fa-IR")
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.goto(base + path, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1200)
            page.evaluate("""() => {
                const m = document.querySelector('[data-ar-modal]');
                if (m) { m.classList.remove('is-open'); m.setAttribute('aria-hidden','true'); }
                document.body.classList.remove('ar-no-scroll');
                document.querySelectorAll('[data-ar-reveal]').forEach(e => e.classList.add('is-revealed'));
            }""")
            page.wait_for_timeout(250)
            page.screenshot(path=str(OUT / f"{pg_name}.png"), full_page=full)
            print(f"shot {pg_name:20s} {w}x{h} full={full} errors={len(errors)}")
            for e in errors[:5]:
                print("   ", e)
            ctx.close()
        browser.close()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
