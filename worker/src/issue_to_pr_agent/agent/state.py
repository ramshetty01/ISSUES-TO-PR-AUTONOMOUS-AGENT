"""Mutable agent state carried across the plan-act-reflect loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentState:
    turns: int = 0
    done: bool = False
    success: bool = False
    plan: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    consecutive_failures: int = 0
    stop_reason: str = ""

    def record_action(self, action: dict[str, Any], observation: str, *, failed: bool) -> None:
        self.actions.append(action)
        self.observations.append(observation)
        self.consecutive_failures = self.consecutive_failures + 1 if failed else 0
