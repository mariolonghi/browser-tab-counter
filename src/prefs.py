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
}


def ensure_dir() -> None:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    try:
        data = json.loads(PREFS_PATH.read_text())
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
    PREFS_PATH.write_text(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    print("prefs path:", PREFS_PATH)
    print("current:", load())
