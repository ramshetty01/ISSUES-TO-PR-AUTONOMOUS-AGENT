"""Git worktree management (isolated checkouts for a branch)."""

from __future__ import annotations

from pathlib import Path

from ..errors import SandboxError
from .clone import GitRunner


def add_worktree(runner: GitRunner, repo_dir: Path, path: Path, branch: str) -> Path:
    res = runner.run(["worktree", "add", "-b", branch, str(path)], cwd=repo_dir)
    if res.returncode != 0:
        raise SandboxError(f"git worktree add failed for {branch}")
    return path


def remove_worktree(runner: GitRunner, repo_dir: Path, path: Path) -> None:
    runner.run(["worktree", "remove", "--force", str(path)], cwd=repo_dir)
