"""Phase 29 observability tests: tracing, event log, cost/run summaries,
redacted artifacts, and Langfuse ingestion. Secret fixtures are assembled from
fragments so no full secret literal appears in source."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from issue_to_pr_agent.job import Job
from issue_to_pr_agent.llm.cost_meter import CostMeter
from issue_to_pr_agent.llm.provider_base import TokenUsage
from issue_to_pr_agent.llm.token_meter import TokenMeter
from issue_to_pr_agent.observability import (
    ArtifactWriter,
    CostReport,
    EventLog,
    LangfuseClient,
    RunSummary,
    Tracer,
    build_redacted_archive,
    build_run_summary,
    read_members,
    verify_no_secrets,
)

_j = lambda *p: "".join(p)  # noqa: E731
GH_TOKEN = _j("ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz")


def _clock():
    """Deterministic monotonic ISO-ish clock for reproducible spans/events."""
    ticks = iter(range(1000))
    return lambda: f"2026-01-01T00:00:{next(ticks):02d}+00:00"


def _job() -> Job:
    return Job.model_validate(
        {
            "id": "job-1",
            "repo": {"owner": "acme", "name": "widgets"},
            "installationId": 42,
            "trigger": "issue_labeled",
            "issueNumber": 7,
        }
    )


# --- trace -----------------------------------------------------------------


def test_tracer_nests_spans_and_exports() -> None:
    tracer = Tracer("run-9", clock=_clock())
    with tracer.span("plan") as root:
        with tracer.span("edit", parent=root, file="a.py"):
            pass
    out = tracer.export()
    assert out["traceId"] == "run-9"
    assert [s["name"] for s in out["spans"]] == ["plan", "edit"]
    edit = out["spans"][1]
    assert edit["parentId"] == out["spans"][0]["spanId"]
    assert edit["attributes"]["file"] == "a.py"
    assert all(s["endedAt"] is not None for s in out["spans"])


def test_tracer_records_error_on_exception() -> None:
    tracer = Tracer("run-e", clock=_clock())
    with pytest.raises(ValueError):
        with tracer.span("boom"):
            raise ValueError("nope")
    assert tracer.spans[0].attributes["error"] == "ValueError"
    assert tracer.spans[0].ended_at is not None


# --- event log -------------------------------------------------------------


def test_event_log_builds_timeline() -> None:
    log = EventLog(clock=_clock())
    log.record("plan", "planned")
    log.record("pr_opened", "opened", {"url": "http://x/pr/1"})
    timeline = log.to_timeline()
    assert timeline[0] == {"at": "2026-01-01T00:00:00+00:00", "kind": "plan", "message": "planned"}
    assert timeline[1]["data"] == {"url": "http://x/pr/1"}


# --- cost report -----------------------------------------------------------


def test_cost_report_reconciles_with_meters() -> None:
    report = CostReport()
    tm, cm = TokenMeter(), CostMeter()
    for provider, usage in [("mock", TokenUsage(100, 40)), ("mock", TokenUsage(10, 5))]:
        report.record(provider, usage)
        tm.record(usage)
        cm.record(provider, usage.total)
    assert report.usage == {"input": 110, "output": 45, "total": 155}
    assert report.reconciles_with(tm, cm)
    assert report.to_dict()["byProvider"]["mock"]["total"] == 155


def test_cost_report_detects_drift() -> None:
    report = CostReport()
    report.record("mock", TokenUsage(100, 40))
    tm = TokenMeter()
    tm.record(TokenUsage(1, 1))
    assert not report.reconciles_with(tm)


def test_cost_report_imputes_dollars() -> None:
    report = CostReport(prices={"paid": 2.0})
    report.record("paid", TokenUsage(500, 500))  # 1000 tokens * $2/1k = $2
    assert report.dollars == pytest.approx(2.0)


# --- run summary -----------------------------------------------------------


def test_run_summary_matches_shared_types_keys() -> None:
    summary = build_run_summary(
        run_id="run-1",
        job=_job(),
        state="succeeded",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
        usage={"input": 110, "output": 45, "total": 155},
        dollars=0.0,
        pr_url="https://github.com/acme/widgets/pull/12",
        trace_url="http://localhost:3000/trace/run-1",
    )
    d = summary.to_dict()
    assert set(d) >= {"runId", "job", "state", "timeline", "usage", "dollars", "safetyEvents", "startedAt"}
    assert d["job"]["installationId"] == 42  # camelCase serialisation
    assert d["prUrl"].endswith("/pull/12")
    assert d["finishedAt"] == "2026-01-01T00:01:00+00:00"


def test_run_summary_refused_carries_refusal() -> None:
    summary = build_run_summary(
        run_id="run-2",
        job=_job(),
        state="refused",
        started_at="2026-01-01T00:00:00+00:00",
        refusal={"reason": "forbidden_path", "message": "blocked"},
    )
    assert summary.to_dict()["refusal"]["reason"] == "forbidden_path"


def test_run_summary_rejects_unknown_state() -> None:
    with pytest.raises(ValueError):
        RunSummary(run_id="x", job=_job(), state="exploded", started_at="t")


# --- langfuse client -------------------------------------------------------


def test_langfuse_trace_url() -> None:
    client = LangfuseClient("http://localhost:3000/")
    assert client.trace_url("run-1") == "http://localhost:3000/trace/run-1"


def test_langfuse_ingest_posts_batch() -> None:
    sent: list[tuple[str, bytes]] = []

    def transport(url, body, headers):
        sent.append((url, body))
        return 207

    client = LangfuseClient("http://lf", transport=transport)
    tracer = Tracer("run-1", clock=_clock())
    with tracer.span("plan"):
        pass
    assert client.ingest(tracer.export()) is True
    url, body = sent[0]
    assert url == "http://lf/api/public/ingestion"
    batch = json.loads(body)["batch"]
    assert batch[0]["type"] == "trace-create"
    assert any(e["type"] == "observation-create" for e in batch)


def test_langfuse_disabled_without_keys() -> None:
    client = LangfuseClient("http://lf")  # default transport, no keys
    assert client.enabled is False
    assert client.ingest({"traceId": "x", "spans": []}) is False


# --- artifact writer & redacted archive ------------------------------------


def test_artifact_writer_redacts(tmp_path: Path) -> None:
    writer = ArtifactWriter(tmp_path / "run-1")
    path = writer.write_json("summary.json", {"token": GH_TOKEN, "ok": True})
    written = json.loads(path.read_text())
    assert GH_TOKEN not in path.read_text()
    assert written["token"] == "[REDACTED:github_token]"
    assert written["ok"] is True


_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_run_summary_example_matches_schema() -> None:
    data = json.loads((_EXAMPLES / "run-summary.example.json").read_text())
    assert set(data) >= {
        "runId", "job", "state", "timeline", "usage", "dollars", "safetyEvents", "startedAt"
    }
    assert data["state"] in {"queued", "dispatched", "running", "succeeded", "failed", "refused"}
    assert set(data["usage"]) == {"input", "output", "total"}
    assert all({"at", "kind", "message"} <= set(ev) for ev in data["timeline"])


def test_trace_example_is_well_formed() -> None:
    data = json.loads((_EXAMPLES / "trace.example.json").read_text())
    assert data["traceId"] and isinstance(data["spans"], list)
    ids = {s["spanId"] for s in data["spans"]}
    for span in data["spans"]:
        assert {"spanId", "name", "startedAt", "endedAt", "attributes"} <= set(span)
        assert span["parentId"] is None or span["parentId"] in ids


def test_redacted_archive_has_no_secrets(tmp_path: Path) -> None:
    dest = tmp_path / "run-1.tar.gz"
    build_redacted_archive(
        dest,
        {
            "summary.json": {"state": "succeeded", "leak": GH_TOKEN},
            "log.txt": f"authorized with {GH_TOKEN}",
        },
    )
    assert verify_no_secrets(dest) is True
    members = read_members(dest)
    assert GH_TOKEN not in members["summary.json"]
    assert GH_TOKEN not in members["log.txt"]
