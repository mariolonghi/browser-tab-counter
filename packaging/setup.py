"""py2app build config for Browser Tab Counter.

The app modules live in ../src; this file lives in packaging/. Build from the
repo root (build_dmg.sh does this for you):

    ./.venv/bin/python packaging/setup.py py2app   # -> dist/ at the repo root

Or just run ./packaging/build_dmg.sh to produce a distributable .dmg.
"""

import os
import sys

from setuptools import setup

# Make the app modules in ../src importable (for `import appinfo` below and for
# py2app's dependency analysis), regardless of the current working directory.
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, _SRC)

import appinfo  # noqa: E402 - resolved via the sys.path insert above

APP = [os.path.join(_SRC, "app.py")]

OPTIONS = {
    "argv_emulation": False,          # menu-bar app; Carbon argv emulation not needed
    "includes": ["tabcount", "login_item", "appinfo", "permissions", "updates",
                 "prefs", "history", "tabexport", "selfupdate",
                 "i18n", "translations"],
    "packages": ["rumps", "certifi"],
    # We never use tkinter; excluding it drops the Tcl/Tk frameworks (smaller
    # bundle + fewer binaries for notarization to scrutinize).
    "excludes": ["tkinter"],
    "plist": {
        "CFBundleName": "Browser Tab Counter",
        "CFBundleDisplayName": "Browser Tab Counter",
        "CFBundleIdentifier": appinfo.BUNDLE_ID,
        "CFBundleVersion": appinfo.VERSION,
        "CFBundleShortVersionString": appinfo.VERSION,
        "LSUIElement": True,          # menu-bar only, no Dock icon / no app window
        "LSMinimumSystemVersion": "11.0",
        # Declare the languages we ship. Without this macOS treats the app as
        # English-only and won't offer it in System Settings › General ›
        # Language & Region › Applications (the per-app language override).
        "CFBundleDevelopmentRegion": "en",
        "CFBundleLocalizations": ["en", "sv", "es", "de"],
        # Run the frozen interpreter in UTF-8 mode. Launched from Finder an app
        # inherits a C/POSIX locale, so without this, subprocess text output and
        # file I/O would default to ASCII and crash on non-ASCII (em dashes,
        # accents, emoji…). Belt-and-suspenders with per-call encoding="utf-8".
        "LSEnvironment": {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        "NSHumanReadableCopyright": "© 2026 Mario Longhi",
        "NSAppleEventsUsageDescription": (
            "Browser Tab Counter reads how many tabs are open in your browsers "
            "so it can show the total in the menu bar."
        ),
    },
}

# macOS reads the Automation-prompt text from Info.plist, so it can't be
# localised in Python — it needs an InfoPlist.strings per .lproj in Resources.
_LOCALES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
DATA_FILES = [
    (name, [os.path.join(_LOCALES, name, "InfoPlist.strings")])
    for name in sorted(os.listdir(_LOCALES))
    if name.endswith(".lproj")
]

setup(
    app=APP,
    name="Browser Tab Counter",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
