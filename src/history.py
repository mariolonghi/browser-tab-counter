"""Tabs-over-time mini-log — deliberately tiny.

Samples the *total* tab count every few minutes into a capped CSV ring buffer
(timestamp,total), and renders a Unicode sparkline + today's min/avg/max for the
menu. Counts only — never any tab content. A few tens of KB at most.
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from pathlib import Path

import prefs

HISTORY_PATH: Path = prefs.APP_SUPPORT / "history.csv"
SAMPLE_INTERVAL = 300          # seconds between samples (5 min)
MAX_AGE_DAYS = 7               # ring-buffer horizon

_BLOCKS = "▁▂▃▄▅▆▇█"
_last_sample = 0.0


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def record(total: int, when: datetime | None = None) -> None:
    """Append one sample and trim anything older than the horizon."""
    prefs.ensure_dir()
    ts = (when or datetime.now()).isoformat(timespec="seconds")
    with HISTORY_PATH.open("a", newline="") as f:
        csv.writer(f).writerow([ts, total])
    _trim()


def maybe_record(total: int) -> None:
    """Record at most once per SAMPLE_INTERVAL (call it as often as you like)."""
    global _last_sample
    now = time.time()
    if now - _last_sample >= SAMPLE_INTERVAL:
        _last_sample = now
        record(total)


def _trim() -> None:
    rows = _read_rows()
    if not rows:
        return
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    kept = [(ts, v) for ts, v in rows if ts.timestamp() >= cutoff]
    if len(kept) != len(rows):
        with HISTORY_PATH.open("w", newline="") as f:
            w = csv.writer(f)
            for ts, v in kept:
                w.writerow([ts.isoformat(timespec="seconds"), v])


# --------------------------------------------------------------------------
# Reading / rendering
# --------------------------------------------------------------------------

def _read_rows() -> list[tuple[datetime, int]]:
    out: list[tuple[datetime, int]] = []
    try:
        with HISTORY_PATH.open(newline="") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                try:
                    out.append((datetime.fromisoformat(row[0]), int(row[1])))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def sparkline(values: list[int]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        return _BLOCKS[3] * len(values)
    span = hi - lo
    return "".join(_BLOCKS[int((v - lo) / span * (len(_BLOCKS) - 1))] for v in values)


def today_samples() -> list[int]:
    today = datetime.now().date()
    return [v for ts, v in _read_rows() if ts.date() == today]


def menu_summary() -> str:
    """One-line summary for the dropdown."""
    vals = today_samples()
    if not vals:
        return "Tab history: collecting…"
    spark = sparkline(vals[-40:])
    avg = round(sum(vals) / len(vals))
    return f"Today {spark}  min {min(vals)} · avg {avg} · max {max(vals)}"


if __name__ == "__main__":
    print("history path:", HISTORY_PATH)
    print("today samples:", today_samples())
    print("summary:", menu_summary())
