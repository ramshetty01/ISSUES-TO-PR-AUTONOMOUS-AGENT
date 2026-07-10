"""Parse a unified diff into a per-file change summary.

Deterministic and dependency-free so the PR body can always describe *what*
changed without an LLM round-trip. Feeds the "Changes" section of the body.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FileChange:
    """Line counts and status for one file in a diff."""

    path: str
    added: int = 0
    removed: int = 0
    status: str = "modified"  # "added" | "removed" | "renamed" | "modified"

    def to_markdown(self) -> str:
        return f"- `{self.path}` ({self.status}, +{self.added}/-{self.removed})"


@dataclass(slots=True)
class DiffSummary:
    """The full set of file changes parsed from a diff."""

    files: list[FileChange] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return sum(f.added for f in self.files)

    @property
    def total_removed(self) -> int:
        return sum(f.removed for f in self.files)

    def is_empty(self) -> bool:
        return not self.files

    def to_markdown(self) -> str:
        if self.is_empty():
            return "_No file changes._"
        return "\n".join(f.to_markdown() for f in self.files)


def _path_from_header(line: str) -> str:
    # "diff --git a/foo.py b/foo.py" -> "foo.py"
    parts = line.split()
    if len(parts) >= 4 and parts[2].startswith("a/"):
        return parts[3][2:] if parts[3].startswith("b/") else parts[3]
    return parts[-1] if parts else ""


def summarize_diff(diff: str) -> DiffSummary:
    """Parse a unified diff into a :class:`DiffSummary`."""
    summary = DiffSummary()
    current: FileChange | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            current = FileChange(path=_path_from_header(line))
            summary.files.append(current)
        elif current is None:
            continue
        elif line.startswith("new file"):
            current.status = "added"
        elif line.startswith("deleted file"):
            current.status = "removed"
        elif line.startswith("rename to "):
            current.status = "renamed"
            current.path = line[len("rename to ") :].strip()
        elif line.startswith("+++ b/"):
            current.path = line[len("+++ b/") :].strip() or current.path
        elif line.startswith("+") and not line.startswith("+++"):
            current.added += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.removed += 1
    return summary
