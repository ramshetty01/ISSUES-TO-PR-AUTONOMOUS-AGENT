"""NVIDIA NIM provider (OpenAI-compatible chat/completions). Primary eval provider."""

from __future__ import annotations

from ..provider_base import (
    Completion,
    Message,
    Provider,
    ProviderError,
    RateLimitError,
    TokenUsage,
    Transport,
    default_transport,
    post_json,
)


class OpenAICompatProvider(Provider):
    """Shared base for OpenAI-compatible chat APIs (NIM, Groq)."""

    name = "openai-compat"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        extra_body: dict[str, object] | None = None,
        transport: Transport = default_transport,
    ) -> None:
        self._key = api_key
        self._base = base_url.rstrip("/")
        self._model = model
        self._extra_body = extra_body or {}
        self._transport = transport

    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion:
        status, data = post_json(
            self._transport,
            f"{self._base}/chat/completions",
            {"Authorization": f"Bearer {self._key}"},
            {
                "model": self._model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **self._extra_body,
            },
        )
        if status == 429:
            raise RateLimitError(f"{self.name} rate limited")
        if status // 100 != 2 or not data:
            raise ProviderError(f"{self.name} error ({status})")
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return Completion(
            text,
            TokenUsage(
                input=int(usage.get("prompt_tokens", 0)),
                output=int(usage.get("completion_tokens", 0)),
            ),
            self.name,
        )


class NvidiaNimProvider(OpenAICompatProvider):
    name = "nvidia_nim"

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3.5-122b-a10b",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        extra_body: dict[str, object] | None = None,
        transport: Transport = default_transport,
    ) -> None:
        payload = extra_body or {"temperature": 0.60, "top_p": 0.95}
        super().__init__(api_key, base_url, model, extra_body=payload, transport=transport)
