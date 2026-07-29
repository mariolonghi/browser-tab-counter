"""Tests for the localisation layer.

Run:  ./.venv/bin/python tests/test_i18n.py
"""

from __future__ import annotations

import ast
import os
import pathlib
import sys

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

import i18n          # noqa: E402
import translations  # noqa: E402

# HTML column headings are looked up dynamically (_(field.replace("_", " "))),
# so a static scan can't see them as literals.
_DYNAMIC_KEYS = {
    "browser", "window", "tab", "title", "url", "active", "pinned",
    "loading", "window mode", "last accessed",
}


def _keys_used_in_source() -> set[str]:
    """Every literal passed to _() / gettext() / ngettext() across src/."""
    found: set[str] = set()
    for path in pathlib.Path(SRC).glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ("_", "gettext", "ngettext")):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(arg.value)
    return found


def test_every_used_string_is_translated():
    """A missing key silently ships English, so guard against typos/drift."""
    used = _keys_used_in_source()
    assert used, "no translatable strings found — did the scan break?"
    for lang, catalogue in translations.CATALOGUES.items():
        missing = sorted(k for k in used if k not in catalogue)
        assert not missing, f"{lang} is missing {len(missing)}: {missing[:3]}"


def test_no_stale_catalogue_entries():
    """Entries nobody uses are dead weight (and usually a renamed string)."""
    used = _keys_used_in_source() | _DYNAMIC_KEYS
    for lang, catalogue in translations.CATALOGUES.items():
        stale = sorted(k for k in catalogue if k not in used)
        assert not stale, f"{lang} has unused entries: {stale[:3]}"


def test_placeholders_survive_translation():
    """A translation that drops/renames {n} would crash at .format() time."""
    import re
    ph = re.compile(r"\{(\w+)\}")
    for lang, catalogue in translations.CATALOGUES.items():
        for source, translated in catalogue.items():
            assert set(ph.findall(source)) == set(ph.findall(translated)), \
                f"{lang}: placeholder mismatch in {source[:40]!r}"


def test_unknown_string_falls_back_to_english():
    i18n.set_language("sv")
    try:
        assert i18n._("Refresh now") == "Uppdatera nu"       # translated
        assert i18n._("not in any catalogue") == "not in any catalogue"
    finally:
        i18n.set_language(None)


def test_plural_forms_pick_the_right_variant():
    for lang in ("en", "sv", "es", "de"):
        i18n.set_language(lang)
        one = i18n.ngettext("{n} tab total", "{n} tabs total", 1)
        many = i18n.ngettext("{n} tab total", "{n} tabs total", 5)
        assert one != many, f"{lang}: singular and plural are identical"
    i18n.set_language(None)


def test_language_detection_prefers_a_supported_language():
    i18n.set_language(None)
    assert i18n.language() in i18n.available()


if __name__ == "__main__":
    test_every_used_string_is_translated()
    test_no_stale_catalogue_entries()
    test_placeholders_survive_translation()
    test_unknown_string_falls_back_to_english()
    test_plural_forms_pick_the_right_variant()
    test_language_detection_prefers_a_supported_language()
    print("all i18n tests passed")
