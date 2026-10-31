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
h=c.get("/admin/Products_Module/product/").content.decode()
secs = re.findall(r'class="section"[^>]*>\s*([^<]+?)\s*<', h)
print("sidebar sections:", [s.strip() for s in secs])
print()
print("nav-filter present:", "nav-filter" in h)
print("nav app modules:", len(re.findall(r'class="app-[A-Za-z_]+ module"', h)))
print("current-model:", "current-model" in h)
print("adm-rail:", 'class="adm-rail"' in h)
print("adm-topbar:", 'adm-topbar' in h)
