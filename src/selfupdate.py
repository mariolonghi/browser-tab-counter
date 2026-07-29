"""In-app self-update: download the latest release DMG, verify it's genuinely
ours, swap the app bundle in place, and relaunch.

Safety model (the whole thing hinges on this):
  * HTTPS download from GitHub (certifi-backed, reused from updates.py).
  * Before anything is installed, the downloaded app is verified to be BOTH
    notarized/accepted by Gatekeeper (`spctl`) AND signed by our pinned Team ID
    (`codesign`). A tampered or fake "update" therefore cannot be installed.

Only runs when the app is a frozen bundle in a user-writable location (the normal
drag-to-install case) — no admin/sudo needed because the app is user-owned. The
caller falls back to opening the release page otherwise. No new dependencies.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import appinfo

TEAM_ID = "ZWXAL8XA46"   # pinned: only ever install builds signed by us

# Where release assets may legitimately come from. The cryptographic gate is
# verify_app(); this allow-list is defense-in-depth so we never even fetch from
# an unexpected place.
_ALLOWED_HOSTS = ("github.com", "objects.githubusercontent.com",
                  "release-assets.githubusercontent.com")
_MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024   # sanity cap; our DMGs are ~30 MB


class UpdateError(Exception):
    pass


# --------------------------------------------------------------------------
# Preconditions
# --------------------------------------------------------------------------

def can_self_update() -> tuple[bool, str]:
    """Whether an in-place self-update can apply in this run."""
    if not appinfo.is_frozen():
        return False, "running from source"
    app = appinfo.bundle_path()
    if app.suffix != ".app":
        return False, "not an .app bundle"
    if not os.access(app, os.W_OK) or not os.access(app.parent, os.W_OK):
        return False, "the install location isn't writable"
    return True, ""


# --------------------------------------------------------------------------
# Download + mount + verify
# --------------------------------------------------------------------------

def _check_url(url: str) -> None:
    """HTTPS + GitHub hosts only (defense-in-depth; verify_app is the real gate)."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        host in _ALLOWED_HOSTS or host.endswith(".githubusercontent.com")
    ):
        raise UpdateError("unexpected update URL — refusing to download")


def _download(url: str, dest: Path, timeout: float = 180) -> None:
    from updates import _SSL_CONTEXT  # reuse the certifi-backed context
    _check_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": f"BrowserTabCounter/{appinfo.VERSION}",
    })
    written = 0
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as r:
        with open(dest, "wb") as f:
            while chunk := r.read(1024 * 1024):
                written += len(chunk)
                if written > _MAX_DOWNLOAD_BYTES:
                    raise UpdateError("update download is unexpectedly large")
                f.write(chunk)


def _mount(dmg: Path) -> Path:
    proc = subprocess.run(
        ["hdiutil", "attach", str(dmg), "-nobrowse", "-noautoopen"],
        capture_output=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise UpdateError(f"couldn't open the update image: {proc.stderr.strip()}")
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if parts and parts[-1].startswith("/Volumes/"):
            return Path(parts[-1].strip())
    raise UpdateError("couldn't find the mounted update volume")


def _unmount(mount: Path) -> None:
    subprocess.run(["hdiutil", "detach", str(mount), "-quiet"],
                   capture_output=True)


def _find_app(mount: Path) -> Path:
    for p in mount.iterdir():
        if p.suffix == ".app":
            return p
    raise UpdateError("no application found inside the update")


def verify_app(app: Path) -> None:
    """Reject anything that isn't a valid, notarized app signed by our Team ID.

    Three independent checks:
      1. codesign --verify --deep --strict — the signature is intact (nothing
         inside the bundle was modified after signing).
      2. spctl -a -t exec — Gatekeeper accepts it (Developer ID + notarized).
      3. TeamIdentifier — the signer is US, not just any notarized developer.
    """
    integ = subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", str(app)],
        capture_output=True, encoding="utf-8", errors="replace")
    if integ.returncode != 0:
        raise UpdateError("the download's code signature is invalid")
    gate = subprocess.run(["spctl", "-a", "-t", "exec", str(app)],
                          capture_output=True, encoding="utf-8", errors="replace")
    if gate.returncode != 0:
        raise UpdateError("the download isn't notarized / accepted by macOS")
    sig = subprocess.run(["codesign", "-dv", "--verbose=4", str(app)],
                         capture_output=True, encoding="utf-8", errors="replace")
    if f"TeamIdentifier={TEAM_ID}" not in (sig.stderr + sig.stdout):
        raise UpdateError("the download isn't signed by the expected developer")


# --------------------------------------------------------------------------
# Swap + relaunch (detached helper)
# --------------------------------------------------------------------------

def _spawn_swap_helper(staged_app: Path, target: Path, wait_pid: int,
                       workdir: Path) -> None:
    """Detached helper: wait for us to quit, swap the bundle, relaunch, clean up.

    The old bundle is moved aside first and only removed after the new one is in
    place, so a failure never leaves a missing app.
    """
    script = f"""#!/bin/bash
target={_q(target)}
staged={_q(staged_app)}
workdir={_q(workdir)}
# wait (up to ~15s) for the running app to exit
for i in $(seq 1 150); do kill -0 {wait_pid} 2>/dev/null || break; sleep 0.1; done
sleep 0.3
rm -rf "$target.old" 2>/dev/null
if mv "$target" "$target.old" 2>/dev/null; then
  if ditto "$staged" "$target"; then
    xattr -dr com.apple.quarantine "$target" 2>/dev/null
    rm -rf "$target.old"
  else
    # restore on failure
    rm -rf "$target"; mv "$target.old" "$target"
  fi
fi
open "$target"
rm -rf "$workdir"
"""
    helper = workdir / "swap.sh"
    helper.write_text(script, encoding="utf-8")
    helper.chmod(0o755)
    subprocess.Popen(
        ["/bin/bash", str(helper)],
        start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _q(p) -> str:
    """Single-quote a path for the shell helper."""
    return "'" + str(p).replace("'", "'\\''") + "'"


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def perform_update(dmg_url: str, target: Path | None = None,
                   wait_pid: int | None = None) -> None:
    """Download -> verify -> stage -> spawn swap helper.

    On return, the caller MUST quit the app so the helper can replace + relaunch
    it. Raises UpdateError with a user-friendly message on any problem.
    """
    ok, why = can_self_update()
    if target is None and not ok:
        raise UpdateError(why)
    target = target or appinfo.bundle_path()
    wait_pid = wait_pid if wait_pid is not None else os.getpid()

    workdir = Path(tempfile.mkdtemp(prefix="btc-update-"))
    dmg = workdir / "update.dmg"
    try:
        _download(dmg_url, dmg)
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(workdir, ignore_errors=True)
        raise UpdateError(f"download failed: {exc}") from exc

    mount = _mount(dmg)
    try:
        new_app = _find_app(mount)
        verify_app(new_app)
        staged = workdir / new_app.name
        subprocess.run(["ditto", str(new_app), str(staged)], check=True)
    except UpdateError:
        shutil.rmtree(workdir, ignore_errors=True)
        raise
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(workdir, ignore_errors=True)
        raise UpdateError(f"couldn't prepare the update: {exc}") from exc
    finally:
        # Single unmount for every path (success and failure alike).
        _unmount(mount)
        dmg.unlink(missing_ok=True)

    _spawn_swap_helper(staged, target, wait_pid, workdir)


if __name__ == "__main__":
    # Manual check: report whether self-update could apply, and (optionally)
    # download + verify a DMG URL without installing.
    import sys
    print("can_self_update:", can_self_update())
    if len(sys.argv) > 1:
        wd = Path(tempfile.mkdtemp(prefix="btc-verify-"))
        d = wd / "u.dmg"
        _download(sys.argv[1], d)
        m = _mount(d)
        try:
            a = _find_app(m)
            verify_app(a)
            print("verify OK:", a.name, "is notarized + Team", TEAM_ID)
        finally:
            _unmount(m)
            shutil.rmtree(wd, ignore_errors=True)
