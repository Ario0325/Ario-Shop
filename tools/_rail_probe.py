import os, sys, re
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
os.environ["DEBUG"]="True"; os.environ.setdefault("DJANGO_SETTINGS_MODULE","Ario_Shop.settings")
import django; django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS += ["testserver"]
from django.contrib.auth import get_user_model
from django.test import Client
U=get_user_model(); a=U.objects.filter(is_superuser=True).first()
c=Client(); c.force_login(a)
h=c.get("/admin/").content.decode()
print("has toggle-nav-sidebar:", "toggle-nav-sidebar" in h)
print("has nav-filter:", "nav-filter" in h)
print("has app-Products_Module:", "app-Products_Module" in h)
print("is_nav_sidebar_enabled:", "adm-rail" in h)
m = re.search(r'<aside class="adm-rail".*?</aside>', h, re.S)
print("\n--- rail content (first 1200) ---")
print(m.group(0)[:1200] if m else "NO RAIL")
