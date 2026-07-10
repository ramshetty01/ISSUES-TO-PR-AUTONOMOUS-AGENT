"""Accumulate token usage across a run."""

from __future__ import annotations

from .provider_base import TokenUsage


class TokenMeter:
    def __init__(self) -> None:
        self._input = 0
        self._output = 0

    def record(self, usage: TokenUsage) -> None:
        self._input += usage.input
        self._output += usage.output

    @property
    def input(self) -> int:
        return self._input

    @property
    def output(self) -> int:
        return self._output

    @property
    def total(self) -> int:
        return self._input + self._output
