#!/usr/bin/env python3
"""Run one seeded issue through a (mock or real) provider and score it.

The ``mock`` provider is a deterministic, zero-token simulation of the agent's
output — enough to exercise the whole harness (solve -> diff -> PR body -> run
summary -> metrics) without spending tokens. Stdlib only, so it runs with a
bare ``python3``.

    python3 eval/runners/run_single_issue.py --provider mock --issue issue-001-null-input
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # eval/
sys.path.insert(0, str(ROOT))

from metrics.coverage_delta import coverage_delta  # noqa: E402
from metrics.cost_latency import cost_latency  # noqa: E402
from metrics.diff_size import diff_size  # noqa: E402
from metrics.operator_ux_score import operator_ux_score  # noqa: E402
from metrics.pr_quality import pr_quality  # noqa: E402
from metrics.safety_score import safety_score  # noqa: E402
from metrics.style_conformance import style_conformance  # noqa: E402

MANIFEST = ROOT / "seeded-issues" / "issues.json"


def load_issues() -> list[dict]:
    return json.loads(MANIFEST.read_text())["issues"]


def find_issue(issue_id: str) -> dict:
    for issue in load_issues():
        if issue["id"] == issue_id:
            return issue
    raise SystemExit(f"unknown issue: {issue_id}")


def _synthetic_diff(issue: dict) -> str:
    stack = issue["stack"]
    return (
        f"diff --git a/src/{stack}/fix.py b/src/{stack}/fix.py\n"
        "--- a/src/fix.py\n+++ b/src/fix.py\n"
        "@@ -1,2 +1,4 @@\n"
        "-def handle(x):\n-    return x.value\n"
        "+def handle(x):\n+    if x is None:\n+        return None\n+    return x.value\n"
        f"diff --git a/tests/test_{stack}.py b/tests/test_{stack}.py\n"
        "new file mode 100644\n--- /dev/null\n+++ b/tests/test_fix.py\n"
        "@@ -0,0 +1,2 @@\n+def test_none():\n+    assert handle(None) is None\n"
    )


def _pr_body(issue: dict) -> str:
    return (
        f"## What\nFix: {issue['title']}\n\n"
        f"## Why\nCloses #{issue['number']} — {issue['title']}.\n\n"
        "## Changes\n- `src/fix.py` (guard added)\n- `tests/test_fix.py` (regression test)\n\n"
        "## Verification\npytest: 1 passed. Coverage +0.8%.\n\n"
        f"## Trace\n[Langfuse trace](http://localhost:3000/trace/{issue['id']})\n"
    )


def solve_issue(issue: dict, provider: str = "mock") -> dict:
    """Produce a deterministic synthetic run for the given issue."""
    refuse = issue.get("expect") == "refuse"
    if refuse:
        # The agent refuses to edit a forbidden path: no PR, a safety refusal.
        run_summary = {
            "runId": issue["id"],
            "state": "refused",
            "traceUrl": f"http://localhost:3000/trace/{issue['id']}",
            "timeline": [{"kind": "plan", "message": "planned"}, {"kind": "refuse", "message": "forbidden_path"}],
            "dollars": 0.0,
            "safetyEvents": [{"reason": "forbidden_path", "message": "edit to .github/workflows blocked"}],
        }
        return {
            "id": issue["id"], "stack": issue["stack"], "provider": provider,
            "expect": "refuse", "refused": True, "passed": True,
            "diff": "", "prBody": "", "runSummary": run_summary,
        }
    diff, body = _synthetic_diff(issue), _pr_body(issue)
    run_summary = {
        "runId": issue["id"], "state": "succeeded",
        "traceUrl": f"http://localhost:3000/trace/{issue['id']}",
        "timeline": [{"kind": "plan"}, {"kind": "edit"}, {"kind": "test"}, {"kind": "pr_opened"}],
        "prUrl": f"https://github.com/itpr-fixtures/{issue['stack']}/pull/{issue['number']}",
        "dollars": 0.0, "safetyEvents": [],
    }
    return {
        "id": issue["id"], "stack": issue["stack"], "provider": provider,
        "expect": "pr", "refused": False, "passed": True,
        "diff": diff, "prBody": body, "runSummary": run_summary,
    }


def score_issue(run: dict) -> dict:
    diff, body, rs = run["diff"], run["prBody"], run["runSummary"]
    wall_ms = 1200 + 100 * len(run["id"])  # deterministic pseudo-latency
    expected_refuse = run["expect"] == "refuse"
    metrics = {
        "prQuality": pr_quality(body) if not expected_refuse else 1.0,
        "diffSize": diff_size(diff),
        "styleConformance": style_conformance(diff),
        "coverageDelta": coverage_delta(80.0, 80.8) if not expected_refuse else 0.0,
        "costLatency": cost_latency(0, 0, wall_ms, dollars=rs.get("dollars", 0.0)),
        "safetyScore": safety_score(
            rs.get("safetyEvents", []), refused=run["refused"], expected_refuse=expected_refuse
        ),
        "operatorUxScore": operator_ux_score(rs),
    }
    return {**{k: run[k] for k in ("id", "stack", "provider", "expect", "refused", "passed")}, "metrics": metrics}


def run_one(issue_id: str, provider: str = "mock") -> dict:
    return score_issue(solve_issue(find_issue(issue_id), provider))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a single seeded eval issue.")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--provider", default="mock")
    ap.add_argument("--json", action="store_true", help="print full result JSON")
    args = ap.parse_args()
    result = run_one(args.issue, args.provider)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        m = result["metrics"]
        print(f"{result['id']} [{result['provider']}] passed={result['passed']} "
              f"prQuality={m['prQuality']} safety={m['safetyScore']} ux={m['operatorUxScore']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
