"""Export a snapshot of every open tab to a CSV — on demand only.

Unlike the counter (which reads only numbers), this captures each tab's **title
and URL** plus whatever extras a browser exposes (active/pinned/loading/window
mode/last-accessed). It is therefore strictly **user-initiated** from the menu,
**read-only**, **local**, and keeps nothing: it gathers when asked, writes the
file the user picks, and forgets.

Sources (same mechanisms as counting, no new permissions):
  * Safari + Chromium — AppleScript.
  * Firefox family — the sessionstore we already parse.

Private/incognito windows don't appear (browsers don't expose them), same as the
count.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime

import tabcount

# Control-char delimiters — vanishingly unlikely inside a title/URL.
_FS = "\x1f"
_RS = "\x1e"

# CSV column order.
FIELDS = [
    "browser", "window", "tab", "active", "pinned", "loading",
    "window_mode", "last_accessed", "title", "url",
]


@dataclass
class Tab:
    browser: str
    window: int
    tab: int
    active: str = "no"        # yes/no
    pinned: str = ""          # yes/no/"" (Firefox)
    loading: str = ""         # yes/no/"" (Chromium)
    window_mode: str = ""     # normal/incognito/"" (Chromium)
    last_accessed: str = ""   # ISO 8601/"" (Firefox)
    title: str = ""
    url: str = ""


# --------------------------------------------------------------------------
# AppleScript gather (Safari + Chromium)
# --------------------------------------------------------------------------

_CHROMIUM_SCRIPT = (
    "set FS to (character id 31)\n"
    "set RS to (character id 30)\n"
    'tell application "{app}"\n'
    '  set outp to ""\n'
    "  set wi to 0\n"
    "  repeat with w in windows\n"
    "    set wi to wi + 1\n"
    "    set atc to (active tab index of w)\n"
    '    set wmode to "normal"\n'
    "    try\n"
    "      set wmode to (mode of w)\n"
    "    end try\n"
    "    set ti to 0\n"
    "    repeat with t in tabs of w\n"
    "      set ti to ti + 1\n"
    '      set ld to "no"\n'
    "      try\n"
    '        if (loading of t) then set ld to "yes"\n'
    "      end try\n"
    "      set outp to outp & wi & FS & ti & FS & atc & FS & wmode & FS & ld "
    "& FS & (title of t) & FS & (URL of t) & RS\n"
    "    end repeat\n"
    "  end repeat\n"
    "  return outp\n"
    "end tell"
)

_SAFARI_SCRIPT = (
    "set FS to (character id 31)\n"
    "set RS to (character id 30)\n"
    'tell application "Safari"\n'
    '  set outp to ""\n'
    "  set wi to 0\n"
    "  repeat with w in windows\n"
    "    set wi to wi + 1\n"
    "    set cti to 0\n"
    "    try\n"
    "      set cti to (index of current tab of w)\n"
    "    end try\n"
    "    set ti to 0\n"
    "    try\n"
    "      repeat with t in tabs of w\n"
    "        set ti to ti + 1\n"
    "        set outp to outp & wi & FS & ti & FS & cti & FS & (name of t) "
    "& FS & (URL of t) & RS\n"
    "      end repeat\n"
    "    end try\n"
    "  end repeat\n"
    "  return outp\n"
    "end tell"
)


def _records(out: str):
    for rec in out.split(_RS):
        rec = rec.strip("\n")
        if rec:
            yield rec.split(_FS)


def _chromium_gather(browser: tabcount.Browser) -> list[Tab]:
    ok, out = tabcount._osascript(_CHROMIUM_SCRIPT.format(app=browser.name), timeout=20)
    if not ok or not out:
        return []
    rows: list[Tab] = []
    for p in _records(out):
        if len(p) < 7:
            continue
        try:
            wi, ti, atc = int(p[0]), int(p[1]), int(p[2])
        except ValueError:
            continue
        rows.append(Tab(
            browser=browser.name, window=wi, tab=ti,
            active="yes" if ti == atc else "no",
            loading=p[4], window_mode=p[3],
            title=p[5], url=p[6],
        ))
    return rows


def _safari_gather(browser: tabcount.Browser) -> list[Tab]:
    ok, out = tabcount._osascript(_SAFARI_SCRIPT, timeout=20)
    if not ok or not out:
        return []
    rows: list[Tab] = []
    for p in _records(out):
        if len(p) < 5:
            continue
        try:
            wi, ti, cti = int(p[0]), int(p[1]), int(p[2])
        except ValueError:
            continue
        rows.append(Tab(
            browser=browser.name, window=wi, tab=ti,
            active="yes" if ti == cti else "no",
            title=p[3], url=p[4],
        ))
    return rows


# --------------------------------------------------------------------------
# Firefox gather (session file)
# --------------------------------------------------------------------------

def _firefox_gather(browser: tabcount.Browser) -> list[Tab]:
    rows: list[Tab] = []
    for profile in tabcount._firefox_profile_dirs(browser.app_support):
        if not tabcount._profile_is_open(profile):
            continue
        data = tabcount._read_firefox_session(profile)
        if not data:
            continue
        for wi, w in enumerate(data.get("windows", []), start=1):
            selected = w.get("selected", 0)
            for ti, t in enumerate(w.get("tabs", []), start=1):
                entries = t.get("entries", [])
                if not entries:
                    continue
                cur = entries[-1]
                last = ""
                ms = t.get("lastAccessed")
                if ms:
                    try:
                        last = datetime.fromtimestamp(ms / 1000).isoformat(timespec="seconds")
                    except (ValueError, OSError, OverflowError):
                        last = ""
                rows.append(Tab(
                    browser=browser.name, window=wi, tab=ti,
                    active="yes" if ti == selected else "no",
                    pinned="yes" if t.get("pinned") else "no",
                    last_accessed=last,
                    title=cur.get("title", ""), url=cur.get("url", ""),
                ))
    return rows


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def gather_all() -> list[Tab]:
    """Snapshot every open tab across running browsers. On demand only."""
    running = tabcount.running_process_names()
    rows: list[Tab] = []
    for b in tabcount.BROWSERS:
        if not tabcount._is_running(b, running):
            continue
        if b.method == "firefox":
            rows += _firefox_gather(b)
        elif b.method == "safari":
            rows += _safari_gather(b)
        else:
            rows += _chromium_gather(b)
    return rows


def write_csv(rows: list[Tab], path: str) -> int:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow([getattr(r, k) for k in FIELDS])
    return len(rows)


if __name__ == "__main__":
    import sys
    dest = sys.argv[1] if len(sys.argv) > 1 else "open-tabs.csv"
    tabs = gather_all()
    n = write_csv(tabs, dest)
    print(f"wrote {n} tab(s) to {dest}")
    for r in tabs[:12]:
        print(f"  [{r.browser}] w{r.window}t{r.tab} active={r.active} {r.title[:45]!r}")
