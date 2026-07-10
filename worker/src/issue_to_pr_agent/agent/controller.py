"""Top-level agent controller: wires the loop with default budgets."""

from __future__ import annotations

from ..llm.client import LLMClient
from ..tools.registry import ToolContext, ToolRegistry
from .loop import AgentResult, run_agent
from .observation_budget import ObservationBudget
from .turn_budget import TurnBudget


class AgentController:
    def __init__(
        self,
        llm: LLMClient,
        registry: ToolRegistry,
        *,
        max_turns: int = 20,
        max_observation_tokens: int = 20000,
    ) -> None:
        self._llm = llm
        self._registry = registry
        self._tb = TurnBudget(max_turns)
        self._ob = ObservationBudget(max_observation_tokens)

    def run(self, ctx: ToolContext, issue: str, *, context: str = "") -> AgentResult:
        return run_agent(
            self._llm,
            self._registry,
            ctx,
            issue,
            context=context,
            turn_budget=self._tb,
            obs_budget=self._ob,
        )
