"""Bound the number of agent iterations."""

from __future__ import annotations


class TurnBudget:
    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns

    def exceeded(self, turns: int) -> bool:
        return turns >= self.max_turns

    def remaining(self, turns: int) -> int:
        return max(0, self.max_turns - turns)
