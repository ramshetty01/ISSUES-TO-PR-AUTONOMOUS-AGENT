"""Bound how much observation text accumulates in the context."""

from __future__ import annotations

import math


class ObservationBudget:
    def __init__(self, max_tokens: int = 20000) -> None:
        self.max_tokens = max_tokens

    @staticmethod
    def estimate(text: str) -> int:
        return math.ceil(len(text) / 4)

    def total(self, observations: list[str]) -> int:
        return sum(self.estimate(o) for o in observations)

    def exceeded(self, observations: list[str]) -> bool:
        return self.total(observations) > self.max_tokens

    def trim(self, observations: list[str]) -> list[str]:
        """Drop oldest observations until under budget (keep most recent)."""
        kept = list(observations)
        while kept and self.total(kept) > self.max_tokens:
            kept.pop(0)
        return kept
