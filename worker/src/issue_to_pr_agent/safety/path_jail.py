"""Confine all file access to the workspace root (safety-level guard)."""

from __future__ import annotations

from pathlib import Path

from .refusal import refuse


def assert_within_jail(root: Path, target: str | Path) -> Path:
    """Resolve `target` under `root`; refuse if it escapes."""
    root = root.resolve()
    resolved = (root / target).resolve()
    if resolved != root and root not in resolved.parents:
        raise refuse("path_jail_escape", "path escapes the workspace", str(target))
    return resolved


def is_within_jail(root: Path, target: str | Path) -> bool:
    try:
        assert_within_jail(root, target)
        return True
    except Exception:
        return False
