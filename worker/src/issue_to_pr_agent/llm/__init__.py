"""LLM layer: providers, router, rate limiting, metering, response parsing."""

from __future__ import annotations

from ..config import WorkerConfig
from .client import LLMClient
from .cost_meter import CostMeter
from .provider_base import (
    Completion,
    Message,
    Provider,
    ProviderError,
    RateLimitError,
    TokenUsage,
)
from .providers import (
    GeminiProvider,
    GroqProvider,
    MockProvider,
    NvidiaNimProvider,
    OllamaProvider,
)
from .rate_limiter import ProviderLimits, RateLimiter, load_provider_limits
from .response_parser import extract_code_blocks, extract_json
from .router import Router
from .token_meter import TokenMeter


def build_providers(config: WorkerConfig) -> list[Provider]:
    """Construct providers in config order; skip remotes with no key. Mock always works."""
    providers: list[Provider] = []
    for name in config.provider_order:
        if name == "mock":
            providers.append(MockProvider())
        elif name == "nvidia_nim" and config.nvidia_nim_api_key:
            providers.append(
                NvidiaNimProvider(
                    config.nvidia_nim_api_key,
                    model=config.nvidia_nim_model,
                )
            )
        elif name == "gemini" and config.gemini_api_key:
            providers.append(GeminiProvider(config.gemini_api_key))
        elif name == "groq" and config.groq_api_key:
            providers.append(GroqProvider(config.groq_api_key))
        elif name == "ollama":
            providers.append(OllamaProvider(host=config.ollama_host))
    if not providers:
        providers.append(MockProvider())
    return providers


def build_client(
    config: WorkerConfig, limits: dict[str, ProviderLimits] | None = None
) -> LLMClient:
    rl = RateLimiter(limits) if limits else None
    return LLMClient(Router(build_providers(config), rl))


__all__ = [
    "LLMClient",
    "CostMeter",
    "TokenMeter",
    "Completion",
    "Message",
    "Provider",
    "ProviderError",
    "RateLimitError",
    "TokenUsage",
    "MockProvider",
    "NvidiaNimProvider",
    "GroqProvider",
    "GeminiProvider",
    "OllamaProvider",
    "ProviderLimits",
    "RateLimiter",
    "load_provider_limits",
    "Router",
    "extract_code_blocks",
    "extract_json",
    "build_providers",
    "build_client",
]
