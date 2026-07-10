"""Tool: git status (porcelain) via the git runner."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from .registry import ToolContext


def git_status(ctx: ToolContext) -> dict[str, Any]:
    if ctx.git is None:
        raise SandboxError("git_status: no git runner in context")
    res = ctx.git.run(["status", "--porcelain"], cwd=ctx.repo_dir)
    files = [line for line in res.stdout.splitlines() if line.strip()]
    return {"ok": res.returncode == 0, "changed": files, "count": len(files)}
