"""Assemble the run result (diff + summary) for the PR stage."""

from __future__ import annotations

from ..tools.registry import ToolContext, ToolRegistry
from .state import AgentState


def finalize(registry: ToolRegistry, ctx: ToolContext, state: AgentState) -> dict[str, str]:
    diff = ""
    if ctx.git is not None:
        try:
            diff = registry.call("git_diff", ctx).get("diff", "")
        except Exception:  # diff is best-effort at finalize time
            diff = ""
    summary = state.plan.strip().splitlines()[0] if state.plan.strip() else "agent run"
    return {"diff": diff, "summary": summary}
