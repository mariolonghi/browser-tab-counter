"""Shared, dependency-light app metadata.

Imported by setup.py (build), app.py (UI) and permissions.py — so keep this to
the standard library only (no rumps / PyObjC) or the build import will break.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

VERSION = "0.4.0"  # threshold alert + tabs-over-time history
APP_NAME = "Browser Tab Counter"
BUNDLE_ID = "com.mariolonghi.browsertabcounter"
WEBSITE = "https://mariolonghi.com"
POLL_SECONDS = 4

# Update checks (About panel) point at the GitHub Releases of this repo.
GITHUB_REPO = "mariolonghi/browser-tab-counter"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"


def is_frozen() -> bool:
    """True when running inside a py2app .app bundle."""
    return bool(getattr(sys, "frozen", False))


def bundle_path() -> Path:
    """The .app bundle when frozen, else the source directory."""
    if is_frozen():
        # .../Browser Tab Counter.app/Contents/MacOS/<bin> -> the .app
        return Path(sys.executable).resolve().parents[2]
    return Path(__file__).resolve().parent


def install_date() -> datetime | None:
    """Best-effort install date: creation time of the app bundle on disk."""
    try:
        st = os.stat(bundle_path())
        ts = getattr(st, "st_birthtime", st.st_mtime)
        return datetime.fromtimestamp(ts)
    except OSError:
        return None
