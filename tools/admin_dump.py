"""Dump the real admin markup skeleton so selectors are written against facts.

Writes ./_shots/admin-dump.html and prints the structural bits we style:
header, nav-sidebar, content wrappers, body classes.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DEBUG"] = "True"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ario_Shop.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver", "localhost", "127.0.0.1"]

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()
c = Client()
c.force_login(admin)

resp = c.get("/admin/Products_Module/product/")
html = resp.content.decode("utf-8", "replace")
Path("_shots").mkdir(exist_ok=True)
Path("_shots/admin-dump.html").write_text(html, encoding="utf-8")

print("status", resp.status_code, "len", len(html))

def show(label, pattern, limit=1400):
    m = re.search(pattern, html, re.S)
    print(f"\n===== {label} =====")
    print((m.group(0)[:limit] if m else "NOT FOUND"))

show("body tag", r"<body[^>]*>", 300)
show("stylesheets", r"(?:<link[^>]+stylesheet[^>]*>\s*)+", 2500)
show("header", r'<header id="header".*?</header>', 2200)
show("nav-sidebar", r'<nav id="nav-sidebar".*?</nav>', 2600)
show("content opening", r'<div id="content".{0,600}', 700)
show("changelist toolbar", r'<div id="toolbar".*?</div>\s*</div>', 900)
show("object-tools", r'<ul class="object-tools".*?</ul>', 700)
