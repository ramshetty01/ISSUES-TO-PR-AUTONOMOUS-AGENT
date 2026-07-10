"""LLM providers: free-tier remotes + a deterministic mock."""

from .mock import MockProvider
from .nvidia_nim import NvidiaNimProvider, OpenAICompatProvider
from .groq import GroqProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider

__all__ = [
    "MockProvider",
    "NvidiaNimProvider",
    "OpenAICompatProvider",
    "GroqProvider",
    "GeminiProvider",
    "OllamaProvider",
]
