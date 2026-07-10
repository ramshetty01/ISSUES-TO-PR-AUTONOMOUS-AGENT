"""How edits are proposed + applied. Currently: direct tool edits, with a
unified-diff patch path as the alternative."""

from __future__ import annotations

from typing import Any

from ..tools.registry import ToolContext, ToolRegistry


def apply_edit(
    registry: ToolRegistry, ctx: ToolContext, *, path: str, old: str, new: str
) -> dict[str, Any]:
    return registry.call("edit_file", ctx, path=path, old=old, new=new)


def apply_patch(registry: ToolRegistry, ctx: ToolContext, *, patch: str) -> dict[str, Any]:
    return registry.call("git_apply_patch", ctx, patch=patch)
