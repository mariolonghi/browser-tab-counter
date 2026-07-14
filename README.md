# Browser Tab Counter (macOS menu-bar POC)

A tiny macOS **menu-bar indicator** answering one question at a glance:

> **How many browser tabs do I have open right now — across all my browsers?**

It shows a single number near the clock (e.g. `⧉ 147`) and, on click, a
per-browser breakdown. No admin rights, no browser extension.

Design dossier (the "why" and the plan) lives at
`~/Documents/MLonghi/Project-1/Browser Tab Counter/`.

## What works

- Sums open tabs across **running** browsers:
  - **Safari + Chromium family** (Chrome/Beta/Canary, Chromium, Edge, Brave,
    Vivaldi, Opera, Opera GX, Arc, Sidekick, Yandex) via AppleScript.
  - **Firefox** (+ LibreWolf, Waterfox, Zen) via session-file parse — no
    AppleScript API exists, so we decode its `mozLz4` `recovery.jsonlz4` with a
    small pure-Python LZ4 decompressor (no third-party deps).
- Menu-bar number, updated every few seconds.
- Click → dropdown with per-browser counts, "Refresh now", and Quit.
- Only queries browsers that are actually running (never launches a closed one).

## ⚠️ Distribution note (Firefox + App Store)

The Firefox counter reads a file in the user's Firefox profile. That's fine for a
**drag-to-install (notarized)** build, but a **Mac App Store** build must be
sandboxed and **cannot read Firefox's files** — so an App Store edition would be
Safari + Chromium only. Full analysis: dossier `distribution.md`.

## Requirements

- macOS
- Python **3.9+** (this repo's venv uses Homebrew `python3.13`; the system
  `/usr/bin/python3` 3.8 is too old for PyObjC/rumps).

## Setup

```bash
cd ~/Project-1/browser-tab-counter
/opt/homebrew/bin/python3.13 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Run

Menu-bar app:

```bash
./.venv/bin/python app.py
```

Or just the counter, straight in the terminal (handy for testing):

```bash
./.venv/bin/python tabcount.py
```

## Permissions (no admin required)

The first time it queries each browser, macOS shows an **Automation** permission
prompt (*System Settings → Privacy & Security → Automation*). Click **OK**. This
is granted by you as the logged-in user — **not** an administrator action. Do it
once per browser.

If a browser shows `— (permission?)` in the dropdown, its Automation permission
was denied; re-enable it in that Privacy pane.

## Files

| File | Purpose |
|------|---------|
| `tabcount.py` | UI-free tab-counting logic (AppleScript + Firefox mozLz4 parse); also a CLI |
| `app.py` | rumps menu-bar app that polls and renders the number |
| `requirements.txt` | Python deps (`rumps`) |

## Roadmap / next steps

See the dossier's `roadmap.md`. Highlights: Firefox support, drag-to-install
`.app` bundle (`py2app`), launch-at-login, and eventually a native SwiftUI
`MenuBarExtra` rewrite.
