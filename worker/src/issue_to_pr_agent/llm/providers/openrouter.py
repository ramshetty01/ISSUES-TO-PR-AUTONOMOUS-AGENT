"""OpenRouter provider using its OpenAI-compatible chat completions API."""

from __future__ import annotations

import time

from ..provider_base import (
    Completion,
    Message,
    ProviderError,
    RateLimitError,
    Transport,
    default_transport,
)
from .nvidia_nim import OpenAICompatProvider


class OpenRouterProvider(OpenAICompatProvider):
    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str = "tencent/hy3:free",
        base_url: str = "https://openrouter.ai/api/v1",
        transport: Transport = default_transport,
    ) -> None:
        super().__init__(
            api_key,
            base_url,
            model,
            extra_body={
                "reasoning": {
                    "enabled": True,
                    "max_tokens": 256,
                },
            },
            transport=transport,
        )

    def complete(
        self,
        messages: list[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Completion:
        last_error: ProviderError | RateLimitError | None = None
        for attempt in range(3):
            try:
                return super().complete(
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except (ProviderError, RateLimitError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1 << attempt)
        assert last_error is not None
        raise last_error
