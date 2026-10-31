"""Smoke-test the interactive layer in a real browser.

Checks the things that are easy to break and impossible to see in a static
screenshot: mega menu, drawers, tabs, theme toggle, password reveal, preloader.

Exit code is non-zero when any check fails.

Requires a dev server on http://127.0.0.1:8001.
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8001"
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{(' - ' + detail) if detail and not ok else ''}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------- desktop ----------
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(400)

        # the loader runs a short exit choreography, so wait for it to detach
        try:
            page.wait_for_selector("#ar-preloader", state="detached", timeout=4000)
            check("preloader removed after load", True)
        except Exception:
            check("preloader removed after load", False, "still attached after 4s")

        page.click('[data-ar-mega-toggle="ar-mega"]')
        page.wait_for_timeout(350)
        check("mega menu opens", page.locator("#ar-mega.is-open").count() == 1)
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
        check("mega menu closes on Escape", page.locator("#ar-mega.is-open").count() == 0)

        page.click('[data-ar-open="ar-drawer-cart"]')
        page.wait_for_timeout(450)
        check("cart drawer opens", page.locator("#ar-drawer-cart.is-open").count() == 1)
        check("page scroll locked while drawer open",
              page.evaluate("() => getComputedStyle(document.body).overflow === 'hidden'"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(450)
        check("cart drawer closes on Escape", page.locator("#ar-drawer-cart.is-open").count() == 0)

        before = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        page.locator("[data-ar-theme-toggle]").first.click()
        page.wait_for_timeout(300)
        after = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        check("theme toggle switches theme", before != after, f"{before} -> {after}")
        check("theme choice persisted",
              page.evaluate("() => localStorage.getItem('ar-theme')") == after)
        ctx.close()

        # ---------- mobile ----------
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, locale="fa-IR",
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/shop/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(500)

        page.click('[data-ar-open="ar-drawer-nav"]')
        page.wait_for_timeout(500)
        check("mobile nav drawer opens", page.locator("#ar-drawer-nav.is-open").count() == 1)
        page.click("#ar-drawer-nav [data-ar-close]")
        page.wait_for_timeout(450)
        check("mobile nav drawer closes", page.locator("#ar-drawer-nav.is-open").count() == 0)

        check("desktop filter column hidden on mobile",
              not page.locator("aside.ar-filters").is_visible())
        page.click('[data-ar-open="ar-filters"]')
        page.wait_for_timeout(450)
        check("mobile filter drawer opens", page.locator("#ar-filters.is-open").count() == 1)
        page.keyboard.press("Escape")
        page.wait_for_timeout(450)

        check("bottom nav visible on mobile", page.locator(".ar-bottomnav").is_visible())
        ctx.close()

        # ---------- auth tabs + password reveal ----------
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="fa-IR")
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/accounts/login/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(400)

        check("login panel active by default", page.locator("#panel-login.is-active").count() == 1)
        page.click("#tab-register")
        page.wait_for_timeout(300)
        check("register tab switches panel", page.locator("#panel-register.is-active").count() == 1)
        page.click("#tab-login")
        page.wait_for_timeout(300)

        page.fill("#singin-password-2", "secret123")
        page.click("[data-ar-pw-toggle='singin-password-2']")
        page.wait_for_timeout(200)
        pw_type = page.get_attribute("#singin-password-2", "type")
        check("password reveal toggles input type", pw_type == "text", f"type={pw_type}")

        # keyboard: focus ring reachable on the first field
        page.focus("#singin-email-2")
        shadow = page.evaluate(
            "() => getComputedStyle(document.querySelector('#singin-email-2')).boxShadow")
        check("focused input has a visible ring", shadow not in ("none", ""), f"box-shadow={shadow}")
        ctx.close()

        browser.close()

    check("no uncaught JS errors", len(errors) == 0, "; ".join(errors[:3]))
    failed = [r for r in results if not r[1]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
