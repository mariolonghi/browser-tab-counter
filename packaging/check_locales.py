#!/usr/bin/env python3
"""Verify the app's three lists of languages agree with each other.

There are three places a language has to exist, and drift between them is
invisible at runtime:

  1. packaging/locales/<lang>.lproj/InfoPlist.strings — the macOS permission
     prompt (rendered by macOS, not by our Python).
  2. CFBundleLocalizations in setup.py — what macOS is *told* we support, which
     is what populates the per-app language picker in System Settings.
  3. src/translations.py CATALOGUES — the actual app UI (menus, dialogs, About).

Declaring a language in 1+2 but not 3 is the nasty case: macOS offers the
language and the permission prompt is translated, but every menu stays English.

Parses each .strings file and compares key SETS against English (order doesn't
matter). Fails on missing/extra/duplicate keys, empty values, and any mismatch
between the three lists, reporting every problem before exiting. Stdlib only.

Usage: python3 packaging/check_locales.py
"""

import ast
import pathlib
import re
import sys

SETUP_PY = pathlib.Path(__file__).resolve().parent / "setup.py"

LOCALES_DIR = pathlib.Path(__file__).resolve().parent / "locales"
TRANSLATIONS_PY = (pathlib.Path(__file__).resolve().parent.parent
                   / "src" / "translations.py")
REFERENCE = "en"

# "key" = "value";  — quoted segments may contain escaped characters (\" \n \\)
PAIR_RE = re.compile(
    r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;'
)


def read_strings(path):
    """Decode a .strings file (UTF-8 by default, UTF-16 if BOM present)."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def parse(name, path, errors):
    """Return {key: value} for one locale, appending problems to errors."""
    text = read_strings(path)
    # Strip /* ... */ block comments and // line comments so commented-out
    # pairs aren't parsed as live keys.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)

    pairs = {}
    for match in PAIR_RE.finditer(text):
        key, value = match.group(1), match.group(2)
        if key in pairs:
            errors.append(f"{name}: duplicate key \"{key}\"")
        if not value.strip():
            errors.append(f"{name}: empty value for key \"{key}\"")
        pairs[key] = value
    return pairs


def declared_localizations():
    """Extract the CFBundleLocalizations list from setup.py without executing it."""
    tree = ast.parse(SETUP_PY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if (
                isinstance(key, ast.Constant)
                and key.value == "CFBundleLocalizations"
                and isinstance(value, (ast.List, ast.Tuple))
            ):
                return [
                    el.value for el in value.elts
                    if isinstance(el, ast.Constant) and isinstance(el.value, str)
                ]
    return None


def ui_catalogue_languages():
    """Language codes in src/translations.py CATALOGUES, without importing it.

    Read via AST so this script stays dependency-free and never executes app
    code. English is the source language and has no catalogue, so it's implied.
    """
    try:
        tree = ast.parse(TRANSLATIONS_PY.read_text(encoding="utf-8"))
    except OSError:
        return None
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if (isinstance(target, ast.Name) and target.id == "CATALOGUES"
                    and isinstance(node.value, ast.Dict)):
                return [k.value for k in node.value.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    return None


def check_plist_parity(locales, errors):
    """CFBundleLocalizations must list exactly the .lproj folders we ship."""
    declared = declared_localizations()
    if declared is None:
        errors.append(f"{SETUP_PY.name}: CFBundleLocalizations list not found")
        return
    for name in sorted(set(locales) - set(declared)):
        errors.append(
            f"{SETUP_PY.name}: {name}.lproj exists but \"{name}\" is not in "
            f"CFBundleLocalizations"
        )
    for name in sorted(set(declared) - set(locales)):
        errors.append(
            f"{SETUP_PY.name}: CFBundleLocalizations declares \"{name}\" but "
            f"{name}.lproj does not exist"
        )


def check_ui_parity(locales, errors):
    """Every language we advertise must also have a translated app UI.

    Without this, a language can be offered in System Settings with a
    translated permission prompt while every menu and dialog stays English.
    """
    ui = ui_catalogue_languages()
    if ui is None:
        errors.append(f"{TRANSLATIONS_PY.name}: CATALOGUES dict not found")
        return
    ui_langs = set(ui) | {REFERENCE}          # English is the source language
    for name in sorted(set(locales) - ui_langs):
        errors.append(
            f"{TRANSLATIONS_PY.name}: \"{name}\" is advertised (.lproj + "
            f"CFBundleLocalizations) but has no UI catalogue — menus and "
            f"dialogs would stay English"
        )
    for name in sorted(ui_langs - set(locales) - {REFERENCE}):
        errors.append(
            f"{TRANSLATIONS_PY.name}: UI catalogue \"{name}\" exists but "
            f"{name}.lproj does not — the permission prompt would stay English"
        )


def main():
    errors = []
    files = sorted(LOCALES_DIR.glob("*.lproj/InfoPlist.strings"))
    locales = {f.parent.name[: -len(".lproj")]: f for f in files}

    if REFERENCE not in locales:
        sys.exit(f"error: reference locale {REFERENCE}.lproj not found in {LOCALES_DIR}")

    en_keys = set(parse(REFERENCE, locales[REFERENCE], errors))
    if not en_keys:
        sys.exit(f"error: no keys parsed from {locales[REFERENCE]}")

    for name, path in locales.items():
        if name == REFERENCE:
            continue
        keys = set(parse(name, path, errors))
        for key in sorted(en_keys - keys):
            errors.append(f"{name}: missing key \"{key}\"")
        for key in sorted(keys - en_keys):
            errors.append(f"{name}: extra key \"{key}\" not present in {REFERENCE}")

    check_plist_parity(locales, errors)
    check_ui_parity(locales, errors)

    if errors:
        print(f"{len(errors)} problem(s) found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print(
        f"OK: {len(en_keys)} prompt key(s) consistent across "
        f"{len(locales)} locales ({', '.join(sorted(locales))}); "
        f"CFBundleLocalizations and the UI catalogues agree."
    )


if __name__ == "__main__":
    main()
