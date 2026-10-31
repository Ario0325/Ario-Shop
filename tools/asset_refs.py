"""Build a static-asset reference graph for safe cleanup.

Usage:
    python tools/asset_refs.py --check          # fail on broken references
    python tools/asset_refs.py --unreferenced   # list orphan static files
    python tools/asset_refs.py --check --include-sw
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

# Files that are deliberately not part of the reference graph yet. They are
# either served by a Django view or are untracked work in progress.
PROTECTED = {
    "sw.js",
    "assets/images/icons/site.webmanifest",
}
PROTECTED_PREFIXES = (
    "admin/",  # admin theme is actively being edited; never auto-delete
    "assets/css/ario-theme.css",  # untracked redesign leftovers
    "assets/css/tokens.css",
)

STATIC_TAG_RE = re.compile(r"{%\s*static\s+(['\"])(?P<path>.*?)\1")
STATIC_URL_RE = re.compile(r"/static/(?P<path>[^\"'\s)>]+)")
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(?P<path>[^'\")]+)\1\s*\)")
CSS_IMPORT_RE = re.compile(r"@import\s+(?:url\(\s*)?(['\"])(?P<path>[^'\"]+)\1")
JS_STATIC_RE = re.compile(r"['\"](/static/[^'\"]+)['\"]")
PY_STATIC_RE = re.compile(r"['\"]((?:admin|assets)/[^'\"]+\.(?:css|js))['\"]")

TEMPLATE_SKIP = {".git", "static", "staticfiles", "_shots", "docs", "tools", ".qoder"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def static_rel(ref: str) -> str:
    ref = ref.strip().split("?", 1)[0].split("#", 1)[0]
    if ref.startswith("/static/"):
        return ref[len("/static/"):]
    if ref.startswith("static/"):
        return ref[len("static/"):]
    return ref.lstrip("/")


def add_ref(refs: set[str], ref: str, source: Path) -> None:
    if not ref or "{{" in ref or "{%" in ref:
        return
    if ref.startswith(("data:", "http://", "https://", "//", "#", "mailto:", "tel:")):
        return
    if ref.startswith("/") and not ref.startswith("/static/"):
        return
    path = static_rel(ref)
    if path:
        refs.add(path)


def templates() -> list[Path]:
    result = []
    for path in ROOT.rglob("*.html"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & TEMPLATE_SKIP:
            continue
        result.append(path)
    return result


def collect_from_css(css_rel: str, refs: set[str], seen_css: set[str]) -> None:
    css_path = STATIC / css_rel
    if css_rel in seen_css or not css_path.is_file():
        return
    seen_css.add(css_rel)
    text = css_path.read_text(encoding="utf-8", errors="ignore")
    for match in list(CSS_URL_RE.finditer(text)) + list(CSS_IMPORT_RE.finditer(text)):
        raw = match.group("path").strip()
        if not raw or raw.startswith(("data:", "http://", "https://", "//", "#")):
            continue
        if raw.startswith("/static/"):
            target = static_rel(raw)
        elif raw.startswith("/"):
            continue
        else:
            resolved = (css_path.parent / raw).resolve()
            try:
                target = resolved.relative_to(STATIC).as_posix()
            except ValueError:
                continue
        refs.add(target)
        if target.lower().endswith(".css"):
            collect_from_css(target, refs, seen_css)


def collect_from_js(js_rel: str, refs: set[str], seen_js: set[str]) -> None:
    js_path = STATIC / js_rel
    if js_rel in seen_js or not js_path.is_file():
        return
    seen_js.add(js_rel)
    text = js_path.read_text(encoding="utf-8", errors="ignore")
    for match in JS_STATIC_RE.finditer(text):
        add_ref(refs, match.group(1), js_path)


def collect() -> tuple[set[str], list[tuple[str, str]]]:
    refs: set[str] = set()
    missing: list[tuple[str, str]] = []
    seen_css: set[str] = set()
    seen_js: set[str] = set()

    # Templates: {% static %}, direct /static/ URLs, referenced CSS/JS.
    for path in templates():
        text = path.read_text(encoding="utf-8", errors="ignore")
        found: list[str] = []
        found.extend(m.group("path") for m in STATIC_TAG_RE.finditer(text))
        found.extend(m.group("path") for m in STATIC_URL_RE.finditer(text))
        for raw in found:
            before = set(refs)
            add_ref(refs, raw, path)
            for added in set(refs) - before:
                target = STATIC / added
                # admin/css and admin/js are also provided by django.contrib.admin;
                # a missing project copy is not a broken reference.
                if not target.exists() and not added.startswith("admin/"):
                    missing.append((rel(path), added))
        for css in [r for r in found if r.lower().endswith(".css")]:
            collect_from_css(static_rel(css), refs, seen_css)
        for js in [r for r in found if r.lower().endswith(".js")]:
            collect_from_js(static_rel(js), refs, seen_js)

    # CSS recursively imported by referenced CSS was handled; scan remaining
    # referenced CSS again in case a template referenced it only by name.
    for css in [r for r in list(refs) if r.lower().endswith(".css")]:
        collect_from_css(css, refs, seen_css)
    for js in [r for r in list(refs) if r.lower().endswith(".js")]:
        collect_from_js(js, refs, seen_js)

    # Django admin Media classes.
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {".git", "static", "staticfiles", "_shots", "docs", "tools"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in PY_STATIC_RE.finditer(text):
            refs.add(match.group(1))

    # PWA manifest icons.
    manifest = STATIC / "assets/images/icons/site.webmanifest"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            for icon in data.get("icons", []):
                src = icon.get("src", "")
                if src:
                    add_ref(refs, src, manifest)
        except json.JSONDecodeError:
            pass

    return refs, missing


def sw_refs() -> set[str]:
    sw = STATIC / "sw.js"
    result: set[str] = set()
    if sw.is_file():
        for match in JS_STATIC_RE.finditer(sw.read_text(encoding="utf-8", errors="ignore")):
            result.add(static_rel(match.group(1)))
    return result


def is_protected(path: str) -> bool:
    return path in PROTECTED or path.startswith(PROTECTED_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail on missing references")
    parser.add_argument("--unreferenced", action="store_true", help="list orphan static files")
    parser.add_argument("--include-sw", action="store_true", help="treat sw.js cache list as references")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    refs, missing = collect()
    if args.include_sw:
        refs |= sw_refs()

    referenced_existing = {r for r in refs if (STATIC / r).exists()}
    all_files = {
        p.relative_to(STATIC).as_posix()
        for p in STATIC.rglob("*")
        if p.is_file()
    }
    orphans = sorted(
        (f for f in all_files - referenced_existing if not is_protected(f)),
        key=lambda f: (STATIC / f).stat().st_size,
        reverse=True,
    )
    missing_sorted = sorted(set(missing))
    sw_missing = sorted(r for r in sw_refs() if not (STATIC / r).exists())

    if args.json:
        payload = {
            "referenced": sorted(referenced_existing),
            "missing": [{"source": s, "path": p} for s, p in missing_sorted],
            "orphans": [{"path": p, "bytes": (STATIC / p).stat().st_size} for p in orphans],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Referenced existing static files: {len(referenced_existing)}")
        print(f"Missing references: {len(missing_sorted)}")
        for source, path in missing_sorted:
            print(f"  MISSING {path}  <- {source}")
        if args.unreferenced:
            total = sum((STATIC / p).stat().st_size for p in orphans)
            print(f"Unreferenced static files: {len(orphans)} ({total / 1024 / 1024:.1f} MB)")
            for path in orphans:
                size = (STATIC / path).stat().st_size
                print(f"  {size:>9}  {path}")
        if sw_missing:
            print(f"sw.js cache entries missing: {len(sw_missing)}")
            for path in sw_missing:
                print(f"  SW-MISSING {path}")

    if args.check and missing_sorted:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
