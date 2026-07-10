"""Ollama provider — fully local inference (Qwen2.5-Coder etc.)."""

from __future__ import annotations

from ..provider_base import (
    Completion,
    Message,
    Provider,
    ProviderError,
    TokenUsage,
    Transport,
    default_transport,
    post_json,
)


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen2.5-coder",
        transport: Transport = default_transport,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._transport = transport

    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion:
        status, data = post_json(
            self._transport,
            f"{self._host}/api/chat",
            {},
            {
                "model": self._model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
        )
        if status // 100 != 2 or not data:
            raise ProviderError(f"ollama error ({status})")
        text = data["message"]["content"]
        return Completion(
            text,
            TokenUsage(
                input=int(data.get("prompt_eval_count", 0)),
                output=int(data.get("eval_count", 0)),
            ),
            self.name,
        )
