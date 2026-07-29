"""Browser Tab Counter — a macOS menu-bar indicator.

Shows a single number near the clock: the total open tabs across all running
browsers. Click it for a per-browser breakdown, an About/troubleshoot panel, a
"re-request permissions" action, and a launch-at-login toggle.

Run:
    ./.venv/bin/python src/app.py

Requires the macOS *Automation* permission (user-granted, no admin) the first
time it queries each browser.
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import rumps

import appinfo
import history
import login_item
import permissions
import prefs
import selfupdate
import tabexport
import updates
from i18n import _, format_date, ngettext
from tabcount import BROWSERS, count_all, total_tabs

POLL_SECONDS = appinfo.POLL_SECONDS

# name -> counting method, for the About panel's permission summary.
_METHOD = {b.name: b.method for b in BROWSERS}


def build_about_text(counts, update_line: str | None = None) -> str:
    """Assemble the About/troubleshoot panel text from a list of BrowserCount."""
    inst = appinfo.install_date()
    inst_s = format_date(inst) if inst else "—"

    perm_lines = []
    for c in counts:
        if not c.running:
            continue
        if _METHOD.get(c.name) == "firefox":
            perm_lines.append(f"   • {c.name}: {_('session file (no prompt)')}")
        elif c.tabs is not None:
            perm_lines.append(f"   • {c.name}: {_('granted ✓')}")
        else:
            perm_lines.append(f"   • {c.name}: {_('needs permission ✗')}")
    if not perm_lines:
        perm_lines = [f"   • {_('(no supported browsers running)')}"]

    version_block = _("Version {version}").format(version=appinfo.VERSION) + "\n"
    if update_line:
        version_block += f"{update_line}\n"

    return (
        version_block
        + f"{appinfo.BUNDLE_ID}\n"
        + _("Installed: {date}").format(date=inst_s) + "\n"
        + _("Polls every {n}s").format(n=appinfo.POLL_SECONDS) + "\n"
        "\n"
        + _("Browser permissions (Automation):") + "\n"
        + "\n".join(perm_lines)
        + "\n\n"
        + _("Developer: Mario Longhi — mariolonghi.com")
    )


class TabCounterApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("⧉ …", quit_button=None)
        self._last_counts = []
        self._was_over = False        # threshold-crossing state (notify once)
        self._first_run_setup()       # default new installs to Launch-at-Login
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
            header = _("Counting…") if first else _("No browsers running")
            self.menu.add(rumps.MenuItem(header))
        else:
            self.menu.add(rumps.MenuItem(
                ngettext("{n} tab total", "{n} tabs total", total).format(n=total)))
            self.menu.add(rumps.separator)
            for c in active_counts:
                value = c.tabs if c.tabs is not None else _("— (permission?)")
                self.menu.add(rumps.MenuItem(f"{c.name}:  {value}"))

        # Tabs-over-time summary — click it to download the history CSV.
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem(history.menu_summary(),
                                     callback=self.download_history))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem(_("Refresh now"), callback=self.refresh))
        self.menu.add(rumps.MenuItem(_("Export open tabs…"),
                                     callback=self.export_tabs))

        threshold = prefs.get("threshold", 0)
        label = (_("Alert threshold: {n}").format(n=threshold) if threshold
                 else _("Alert threshold: off"))
        self.menu.add(rumps.MenuItem(label, callback=self.set_threshold))

        # Permissions submenu.
        perms = rumps.MenuItem(_("Permissions"))
        perms.add(rumps.MenuItem(_("Re-request browser permissions"),
                                 callback=self.rerequest_permissions))
        perms.add(rumps.MenuItem(_("Open Automation settings…"),
                                 callback=self.open_permission_settings))
        self.menu.add(perms)

        login = rumps.MenuItem(_("Launch at Login"), callback=self.toggle_login)
        login.state = 1 if login_item.is_enabled() else 0
        self.menu.add(login)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem(_("About {app}").format(app=appinfo.APP_NAME),
                                     callback=self.show_about))
        self.menu.add(rumps.MenuItem(_("Quit"), callback=rumps.quit_application))

    # ---- actions -----------------------------------------------------------

    def _first_run_setup(self) -> None:
        """On the very first launch of an installed build, enable Launch-at-Login
        by default. Runs once — if the user later turns it off, it stays off.
        Skipped when running from source so dev runs don't create a login item.
        """
        if prefs.get("first_run_done", False):
            return
        prefs.update("first_run_done", True)
        if appinfo.is_frozen() and not login_item.is_enabled():
            try:
                login_item.enable()
            except Exception:  # noqa: BLE001 - best effort, never block startup
                pass

    def toggle_login(self, sender) -> None:
        try:
            now_on = login_item.toggle()
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the menu bar
            rumps.alert(_("Launch at Login"),
                        _("Couldn't update setting:\n{error}").format(error=exc))
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
            body = _(
                "Cleared the previous Automation choices.\n\n"
                "macOS will now ask again the next time each browser is "
                "checked — click Allow on those prompts.\n\n"
                "If nothing appears, use “Open Automation settings…” and enable "
                "each browser under “{app}”."
            ).format(app=appinfo.APP_NAME)
        else:
            body = (
                _("Couldn't reset the permissions automatically")
                + (f":\n{msg}\n\n" if msg else ".\n\n")
                + _("Open Automation settings and enable each browser under "
                    "“{app}”.").format(app=appinfo.APP_NAME)
            )
        result = rumps.alert(
            title=_("Re-request Browser Permissions"),
            message=body,
            ok=_("OK"),
            other=_("Open Automation settings…"),
        )
        if result == -1:
            permissions.open_automation_settings()

    def open_permission_settings(self, _sender) -> None:
        permissions.open_automation_settings()

    def set_threshold(self, _sender) -> None:
        current = prefs.get("threshold", 0)
        window = rumps.Window(
            message=_("Show ⚠️ and notify once when the total goes above this "
                      "many tabs.\nEnter 0 to turn the alert off."),
            title=_("Alert Threshold"),
            default_text=str(current),
            ok=_("Save"),
            cancel=_("Cancel"),
            dimensions=(120, 22),
        )
        response = window.run()
        if not response.clicked:
            return
        try:
            value = max(0, int(response.text.strip()))
        except ValueError:
            rumps.alert(_("Alert Threshold"),
                        _("Please enter a whole number (0 turns the alert off)."))
            return
        prefs.update("threshold", value)
        self._was_over = False        # re-arm so it can fire again
        self.refresh(None)

    def download_history(self, _sender) -> None:
        """Save a copy of the tab-count history CSV wherever the user chooses."""
        if not history.HISTORY_PATH.exists():
            rumps.alert(_("Tab History"),
                        _("No history recorded yet — it starts filling in within "
                          "a few minutes of running."))
            return
        default_name = f"{appinfo.APP_NAME} - {_('tab history')} - {datetime.now():%Y-%m-%d}.csv"
        path = self._ask_save_path(default_name, title=_("Save Tab History"))
        if not path:
            return
        try:
            shutil.copyfile(history.HISTORY_PATH, path)
        except OSError as exc:
            rumps.alert(_("Tab History"),
                        _("Couldn't save the file:\n{error}").format(error=exc))
            return
        subprocess.run(["open", "-R", path], capture_output=True)  # reveal in Finder

    def export_tabs(self, _sender) -> None:
        """Gather every open tab right now and save it as a CSV the user picks."""
        # Re-poll first so anything opened in the last few seconds is included
        # (Chromium/Safari are read live anyway; this also refreshes Firefox's
        # session read and keeps the menu-bar count in step with the export).
        self.refresh(None)
        try:
            rows = tabexport.gather_all()
        except Exception as exc:  # noqa: BLE001 - never crash the menu bar
            rumps.alert(_("Export Open Tabs"),
                        _("Couldn't read the open tabs:\n{error}").format(error=exc))
            return
        if not rows:
            rumps.alert(_("Export Open Tabs"),
                        _("No open tabs found in the running browsers."))
            return

        # Let the user pick a format. ok = CSV, other = HTML, cancel = abort.
        choice = rumps.alert(
            title=_("Export Open Tabs"),
            message=ngettext(
                "{n} open tab found.\n\nChoose a format:\n\n"
                "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
                "• Web page (HTML) — a sortable table with clickable links, "
                "viewable in any browser.",
                "{n} open tabs found.\n\nChoose a format:\n\n"
                "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
                "• Web page (HTML) — a sortable table with clickable links, "
                "viewable in any browser.",
                len(rows)).format(n=len(rows)),
            ok=_("Spreadsheet (CSV)"),
            cancel=_("Cancel"),
            other=_("Web page (HTML)"),
        )
        if choice == 0:                       # cancelled
            return
        as_html = (choice == -1)
        ext = "html" if as_html else "csv"

        default_name = (f"{appinfo.APP_NAME} - {_('open tabs')} - "
                        f"{datetime.now():%Y-%m-%d-%H%M%S}.{ext}")
        path = self._ask_save_path(default_name, title=_("Export Open Tabs"))
        if not path:
            return
        try:
            if as_html:
                tabexport.write_html(rows, path)
            else:
                tabexport.write_csv(rows, path)
        except OSError as exc:
            rumps.alert(_("Export Open Tabs"),
                        _("Couldn't write the file:\n{error}").format(error=exc))
            return
        subprocess.run(["open", "-R", path], capture_output=True)  # reveal in Finder

    def _ask_save_path(self, default_name: str,
                       title: str = "Save") -> str | None:
        """A native Save panel; falls back to ~/Downloads if it can't be shown."""
        try:
            import AppKit
            AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            panel = AppKit.NSSavePanel.savePanel()
            panel.setNameFieldStringValue_(default_name)
            panel.setTitle_(title)
            if panel.runModal() == 1:            # NSModalResponseOK
                return panel.URL().path()
            return None                          # user cancelled
        except Exception:  # noqa: BLE001 - AppKit unavailable / panel failed
            return str(Path.home() / "Downloads" / default_name)

    def _notify_threshold(self, total: int, threshold: int) -> None:
        try:
            rumps.notification(
                title=appinfo.APP_NAME,
                subtitle=_("Over your {n}-tab limit").format(n=threshold),
                message=_("You have {n} tabs open.").format(n=total),
            )
        except Exception:  # noqa: BLE001 - notifications need a bundle; never crash
            pass

    def show_about(self, _sender) -> None:
        # User-initiated update check (short timeout; cached for a few minutes).
        status = updates.check(timeout=3.0)
        body = build_about_text(self._last_counts, update_line=status.summary())

        if status.available:
            can_update, _why = selfupdate.can_self_update()
            if can_update and status.asset_url:
                # In-app self-update available: ok = install now, other = notes.
                result = rumps.alert(
                    title="Browser Tab Counter",
                    message=body,
                    ok=_("Update now to v{latest}").format(latest=status.latest),
                    cancel=_("Later"),
                    other=_("Release notes"),
                )
                if result == 1:
                    self._do_self_update(status)
                elif result == -1:
                    permissions.open_website(status.url)
            else:
                # Fallback (running from source, or read-only install): open page.
                result = rumps.alert(
                    title="Browser Tab Counter",
                    message=body,
                    ok=_("Download update"),
                    cancel=_("Close"),
                    other=_("Visit mariolonghi.com"),
                )
                if result == 1:
                    permissions.open_website(status.url)
                elif result == -1:
                    permissions.open_website(appinfo.WEBSITE)
        else:
            result = rumps.alert(
                title="Browser Tab Counter",
                message=body,
                ok=_("OK"),
                other=_("Visit mariolonghi.com"),
            )
            if result == -1:
                permissions.open_website(appinfo.WEBSITE)

    def _do_self_update(self, status) -> None:
        """Download + verify + install the new version, then quit so the helper
        can swap the bundle and relaunch us."""
        try:
            rumps.notification(
                appinfo.APP_NAME,
                _("Updating to v{latest}…").format(latest=status.latest),
                _("Downloading and verifying — the app will relaunch itself."),
            )
        except Exception:  # noqa: BLE001 - notifications need a bundle
            pass
        try:
            selfupdate.perform_update(status.asset_url)
        except selfupdate.UpdateError as exc:
            result = rumps.alert(
                _("Update"),
                _("Couldn't update automatically:\n{error}").format(error=exc),
                ok=_("Open download page"), cancel=_("Cancel"),
            )
            if result == 1:
                permissions.open_website(status.url)
            return
        except Exception as exc:  # noqa: BLE001
            rumps.alert(_("Update"),
                        _("Update failed:\n{error}").format(error=exc))
            return
        # Staged and verified — quit so the detached helper swaps + relaunches.
        rumps.quit_application()

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
