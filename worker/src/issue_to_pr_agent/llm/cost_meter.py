"""Impute dollar cost from tokens at provider list price (0 for free/local)."""

from __future__ import annotations

# Dollars per 1k total tokens (imputed list price; free tiers metered at $0).
DEFAULT_PRICES: dict[str, float] = {
    "mock": 0.0,
    "ollama": 0.0,
    "nvidia_nim": 0.0,
    "gemini": 0.0,
    "groq": 0.0,
}


class CostMeter:
    def __init__(self, prices: dict[str, float] | None = None) -> None:
        self._prices = prices or DEFAULT_PRICES
        self._dollars = 0.0

    def record(self, provider: str, total_tokens: int) -> float:
        cost = self._prices.get(provider, 0.0) * total_tokens / 1000.0
        self._dollars += cost
        return cost

    @property
    def dollars(self) -> float:
        return self._dollars
