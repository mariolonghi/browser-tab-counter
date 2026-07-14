"""Browser Tab Counter — a macOS menu-bar indicator.

Shows a single number near the clock: the total open tabs across all running
browsers. Click it for a per-browser breakdown.

Run:
    ./.venv/bin/python app.py

Requires the macOS *Automation* permission (user-granted, no admin) the first
time it queries each browser.
"""

from __future__ import annotations

import rumps

from tabcount import count_all, total_tabs

POLL_SECONDS = 4


class TabCounterApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("⧉ …", quit_button=None)
        self._build_menu([], 0, first=True)
        self.timer = rumps.Timer(self.refresh, POLL_SECONDS)
        self.timer.start()
        # Do one immediate count so we don't sit on "…" for POLL_SECONDS.
        self.refresh(None)

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
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh now", callback=self.refresh))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def refresh(self, _sender=None) -> None:
        counts = count_all()
        total = total_tabs(counts)
        self.title = f"⧉ {total}"
        active = [c for c in counts if c.running]
        self._build_menu(active, total)


if __name__ == "__main__":
    TabCounterApp().run()
