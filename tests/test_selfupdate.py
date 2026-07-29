"""Tests for the self-updater's pure logic (not the network/mount I/O).

Run:  ./.venv/bin/python tests/test_selfupdate.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import selfupdate  # noqa: E402


def test_shell_quoting_is_injection_safe():
    # A path with spaces, quotes, and shell metacharacters must be safely quoted.
    nasty = "/Applications/Browser Tab Counter.app; rm -rf ~ '$(x)'"
    q = selfupdate._q(nasty)
    assert q.startswith("'") and q.endswith("'")
    # The only way a single quote appears inside is via the '\'' escape.
    inner = q[1:-1]
    assert "'" not in inner.replace("'\\''", "")


def test_verify_rejects_missing_app():
    try:
        selfupdate.verify_app(selfupdate.Path("/no/such/app.app"))
        raise AssertionError("should have rejected a non-existent app")
    except selfupdate.UpdateError:
        pass


def test_team_id_is_pinned():
    assert selfupdate.TEAM_ID == "ZWXAL8XA46"


if __name__ == "__main__":
    test_shell_quoting_is_injection_safe()
    test_verify_rejects_missing_app()
    test_team_id_is_pinned()
    print("all self-update tests passed")
