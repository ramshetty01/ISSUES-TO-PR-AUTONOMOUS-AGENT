"""Parse the model's response into the next action."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from ..llm.response_parser import extract_json


@dataclass(slots=True)
class Action:
    kind: Literal["tool", "finish", "invalid"]
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    thought: str = ""


def parse_action(text: str) -> Action:
    """Interpret an LLM response.

    Expected JSON: {"tool": "edit_file", "args": {...}} to act, or
    {"finish": true, "success": true} to stop.
    """
    data = extract_json(text)
    if not isinstance(data, dict):
        return Action(kind="invalid", thought=text[:200])
    if data.get("finish"):
        return Action(kind="finish", success=bool(data.get("success", False)))
    tool = data.get("tool")
    if isinstance(tool, str):
        args = data.get("args")
        return Action(
            kind="tool",
            tool=tool,
            args=args if isinstance(args, dict) else {},
            thought=str(data.get("thought", "")),
        )
    return Action(kind="invalid", thought=text[:200])
