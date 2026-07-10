"""LLM provider interface + shared value types."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from ..errors import LLMError

# (method, url, headers, body_bytes) -> (status, parsed_json)
Transport = Callable[[str, str, dict[str, str], bytes | None], "tuple[int, Any]"]


def default_transport(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 - https provider APIs
            payload = resp.read()
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        return exc.code, (json.loads(payload) if payload else None)


def post_json(
    transport: Transport, url: str, headers: dict[str, str], body: dict[str, Any]
) -> tuple[int, Any]:
    data = json.dumps(body).encode()
    hdrs = {"Content-Type": "application/json", **headers}
    return transport("POST", url, hdrs, data)


class ProviderError(LLMError):
    """A provider call failed (network / 5xx / bad response)."""


class RateLimitError(LLMError):
    """A provider signalled rate limiting (429)."""


@dataclass(slots=True, frozen=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(slots=True, frozen=True)
class TokenUsage:
    input: int
    output: int

    @property
    def total(self) -> int:
        return self.input + self.output


@dataclass(slots=True, frozen=True)
class Completion:
    text: str
    usage: TokenUsage
    provider: str


class Provider(ABC):
    """A chat/completion backend. Capabilities are uniform across providers."""

    name: str

    @abstractmethod
    def complete(
        self, messages: list[Message], *, max_tokens: int = 1024, temperature: float = 0.2
    ) -> Completion: ...


def estimate_prompt_tokens(messages: list[Message]) -> int:
    """~4 chars/token estimate of the prompt size."""
    return sum(len(m.content) for m in messages) // 4
