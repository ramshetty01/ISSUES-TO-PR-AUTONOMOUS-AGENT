"""High-level LLM client: router + token/cost metering in one place."""

from __future__ import annotations

from .cost_meter import CostMeter
from .provider_base import Completion, Message
from .router import Router
from .token_meter import TokenMeter


class LLMClient:
    def __init__(self, router: Router) -> None:
        self._router = router
        self.tokens = TokenMeter()
        self.cost = CostMeter()

    def complete(
        self,
        messages: list[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Completion:
        result = self._router.complete(
            messages, max_tokens=max_tokens, temperature=temperature
        )
        self.tokens.record(result.usage)
        self.cost.record(result.provider, result.usage.total)
        return result
