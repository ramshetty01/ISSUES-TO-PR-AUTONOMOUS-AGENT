"""The plan-act-reflect loop."""

from __future__ import annotations

import json
from dataclasses import dataclass

from ..errors import LLMError
from ..llm.client import LLMClient
from ..llm.provider_base import Message
from ..tools.registry import ToolContext, ToolRegistry
from . import executor, finalizer, planner
from .observation_budget import ObservationBudget
from .reflector import parse_action
from .state import AgentState
from .stopping import should_stop
from .turn_budget import TurnBudget

_ACTION_INSTRUCTION = (
    "Respond with exactly one JSON object and nothing else. Do not explain, "
    "analyze, or use Markdown. To act: "
    '{"tool": "<name>", "args": {...}}. To stop: '
    '{"finish": true, "success": true|false}.'
)


@dataclass(slots=True)
class AgentResult:
    success: bool
    turns: int
    stop_reason: str
    diff: str
    summary: str
    state: AgentState


def _messages(state: AgentState, issue: str, registry: ToolRegistry) -> list[Message]:
    recent = "\n".join(state.observations[-8:])
    tools = json.dumps(registry.schemas(), indent=2)
    return [
        Message("system", planner._load("system.md")),
        Message(
            "user",
            f"## Issue\n{issue}\n\n## Plan\n{state.plan}\n\n"
            f"## Available tools\n{tools}\n\n"
            f"## Recent observations\n{recent}\n\n{_ACTION_INSTRUCTION}",
        ),
    ]


def run_agent(
    llm: LLMClient,
    registry: ToolRegistry,
    ctx: ToolContext,
    issue: str,
    *,
    context: str = "",
    turn_budget: TurnBudget | None = None,
    obs_budget: ObservationBudget | None = None,
) -> AgentResult:
    tb = turn_budget or TurnBudget()
    ob = obs_budget or ObservationBudget()
    state = AgentState()
    state.plan = planner.plan(llm, issue, context)

    while True:
        stop, reason = should_stop(state, tb, ob)
        if stop:
            state.stop_reason = reason
            break

        state.turns += 1
        try:
            response = llm.complete(_messages(state, issue, registry), max_tokens=1024)
        except LLMError:
            state.stop_reason = "provider_error"
            break
        action = parse_action(response.text)

        if action.kind == "finish":
            state.done = True
            state.success = action.success
            state.stop_reason = "finished" if action.success else "gave_up"
            break
        if action.kind == "invalid":
            state.record_action(
                {"raw": response.text[:120]}, "invalid action; expected JSON", failed=True
            )
            continue

        obs, failed = executor.execute(registry, ctx, action)
        state.record_action(
            {"tool": action.tool, "args": action.args}, obs, failed=failed
        )
        state.observations = ob.trim(state.observations)

    final = finalizer.finalize(registry, ctx, state)
    return AgentResult(
        success=state.success,
        turns=state.turns,
        stop_reason=state.stop_reason,
        diff=final["diff"],
        summary=final["summary"],
        state=state,
    )


def action_json(
    tool: str | None = None,
    args: dict[str, object] | None = None,
    *,
    finish: bool = False,
    success: bool = False,
) -> str:
    """Helper to build an action JSON string (used by scripted providers/tests)."""
    if finish:
        return json.dumps({"finish": True, "success": success})
    return json.dumps({"tool": tool, "args": args or {}})
