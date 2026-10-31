import os, sys
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
import re
print("ario-admin.css:", "ario-admin.css" in h)
print("adm-app:", 'class="adm-app' in h)
print("adm-rail:", 'id="adm-rail"' in h)
print("stat-card:", 'stat-card' in h)
for m in re.findall(r'<link[^>]*stylesheet[^>]*>', h): print("  ", m)
