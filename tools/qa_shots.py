"""Focused QA captures: preloader, dark mode, mobile layouts.

Usage: python tools/qa_shots.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8001"


def dismiss_promo(page):
    page.evaluate("""() => {
        const m = document.querySelector('[data-ar-modal]');
        if (m) { m.classList.remove('is-open'); m.setAttribute('aria-hidden','true'); }
        document.body.classList.remove('ar-no-scroll');
        document.querySelectorAll('[data-ar-reveal]').forEach(e => e.classList.add('is-revealed'));
    }""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # 1) preloader — capture right after first paint
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="fa-IR")
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(420)
        page.screenshot(path=str(OUT / "preloader.png"))
        print("shot preloader")
        ctx.close()

        # 2) dark mode home + shop
        for name, path in (("home-dark", "/"), ("shop-dark", "/shop/")):
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
            ctx.add_init_script("try{localStorage.setItem('ar-theme','dark');}catch(e){}")
            page = ctx.new_page()
            page.goto(BASE + path, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(900)
            dismiss_promo(page)
            page.screenshot(path=str(OUT / f"{name}.png"))
            print("shot", name)
            ctx.close()

        # 3) mobile layouts
        for name, path in (("m-home", "/"), ("m-shop", "/shop/"), ("m-login", "/accounts/login/"),
                           ("m-product", "/shop/womens-scarf/")):
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="fa-IR",
                                      is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.goto(BASE + path, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(900)
            dismiss_promo(page)
            page.screenshot(path=str(OUT / f"{name}.png"))
            print("shot", name)
            ctx.close()

        browser.close()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
