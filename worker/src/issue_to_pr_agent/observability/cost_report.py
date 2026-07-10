"""Per-provider token + imputed-dollar report for a run.

Accumulates usage as the run charges each provider, then reconciles its totals
against the run's ``TokenMeter``/``CostMeter`` so the report can never silently
diverge from the meters that gated the budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm.cost_meter import DEFAULT_PRICES
from ..llm.provider_base import TokenUsage


@dataclass(slots=True)
class ProviderCost:
    """Running totals for a single provider."""

    input: int = 0
    output: int = 0
    dollars: float = 0.0

    @property
    def total(self) -> int:
        return self.input + self.output

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "total": self.total,
            "dollars": round(self.dollars, 6),
        }


class CostReport:
    """Builds a tokens-and-dollars breakdown, imputing $ at list price."""

    def __init__(self, prices: dict[str, float] | None = None) -> None:
        self._prices = prices or DEFAULT_PRICES
        self._by_provider: dict[str, ProviderCost] = {}

    def record(self, provider: str, usage: TokenUsage) -> float:
        """Charge ``usage`` to ``provider``; return the imputed dollars added."""
        entry = self._by_provider.setdefault(provider, ProviderCost())
        entry.input += usage.input
        entry.output += usage.output
        cost = self._prices.get(provider, 0.0) * usage.total / 1000.0
        entry.dollars += cost
        return cost

    @property
    def usage(self) -> dict[str, int]:
        input_ = sum(p.input for p in self._by_provider.values())
        output = sum(p.output for p in self._by_provider.values())
        return {"input": input_, "output": output, "total": input_ + output}

    @property
    def dollars(self) -> float:
        return sum(p.dollars for p in self._by_provider.values())

    @property
    def by_provider(self) -> dict[str, dict[str, Any]]:
        return {name: cost.to_dict() for name, cost in self._by_provider.items()}

    def reconciles_with(self, token_meter: Any, cost_meter: Any | None = None) -> bool:
        """True when totals match the run meters (guards drift)."""
        usage = self.usage
        if usage["input"] != token_meter.input or usage["output"] != token_meter.output:
            return False
        if cost_meter is not None and abs(self.dollars - cost_meter.dollars) > 1e-9:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "usage": self.usage,
            "dollars": round(self.dollars, 6),
            "byProvider": self.by_provider,
        }
