"""Stage + commit changes with the app identity."""

from __future__ import annotations

from pathlib import Path

from ..errors import SandboxError
from .clone import GitRunner

APP_AUTHOR_NAME = "issue-to-pr-agent[bot]"
APP_AUTHOR_EMAIL = "issue-to-pr-agent[bot]@users.noreply.github.com"


def commit_all(
    runner: GitRunner,
    repo_dir: Path,
    message: str,
    *,
    author_name: str = APP_AUTHOR_NAME,
    author_email: str = APP_AUTHOR_EMAIL,
) -> str:
    """Stage every change and commit; returns the new commit sha."""
    for args in (
        ["config", "user.name", author_name],
        ["config", "user.email", author_email],
        ["add", "-A"],
        ["commit", "-m", message],
    ):
        res = runner.run(args, cwd=repo_dir)
        if res.returncode != 0:
            raise SandboxError(f"git {args[0]} failed: {res.stderr.strip()}")
    head = runner.run(["rev-parse", "HEAD"], cwd=repo_dir)
    if head.returncode != 0:
        raise SandboxError("cannot read HEAD sha")
    return head.stdout.strip()
