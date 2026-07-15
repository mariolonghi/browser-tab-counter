"""Browser Tab Counter — a macOS menu-bar indicator.

Shows a single number near the clock: the total open tabs across all running
browsers. Click it for a per-browser breakdown, an About/troubleshoot panel, a
"re-request permissions" action, and a launch-at-login toggle.

Run:
    ./.venv/bin/python app.py

Requires the macOS *Automation* permission (user-granted, no admin) the first
time it queries each browser.
"""

from __future__ import annotations

import subprocess

import rumps

import appinfo
import history
import login_item
import permissions
import prefs
import updates
from tabcount import BROWSERS, count_all, total_tabs

POLL_SECONDS = appinfo.POLL_SECONDS

# name -> counting method, for the About panel's permission summary.
_METHOD = {b.name: b.method for b in BROWSERS}


def build_about_text(counts, update_line: str | None = None) -> str:
    """Assemble the About/troubleshoot panel text from a list of BrowserCount."""
    inst = appinfo.install_date()
    inst_s = inst.strftime("%d %b %Y") if inst else "unknown"

    perm_lines = []
    for c in counts:
        if not c.running:
            continue
        if _METHOD.get(c.name) == "firefox":
            perm_lines.append(f"   • {c.name}: session file (no prompt)")
        elif c.tabs is not None:
            perm_lines.append(f"   • {c.name}: granted ✓")
        else:
            perm_lines.append(f"   • {c.name}: needs permission ✗")
    if not perm_lines:
        perm_lines = ["   • (no supported browsers running)"]

    version_block = f"Version {appinfo.VERSION}\n"
    if update_line:
        version_block += f"{update_line}\n"

    return (
        version_block
        + f"{appinfo.BUNDLE_ID}\n"
        f"Installed: {inst_s}\n"
        f"Polls every {appinfo.POLL_SECONDS}s\n"
        "\n"
        "Browser permissions (Automation):\n"
        + "\n".join(perm_lines)
        + "\n\n"
        "Developer: Mario Longhi — mariolonghi.com"
    )


class TabCounterApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("⧉ …", quit_button=None)
        self._last_counts = []
        self._was_over = False        # threshold-crossing state (notify once)
        self._build_menu([], 0, first=True)
        self.timer = rumps.Timer(self.refresh, POLL_SECONDS)
        self.timer.start()
        # Do one immediate count so we don't sit on "…" for POLL_SECONDS.
        self.refresh(None)

    # ---- menu construction -------------------------------------------------

    def _build_menu(self, active_counts, total, first=False) -> None:
        """Rebuild the whole dropdown. Simple and race-free."""
        self.menu.clear()
        if not active_counts:
            header = "Counting…" if first else "No browsers running"
            self.menu.add(rumps.MenuItem(header))
        else:
            self.menu.add(rumps.MenuItem(f"{total} tab(s) total"))
            self.menu.add(rumps.separator)
            for c in active_counts:
                value = c.tabs if c.tabs is not None else "— (permission?)"
                self.menu.add(rumps.MenuItem(f"{c.name}:  {value}"))

        # Tabs-over-time summary (non-clickable info line).
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem(history.menu_summary()))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh now", callback=self.refresh))

        threshold = prefs.get("threshold", 0)
        label = f"Alert threshold: {threshold}" if threshold else "Alert threshold: off"
        self.menu.add(rumps.MenuItem(label, callback=self.set_threshold))
        self.menu.add(rumps.MenuItem("Reveal tab-history file",
                                     callback=self.reveal_history))

        # Permissions submenu.
        perms = rumps.MenuItem("Permissions")
        perms.add(rumps.MenuItem("Re-request browser permissions",
                                 callback=self.rerequest_permissions))
        perms.add(rumps.MenuItem("Open Automation settings…",
                                 callback=self.open_permission_settings))
        self.menu.add(perms)

        login = rumps.MenuItem("Launch at Login", callback=self.toggle_login)
        login.state = 1 if login_item.is_enabled() else 0
        self.menu.add(login)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("About Browser Tab Counter",
                                     callback=self.show_about))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    # ---- actions -----------------------------------------------------------

    def toggle_login(self, sender) -> None:
        try:
            now_on = login_item.toggle()
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the menu bar
            rumps.alert("Launch at Login", f"Couldn't update setting:\n{exc}")
            return
        sender.state = 1 if now_on else 0

    def rerequest_permissions(self, _sender) -> None:
        ok, msg = permissions.reset_automation()
        # Bring the app forward so macOS is willing to present the Automation
        # prompt (background agents are otherwise sometimes denied silently).
        try:
            import AppKit
            AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:  # noqa: BLE001 - best effort
            pass
        # Firing a count now triggers fresh Automation prompts for running browsers.
        self.refresh(None)
        if ok:
            body = (
                "Cleared the previous Automation choices.\n\n"
                "macOS will now ask again the next time each browser is "
                "checked — click Allow on those prompts.\n\n"
                "If nothing appears, use “Open Automation settings…” and enable "
                "each browser under “Browser Tab Counter”."
            )
        else:
            body = (
                "Couldn't reset the permissions automatically"
                + (f":\n{msg}\n\n" if msg else ".\n\n")
                + "Open Automation settings and toggle each browser under "
                "“Browser Tab Counter”."
            )
        result = rumps.alert(
            title="Re-request Browser Permissions",
            message=body,
            ok="OK",
            other="Open Automation settings…",
        )
        if result == -1:
            permissions.open_automation_settings()

    def open_permission_settings(self, _sender) -> None:
        permissions.open_automation_settings()

    def set_threshold(self, _sender) -> None:
        current = prefs.get("threshold", 0)
        window = rumps.Window(
            message="Show ⚠️ and notify once when the total goes above this many "
                    "tabs.\nEnter 0 to turn the alert off.",
            title="Alert Threshold",
            default_text=str(current),
            ok="Save",
            cancel="Cancel",
            dimensions=(120, 22),
        )
        response = window.run()
        if not response.clicked:
            return
        try:
            value = max(0, int(response.text.strip()))
        except ValueError:
            rumps.alert("Alert Threshold",
                        "Please enter a whole number (0 turns the alert off).")
            return
        prefs.update("threshold", value)
        self._was_over = False        # re-arm so it can fire again
        self.refresh(None)

    def reveal_history(self, _sender) -> None:
        if history.HISTORY_PATH.exists():
            subprocess.run(["open", "-R", str(history.HISTORY_PATH)],
                           capture_output=True)
        else:
            rumps.alert("Tab History",
                        "No history recorded yet — it starts filling in within a "
                        "few minutes of running.")

    def _notify_threshold(self, total: int, threshold: int) -> None:
        try:
            rumps.notification(
                title="Browser Tab Counter",
                subtitle=f"Over your {threshold}-tab limit",
                message=f"You have {total} tabs open.",
            )
        except Exception:  # noqa: BLE001 - notifications need a bundle; never crash
            pass

    def show_about(self, _sender) -> None:
        # User-initiated update check (short timeout; cached for a few minutes).
        status = updates.check(timeout=3.0)
        body = build_about_text(self._last_counts, update_line=status.summary())

        if status.available:
            # ok = download, cancel = close, other = website.
            result = rumps.alert(
                title="Browser Tab Counter",
                message=body,
                ok="Download update",
                cancel="Close",
                other="Visit mariolonghi.com",
            )
            if result == 1:
                permissions.open_website(status.url)
            elif result == -1:
                permissions.open_website(appinfo.WEBSITE)
        else:
            result = rumps.alert(
                title="Browser Tab Counter",
                message=body,
                ok="OK",
                other="Visit mariolonghi.com",
            )
            if result == -1:
                permissions.open_website(appinfo.WEBSITE)

    # ---- polling -----------------------------------------------------------

    def refresh(self, _sender=None) -> None:
        counts = count_all()
        self._last_counts = counts
        total = total_tabs(counts)

        # Threshold alert: keep the ⧉ icon, add ⚠️ + one-time notification on
        # the upward crossing.
        threshold = prefs.get("threshold", 0)
        over = threshold > 0 and total > threshold
        self.title = f"⧉ ⚠️ {total}" if over else f"⧉ {total}"
        if over and not self._was_over:
            self._notify_threshold(total, threshold)
        self._was_over = over

        history.maybe_record(total)

        active = [c for c in counts if c.running]
        self._build_menu(active, total)


if __name__ == "__main__":
    TabCounterApp().run()
