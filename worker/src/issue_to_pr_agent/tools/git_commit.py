"""Tool: stage + commit all changes with the app identity."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from ..github.commits import commit_all
from .registry import ToolContext


def git_commit(ctx: ToolContext, *, message: str) -> dict[str, Any]:
    if ctx.git is None:
        raise SandboxError("git_commit: no git runner in context")
    sha = commit_all(ctx.git, ctx.repo_dir, message)
    return {"ok": True, "sha": sha}
