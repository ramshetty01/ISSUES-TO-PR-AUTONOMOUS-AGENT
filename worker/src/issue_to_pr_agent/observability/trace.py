"""Lightweight span/trace model emitted across a run.

A ``Tracer`` collects nested ``Span`` objects into a single trace keyed by the
run id. The exported payload feeds ``langfuse_client`` (self-hosted ingestion)
and mirrors ``examples/trace.example.json``. The clock is injectable so runs are
deterministic under test.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterator

Clock = Callable[[], str]


def utc_now_iso() -> str:
    """ISO-8601 UTC timestamp; the default trace/event clock."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Span:
    """A single timed unit of work, optionally nested under a parent span."""

    name: str
    span_id: str
    started_at: str
    parent_id: str | None = None
    ended_at: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spanId": self.span_id,
            "parentId": self.parent_id,
            "name": self.name,
            "startedAt": self.started_at,
            "endedAt": self.ended_at,
            "attributes": self.attributes,
        }


class Tracer:
    """Collects spans for one run into a trace payload."""

    def __init__(self, run_id: str, *, name: str = "run", clock: Clock = utc_now_iso) -> None:
        self.trace_id = run_id
        self.name = name
        self._clock = clock
        self._spans: list[Span] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"{self.trace_id}-{self._counter:04d}"

    def start_span(self, name: str, *, parent: Span | None = None, **attributes: Any) -> Span:
        span = Span(
            name=name,
            span_id=self._next_id(),
            started_at=self._clock(),
            parent_id=parent.span_id if parent else None,
            attributes=dict(attributes),
        )
        self._spans.append(span)
        return span

    def end_span(self, span: Span, **attributes: Any) -> None:
        span.ended_at = self._clock()
        if attributes:
            span.attributes.update(attributes)

    @contextmanager
    def span(self, name: str, *, parent: Span | None = None, **attributes: Any) -> Iterator[Span]:
        """Open a span, closing it (even on error) when the block exits."""
        span = self.start_span(name, parent=parent, **attributes)
        try:
            yield span
        except Exception as exc:  # record the failure, then re-raise
            span.attributes.setdefault("error", type(exc).__name__)
            raise
        finally:
            self.end_span(span)

    @property
    def spans(self) -> list[Span]:
        return list(self._spans)

    def export(self) -> dict[str, Any]:
        """Serialise the whole trace (camelCase, JSON-ready)."""
        return {
            "traceId": self.trace_id,
            "name": self.name,
            "spans": [s.to_dict() for s in self._spans],
        }
