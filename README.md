# Browser Tab Counter

A tiny **macOS menu-bar app** that answers one question at a glance:

> **How many browser tabs do I have open right now — across all my browsers?**

It shows a single number near the clock (e.g. `⧉ 147`). Click it for a
per-browser breakdown. No admin rights, no browser extension, no account.

```
menu bar:  … ⧉ 8  🔋  🔎  Wed 16:32
              └─ click ─┐
                        ▼
              ┌───────────────────┐
              │ 8 tab(s) total    │
              ├───────────────────┤
              │ Safari:         2 │
              │ Microsoft Edge: 4 │
              │ Firefox:        2 │
              ├───────────────────┤
              │ Refresh now       │
              │ ✓ Launch at Login │
              │ Quit              │
              └───────────────────┘
```

---

## 🚀 Quick start (install & run)

1. **Download** the latest `BrowserTabCounter-x.y.z.dmg` from the
   [**Releases**](https://github.com/mariolonghi/browser-tab-counter/releases/latest) page.
2. **Open the `.dmg`** and **drag** *Browser Tab Counter* onto the **Applications**
   folder shown in the window.
3. **First launch — important:** the app isn't signed with a paid Apple
   Developer certificate, so macOS Gatekeeper blocks a normal double-click.
   Do this **once**:
   - In **Applications**, **right-click** (or Control-click) *Browser Tab Counter*
     → **Open** → in the dialog, click **Open** again.
   - *(If macOS says the app "is damaged / can't be opened", run once in Terminal:*
     `xattr -dr com.apple.quarantine "/Applications/Browser Tab Counter.app"`*, then reopen.)*
4. A **`⧉` number appears in your menu bar.** That's it — there's no window.

### 🔐 Grant the permission pop-ups (no admin needed)

The first time the app reads each browser, macOS shows an **Automation** pop-up:

> *"Browser Tab Counter" wants access to control "Safari".*

👉 **Click `OK`** on each one. You'll see one per browser you use (Safari, Chrome,
Edge, …). This is a normal per-user permission — **not** an administrator action,
and the app only ever *counts* tabs, it never reads their content.

- If you accidentally clicked *Don't Allow*, re-enable it under
  **System Settings → Privacy & Security → Automation → Browser Tab Counter**.
- A browser showing `— (permission?)` in the dropdown just means its Automation
  permission is still off.
- **Firefox needs no pop-up** — it's counted by reading its own session file.

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

## Build from source

Requirements: macOS, Python **3.9+** (system `/usr/bin/python3` 3.8 is too old
for PyObjC/rumps — use Homebrew's `python3.13`).

```bash
git clone https://github.com/mariolonghi/browser-tab-counter.git
cd browser-tab-counter
/opt/homebrew/bin/python3.13 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Run the menu-bar app:

```bash
./.venv/bin/python app.py
```

Or just the counter in the terminal (handy for testing):

```bash
./.venv/bin/python tabcount.py
```

### Build the distributable `.dmg`

```bash
./.venv/bin/pip install py2app
./build_dmg.sh          # → dist/BrowserTabCounter-<version>.dmg
```

The build ad-hoc signs the app (required to run on Apple Silicon). It is **not**
notarized, which is why users need the one-time right-click → Open step. To ship
without that step you'd enrol in the paid Apple Developer Program and add
`codesign` (Developer ID) + `notarytool` steps.

---

## Project layout

| File | Purpose |
|------|---------|
| `tabcount.py` | UI-free tab-counting logic (AppleScript + Firefox mozLz4 parse); also a CLI |
| `app.py` | rumps menu-bar app that polls and renders the number |
| `login_item.py` | Launch-at-login toggle (per-user LaunchAgent) |
| `setup.py` | py2app bundle config (`LSUIElement`, Automation usage string) |
| `build_dmg.sh` | One-shot build → ad-hoc sign → `.dmg` |
| `requirements.txt` | Runtime dep (`rumps`) |

---

## Notes & limitations

- **Firefox count can lag ~15 s** — Firefox rewrites its session file on a timer,
  so newly opened/closed Firefox tabs take a moment to reflect.
- **No Mac App Store build.** The App Store requires sandboxing, which blocks
  reading Firefox's session file (and realistically needs a native Swift rewrite).
  This project targets **drag-to-install** only. Design rationale lives in the
  dossier under `~/Documents/MLonghi/Project-1/Browser Tab Counter/distribution.md`.
- The design dossier (the "why") is kept separately from this code repo.

## License

MIT — see [LICENSE](LICENSE).
