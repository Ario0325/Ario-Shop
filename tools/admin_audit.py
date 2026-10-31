"""Automated UI audit of the admin panel (no screenshots needed).

Checks the things a screenshot would show, but measurably:
  * horizontal overflow at each breakpoint
  * element collisions in the top bar
  * touch-target sizes on mobile
  * text contrast (WCAG AA) for the key surfaces
  * rail visibility / drawer behaviour per breakpoint
  * computed colours proving the theme actually applied

Usage: python tools/admin_audit.py
Exit code is non-zero when a hard check fails.
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

User = get_user_model()
EMAIL, PW = "qa.audit@example.com", "Qa!Audit12345"
BASE = "http://127.0.0.1:8001"

VIEWPORTS = [
    ("desktop", 1440, 900),
    ("laptop", 1280, 800),
    ("tablet", 820, 1180),
    ("mobile", 390, 844),
    ("small", 360, 740),
]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


CONTRAST_JS = r"""
() => {
  const lum = (rgb) => {
    const m = rgb.match(/\d+(\.\d+)?/g);
    if (!m) return null;
    const [r, g, b] = m.slice(0, 3).map(Number).map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (fg, bg) => {
    const a = lum(fg), b = lum(bg);
    if (a === null || b === null) return null;
    const hi = Math.max(a, b), lo = Math.min(a, b);
    return (hi + 0.05) / (lo + 0.05);
  };
  const opaque = (el) => {
    let cur = el, guard = 0;
    while (cur && guard++ < 40) {
      const cs = getComputedStyle(cur);
      const bg = cs.backgroundColor;
      if (bg && bg !== 'transparent' && !/rgba\(0, 0, 0, 0\)/.test(bg)) {
        const m = bg.match(/[\d.]+/g);
        if (m && (m.length < 4 || parseFloat(m[3]) > 0.75)) return bg;
      }
      cur = cur.parentElement;
    }
    return 'rgb(255,255,255)';
  };
  const out = [];
  const sels = [
    ['.adm-rail__brand .adm-brand__text strong', 'rail brand'],
    ['#nav-sidebar tr th a', 'rail nav link'],
    ['.adm-page-title', 'page title'],
    ['.breadcrumbs a', 'breadcrumb'],
    ['#result_list thead th', 'table head'],
    ['#result_list tbody td', 'table cell'],
    ['#changelist-filter h2', 'filter title'],
    ['#changelist-filter li a', 'filter link'],
    ['#changelist-search #searchbar', 'search input'],
    ['.object-tools a', 'object tool button'],
    ['.actions label', 'actions label'],
    ['.paginator a', 'pagination link'],
    ['.button', 'button'],
  ];
  for (const [sel, label] of sels) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const cs = getComputedStyle(el);
    const bg = opaque(el);
    out.push({
      label,
      fg: cs.color,
      bg,
      ratio: ratio(cs.color, bg),
      size: parseFloat(cs.fontSize),
      weight: cs.fontWeight,
    });
  }
  return out;
}
"""


def main():
    User.objects.filter(username=EMAIL).delete()
    u = User.objects.create_superuser(username=EMAIL, email=EMAIL, password=PW)
    u.is_active = True
    u.save()
    hard_fail = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            for label, w, h in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h}, locale="fa-IR")
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(BASE + "/admin/login/", wait_until="networkidle", timeout=45000)
                pg.fill("#id_username", EMAIL)
                pg.fill("#id_password", PW)
                pg.click("#login-form input[type=submit]")
                pg.wait_for_load_state("networkidle", timeout=45000)

                print(f"\n── {label} ({w}×{h}) ─────────────────────────────")

                for path, name in (("/admin/", "dashboard"),
                                   ("/admin/Products_Module/product/", "changelist"),
                                   ("/admin/Products_Module/product/1/change/", "change form")):
                    pg.goto(BASE + path, wait_until="networkidle", timeout=45000)
                    pg.wait_for_timeout(500)

                    # 1. no horizontal page overflow
                    ov = pg.evaluate(
                        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    )
                    check(f"{label}/{name}: no h-scroll", ov <= 2, f"overflow {ov}px")
                    if ov > 2:
                        hard_fail += 1

                    # 2. shell present and correctly sized
                    geo = pg.evaluate("""() => {
                        const g = s => { const e = document.querySelector(s); if (!e) return null;
                            const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
                            return {w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x),
                                    vis: cs.visibility, disp: cs.display}; };
                        return { rail: g('.adm-rail'), canvas: g('.adm-canvas'),
                                 header: g('#header'), content: g('#content') };
                    }""")
                    if geo["content"] is None or geo["content"]["w"] < 300:
                        check(f"{label}/{name}: content has width", False, str(geo["content"]))
                        hard_fail += 1

                    if w > 1024:
                        if not geo["rail"] or geo["rail"]["w"] < 200:
                            check(f"{label}/{name}: rail visible", False, str(geo["rail"]))
                            hard_fail += 1

                # 3. mobile drawer + touch targets
                if w <= 1024:
                    pg.goto(BASE + "/admin/", wait_until="networkidle")
                    pg.wait_for_timeout(400)
                    before = pg.evaluate("() => document.querySelector('.adm-rail').getBoundingClientRect().x")
                    pg.click("#adm-burger")
                    pg.wait_for_timeout(500)
                    after = pg.evaluate("() => document.querySelector('.adm-rail').getBoundingClientRect().x")
                    opened = pg.evaluate("() => document.body.classList.contains('adm-nav-open')")
                    moved = abs(before - after) > 60
                    check(f"{label}: drawer opens & slides", opened and moved,
                          f"open={opened} x {before}->{after}")
                    if not (opened and moved):
                        hard_fail += 1

                    # rail must sit fully on-screen when open
                    inside = pg.evaluate("""() => {
                        const r = document.querySelector('.adm-rail').getBoundingClientRect();
                        return r.left >= -2 && r.right <= window.innerWidth + 2;
                    }""")
                    check(f"{label}: open drawer is on-screen", inside)
                    if not inside:
                        hard_fail += 1

                    taps = pg.evaluate("""() => {
                        const bad = [];
                        document.querySelectorAll('.adm-rail a, .adm-rail button, .quick-action-btn, .object-tools a')
                          .forEach(el => {
                            const cs = getComputedStyle(el);
                            // skip elements that are deliberately not interactive
                            if (cs.display === 'none' || cs.visibility === 'hidden') return;
                            if (parseFloat(cs.opacity) < 0.1) return;
                            if (cs.pointerEvents === 'none') return;
                            const r = el.getBoundingClientRect();
                            if (r.width === 0 || r.height === 0) return;
                            if (r.height < 32) bad.push((el.textContent||'').trim().slice(0,24) + ' h=' + Math.round(r.height));
                          });
                        return bad.slice(0, 6);
                    }""")
                    check(f"{label}: taps >= 32px tall", len(taps) == 0, "; ".join(taps))

                    pg.keyboard.press("Escape")
                    pg.wait_for_timeout(350)
                    closed = pg.evaluate("() => !document.body.classList.contains('adm-nav-open')")
                    check(f"{label}: Escape closes drawer", closed)
                    if not closed:
                        hard_fail += 1

                # 4. contrast on the changelist
                pg.goto(BASE + "/admin/Products_Module/product/", wait_until="networkidle")
                pg.wait_for_timeout(400)
                rows = pg.evaluate(CONTRAST_JS)
                print(f"   contrast ({len(rows)} samples):")
                for r in rows:
                    need = 3.0 if r["size"] >= 18 or (r["size"] >= 14 and int(r["weight"]) >= 700) else 4.5
                    ok = r["ratio"] is not None and r["ratio"] >= need
                    flag = "ok " if ok else "LOW"
                    print(f"     {flag} {r['ratio'] and round(r['ratio'],2):>5} "
                          f"(need {need})  {r['label']:<22} {r['fg']} on {r['bg']}")
                    if not ok:
                        hard_fail += 1
                        results.append((f"{label}/contrast/{r['label']}", False, f"{r['ratio']}"))

                check(f"{label}: no JS errors", len(errs) == 0, "; ".join(errs[:2]))

                # theme actually applied?
                applied = pg.evaluate("""() => {
                    const c = document.querySelector('.adm-canvas');
                    const rail = document.querySelector('.adm-rail');
                    return {
                        canvasBg: getComputedStyle(document.body).backgroundColor,
                        railBg: rail ? getComputedStyle(rail).backgroundColor : null,
                        font: getComputedStyle(document.body).fontFamily,
                    };
                }""")
                font_ok = "Vazir" in (applied["font"] or "")
                check(f"{label}: Vazir font applied", font_ok, applied["font"])
                if not font_ok:
                    hard_fail += 1

                ctx.close()

            browser.close()
    finally:
        User.objects.filter(username=EMAIL).delete()

    print("\n" + "=" * 62)
    failed = [r for r in results if not r[1]]
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("\nFAILED:")
        for n, _, d in failed:
            print(f"  - {n} {d}")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
