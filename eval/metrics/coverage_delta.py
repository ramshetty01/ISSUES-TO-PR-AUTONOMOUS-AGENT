"""Test-coverage change introduced by the run (percentage points)."""

from __future__ import annotations


def coverage_delta(before_pct: float, after_pct: float) -> float:
    return round(after_pct - before_pct, 4)
