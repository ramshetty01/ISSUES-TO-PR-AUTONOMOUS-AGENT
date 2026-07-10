"""Crude style score over added lines: penalize tabs, trailing ws, long lines."""

from __future__ import annotations


def style_conformance(diff: str) -> float:
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    if not added:
        return 1.0
    bad = sum(1 for l in added if "\t" in l or l.rstrip() != l or len(l) > 100)
    return round(1 - bad / len(added), 4)
