#!/usr/bin/env bash
set -euo pipefail

# Entry point for the worker container. The job is passed via the ITPR_JOB env
# var by the dispatcher's docker runner.
exec python -m issue_to_pr_agent.main "$@"
