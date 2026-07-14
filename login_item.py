"""Launch-at-login toggle via a per-user LaunchAgent.

No admin rights required — we just drop (or remove) a plist in
``~/Library/LaunchAgents``. At the next login, launchd loads it and starts the
app. We deliberately do **not** ``launchctl load`` it the moment the user
enables it, because the app is already running — loading a RunAtLoad agent then
would spawn a duplicate. Writing the file is enough for it to start next login.

Works both when running from source (``python app.py``) and when frozen into a
py2app ``.app`` bundle.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LABEL = "com.mariolonghi.browsertabcounter"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _program_arguments() -> list[str]:
    """How launchd should start us, adapting to frozen vs. source runs."""
    if getattr(sys, "frozen", False):
        # py2app: sys.executable is <App>.app/Contents/MacOS/<binary>.
        # Launch via `open` so macOS treats it as a proper app activation.
        app_bundle = Path(sys.executable).parents[2]
        return ["/usr/bin/open", str(app_bundle)]
    # Running from source: re-run this app.py with the same interpreter.
    app_py = str(Path(__file__).resolve().parent / "app.py")
    return [sys.executable, app_py]


def _plist_xml(program_args: list[str]) -> str:
    args_xml = "\n".join(f"        <string>{a}</string>" for a in program_args)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{args_xml}\n"
        "    </array>\n"
        "    <key>RunAtLoad</key>\n"
        "    <true/>\n"
        "    <key>ProcessType</key>\n"
        "    <string>Interactive</string>\n"
        "</dict>\n"
        "</plist>\n"
    )


def is_enabled() -> bool:
    return PLIST_PATH.exists()


def enable() -> None:
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(_plist_xml(_program_arguments()))
    # Do NOT launchctl-load now (avoids a duplicate instance); it loads at login.


def disable() -> None:
    if PLIST_PATH.exists():
        # Unload if it happens to be registered, then remove the file.
        subprocess.run(
            ["launchctl", "unload", str(PLIST_PATH)],
            capture_output=True, text=True,
        )
        PLIST_PATH.unlink(missing_ok=True)


def toggle() -> bool:
    """Flip the state; return the new enabled value."""
    if is_enabled():
        disable()
    else:
        enable()
    return is_enabled()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "enable":
        enable()
    elif action == "disable":
        disable()
    elif action == "toggle":
        toggle()
    print(f"launch-at-login: {'ON' if is_enabled() else 'OFF'}  ({PLIST_PATH})")
