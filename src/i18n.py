"""Tiny localisation layer (English source strings + per-language catalogues).

Deliberately dict-based rather than gettext/.mo: the app has well under a
hundred strings, so plain Python dicts stay reviewable in a diff, need no
compilation step, and add nothing to the bundle beyond one module.

Language detection uses macOS's **AppleLanguages** preference, which respects a
per-app language override (System Settings › General › Language & Region ›
Applications). It deliberately does *not* trust Python's `locale` module: the
frozen app runs with PYTHONUTF8/C locale, so `locale.getlocale()` reports "C"
and would make everyone English.

Any string with no translation falls back to the English source, so a partial
catalogue is always safe.
"""

from __future__ import annotations

import os

import translations

DEFAULT_LANG = "en"
_lang: str | None = None


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

def available() -> list[str]:
    return [DEFAULT_LANG] + sorted(translations.CATALOGUES)


def _from_apple_languages() -> str | None:
    """The user's preferred languages, in order, as macOS reports them."""
    try:
        from Foundation import NSUserDefaults
        langs = NSUserDefaults.standardUserDefaults().objectForKey_("AppleLanguages")
    except Exception:  # noqa: BLE001 - PyObjC missing (tests, plain CLI runs)
        return None
    for tag in list(langs or []):
        base = str(tag).replace("_", "-").split("-")[0].lower()
        if base in translations.CATALOGUES or base == DEFAULT_LANG:
            return base
    return None


def _from_env() -> str | None:
    """Fallback for source runs / tests: honour the usual locale env vars."""
    for var in ("BTC_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var)
        if not val or val in ("C", "POSIX"):
            continue
        base = val.split(":")[0].split(".")[0].replace("_", "-").split("-")[0].lower()
        if base in translations.CATALOGUES or base == DEFAULT_LANG:
            return base
    return None


def language() -> str:
    global _lang
    if _lang is None:
        _lang = _from_apple_languages() or _from_env() or DEFAULT_LANG
    return _lang


def set_language(code: str | None) -> None:
    """Force a language (used by tests); None re-enables auto-detection."""
    global _lang
    _lang = code


# --------------------------------------------------------------------------
# Lookup
# --------------------------------------------------------------------------

def gettext(message: str) -> str:
    """Translate one English source string, falling back to English."""
    return translations.CATALOGUES.get(language(), {}).get(message, message)


# The conventional short alias.
_ = gettext


def ngettext(singular: str, plural: str, n: int) -> str:
    """Pick the singular or plural source string, then translate it.

    Swedish, Spanish and German all share English's one-vs-many rule, so a
    two-form choice is enough; a language needing more forms would want a real
    plural-rule function here.
    """
    return gettext(singular if n == 1 else plural)


def format_date(dt) -> str:
    """A medium-style date in the user's language ("14 Jul 2026", "14 juli 2026").

    Uses NSDateFormatter so month names come from macOS rather than from us.
    Falls back to an unambiguous ISO date if AppKit isn't available.
    """
    try:
        from Foundation import (NSDate, NSDateFormatter, NSLocale,
                                NSDateFormatterMediumStyle)
        fmt = NSDateFormatter.alloc().init()
        fmt.setDateStyle_(NSDateFormatterMediumStyle)
        fmt.setLocale_(NSLocale.alloc().initWithLocaleIdentifier_(language()))
        return str(fmt.stringFromDate_(
            NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())))
    except Exception:  # noqa: BLE001 - no PyObjC / odd date
        return dt.strftime("%Y-%m-%d")


def format_datetime(dt) -> str:
    """Date + time for the HTML report header, localised where possible."""
    try:
        from Foundation import (NSDate, NSDateFormatter, NSLocale,
                                NSDateFormatterMediumStyle,
                                NSDateFormatterShortStyle)
        fmt = NSDateFormatter.alloc().init()
        fmt.setDateStyle_(NSDateFormatterMediumStyle)
        fmt.setTimeStyle_(NSDateFormatterShortStyle)
        fmt.setLocale_(NSLocale.alloc().initWithLocaleIdentifier_(language()))
        return str(fmt.stringFromDate_(
            NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())))
    except Exception:  # noqa: BLE001
        return dt.strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    from datetime import datetime
    print("available:", available())
    print("detected :", language())
    for code in available():
        set_language(code)
        print(f"  [{code}] {_('Refresh now')!r} | {_('Quit')!r} | "
              f"{format_date(datetime.now())}")
