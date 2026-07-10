"""PR-body quality: fraction of the required sections present."""

from __future__ import annotations

REQUIRED_SECTIONS = ["## What", "## Why", "## Changes", "## Verification", "## Trace"]


def pr_quality(body: str) -> float:
    if not body:
        return 0.0
    return round(sum(1 for s in REQUIRED_SECTIONS if s in body) / len(REQUIRED_SECTIONS), 4)
