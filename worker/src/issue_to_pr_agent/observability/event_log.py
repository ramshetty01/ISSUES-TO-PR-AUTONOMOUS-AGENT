"""Append-only timeline of run events.

Mirrors ``TimelineEvent`` in packages/shared-types/src/run.ts. The list this
produces is what ``run_summary`` embeds as ``timeline``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .trace import Clock, utc_now_iso


@dataclass(slots=True)
class TimelineEvent:
    """One machine-readable event on the run timeline."""

    at: str
    kind: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"at": self.at, "kind": self.kind, "message": self.message}
        if self.data:
            out["data"] = self.data
        return out


class EventLog:
    """Records timeline events in order, stamping each with the clock."""

    def __init__(self, *, clock: Clock = utc_now_iso) -> None:
        self._clock = clock
        self._events: list[TimelineEvent] = []

    def record(self, kind: str, message: str, data: dict[str, Any] | None = None) -> TimelineEvent:
        event = TimelineEvent(at=self._clock(), kind=kind, message=message, data=dict(data or {}))
        self._events.append(event)
        return event

    @property
    def events(self) -> list[TimelineEvent]:
        return list(self._events)

    def to_timeline(self) -> list[dict[str, Any]]:
        """Serialise to the camelCase list embedded in a run summary."""
        return [e.to_dict() for e in self._events]
