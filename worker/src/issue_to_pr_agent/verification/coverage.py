"""Normalized coverage summary."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Coverage:
    percent: float  # 0..100
    covered_lines: int = 0
    total_lines: int = 0
    per_file: dict[str, float] = field(default_factory=dict)
