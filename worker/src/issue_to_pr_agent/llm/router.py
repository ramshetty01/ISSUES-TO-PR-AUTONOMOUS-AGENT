"""Provider router: ordered fallback chain with rate-limit awareness + backoff."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import LLMError
from .provider_base import (
    Completion,
    Message,
    Provider,
    ProviderError,
    RateLimitError,
    estimate_prompt_tokens,
)
from .rate_limiter import RateLimiter


@dataclass(slots=True)
class RouteAttempt:
    provider: str
    outcome: str  # "ok" | "rate_limited" | "throttled" | "error"


class Router:
    """Try providers in order; fall through on rate limits + errors."""

    def __init__(self, providers: list[Provider], rate_limiter: RateLimiter | None = None) -> None:
        if not providers:
            raise ValueError("router needs at least one provider")
        self._providers = providers
        self._rl = rate_limiter
        self.attempts: list[RouteAttempt] = []

    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion:
        self.attempts = []
        est = estimate_prompt_tokens(messages) + max_tokens
        errors: list[str] = []

        for provider in self._providers:
            if self._rl is not None and not self._rl.allow(provider.name, est):
                self.attempts.append(RouteAttempt(provider.name, "throttled"))
                errors.append(f"{provider.name}: locally throttled")
                continue
            try:
                result = provider.complete(
                    messages, max_tokens=max_tokens, temperature=temperature
                )
                if self._rl is not None:
                    self._rl.record(provider.name, result.usage.total)
                self.attempts.append(RouteAttempt(provider.name, "ok"))
                return result
            except RateLimitError as exc:
                self.attempts.append(RouteAttempt(provider.name, "rate_limited"))
                errors.append(f"{provider.name}: {exc}")
            except ProviderError as exc:
                self.attempts.append(RouteAttempt(provider.name, "error"))
                errors.append(f"{provider.name}: {exc}")

        raise LLMError("all providers failed: " + "; ".join(errors))
