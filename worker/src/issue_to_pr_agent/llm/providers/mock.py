"""Deterministic mock provider — ALL integration tests run against this. Zero
real tokens, zero network. Optionally configured to fail (for fallback tests).
"""

from __future__ import annotations

from ..provider_base import (
    Completion,
    Message,
    Provider,
    TokenUsage,
    estimate_prompt_tokens,
)


class MockProvider(Provider):
    name = "mock"

    def __init__(self, response: str = "MOCK: no-op change", fail_with: Exception | None = None) -> None:
        self._response = response
        self._fail_with = fail_with
        self.calls = 0

    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion:
        self.calls += 1
        if self._fail_with is not None:
            raise self._fail_with
        usage = TokenUsage(
            input=estimate_prompt_tokens(messages),
            output=max(1, len(self._response) // 4),
        )
        return Completion(self._response, usage, self.name)
