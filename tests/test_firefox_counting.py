"""Regression tests for Firefox tab counting.

Focus on the accuracy cases that bit us on multi-window / multi-profile setups.
Run with:  ./.venv/bin/python -m pytest test_firefox_counting.py   (or just run it)
No third-party deps required — plain asserts, runnable directly.
"""

from __future__ import annotations

import os
import sys

# App modules live in ../src.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tabcount as t  # noqa: E402


def test_sum_across_multiple_windows():
    data = {"windows": [
        {"tabs": [{}, {}, {}, {}]},   # 4 tabs
        {"tabs": [{}, {}]},           # 2 tabs
    ]}
    assert t._count_session_tabs(data) == 6


def test_empty_and_missing_windows():
    assert t._count_session_tabs({"windows": []}) == 0
    assert t._count_session_tabs({}) == 0
    # A window with no "tabs" key contributes 0, not a crash.
    assert t._count_session_tabs({"windows": [{}, {"tabs": [{}]}]}) == 1


def test_closed_windows_not_counted():
    # Tabs of already-closed windows must not be included.
    data = {
        "windows": [{"tabs": [{}, {}]}],
        "_closedWindows": [{"tabs": [{}, {}, {}]}],
    }
    assert t._count_session_tabs(data) == 2


def test_multi_profile_summation(monkeypatch=None):
    """Two open profiles => their tabs add up; closed/unreadable => skipped."""
    calls = {"a": {"windows": [{"tabs": [{}, {}, {}]}]},   # 3
             "b": {"windows": [{"tabs": [{}]}]},            # 1
             "closed": None}

    import types
    fake_profiles = [types.SimpleNamespace(name=n) for n in ("a", "b", "closed")]
    t_orig_dirs = t._firefox_profile_dirs
    t_orig_open = t._profile_is_open
    t_orig_read = t._read_firefox_session
    try:
        t._firefox_profile_dirs = lambda app: fake_profiles
        # "closed" is not open -> excluded even though it might have data.
        t._profile_is_open = lambda p: p.name in ("a", "b")
        t._read_firefox_session = lambda p: calls[p.name]
        assert t._count_via_firefox("Firefox") == (4, None)
    finally:
        t._firefox_profile_dirs = t_orig_dirs
        t._profile_is_open = t_orig_open
        t._read_firefox_session = t_orig_read


if __name__ == "__main__":
    test_sum_across_multiple_windows()
    test_empty_and_missing_windows()
    test_closed_windows_not_counted()
    test_multi_profile_summation()
    print("all Firefox-counting tests passed")
