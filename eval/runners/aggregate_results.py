#!/usr/bin/env python3
"""Merge the internal-eval + ablation result files into one aggregate report.

Writes eval/results/aggregate-results.json (machine) and refreshes the
final scorecard header. Safe to run after any runner.

    python3 eval/runners/aggregate_results.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _load(name: str) -> dict:
    path = RESULTS / name
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def main() -> int:
    internal = _load("internal-30-issues.json")
    ablation = _load("model-ablation.json")
    aggregate = {
        "internal": internal.get("summary", {}),
        "internalProvider": internal.get("provider"),
        "internalSubset": internal.get("subset"),
        "ablation": ablation.get("byProvider", {}),
    }
    out = RESULTS / "aggregate-results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(aggregate, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT.parent)}")
    summ = aggregate["internal"]
    if summ:
        print(f"internal pass rate: {summ.get('passRate', 0) * 100:.1f}% over {summ.get('count', 0)} issues")
    return 0 if summ else 1


if __name__ == "__main__":
    raise SystemExit(main())
