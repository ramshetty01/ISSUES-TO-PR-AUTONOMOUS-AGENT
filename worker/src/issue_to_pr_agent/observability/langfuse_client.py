"""Client for the self-hosted Langfuse instance at ``LANGFUSE_HOST``.

Dependency-free: a trace exported by ``Tracer`` is shaped into a Langfuse
ingestion batch and POSTed via an injectable transport (default: stdlib
urllib). Without credentials the client is disabled and ingestion is a no-op,
so a run never fails because tracing is unconfigured.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from ..config import WorkerConfig

# transport(url, body_bytes, headers) -> HTTP status code
Transport = Callable[[str, bytes, dict[str, str]], int]


def _urllib_transport(url: str, body: bytes, headers: dict[str, str]) -> int:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 - fixed host
            return int(resp.status)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network path
        return int(exc.code)


class LangfuseClient:
    """Ships traces to self-hosted Langfuse and builds trace deep-links."""

    def __init__(
        self,
        host: str,
        *,
        public_key: str | None = None,
        secret_key: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self._public_key = public_key
        self._secret_key = secret_key
        self._transport = transport or _urllib_transport

    @classmethod
    def from_config(cls, config: WorkerConfig, *, transport: Transport | None = None) -> "LangfuseClient":
        return cls(
            config.langfuse_host,
            public_key=getattr(config, "langfuse_public_key", None),
            secret_key=getattr(config, "langfuse_secret_key", None),
            transport=transport,
        )

    @property
    def enabled(self) -> bool:
        """Ingestion is attempted only when a transport override or keys exist."""
        return bool(self._public_key and self._secret_key) or self._transport is not _urllib_transport

    def trace_url(self, trace_id: str) -> str:
        """Deep-link into the Langfuse UI for a trace (goes into RunSummary)."""
        return f"{self.host}/trace/{trace_id}"

    def build_batch(self, trace: dict[str, Any]) -> dict[str, Any]:
        """Shape an exported trace into a Langfuse ingestion batch."""
        events: list[dict[str, Any]] = [
            {
                "type": "trace-create",
                "id": trace["traceId"],
                "body": {"id": trace["traceId"], "name": trace.get("name", "run")},
            }
        ]
        for span in trace.get("spans", []):
            events.append(
                {
                    "type": "observation-create",
                    "id": span["spanId"],
                    "body": {
                        "id": span["spanId"],
                        "traceId": trace["traceId"],
                        "parentObservationId": span.get("parentId"),
                        "type": "SPAN",
                        "name": span["name"],
                        "startTime": span.get("startedAt"),
                        "endTime": span.get("endedAt"),
                        "metadata": span.get("attributes", {}),
                    },
                }
            )
        return {"batch": events}

    def ingest(self, trace: dict[str, Any]) -> bool:
        """POST the trace to Langfuse; return whether it was accepted."""
        if not self.enabled:
            return False
        body = json.dumps(self.build_batch(trace)).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._public_key and self._secret_key:
            import base64

            token = base64.b64encode(f"{self._public_key}:{self._secret_key}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        status = self._transport(f"{self.host}/api/public/ingestion", body, headers)
        return 200 <= status < 300
