"""Execute a tool action, capturing the observation (and any failure)."""

from __future__ import annotations

from ..tools.registry import ToolContext, ToolRegistry
from .reflector import Action


def execute(registry: ToolRegistry, ctx: ToolContext, action: Action) -> tuple[str, bool]:
    """Run the action's tool. Returns (observation, failed)."""
    if action.kind != "tool" or action.tool is None:
        return "no tool to execute", True
    try:
        result = registry.call(action.tool, ctx, **action.args)
        return f"{action.tool} -> {result}", False
    except Exception as exc:  # tool errors are recoverable, not fatal
        return f"{action.tool} failed: {exc}", True
