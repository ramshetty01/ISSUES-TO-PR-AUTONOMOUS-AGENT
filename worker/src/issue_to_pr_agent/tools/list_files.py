"""Tool: list repository files (noise dirs skipped)."""

from __future__ import annotations

from typing import Any

from ..repo_map.tree import list_files as _list
from .registry import ToolContext


def list_files_tool(ctx: ToolContext, *, max_files: int = 500) -> dict[str, Any]:
    files = [str(p) for p in _list(ctx.repo_dir, max_files=max_files)]
    return {"ok": True, "files": files, "count": len(files)}
