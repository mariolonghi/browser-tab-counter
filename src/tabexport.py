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
import html
from dataclasses import dataclass
from datetime import datetime

import appinfo
import tabcount
from i18n import _, format_datetime, ngettext

# Control-char delimiters — vanishingly unlikely inside a title/URL.
_FS = "\x1f"
_RS = "\x1e"


class ExportError(Exception):
    """A browser could not be read. Raised rather than returning an empty
    list, so a timeout is never silently presented as "you have no tabs".
    """


# Reading every tab is bulk-fetched now, so even thousands of tabs finish in
# about a second. The generous ceiling is a safety net, not the normal path.
GATHER_TIMEOUT = 60

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

# Ask for each property of *every* tab in one go. Reading `title of t` per tab
# costs one Apple Event round-trip each, so a browser with hundreds of tabs took
# tens of seconds (measured: 53 ms/tab, ~11 s for 213 tabs). Bulk access is one
# round-trip per property per window, which is ~27x faster and scales with the
# number of windows rather than tabs. See issue #1.
_CHROMIUM_SCRIPT = (
    "set FS to (character id 31)\n"
    "set RS to (character id 30)\n"
    "set acc to {{}}\n"
    'tell application "{app}"\n'
    "  set wi to 0\n"
    "  repeat with w in windows\n"
    "    set wi to wi + 1\n"
    "    set atc to (active tab index of w)\n"
    '    set wmode to "normal"\n'
    "    try\n"
    "      set wmode to (mode of w)\n"
    "    end try\n"
    "    set tt to title of every tab of w\n"
    "    set uu to URL of every tab of w\n"
    "    set ll to {{}}\n"
    "    try\n"
    "      set ll to loading of every tab of w\n"
    "    end try\n"
    "    repeat with k from 1 to (count of tt)\n"
    '      set ld to ""\n'
    "      try\n"
    "        set ld to (item k of ll) as text\n"
    "      end try\n"
    "      set end of acc to ((wi as text) & FS & (k as text) & FS & "
    "(atc as text) & FS & wmode & FS & ld & FS & (item k of tt) & FS & "
    "(item k of uu))\n"
    "    end repeat\n"
    "  end repeat\n"
    "end tell\n"
    "set AppleScript's text item delimiters to RS\n"
    "set outp to acc as text\n"
    'set AppleScript\'s text item delimiters to ""\n'
    "return outp"
)

_SAFARI_SCRIPT = (
    "set FS to (character id 31)\n"
    "set RS to (character id 30)\n"
    "set acc to {}\n"
    'tell application "Safari"\n'
    "  set wi to 0\n"
    "  repeat with w in windows\n"
    "    set wi to wi + 1\n"
    "    set cti to 0\n"
    "    try\n"
    "      set cti to (index of current tab of w)\n"
    "    end try\n"
    "    try\n"
    "      set tt to name of every tab of w\n"
    "      set uu to URL of every tab of w\n"
    "      repeat with k from 1 to (count of tt)\n"
    "        set end of acc to ((wi as text) & FS & (k as text) & FS & "
    "(cti as text) & FS & (item k of tt) & FS & (item k of uu))\n"
    "      end repeat\n"
    "    end try\n"
    "  end repeat\n"
    "end tell\n"
    "set AppleScript's text item delimiters to RS\n"
    "set outp to acc as text\n"
    'set AppleScript\'s text item delimiters to ""\n'
    "return outp"
)


def _yesno(value: str) -> str:
    """AppleScript booleans arrive as "true"/"false"; the CSV uses yes/no."""
    v = (value or "").strip().lower()
    return "yes" if v == "true" else ("no" if v == "false" else "")


def _records(out: str):
    for rec in out.split(_RS):
        rec = rec.strip("\n")
        if rec:
            yield rec.split(_FS)


def _chromium_gather(browser: tabcount.Browser) -> list[Tab]:
    ok, out = tabcount._osascript(_CHROMIUM_SCRIPT.format(app=browser.name),
                                  timeout=GATHER_TIMEOUT)
    if not ok:
        raise ExportError(f"{browser.name}: {out or 'could not be read'}")
    if not out:
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
            loading=_yesno(p[4]), window_mode=p[3],
            title=p[5], url=p[6],
        ))
    return rows


def _safari_gather(browser: tabcount.Browser) -> list[Tab]:
    ok, out = tabcount._osascript(_SAFARI_SCRIPT, timeout=GATHER_TIMEOUT)
    if not ok:
        raise ExportError(f"{browser.name}: {out or 'could not be read'}")
    if not out:
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


def disclaimer_text() -> str:
    """Plain-text provenance note for the CSV footer row. The HTML report shows
    the same information as markup (with a real link) in its <footer>; both read
    APP_NAME / VERSION / GITHUB_REPO from appinfo, so they can't drift."""
    return (
        f"Generated by {appinfo.APP_NAME} v{appinfo.VERSION}, a macOS menu-bar "
        "app that counts your open browser tabs across every browser. "
        "This file is a local snapshot: it was created on your Mac and nothing "
        f"was sent anywhere. https://github.com/{appinfo.GITHUB_REPO}"
    )


def write_csv(rows: list[Tab], path: str) -> int:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow([getattr(r, k) for k in FIELDS])
        # Blank separator + provenance line, so it reads as a footnote rather
        # than another data row when opened in a spreadsheet.
        writer.writerow([])
        writer.writerow([disclaimer_text()])
    return len(rows)


# --------------------------------------------------------------------------
# HTML report (self-contained, links clickable, sortable columns)
# --------------------------------------------------------------------------

# Only these schemes get turned into clickable links. Anything else (javascript:,
# data:, file:, custom app schemes…) is shown as plain text, so opening the
# report can never execute something odd on a click.
_LINKABLE_SCHEMES = ("http://", "https://")

_HTML_STYLE = """
:root { color-scheme: light dark; }
body { font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
       margin: 2rem 1.5rem; }
h1 { font-size: 1.25rem; margin: 0 0 .25rem; }
p.meta { color: #888; margin: 0 0 1.25rem; }
.wrap { overflow-x: auto; }              /* never break the page layout */
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid rgba(127,127,127,.28);
         white-space: nowrap; }
th { position: sticky; top: 0; background: Canvas; cursor: pointer;
     user-select: none; border-bottom-width: 2px; }
th:hover { background: rgba(127,127,127,.15); }
th .arrow { opacity: .5; font-size: .8em; }
tbody tr:nth-child(even) { background: rgba(127,127,127,.05); }
tbody tr:hover { background: rgba(127,127,127,.13); }
footer { margin-top: 1.5rem; padding-top: .9rem; color: #888; font-size: 12px;
         border-top: 1px solid rgba(127,127,127,.28); }
footer a { color: inherit; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
/* Keep long titles/URLs on one line with an ellipsis; the full text is in the
   tooltip (and, for links, the href), so nothing is lost. */
td.title, td.url { max-width: 38ch; overflow: hidden; text-overflow: ellipsis; }
td.url a { color: inherit; text-decoration-color: rgba(127,127,127,.6); }
"""

# Sorting: click a header to sort by that column, click again to reverse.
# Numeric columns sort numerically, everything else case-insensitively.
_HTML_SCRIPT = """
document.querySelectorAll('th').forEach(function (th, idx) {
  th.addEventListener('click', function () {
    var tbody = th.closest('table').querySelector('tbody');
    var rows = Array.prototype.slice.call(tbody.rows);
    var numeric = th.dataset.numeric === '1';
    var dir = th.dataset.dir === 'asc' ? -1 : 1;
    document.querySelectorAll('th').forEach(function (o) {
      delete o.dataset.dir;
      var a = o.querySelector('.arrow'); if (a) a.textContent = '';
    });
    th.dataset.dir = dir === 1 ? 'asc' : 'desc';
    var arrow = th.querySelector('.arrow');
    if (arrow) arrow.textContent = dir === 1 ? '▲' : '▼';
    rows.sort(function (a, b) {
      var x = a.cells[idx].dataset.sort, y = b.cells[idx].dataset.sort;
      if (numeric) return (parseFloat(x) - parseFloat(y)) * dir;
      return x.toLowerCase().localeCompare(y.toLowerCase()) * dir;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  });
});
"""

_NUMERIC_FIELDS = {"window", "tab"}

# Same columns as the CSV, but ordered for reading: what the tab *is* (title and
# link) comes before the per-tab flags.
_HTML_FIELDS = ["browser", "window", "tab", "title", "url",
                "active", "pinned", "loading", "window_mode", "last_accessed"]

_REPO_URL = html.escape(f"https://github.com/{appinfo.GITHUB_REPO}", quote=True)


def _cell_html(field: str, value) -> str:
    """One <td>. Everything is escaped; only http(s) URLs become links.

    Long title/URL cells are clipped with an ellipsis in CSS and carry the full
    text as a tooltip, so the table stays readable without losing anything.
    """
    text = "" if value is None else str(value)
    esc = html.escape(text)
    sort_key = html.escape(text, quote=True)
    tip = f' title="{sort_key}"' if field in ("title", "url") else ""

    if field == "url" and text.lower().startswith(_LINKABLE_SCHEMES):
        href = html.escape(text, quote=True)
        return (f'<td class="url" data-sort="{sort_key}"{tip}>'
                f'<a href="{href}" target="_blank" rel="noopener noreferrer">'
                f'{esc}</a></td>')
    css = ' class="num"' if field in _NUMERIC_FIELDS else (
        f' class="{field}"' if field in ("title", "url") else "")
    return f'<td{css} data-sort="{sort_key}"{tip}>{esc}</td>'


def write_html(rows: list[Tab], path: str, generated: datetime | None = None) -> int:
    """Write a self-contained HTML report: one row per tab, sortable columns,
    clickable links. No external assets, so it works offline from disk."""
    when = format_datetime(generated or datetime.now())
    browsers = sorted({r.browser for r in rows})

    head = "".join(
        f"<th data-numeric='{1 if f in _NUMERIC_FIELDS else 0}'>"
        f"{html.escape(_(f.replace(chr(95), chr(32))))} <span class='arrow'></span></th>"
        for f in _HTML_FIELDS
    )
    body = "\n".join(
        "<tr>" + "".join(_cell_html(f, getattr(r, f)) for f in _HTML_FIELDS) + "</tr>"
        for r in rows
    )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Open tabs {html.escape(when)}</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<h1>{_('Open browser tabs')}</h1>
<p class="meta">{html.escape(ngettext("{n} tab across {browsers} · captured {when} · click a column heading to sort", "{n} tabs across {browsers} · captured {when} · click a column heading to sort", len(rows)).format(n=len(rows), browsers=", ".join(browsers) or _("no browsers"), when=when))}</p>
<div class="wrap">
<table>
<thead><tr>{head}</tr></thead>
<tbody>
{body}
</tbody>
</table>
</div>
<footer>
Generated by <strong>{html.escape(appinfo.APP_NAME)}</strong>
v{html.escape(appinfo.VERSION)}, a macOS menu-bar app that counts your open
browser tabs across every browser.
This file is a local snapshot: it was created on your Mac and nothing was sent
anywhere.<br>
<a href="{_REPO_URL}" target="_blank" rel="noopener noreferrer">{html.escape(appinfo.GITHUB_REPO)}</a>
</footer>
<script>{_HTML_SCRIPT}</script>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return len(rows)


if __name__ == "__main__":
    import sys
    dest = sys.argv[1] if len(sys.argv) > 1 else "open-tabs.csv"
    tabs = gather_all()
    n = write_html(tabs, dest) if dest.lower().endswith(".html") else write_csv(tabs, dest)
    print(f"wrote {n} tab(s) to {dest}")
    for r in tabs[:12]:
        print(f"  [{r.browser}] w{r.window}t{r.tab} active={r.active} {r.title[:45]!r}")
