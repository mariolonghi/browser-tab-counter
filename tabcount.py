"""Count open browser tabs across all running browsers on macOS.

Two counting methods, chosen per browser:

* **AppleScript** (via ``osascript``) — Safari + every Chromium-family browser
  (Chrome, Edge, Brave, Vivaldi, Opera, Arc, …). Needs the standard macOS
  *Automation* permission (user-granted, no admin) the first time each browser
  is queried.
* **Session-file parse** — Firefox and its forks (LibreWolf, Waterfox, Zen)
  have no usable tab-scripting API, so we read their ``sessionstore`` file
  instead. It is compressed with Mozilla's ``mozLz4`` container; we decode it
  with a small pure-Python LZ4 block decompressor (no third-party deps).

This module is UI-free so it can be exercised straight from the command line:

    python3 tabcount.py

NOTE on distribution: the Firefox path reads files under
``~/Library/Application Support/Firefox``. That works for a drag-to-install
(notarized) build, but NOT inside a Mac App Store sandbox — see the dossier's
distribution notes.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Browser registry
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Browser:
    name: str                 # display name (also the AppleScript app name)
    method: str               # "chromium" | "safari" | "firefox"
    proc_names: tuple[str, ...] = ()   # System Events process name(s); default = name
    app_support: str = ""     # for firefox method: dir under ~/Library/Application Support

    @property
    def running_keys(self) -> tuple[str, ...]:
        return self.proc_names or (self.name,)


BROWSERS: list[Browser] = [
    Browser("Safari", "safari"),
    # Chromium family — all share the Chrome scripting dictionary.
    Browser("Google Chrome", "chromium"),
    Browser("Google Chrome Beta", "chromium"),
    Browser("Google Chrome Canary", "chromium"),
    Browser("Chromium", "chromium"),
    Browser("Microsoft Edge", "chromium"),
    Browser("Brave Browser", "chromium"),
    Browser("Vivaldi", "chromium"),
    Browser("Opera", "chromium"),
    Browser("Opera GX", "chromium"),
    Browser("Arc", "chromium"),
    Browser("Sidekick", "chromium"),
    Browser("Yandex", "chromium"),
    # Firefox family — session-file parse.
    # NOTE: regular Firefox and Firefox Developer Edition both run as process
    # "firefox" and share the ~/Library/Application Support/Firefox/Profiles
    # tree, so a single entry covers both (a separate one would double-count).
    Browser("Firefox", "firefox", proc_names=("firefox",), app_support="Firefox"),
    Browser("LibreWolf", "firefox", proc_names=("librewolf",), app_support="librewolf"),
    Browser("Waterfox", "firefox", proc_names=("waterfox",), app_support="Waterfox"),
    Browser("Zen Browser", "firefox", proc_names=("zen",), app_support="zen"),
]


@dataclass
class BrowserCount:
    name: str
    running: bool
    tabs: int | None          # None => running but count failed (e.g. permission denied)
    error: str | None = None


# --------------------------------------------------------------------------
# AppleScript path (Safari + Chromium)
# --------------------------------------------------------------------------

_COUNT_SCRIPT = (
    'tell application "{app}"\n'
    "  set n to 0\n"
    "  repeat with w in windows\n"
    "    set n to n + (count of tabs of w)\n"
    "  end repeat\n"
    "  return n\n"
    "end tell"
)


def _osascript(script: str) -> tuple[bool, str]:
    """Run an AppleScript, returning (ok, stdout-or-stderr)."""
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def _count_via_applescript(app_name: str) -> tuple[int | None, str | None]:
    ok, out = _osascript(_COUNT_SCRIPT.format(app=app_name))
    if not ok:
        return None, out
    try:
        return int(out), None
    except ValueError:
        return None, f"bad output: {out!r}"


# --------------------------------------------------------------------------
# Firefox path (mozLz4 session-file parse)
# --------------------------------------------------------------------------

_MOZLZ4_MAGIC = b"mozLz40\0"


def _lz4_decompress_block(src: bytes, expected_size: int) -> bytes:
    """Decode a raw LZ4 block (the format Mozilla wraps in mozLz4).

    Pure Python so nothing needs compiling into the app bundle.
    """
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        # literals
        lit_len = token >> 4
        if lit_len == 15:
            while True:
                b = src[i]
                i += 1
                lit_len += b
                if b != 255:
                    break
        out += src[i:i + lit_len]
        i += lit_len
        if i >= n:
            break
        # match
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while True:
                b = src[i]
                i += 1
                match_len += b
                if b != 255:
                    break
        start = len(out) - offset
        for j in range(match_len):
            out.append(out[start + j])
    if expected_size and len(out) != expected_size:
        # Not fatal — some writers pad — but worth surfacing in debugging.
        pass
    return bytes(out)


def _read_mozlz4(path: Path) -> bytes:
    data = path.read_bytes()
    if data[:8] != _MOZLZ4_MAGIC:
        raise ValueError("not a mozLz4 file")
    expected = int.from_bytes(data[8:12], "little")
    return _lz4_decompress_block(data[12:], expected)


def _firefox_session_file(app_support: str) -> Path | None:
    """Most recently updated sessionstore for a Firefox-family profile."""
    base = Path.home() / "Library" / "Application Support" / app_support / "Profiles"
    if not base.exists():
        return None
    # While running, recovery.jsonlz4 is the live file; fall back to the
    # on-close sessionstore.jsonlz4.
    candidates = list(base.glob("*/sessionstore-backups/recovery.jsonlz4"))
    candidates += list(base.glob("*/sessionstore.jsonlz4"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _count_via_firefox(app_support: str) -> tuple[int | None, str | None]:
    path = _firefox_session_file(app_support)
    if path is None:
        return None, "no session file"
    try:
        raw = _read_mozlz4(path)
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - report, don't crash the menu bar
        return None, f"{type(exc).__name__}: {exc}"
    total = 0
    for w in data.get("windows", []):
        total += len(w.get("tabs", []))
    return total, None


# --------------------------------------------------------------------------
# Running-process detection
# --------------------------------------------------------------------------


def running_process_names() -> set[str]:
    """Lower-cased names of visible (non-background) processes currently running."""
    ok, out = _osascript(
        'tell application "System Events" to get name of '
        "(processes where background only is false)"
    )
    if not ok:
        return set()
    return {p.strip().lower() for p in out.split(",")}


def _is_running(browser: Browser, running: set[str]) -> bool:
    return any(key.lower() in running for key in browser.running_keys)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def count_browser(browser: Browser, running: set[str]) -> BrowserCount:
    if not _is_running(browser, running):
        return BrowserCount(name=browser.name, running=False, tabs=0)

    if browser.method == "firefox":
        tabs, err = _count_via_firefox(browser.app_support)
    else:  # chromium / safari
        tabs, err = _count_via_applescript(browser.name)

    return BrowserCount(name=browser.name, running=True, tabs=tabs, error=err)


def count_all() -> list[BrowserCount]:
    """Count tabs for every known browser that is currently running."""
    running = running_process_names()
    return [count_browser(b, running) for b in BROWSERS]


def total_tabs(counts: list[BrowserCount]) -> int:
    return sum(c.tabs or 0 for c in counts)


if __name__ == "__main__":
    counts = count_all()
    active = [c for c in counts if c.running]
    if not active:
        print("No supported browsers are running.")
    for c in active:
        if c.tabs is None:
            print(f"  {c.name:<26} ERROR: {c.error}")
        else:
            print(f"  {c.name:<26} {c.tabs}")
    print(f"\nTOTAL: {total_tabs(counts)} tab(s)")
