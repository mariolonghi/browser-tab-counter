# Browser Tab Counter

A tiny **macOS menu-bar app** that answers one question at a glance:

> **How many browser tabs do I have open right now — across all my browsers?**

It shows a single number near the clock (e.g. `⧉ 147`). Click it for a
per-browser breakdown. No admin rights, no browser extension, no account.

```
menu bar:  … ⧉ 8  🔋  🔎  Wed 16:32
              └─ click ─┐
                        ▼
              ┌────────────────────────┐
              │ 8 tab(s) total         │
              ├────────────────────────┤
              │ Safari:              2 │
              │ Microsoft Edge:      4 │
              │ Firefox:             2 │
              ├────────────────────────┤
              │ Refresh now            │
              │ Permissions          ▸ │
              │ ✓ Launch at Login      │
              ├────────────────────────┤
              │ About Browser Tab Cou… │
              │ Quit                   │
              └────────────────────────┘
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

`build_dmg.sh` signs **automatically**:

- **No Developer ID cert** → ad-hoc signature (runs on Apple Silicon, but users
  need the one-time right-click → Open).
- **Developer ID Application cert present** → signs with it + the **hardened
  runtime** + `entitlements.plist`, making the app **notarizable**.

### Signing & notarizing with a paid Apple Developer account

A paid membership lets you remove the scary first-launch step entirely. One-time
setup:

1. **Create the right certificate.** You need a **"Developer ID Application"**
   cert — *not* the "Apple Development" cert Xcode makes by default (that one
   can't be notarized). In **Xcode → Settings → Accounts → Manage Certificates →
   `+` → Developer ID Application**, or via the Apple Developer portal. It lands
   in your keychain; `build_dmg.sh` auto-detects it.
2. **Store notarization credentials once** (needs Xcode installed for
   `notarytool`):
   ```bash
   xcrun notarytool store-credentials btc-notary \
     --apple-id "you@example.com" --team-id "TEAMID" \
     --password "app-specific-password"   # from appleid.apple.com
   ```
3. **Build + sign + notarize + staple** in one go:
   ```bash
   NOTARY_PROFILE=btc-notary ./build_dmg.sh
   ```
   (Or pass `NOTARY_APPLE_ID` / `NOTARY_TEAM_ID` / `NOTARY_PASSWORD` instead of a
   stored profile.) The script signs with Developer ID, uploads for
   notarization, waits, and staples the ticket to the `.dmg` — after which
   users can just double-click to open.

### Notarized releases via GitHub Actions

`.github/workflows/release.yml` builds, **signs, notarizes, staples and
publishes** a DMG whenever you push a `v*` tag — once these five repo secrets are
set. (Without them it still builds an ad-hoc DMG.)

**1. Export your Developer ID cert as a `.p12`** (from the Mac that has it):
Keychain Access → **login** keychain → **My Certificates** → expand
*Developer ID Application: Mario Longhi* so both the certificate **and its
private key** are selected → right-click → **Export 2 items…** → save
`DeveloperID.p12` and set an export password. Then base64-encode it:
```bash
base64 -i DeveloperID.p12 | pbcopy      # now on your clipboard
```

**2. Create an app-specific password** at
appleid.apple.com → *Sign-In and Security → App-Specific Passwords*.

**3. Set the secrets** (run these yourself — the values never leave your machine):
```bash
gh secret set MACOS_CERT_P12_BASE64   # paste the base64 from step 1
gh secret set MACOS_CERT_PASSWORD     # the .p12 export password from step 1
gh secret set NOTARY_APPLE_ID         # your Apple ID email
gh secret set NOTARY_TEAM_ID          # ZWXAL8XA46
gh secret set NOTARY_PASSWORD         # the app-specific password from step 2
```

**4. Release:** bump `VERSION` in `appinfo.py`, commit, then:
```bash
git tag v0.3.1 && git push origin v0.3.1
```
The workflow imports the cert into a throwaway keychain, runs `build_dmg.sh`
(Developer ID sign → notarize → staple), and uploads the DMG to the release —
which then opens with a **plain double-click**.

---

## Project layout

| File | Purpose |
|------|---------|
| `tabcount.py` | UI-free tab-counting logic (AppleScript + Firefox mozLz4 parse); also a CLI |
| `app.py` | rumps menu-bar app: polls, renders the number, About + Permissions menus |
| `appinfo.py` | Shared metadata (version, bundle id, install date) — no heavy deps |
| `permissions.py` | Re-trigger Automation prompts (`tccutil`) + open settings pane |
| `updates.py` | Check GitHub Releases for a newer version (certifi-backed HTTPS) |
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

## License

MIT — see [LICENSE](LICENSE).
