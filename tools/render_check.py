"""Render every public route with Django's test client and report template errors.

Usage: python tools/render_check.py [--verbose]
Exit code is non-zero when any route fails.
"""
import os
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ario_Shop.settings")
os.environ.setdefault("DEBUG", "True")
os.environ["DEBUG"] = "True"

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver", "localhost", "127.0.0.1"]

from django.test import Client  # noqa: E402

PUBLIC = [
    "/",
    "/shop/",
    "/shop/search/?q=a",
    "/cart/",
    "/accounts/login/",
    "/accounts/forget-password/",
    "/accounts/forget-password/verify/",
    "/accounts/reset/done/",
    "/accounts/verify-email/?email=nobody@example.com",
    "/Contact_us/",
    "/About_us/",
    "/robots.txt",
    "/manifest.json",
]


def object_routes():
    """Discover a product slug and a category slug so detail pages get tested."""
    routes = []
    try:
        from Products_Module.models import Product, Category

        p = Product.objects.filter(is_available=True).first() or Product.objects.first()
        if p:
            routes.append(f"/shop/{p.slug}/")
        c = Category.objects.filter(is_active=True).first() or Category.objects.first()
        if c:
            routes.append(f"/shop/category/{c.slug}/")
    except Exception as exc:  # pragma: no cover
        print(f"  (could not load product/category: {exc})")
    return routes


def main():
    verbose = "--verbose" in sys.argv
    client = Client()
    routes = PUBLIC + object_routes()
    failures = []

    for url in routes:
        try:
            resp = client.get(url, follow=True)
            status = resp.status_code
            body = resp.content.decode("utf-8", "replace")
            length = len(body)
            # surface Django template errors that render as 200 in some setups
            bad = re.findall(r"(TemplateSyntaxError|TemplateDoesNotExist|VariableDoesNotExist)", body)
            note = ""
            if bad:
                note = " TEMPLATE-ERROR:" + ",".join(sorted(set(bad)))
            print(f"{status}  {length:>7}  {url}{note}")
            if status >= 400 or bad:
                failures.append((url, status, note))
            if verbose and status >= 400:
                print(body[:1500])
        except Exception:
            print(f"ERR  {'':>7}  {url}")
            traceback.print_exc()
            failures.append((url, "exception", ""))

    print()
    if failures:
        print(f"FAILED {len(failures)}/{len(routes)}")
        return 1
    print(f"OK — {len(routes)} routes rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
