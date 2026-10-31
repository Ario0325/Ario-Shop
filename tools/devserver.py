"""Development server with DEBUG forced on.

`python manage.py runserver` picks DEBUG up from the environment, and when it is
False Django wraps the template loaders in `cached.Loader` - which silently
serves stale templates until the process restarts. Setting the flag in-process
before settings load removes that footgun.

Usage:  python tools/devserver.py [port] [--reload]
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DEBUG"] = "True"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ario_Shop.settings")

from django.conf import settings  # noqa: E402
from django.core.management import execute_from_command_line  # noqa: E402

if not settings.DEBUG:  # pragma: no cover - defensive
    raise SystemExit("DEBUG is False; refusing to start the dev server.")

port = "8001"
argv = sys.argv[1:]
reload = "--reload" in argv
for a in argv:
    if a.isdigit():
        port = a

args = [sys.argv[0], "runserver", f"127.0.0.1:{port}"]
if not reload:
    args.append("--noreload")

print(f"[devserver] DEBUG={settings.DEBUG}  http://127.0.0.1:{port}/")
execute_from_command_line(args)
