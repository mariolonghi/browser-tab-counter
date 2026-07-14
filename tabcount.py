"""Count open browser tabs across all running browsers on macOS.

Uses AppleScript (via `osascript`) to ask each running browser how many tabs it
has open. Requires the standard macOS *Automation* permission (user-granted, no
admin) the first time each browser is queried.

This module is UI-free so it can be exercised straight from the command line:

    python3 tabcount.py

Chromium-family browsers (Chrome, Edge, Brave, Vivaldi, Opera, Arc) share one
AppleScript dialect. Safari uses its own. Firefox has no usable tab-scripting
API and is intentionally out of POC scope (see the dossier).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

# name -> (macOS process name, AppleScript dialect)
# "chromium" = `count of tabs of windows` works via the Chrome dictionary.
# "safari"   = same idea, slightly different phrasing.
BROWSERS: dict[str, tuple[str, str]] = {
    "Safari": ("Safari", "safari"),
    "Google Chrome": ("Google Chrome", "chromium"),
    "Microsoft Edge": ("Microsoft Edge", "chromium"),
    "Brave Browser": ("Brave Browser", "chromium"),
    "Vivaldi": ("Vivaldi", "chromium"),
    "Opera": ("Opera", "chromium"),
    "Arc": ("Arc", "chromium"),
}

# Counting scripts per dialect. Kept deliberately tiny.
_COUNT_SCRIPT = {
    "chromium": (
        'tell application "{app}"\n'
        "  set n to 0\n"
        "  repeat with w in windows\n"
        "    set n to n + (count of tabs of w)\n"
        "  end repeat\n"
        "  return n\n"
        "end tell"
    ),
    "safari": (
        'tell application "{app}"\n'
        "  set n to 0\n"
        "  repeat with w in windows\n"
        "    set n to n + (count of tabs of w)\n"
        "  end repeat\n"
        "  return n\n"
        "end tell"
    ),
}


@dataclass
class BrowserCount:
    name: str
    running: bool
    tabs: int | None      # None => running but count failed (e.g. permission denied)
    error: str | None = None


def _osascript(script: str) -> tuple[bool, str]:
    """Run an AppleScript, returning (ok, stdout-or-stderr)."""
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def running_process_names() -> set[str]:
    """Names of visible (non-background) processes currently running."""
    ok, out = _osascript(
        'tell application "System Events" to get name of '
        "(processes where background only is false)"
    )
    if not ok:
        return set()
    return {p.strip() for p in out.split(",")}


def count_browser(name: str, running: set[str]) -> BrowserCount:
    proc_name, dialect = BROWSERS[name]
    if proc_name not in running:
        return BrowserCount(name=name, running=False, tabs=0)

    script = _COUNT_SCRIPT[dialect].format(app=name)
    ok, out = _osascript(script)
    if not ok:
        return BrowserCount(name=name, running=True, tabs=None, error=out)
    try:
        return BrowserCount(name=name, running=True, tabs=int(out))
    except ValueError:
        return BrowserCount(name=name, running=True, tabs=None, error=f"bad output: {out!r}")


def count_all() -> list[BrowserCount]:
    """Count tabs for every known browser that is currently running."""
    running = running_process_names()
    return [count_browser(name, running) for name in BROWSERS]


def total_tabs(counts: list[BrowserCount]) -> int:
    return sum(c.tabs or 0 for c in counts)


if __name__ == "__main__":
    counts = count_all()
    active = [c for c in counts if c.running]
    if not active:
        print("No supported browsers are running.")
    for c in active:
        if c.tabs is None:
            print(f"  {c.name:<18} ERROR: {c.error}")
        else:
            print(f"  {c.name:<18} {c.tabs}")
    print(f"\nTOTAL: {total_tabs(counts)} tab(s)")
