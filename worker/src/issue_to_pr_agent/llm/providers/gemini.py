"""Google Gemini provider (AI Studio free tier)."""

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


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: Transport = default_transport,
    ) -> None:
        self._key = api_key
        self._model = model
        self._base = base_url.rstrip("/")
        self._transport = transport

    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion:
        # Gemini has no system role: fold system messages into the first user turn.
        contents = [
            {
                "role": "user" if m.role != "assistant" else "model",
                "parts": [{"text": m.content}],
            }
            for m in messages
        ]
        url = f"{self._base}/models/{self._model}:generateContent?key={self._key}"
        status, data = post_json(
            self._transport,
            url,
            {},
            {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                },
            },
        )
        if status == 429:
            raise RateLimitError("gemini rate limited")
        if status // 100 != 2 or not data:
            raise ProviderError(f"gemini error ({status})")
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        meta = data.get("usageMetadata", {})
        return Completion(
            text,
            TokenUsage(
                input=int(meta.get("promptTokenCount", 0)),
                output=int(meta.get("candidatesTokenCount", 0)),
            ),
            self.name,
        )
