"""Phase 28 PR-authoring tests: body generation, diff summary, labels, title,
trace link, open_pr base/head, and reviewer comments. Secret fixtures are
assembled from fragments so no full literal appears in source."""

from __future__ import annotations

import pytest

from issue_to_pr_agent.github.client import GitHubClient
from issue_to_pr_agent.job import Repo
from issue_to_pr_agent.pr import (
    PRBodyInput,
    ReviewComment,
    apply_outcome_labels,
    build_review,
    generate_body,
    generate_title,
    open_pr,
    outcome_labels,
    post_review,
    summarize_diff,
    trace_url,
)

_j = lambda *p: "".join(p)  # noqa: E731
GH_TOKEN = _j("ghp", "_", "0123456789abcdefghijklmnopqrstuvwxyz")

_DIFF = """diff --git a/src/parser.py b/src/parser.py
--- a/src/parser.py
+++ b/src/parser.py
@@ -1,3 +1,4 @@
-def parse(x):
-    return x.value
+def parse(x):
+    if x is None:
+        return None
+    return x.value
diff --git a/tests/test_parser.py b/tests/test_parser.py
new file mode 100644
--- /dev/null
+++ b/tests/test_parser.py
@@ -0,0 +1,2 @@
+def test_none():
+    assert parse(None) is None
"""


def _repo() -> Repo:
    return Repo(owner="acme", name="widgets")


def _fake_client(recorder: dict, *, default_branch: str = "main") -> GitHubClient:
    def transport(method, url, headers, body):
        import json

        recorder["calls"].append((method, url, json.loads(body) if body else None))
        if method == "GET":  # get_default_branch
            return 200, {"default_branch": default_branch}
        return 201, {"number": 12, "html_url": "https://github.com/acme/widgets/pull/12"}

    return GitHubClient("tok", transport=transport)


# --- diff summary ----------------------------------------------------------


def test_summarize_diff_counts_and_status() -> None:
    summary = summarize_diff(_DIFF)
    by_path = {f.path: f for f in summary.files}
    assert set(by_path) == {"src/parser.py", "tests/test_parser.py"}
    assert by_path["tests/test_parser.py"].status == "added"
    assert by_path["src/parser.py"].added == 4
    assert by_path["src/parser.py"].removed == 2
    assert summary.total_added == 6


# --- body generator (the phase's headline verification) --------------------


def test_body_includes_summary_rationale_and_trace() -> None:
    body = generate_body(
        PRBodyInput(
            issue_number=7,
            issue_title="parser crashes on None input",
            plan="Guard parse() against None before dereferencing.",
            diff=_DIFF,
            trace_id="run-3f2a",
            langfuse_host="http://localhost:3000",
            verification="pytest: 12 passed",
            coverage_delta="+1.2%",
        )
    )
    # Summary (What) + Changes
    assert "## What" in body and "## Changes" in body
    assert "`src/parser.py`" in body
    # Rationale (Why) tied to the issue
    assert "Closes #7" in body
    assert "parser crashes on None input" in body
    # Verification + coverage
    assert "pytest: 12 passed" in body
    assert "+1.2%" in body
    # Trace link to self-hosted Langfuse
    assert "http://localhost:3000/trace/run-3f2a" in body


def test_body_has_no_secrets() -> None:
    body = generate_body(
        PRBodyInput(
            issue_number=7,
            issue_title="fix auth",
            plan=f"Rotate the leaked token {GH_TOKEN} in config.",
            diff=f"diff --git a/c.py b/c.py\n+TOKEN = {GH_TOKEN}\n",
            trace_id="run-1",
        )
    )
    assert GH_TOKEN not in body
    assert "[REDACTED:github_token]" in body


# --- title -----------------------------------------------------------------


def test_generate_title_template_and_length() -> None:
    title = generate_title(issue_title="parser crashes on None input", issue_number=7)
    assert title.startswith("Fix:")
    assert title.endswith("(#7)")
    assert len(title) <= 72


# --- labels ----------------------------------------------------------------


def test_outcome_labels_by_state() -> None:
    assert outcome_labels("succeeded") == ["agent", "automated-pr"]
    assert "safety-refused" in outcome_labels("refused")
    assert outcome_labels("succeeded", extra=["python"]) == ["agent", "automated-pr", "python"]


def test_apply_outcome_labels_calls_github() -> None:
    rec: dict = {"calls": []}
    client = _fake_client(rec)
    labels = apply_outcome_labels(client, _repo(), 12, "succeeded")
    assert labels == ["agent", "automated-pr"]
    method, url, body = rec["calls"][-1]
    assert method == "POST" and url.endswith("/issues/12/labels")
    assert body == {"labels": ["agent", "automated-pr"]}


# --- trace link ------------------------------------------------------------


def test_trace_url_matches_langfuse_shape() -> None:
    assert trace_url("http://localhost:3000/", "run-1") == "http://localhost:3000/trace/run-1"


# --- open_pr ---------------------------------------------------------------


def test_open_pr_uses_default_base_and_given_head() -> None:
    rec: dict = {"calls": []}
    client = _fake_client(rec, default_branch="main")
    opened = open_pr(
        client, _repo(), title="Fix: parser (#7)", head="agent/run-3f2a", body="body"
    )
    assert opened.base == "main" and opened.head == "agent/run-3f2a"
    assert opened.number == 12
    assert opened.url.endswith("/pull/12")
    post = [c for c in rec["calls"] if c[0] == "POST"][-1]
    method, url, sent = post
    assert url.endswith("/pulls")
    assert sent["base"] == "main" and sent["head"] == "agent/run-3f2a"


def test_open_pr_rejects_same_head_and_base() -> None:
    rec: dict = {"calls": []}
    client = _fake_client(rec, default_branch="main")
    with pytest.raises(ValueError):
        open_pr(client, _repo(), title="t", head="main", body="b")


# --- reviewer comments -----------------------------------------------------


def test_build_review_scrubs_inline_comments() -> None:
    review = build_review(
        [ReviewComment(path="c.py", line=3, body=f"leaked {GH_TOKEN}")],
        body="Please double-check the guard.",
    )
    assert review["event"] == "COMMENT"
    assert review["comments"][0]["line"] == 3
    assert GH_TOKEN not in review["comments"][0]["body"]


def test_post_review_calls_github() -> None:
    rec: dict = {"calls": []}
    client = _fake_client(rec)
    post_review(client, _repo(), 12, [ReviewComment(path="c.py", line=1, body="note")])
    method, url, body = rec["calls"][-1]
    assert method == "POST" and url.endswith("/pulls/12/reviews")
    assert body["comments"][0]["path"] == "c.py"


def test_post_review_noop_when_empty() -> None:
    rec: dict = {"calls": []}
    client = _fake_client(rec)
    assert post_review(client, _repo(), 12, []) == {}
    assert rec["calls"] == []
