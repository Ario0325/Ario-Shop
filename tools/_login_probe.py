import os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
os.environ["DEBUG"]="True"; os.environ.setdefault("DJANGO_SETTINGS_MODULE","Ario_Shop.settings")
import django; django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS += ["testserver"]
from django.test import Client
c=Client()
h=c.get("/admin/login/").content.decode()
for k in ('adm-rail','nav-sidebar','body class','adm-topbar','adm-app'):
    print(k, ':', k in h)
import re
m=re.search(r'<body[^>]*>', h); print(m.group(0) if m else 'no body')
m=re.search(r'<div class="adm-app[^>]*>', h); print(m.group(0) if m else 'no shell')
