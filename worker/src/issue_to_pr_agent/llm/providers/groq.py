"""Groq provider (OpenAI-compatible; fast, good for planner steps)."""

from __future__ import annotations

from ..provider_base import Transport, default_transport
from .nvidia_nim import OpenAICompatProvider


class GroqProvider(OpenAICompatProvider):
    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        transport: Transport = default_transport,
    ) -> None:
        super().__init__(api_key, base_url, model, transport)
