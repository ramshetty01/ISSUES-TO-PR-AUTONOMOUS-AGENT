"""Block edits to forbidden paths (CI workflows, secrets, etc.)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

DEFAULT_FORBIDDEN = [
    ".github/workflows/",
    ".github/actions/",
    ".git/",
]

_DIFF_GIT = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
_PLUSPLUS = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def changed_paths_from_diff(diff: str) -> list[str]:
    """Extract changed file paths from a unified diff."""
    paths: list[str] = []
    for m in _DIFF_GIT.finditer(diff):
        paths.append(m.group(2))
    if not paths:  # fall back to +++ headers
        for m in _PLUSPLUS.finditer(diff):
            p = m.group(1)
            if p != "/dev/null":
                paths.append(p)
    return paths


@dataclass(slots=True)
class ForbiddenDiffResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def check_forbidden_paths(
    paths: list[str], forbidden: list[str] = DEFAULT_FORBIDDEN
) -> ForbiddenDiffResult:
    violations = [p for p in paths if any(p.startswith(f) or f.rstrip("/") == p for f in forbidden)]
    return ForbiddenDiffResult(ok=not violations, violations=violations)


def check_forbidden_diff(
    diff: str, forbidden: list[str] = DEFAULT_FORBIDDEN
) -> ForbiddenDiffResult:
    return check_forbidden_paths(changed_paths_from_diff(diff), forbidden)


def load_forbidden_paths(path: str | Path) -> list[str]:
    import yaml

    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return cast(list[str], doc.get("forbidden", DEFAULT_FORBIDDEN))
