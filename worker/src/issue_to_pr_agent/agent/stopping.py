"""Stopping criteria for the agent loop."""

from __future__ import annotations

from .observation_budget import ObservationBudget
from .state import AgentState
from .turn_budget import TurnBudget

MAX_CONSECUTIVE_FAILURES = 3


def should_stop(
    state: AgentState, turn_budget: TurnBudget, obs_budget: ObservationBudget
) -> tuple[bool, str]:
    if state.done:
        return True, "finished" if state.success else "gave_up"
    if turn_budget.exceeded(state.turns):
        return True, "turn_budget_exceeded"
    if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
        return True, "too_many_failures"
    if obs_budget.exceeded(state.observations):
        # not terminal by itself — the loop trims — but stop if trimming can't help
        if len(state.observations) <= 1:
            return True, "observation_budget_exceeded"
    return False, ""
