"""Tool: apply a unified diff patch atomically (git apply --check then apply)."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from .registry import ToolContext

_PATCH_FILE = ".itpr.patch"


def git_apply_patch(ctx: ToolContext, *, patch: str) -> dict[str, Any]:
    if ctx.git is None:
        raise SandboxError("git_apply_patch: no git runner in context")
    (ctx.repo_dir / _PATCH_FILE).write_text(patch, encoding="utf-8")
    # Validate first so a bad patch leaves the tree untouched.
    check = ctx.git.run(["apply", "--check", _PATCH_FILE], cwd=ctx.repo_dir)
    if check.returncode != 0:
        raise SandboxError(f"patch does not apply cleanly: {check.stderr.strip()}")
    applied = ctx.git.run(["apply", _PATCH_FILE], cwd=ctx.repo_dir)
    (ctx.repo_dir / _PATCH_FILE).unlink(missing_ok=True)
    if applied.returncode != 0:
        raise SandboxError("patch apply failed after passing --check")
    return {"ok": True}
