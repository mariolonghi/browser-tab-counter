# Browser Tab Counter

A tiny **macOS menu-bar app** that answers one question at a glance:

> **How many browser tabs do I have open right now — across all my browsers?**

It shows a single number near the clock (e.g. `⧉ 147`). Click it for a
per-browser breakdown. No admin rights, no browser extension, no account.

```
menu bar:  … ⧉ 8  🔋  🔎  Wed 16:32     (⧉ ⚠️ 8 when over your alert threshold)
              └─ click ─┐
                        ▼
              ┌──────────────────────────────────┐
              │ 8 tab(s) total                   │
              ├──────────────────────────────────┤
              │ Safari:                        2 │
              │ Microsoft Edge:                4 │
              │ Firefox:                       2 │
              ├──────────────────────────────────┤
              │ Today ▁▂▃▅▇▆▄  min 5·avg 34·max 61│
              ├──────────────────────────────────┤
              │ Refresh now                      │
              │ Alert threshold: off             │
              │ Reveal tab-history file          │
              │ Permissions                    ▸ │
              │ ✓ Launch at Login                │
              ├──────────────────────────────────┤
              │ About Browser Tab Counter        │
              │ Quit                             │
              └──────────────────────────────────┘
```

---

## 🚀 Quick start (install & run)

1. **Download** the latest `BrowserTabCounter-x.y.z.dmg` from the
   [**Releases**](https://github.com/mariolonghi/browser-tab-counter/releases/latest) page.
2. **Open the `.dmg`** and **drag** *Browser Tab Counter* onto the **Applications**
   folder shown in the window.
3. **Double-click** *Browser Tab Counter* in **Applications** to launch it. The
   app is Apple-notarized (v0.3.1+), so it just opens — no Gatekeeper warning.
   *(Very old builds ≤ v0.3.0 were unsigned; if you're on one of those, either
   grab the latest release or right-click → Open once.)*
4. A **`⧉` number appears in your menu bar.** That's it — there's no window.

### 🔐 Grant the permission pop-ups (no admin needed)

The first time the app reads each browser, macOS shows an **Automation** pop-up:

> *"Browser Tab Counter" wants access to control "Safari".*

👉 **Click `OK`** on each one. You'll see one per browser you use (Safari, Chrome,
Edge, …). This is a normal per-user permission — **not** an administrator action,
and the app only ever *counts* tabs, it never reads their content.

- **Clicked *Don't Allow* or missed a prompt?** Use the menu →
  **Permissions → Re-request browser permissions**. It clears the previous
  decision (via `tccutil`) and asks again. There's also
  **Permissions → Open Automation settings…** to jump straight to
  *System Settings → Privacy & Security → Automation → Browser Tab Counter*.
- A browser showing `— (permission?)` in the dropdown just means its Automation
  permission is still off.
- **Firefox needs no pop-up** — it's counted by reading its own session file.

### ℹ️ About / troubleshoot

The menu → **About Browser Tab Counter** shows version, install date, poll
interval, and each running browser's current permission status — handy when
something isn't counting. It also links to the developer site, mariolonghi.com.

**Update check.** Opening About checks GitHub Releases and tells you whether
you're on the latest version; if a newer one exists you get a **Download update**
button straight to the release. This runs only when you open About (not in the
background), is a plain read-only request to GitHub — no personal data sent — and
fails quietly if you're offline.

### ⚠️ Alert threshold (optional)

Menu → **Alert threshold** lets you pick a number. When your total goes **above**
it, the menu-bar indicator adds a **`⚠️`** (so it reads `⧉ ⚠️ N`) and you get a
single notification (it re-arms once the count drops back below). Enter **0** to
turn it off. Your choice is saved locally.

### 📈 Tabs over time

The dropdown shows a tiny **sparkline** of today's total with **min · avg · max**.
The app samples the total every few minutes into a small, capped local file
(≈ a week of history, a few KB — **counts only, never tab content**). Menu →
**Reveal tab-history file** opens it in Finder if you want the raw numbers.

### ⭐ Launch at login (optional)

Click the `⧉` menu → **Launch at Login** to toggle it on (a checkmark appears).
The app will start automatically each time you log in. Toggle again to turn off.
No admin required — it uses a per-user LaunchAgent.

### Quit

Click the `⧉` menu → **Quit**.

---

## Which browsers are counted

| Family | Browsers | How |
|--------|----------|-----|
| **Chromium** | Chrome (+ Beta/Canary), Chromium, Edge, Brave, Vivaldi, Opera, Opera GX, Arc, Sidekick, Yandex | AppleScript (Automation permission) |
| **WebKit** | Safari | AppleScript (Automation permission) |
| **Gecko** | Firefox, LibreWolf, Waterfox, Zen | Reads the browser's own session file — no permission pop-up |

Only **running** browsers are counted; a closed browser contributes 0 and is
never launched just to count it.

---

## The technical stuff

### Build from source

Requirements: macOS, Python **3.9+** (system `/usr/bin/python3` 3.8 is too old
for PyObjC/rumps — use Homebrew's `python3.13`).

```bash
git clone https://github.com/mariolonghi/browser-tab-counter.git
cd browser-tab-counter
/opt/homebrew/bin/python3.13 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Run the menu-bar app, or just the counter in the terminal (handy for testing):

```bash
./.venv/bin/python app.py
./.venv/bin/python tabcount.py
```

Build the distributable `.dmg`:

```bash
./.venv/bin/pip install py2app
./build_dmg.sh          # → dist/BrowserTabCounter-<version>.dmg
```

`build_dmg.sh` signs with a Developer ID certificate if one is present (and can
notarize + staple the result), otherwise it falls back to an ad-hoc signature.
**If you need info on signing and notarizing, reach out.**

### Project layout

| File | Purpose |
|------|---------|
| `tabcount.py` | UI-free tab-counting logic (AppleScript + Firefox mozLz4 parse); also a CLI |
| `app.py` | rumps menu-bar app: polls, renders the number, About + Permissions menus |
| `appinfo.py` | Shared metadata (version, bundle id, install date) — no heavy deps |
| `permissions.py` | Re-trigger Automation prompts (`tccutil`) + open settings pane |
| `updates.py` | Check GitHub Releases for a newer version (certifi-backed HTTPS) |
| `prefs.py` | Local settings store (`prefs.json`) — threshold, etc. |
| `history.py` | Tabs-over-time sampling → capped `history.csv` + sparkline |
| `login_item.py` | Launch-at-login toggle (per-user LaunchAgent) |
| `setup.py` | py2app bundle config (`LSUIElement`, Automation usage string) |
| `entitlements.plist` | Hardened-runtime entitlements (for Developer ID / notarization) |
| `build_dmg.sh` | Build → sign (Developer ID *or* ad-hoc) → `.dmg` → optional notarize |
| `test_firefox_counting.py` | Regression tests for multi-window / multi-profile counting |
| `requirements.txt` | Runtime deps (`rumps`, `certifi`) |

---

## Notes & limitations

**How Firefox counting works & its caveats.** Firefox has no tab-scripting API,
so tabs are counted by reading its `sessionstore` files (windows × tabs, summed).
That's accurate for normal multi-window use and now sums across **multiple open
profiles**, but two limits are inherent to the approach:

- **~15 s lag.** Firefox only rewrites its session file on a timer (and pauses
  when idle), so a tab you just opened/closed takes a few seconds to show up. The
  count is right once Firefox next saves.
- **Private windows aren't counted.** Firefox deliberately never writes private
  browsing windows to disk, so their tabs are invisible to any external counter.
- Session restore must be enabled (the default). If a profile is set to never
  save history/session, its tabs can't be read.

Chromium/Safari counts (via AppleScript) don't have these caveats — they're
real-time. If you need Firefox to be real-time too, that requires the macOS
Accessibility API (an extra permission + fragile UI parsing) — not currently done.
- **No Mac App Store build.** The App Store requires sandboxing, which blocks
  reading Firefox's session file (and realistically needs a native Swift rewrite).
  This project targets **drag-to-install** only. Design rationale lives in the
  dossier under `~/Documents/MLonghi/Project-1/Browser Tab Counter/distribution.md`.
- The design dossier (the "why") is kept separately from this code repo.

## Disclaimer

- **Privacy.** Once installed on your system, this app does not send any
  information to the internet. No cloud linkage, no account needed, no telemetry.
  Your settings and the tab-history log stay on your Mac in
  `~/Library/Application Support/BrowserTabCounter/`.
  *(The only network use is the optional update check, which runs only when you
  open the About window — a read-only request to GitHub, no personal data.)*
- **Support.** The app is provided free to use, with limited support.

## License

MIT — see [LICENSE](LICENSE).
