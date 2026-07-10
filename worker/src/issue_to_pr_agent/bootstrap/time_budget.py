"""Wall-clock time budget: a hard deadline with soft checkpoints."""

from __future__ import annotations

import time
from collections.abc import Callable


class TimeBudget:
    """Tracks a run's wall-clock budget. `clock` is injectable for tests."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._deadline = clock() + seconds
        self._total = seconds

    def remaining(self) -> float:
        """Seconds left (may be negative once expired)."""
        return self._deadline - self._clock()

    def expired(self) -> bool:
        return self.remaining() <= 0

    def fraction_used(self) -> float:
        used = self._total - self.remaining()
        return max(0.0, min(1.0, used / self._total)) if self._total > 0 else 1.0

    def checkpoint(self, label: str = "") -> float:
        """Return remaining seconds; callers stop work when this trends to 0."""
        return self.remaining()
