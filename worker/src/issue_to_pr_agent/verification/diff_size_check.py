"""Cap the size of a change (added/removed lines + files touched)."""

from __future__ import annotations

from dataclasses import dataclass

from .forbidden_diff_check import changed_paths_from_diff


@dataclass(slots=True)
class DiffStats:
    files: int
    added: int
    removed: int

    @property
    def changed_lines(self) -> int:
        return self.added + self.removed


def diff_stats(diff: str) -> DiffStats:
    added = removed = 0
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return DiffStats(files=len(changed_paths_from_diff(diff)), added=added, removed=removed)


@dataclass(slots=True)
class DiffSizeResult:
    ok: bool
    stats: DiffStats
    reason: str = ""


def check_diff_size(diff: str, *, max_lines: int = 500, max_files: int = 20) -> DiffSizeResult:
    stats = diff_stats(diff)
    if stats.files > max_files:
        return DiffSizeResult(False, stats, f"too many files ({stats.files} > {max_files})")
    if stats.changed_lines > max_lines:
        return DiffSizeResult(
            False, stats, f"too many changed lines ({stats.changed_lines} > {max_lines})"
        )
    return DiffSizeResult(True, stats)
