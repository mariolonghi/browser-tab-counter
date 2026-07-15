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
                 "prefs", "history"],
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
        "NSHumanReadableCopyright": "© 2026 Mario Longhi",
        "NSAppleEventsUsageDescription": (
            "Browser Tab Counter reads how many tabs are open in your browsers "
            "so it can show the total in the menu bar."
        ),
    },
}

setup(
    app=APP,
    name="Browser Tab Counter",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
