# Browser Tab Counter (macOS menu-bar POC)

A tiny macOS **menu-bar indicator** answering one question at a glance:

> **How many browser tabs do I have open right now — across all my browsers?**

It shows a single number near the clock (e.g. `⧉ 147`) and, on click, a
per-browser breakdown. No admin rights, no browser extension.

Design dossier (the "why" and the plan) lives at
`~/Documents/MLonghi/Project-1/Browser Tab Counter/`.

## What works in this POC

- Sums open tabs across **running** Safari + Chromium-family browsers
  (Chrome, Edge, Brave, Vivaldi, Opera, Arc) via AppleScript.
- Menu-bar number, updated every few seconds.
- Click → dropdown with per-browser counts, "Refresh now", and Quit.
- Only queries browsers that are actually running (never launches a closed one).
- Firefox is **out of scope** for the POC (no usable tab-scripting API — see dossier).

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
| `tabcount.py` | UI-free tab-counting logic (also a CLI) |
| `app.py` | rumps menu-bar app that polls and renders the number |
| `requirements.txt` | Python deps (`rumps`) |

## Roadmap / next steps

See the dossier's `roadmap.md`. Highlights: Firefox support, drag-to-install
`.app` bundle (`py2app`), launch-at-login, and eventually a native SwiftUI
`MenuBarExtra` rewrite.
