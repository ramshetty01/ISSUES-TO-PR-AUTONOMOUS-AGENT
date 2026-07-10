#!/usr/bin/env bash
#
# run-local-worker.sh — run one job through the worker container locally, exactly
# the way the dispatcher would. Pass a job JSON file (see examples/run-summary or
# the dispatcher's job normalizer) as $1, or set ITPR_JOB directly.
#
#   ./scripts/run-local-worker.sh path/to/job.json
#
# Uses the itpr-worker:local image (build it with scripts/build-worker-image.sh).
# See docs/sandbox-design.md for the container's isolation model.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${WORKER_IMAGE_TAG:-itpr-worker:local}"
ENV_FILE="${ROOT_DIR}/.env"
JOB_FILE="${1:-}"

if ! docker image inspect "${IMAGE_TAG}" >/dev/null 2>&1; then
  echo "==> ${IMAGE_TAG} not found; building it first."
  "${ROOT_DIR}/scripts/build-worker-image.sh"
fi

if [[ -n "${JOB_FILE}" ]]; then
  [[ -f "${JOB_FILE}" ]] || { echo "!! job file not found: ${JOB_FILE}" >&2; exit 1; }
  ITPR_JOB="$(cat "${JOB_FILE}")"
fi
: "${ITPR_JOB:?Provide a job JSON file as \$1 or set ITPR_JOB}"

ENV_ARGS=()
[[ -f "${ENV_FILE}" ]] && ENV_ARGS+=(--env-file "${ENV_FILE}")

echo "==> Running one job in ${IMAGE_TAG}"
# --network host so the container can reach LocalStack / Ollama on the host.
# The worker writes only inside its /workspace jail (see path_jail.py).
exec docker run --rm \
  "${ENV_ARGS[@]}" \
  --env "ITPR_JOB=${ITPR_JOB}" \
  --network host \
  --memory "${WORKER_MEM:-2g}" \
  --cpus "${WORKER_CPUS:-2}" \
  "${IMAGE_TAG}"
