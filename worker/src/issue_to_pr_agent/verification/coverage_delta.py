"""Coverage regression check: head coverage must not drop below base."""

from __future__ import annotations

from dataclasses import dataclass

from .coverage import Coverage

# Allow tiny float noise before flagging a regression.
DEFAULT_TOLERANCE = 0.01


@dataclass(slots=True)
class CoverageDelta:
    base: float
    head: float
    delta: float
    regressed: bool


def coverage_delta(
    base: Coverage, head: Coverage, tolerance: float = DEFAULT_TOLERANCE
) -> CoverageDelta:
    delta = round(head.percent - base.percent, 4)
    return CoverageDelta(
        base=base.percent,
        head=head.percent,
        delta=delta,
        regressed=delta < -tolerance,
    )
