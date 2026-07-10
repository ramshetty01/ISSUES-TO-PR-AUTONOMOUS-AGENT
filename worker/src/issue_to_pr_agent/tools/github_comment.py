"""Tool: post a progress/result comment on the issue or PR."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from ..github.comments import post_comment
from .registry import ToolContext


def github_comment(ctx: ToolContext, *, issue_number: int, body: str) -> dict[str, Any]:
    if ctx.github is None or ctx.repo is None:
        raise SandboxError("github_comment: no github client/repo in context")
    url = post_comment(ctx.github, ctx.repo, issue_number, body)
    return {"ok": True, "url": url}
