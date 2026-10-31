"""Audit icon classes used by templates against the extracted icon font."""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
blk = (root / "static/assets/css/ario-icons.css").read_text(encoding="utf-8")
have = {m for m in re.findall(r"\.(icon-[a-z0-9-]+):before", blk)}

skip = ("static", "docs", ".git", "admin", "node_modules")
used = set()
for p in root.rglob("*.html"):
    if any(part in skip for part in p.parts):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in re.findall(r'class="([^"]*)"', t):
        for c in m.split():
            if c.startswith("icon-"):
                used.add(c)

print(f"templates scanned, distinct icon classes used: {len(used)}")
missing = sorted(used - have)
print(f"MISSING ({len(missing)}): {missing}")
