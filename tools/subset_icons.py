"""Subset the molla icon font down to the classes the site actually uses.

Run after adding/removing icon classes in templates or ``ar.js``:
    python tools/subset_icons.py
The full font is kept as ``molla0ab2.full.woff2`` for rebuilds and rollback.
"""
import re
import shutil
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "static/assets/css/ario-icons.css"
JS = ROOT / "static/assets/js/ar.js"
FONT = ROOT / "static/assets/fonts/molla0ab2.woff2"
FULL_FONT = ROOT / "static/assets/fonts/molla0ab2.full.woff2"
SKIP_DIRS = {"static", "docs", ".git", "admin", "node_modules", ".qoder", "media", "staticfiles"}


def glyph_map():
    css = CSS.read_text(encoding="utf-8")
    mapping = {}
    rule = re.compile(r"([^{}]+?):before\s*\{[^}]*?content:\s*'\\([0-9a-fA-F]+)'[^}]*\}")
    for selector, code in rule.findall(css):
        for name in re.findall(r"\.(icon-[a-z0-9-]+)", selector):
            mapping[name] = int(code, 16)
    return mapping


def used_classes():
    found = set()
    for path in ROOT.rglob("*.html"):
        parts = path.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        found.update(re.findall(r"\bicon-[a-z0-9-]+", text))
    if JS.is_file():
        found.update(re.findall(r"\bicon-[a-z0-9-]+", JS.read_text(encoding="utf-8")))
    return found


def main():
    if not FULL_FONT.exists():
        shutil.copy2(FONT, FULL_FONT)

    mapping = glyph_map()
    used = used_classes()
    codepoints = {mapping[name] for name in used if name in mapping}
    unknown = sorted(used - mapping.keys())

    options = subset.Options()
    options.flavor = "woff2"
    options.notdef_outline = True
    options.name_IDs = ["*"]

    font = subset.load_font(str(FULL_FONT), options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    subset.save_font(font, str(FONT), options)

    print(f"used icon classes: {len(used)} (mapped: {len(used) - len(unknown)})")
    if unknown:
        print(f"unknown classes (ignored): {unknown}")
    print(f"glyphs kept: {len(codepoints)} of {len(mapping)}")
    print(f"size: {FULL_FONT.stat().st_size / 1024:.1f} KB -> {FONT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
