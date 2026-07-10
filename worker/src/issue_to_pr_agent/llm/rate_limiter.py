"""Per-provider rate limiting for free tiers (requests + tokens per minute)."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ProviderLimits:
    rpm: int  # requests per minute (0 = unlimited)
    tpm: int  # tokens per minute (0 = unlimited)


class RateLimiter:
    """Sliding 60s window per provider. `allow` checks, `record` commits usage."""

    def __init__(
        self, limits: dict[str, ProviderLimits], clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limits = limits
        self._clock = clock
        # provider -> deque of (timestamp, tokens)
        self._events: dict[str, deque[tuple[float, int]]] = {}

    def _evict(self, provider: str, now: float) -> None:
        dq = self._events.setdefault(provider, deque())
        while dq and now - dq[0][0] >= 60.0:
            dq.popleft()

    def allow(self, provider: str, est_tokens: int) -> bool:
        limits = self._limits.get(provider)
        if limits is None:
            return True
        now = self._clock()
        self._evict(provider, now)
        dq = self._events[provider]
        if limits.rpm and len(dq) >= limits.rpm:
            return False
        if limits.tpm and sum(t for _, t in dq) + est_tokens > limits.tpm:
            return False
        return True

    def record(self, provider: str, tokens: int) -> None:
        now = self._clock()
        self._evict(provider, now)
        self._events.setdefault(provider, deque()).append((now, tokens))


def load_provider_limits(path: str | Path) -> dict[str, ProviderLimits]:
    """Load per-provider RPM/TPM caps from a YAML policy file."""
    import yaml  # local import: only needed at load time

    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    providers = doc.get("providers", {})
    return {
        name: ProviderLimits(rpm=int(cfg.get("rpm", 0)), tpm=int(cfg.get("tpm", 0)))
        for name, cfg in providers.items()
    }
