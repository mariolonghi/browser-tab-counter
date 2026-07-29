"""Tiny local preferences store.

A single JSON file under the app's Application Support directory. No cloud, no
telemetry — just user-owned settings on disk. Shared by the threshold alert and
the tabs-over-time history (which keeps its data alongside).
"""

from __future__ import annotations

import json
from pathlib import Path

APP_SUPPORT = Path.home() / "Library" / "Application Support" / "BrowserTabCounter"
PREFS_PATH = APP_SUPPORT / "prefs.json"

DEFAULTS: dict = {
    "threshold": 0,          # alert when total > threshold; 0 = off
    "first_run_done": False,  # first launch enables Launch-at-Login by default
}


def ensure_dir() -> None:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    try:
        data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**DEFAULTS, **data}
    except (OSError, ValueError):
        pass
    return dict(DEFAULTS)


def get(key: str, default=None):
    return load().get(key, DEFAULTS.get(key, default))


def update(key: str, value) -> dict:
    ensure_dir()
    data = load()
    data[key] = value
    # Atomic write (temp file + rename): a crash mid-write can never leave a
    # truncated/corrupt prefs.json behind.
    tmp = PREFS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(PREFS_PATH)
    return data


if __name__ == "__main__":
    print("prefs path:", PREFS_PATH)
    print("current:", load())
