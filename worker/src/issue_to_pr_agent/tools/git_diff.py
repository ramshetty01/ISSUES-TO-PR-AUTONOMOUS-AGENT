"""Tool: git diff via the git runner."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from .registry import ToolContext


def git_diff(ctx: ToolContext, *, base: str | None = None) -> dict[str, Any]:
    if ctx.git is None:
        raise SandboxError("git_diff: no git runner in context")
    args = ["diff"]
    if base:
        args.append(base)
    res = ctx.git.run(args, cwd=ctx.repo_dir)
    return {"ok": res.returncode == 0, "diff": res.stdout}
