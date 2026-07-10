"""Fraction of eval issues whose run reached the expected terminal outcome."""

from __future__ import annotations


def pass_rate(results: list[dict]) -> float:
    """results: list of per-issue result dicts carrying a boolean ``passed``."""
    if not results:
        return 0.0
    return round(sum(1 for r in results if r.get("passed")) / len(results), 4)
