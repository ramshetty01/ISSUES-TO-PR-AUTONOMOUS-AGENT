"""Change-size metric parsed from a unified diff (lower is usually better)."""

from __future__ import annotations


def diff_size(diff: str) -> dict:
    added = removed = files = 0
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            files += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return {"added": added, "removed": removed, "files": files, "total": added + removed}
