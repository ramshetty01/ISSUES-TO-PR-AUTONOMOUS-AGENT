#!/usr/bin/env python3
"""Compare free providers on a subset of seeded issues (design-level ablation).

For the zero-token smoke path every provider is simulated through the mock
solver, so the harness runs offline; against real keys each ``--provider`` would
route to that provider. Writes eval/results/model-ablation.json.

    python3 eval/runners/run_model_ablation.py --providers mock,gemini,ollama --subset smoke
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from run_internal_eval import _select, aggregate  # noqa: E402
from run_single_issue import run_one  # noqa: E402

OUT = ROOT / "results" / "model-ablation.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Model ablation across free providers.")
    ap.add_argument("--providers", default="mock,gemini,ollama")
    ap.add_argument("--subset", choices=["smoke", "full"], default="smoke")
    args = ap.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    issues = _select(args.subset)
    table = {}
    for provider in providers:
        results = [run_one(i["id"], provider) for i in issues]
        table[provider] = aggregate(results)
        print(f"  {provider}: pass={table[provider]['passRate'] * 100:.0f}% "
              f"ux={table[provider]['avgOperatorUxScore']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"subset": args.subset, "providers": providers, "byProvider": table}, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
