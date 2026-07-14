"""py2app build config for Browser Tab Counter.

Build a standalone menu-bar .app:

    ./.venv/bin/python setup.py py2app

Or use ./build_dmg.sh to produce a distributable .dmg.
"""

from setuptools import setup

APP = ["app.py"]

OPTIONS = {
    "argv_emulation": False,          # menu-bar app; Carbon argv emulation not needed
    "includes": ["tabcount", "login_item"],
    "packages": ["rumps"],
    "plist": {
        "CFBundleName": "Browser Tab Counter",
        "CFBundleDisplayName": "Browser Tab Counter",
        "CFBundleIdentifier": "com.mariolonghi.browsertabcounter",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
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
