"""Check GitHub Releases to see whether a newer version is available.

Used by the About panel. Deliberately **user-initiated** (runs when About is
opened) rather than a silent background poll, so the app only contacts GitHub
when the user asks. It sends a plain GET to the public GitHub API — no user
data, no auth — and exposes only the usual IP/User-Agent of any HTTP request.

Standard library only (urllib + json); nothing extra to bundle.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.request

from appinfo import GITHUB_REPO, RELEASES_URL, VERSION

# Use certifi's CA bundle so HTTPS verification works inside the frozen .app.
# (The system OpenSSL cert path is Homebrew-specific on the build machine and
# won't exist on a normal user's Mac, so we must bundle our own CA roots.)
try:
    import certifi
    _SSL_CONTEXT: ssl.SSLContext | None = ssl.create_default_context(cafile=certifi.where())
except Exception:  # noqa: BLE001 - fall back to system default if certifi is missing
    _SSL_CONTEXT = ssl.create_default_context()

_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_CACHE_TTL = 600.0  # seconds — re-opening About won't re-hit the network
_cache: dict = {"ts": 0.0, "result": None}


def _vtuple(tag: str) -> tuple[int, ...]:
    """'v0.2.1' -> (0, 2, 1); tolerant of missing/odd parts."""
    tag = (tag or "").strip().lstrip("vV")
    out = []
    for part in tag.split("."):
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out) or (0,)


class UpdateStatus:
    def __init__(self, current: str, latest: str | None = None,
                 url: str | None = None, error: str | None = None) -> None:
        self.current = current
        self.latest = latest
        self.url = url or RELEASES_URL
        self.error = error

    @property
    def checked(self) -> bool:
        return self.error is None and self.latest is not None

    @property
    def available(self) -> bool:
        return self.latest is not None and _vtuple(self.latest) > _vtuple(self.current)

    def summary(self) -> str:
        """One-line status for the About panel."""
        if not self.checked:
            return "Update check unavailable (offline?)"
        if self.available:
            return f"⬆ Update available: v{self.latest} (you have v{self.current})"
        return f"✓ You're on the latest version (v{self.current})"


def check(timeout: float = 3.0, use_cache: bool = True) -> UpdateStatus:
    now = time.time()
    if use_cache and _cache["result"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["result"]

    req = urllib.request.Request(_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"BrowserTabCounter/{VERSION}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            data = json.load(resp)
        latest = (data.get("tag_name") or "").strip().lstrip("vV")
        status = UpdateStatus(VERSION, latest=latest or None,
                              url=data.get("html_url"))
    except Exception as exc:  # noqa: BLE001 - offline/timeout/rate-limit are non-fatal
        status = UpdateStatus(VERSION, error=f"{type(exc).__name__}: {exc}")

    _cache.update(ts=now, result=status)
    return status


if __name__ == "__main__":
    # Sanity checks + a live check.
    assert _vtuple("v0.2.1") == (0, 2, 1)
    assert _vtuple("1.0") == (1, 0)
    assert UpdateStatus("0.2.1", "0.3.0").available is True
    assert UpdateStatus("0.2.1", "0.2.1").available is False
    assert UpdateStatus("0.2.1", "0.2.0").available is False
    assert UpdateStatus("0.2.1", error="boom").checked is False
    print("version-compare assertions passed")
    st = check(use_cache=False)
    print("live:", st.summary(), "| url:", st.url, "| error:", st.error)
