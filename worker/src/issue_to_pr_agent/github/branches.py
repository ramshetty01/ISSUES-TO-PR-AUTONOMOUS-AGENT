"""Branch creation + a push guard that never targets a protected branch."""

from __future__ import annotations

from pathlib import Path

from ..errors import SafetyRefusal, SandboxError
from .clone import GitRunner


def current_branch(runner: GitRunner, repo_dir: Path) -> str:
    res = runner.run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    if res.returncode != 0:
        raise SandboxError("cannot determine current branch")
    return res.stdout.strip()


def create_branch(
    runner: GitRunner, repo_dir: Path, name: str, base: str | None = None
) -> str:
    args = ["checkout", "-b", name]
    if base:
        args.append(base)
    res = runner.run(args, cwd=repo_dir)
    if res.returncode != 0:
        raise SandboxError(f"cannot create branch {name}")
    return name


def push_branch(
    runner: GitRunner,
    repo_dir: Path,
    branch: str,
    *,
    protected: set[str],
    force: bool = False,
) -> None:
    """Push a feature branch. Refuses to push to a protected branch or to force."""
    if branch in protected:
        raise SafetyRefusal(
            "force_push_blocked" if force else "workflow_write_blocked",
            f"refusing to push directly to protected branch '{branch}'",
        )
    if force:
        raise SafetyRefusal("force_push_blocked", "force push is not allowed")
    res = runner.run(["push", "origin", branch], cwd=repo_dir)
    if res.returncode != 0:
        raise SandboxError(f"git push failed for {branch}")
