"""Automation-permission helpers (re-trigger the pop-ups, open the settings pane).

macOS remembers a "Don't Allow" for Apple Events, so it won't spontaneously
re-prompt. We reset this app's Automation (Apple Events) consent with `tccutil`
— a per-user operation, no admin — after which the next query to each browser
raises a fresh permission pop-up.
"""

from __future__ import annotations

import subprocess

from appinfo import BUNDLE_ID

# Deep-link straight to the Automation list in System Settings > Privacy.
AUTOMATION_PANE = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"
)


def reset_automation() -> tuple[bool, str]:
    """Clear this app's stored Apple Events (Automation) decisions.

    Returns (ok, message). After this, the next Apple event to a browser will
    prompt again. Only affects entries where THIS app is the source.
    """
    proc = subprocess.run(
        ["tccutil", "reset", "AppleEvents", BUNDLE_ID],
        capture_output=True, text=True,
    )
    msg = (proc.stdout or proc.stderr).strip()
    return proc.returncode == 0, msg


def open_automation_settings() -> None:
    subprocess.run(["open", AUTOMATION_PANE], capture_output=True)


def open_website(url: str) -> None:
    subprocess.run(["open", url], capture_output=True)


if __name__ == "__main__":
    ok, msg = reset_automation()
    print(f"reset AppleEvents for {BUNDLE_ID}: {'OK' if ok else 'FAILED'}  {msg}")
