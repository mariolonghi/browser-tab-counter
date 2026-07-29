"""Tests for the open-tabs CSV export.

Run:  ./.venv/bin/python tests/test_tabexport.py
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tabexport  # noqa: E402


def test_csv_roundtrip_has_all_columns():
    rows = [
        tabexport.Tab(browser="Safari", window=1, tab=2, active="yes",
                      title="Hello, world", url="https://example.com/a,b"),
        tabexport.Tab(browser="Firefox", window=1, tab=1, active="no",
                      pinned="yes", last_accessed="2026-07-15T12:00:00",
                      title="Wiki", url="https://wikipedia.org"),
    ]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        n = tabexport.write_csv(rows, path)
        assert n == 2
        with open(path, newline="", encoding="utf-8") as f:
            got = list(csv.reader(f))
    assert got[0] == tabexport.FIELDS
    # Commas in title/URL must survive (proper CSV quoting).
    assert got[1][tabexport.FIELDS.index("title")] == "Hello, world"
    assert got[1][tabexport.FIELDS.index("url")] == "https://example.com/a,b"
    assert got[2][tabexport.FIELDS.index("pinned")] == "yes"


def test_firefox_gather_pulls_extras(monkeypatch=None):
    """Firefox rows carry title/url + active/pinned/last_accessed."""
    import types
    fake_profile = types.SimpleNamespace(name="p")
    session = {
        "windows": [{
            "selected": 2,
            "tabs": [
                {"pinned": True, "lastAccessed": 1_700_000_000_000,
                 "entries": [{"title": "Pinned home", "url": "https://home"}]},
                {"entries": [{"title": "Second", "url": "https://second"}]},
                {"entries": []},  # no entries -> skipped
            ],
        }],
    }
    orig_dirs = tabexport.tabcount._firefox_profile_dirs
    orig_open = tabexport.tabcount._profile_is_open
    orig_read = tabexport.tabcount._read_firefox_session
    try:
        tabexport.tabcount._firefox_profile_dirs = lambda app: [fake_profile]
        tabexport.tabcount._profile_is_open = lambda p: True
        tabexport.tabcount._read_firefox_session = lambda p: session
        browser = types.SimpleNamespace(name="Firefox", app_support="Firefox")
        rows = tabexport._firefox_gather(browser)
    finally:
        tabexport.tabcount._firefox_profile_dirs = orig_dirs
        tabexport.tabcount._profile_is_open = orig_open
        tabexport.tabcount._read_firefox_session = orig_read

    assert len(rows) == 2                         # empty-entries tab skipped
    assert rows[0].pinned == "yes"
    assert rows[0].last_accessed.startswith("20")  # ISO timestamp
    assert rows[1].active == "yes"                 # tab 2 == selected
    assert rows[0].title == "Pinned home"


if __name__ == "__main__":
    test_csv_roundtrip_has_all_columns()
    test_firefox_gather_pulls_extras()
    print("all tab-export tests passed")
