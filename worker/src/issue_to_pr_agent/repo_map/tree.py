"""List a repository's files, skipping noise directories."""

from __future__ import annotations

from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "target", ".turbo",
}


def list_files(repo_dir: Path, max_files: int = 2000) -> list[Path]:
    """Repo-relative file paths, excluding SKIP_DIRS, capped at max_files."""
    out: list[Path] = []
    for p in sorted(repo_dir.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(repo_dir).parts):
            continue
        out.append(p.relative_to(repo_dir))
        if len(out) >= max_files:
            break
    return out


def build_tree(repo_dir: Path, max_files: int = 2000) -> str:
    """A newline-joined file listing (a compact repo map)."""
    return "\n".join(str(p) for p in list_files(repo_dir, max_files))
