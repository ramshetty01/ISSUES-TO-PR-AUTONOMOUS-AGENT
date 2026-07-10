#!/usr/bin/env bash
#
# build-worker-image.sh — build the Python worker container the dispatcher runs
# per job. Tags it itpr-worker:local so run-local-worker.sh and the dispatcher's
# docker runner can find it. See worker/Dockerfile and docs/sandbox-design.md.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${WORKER_IMAGE_TAG:-itpr-worker:local}"

if ! command -v docker >/dev/null 2>&1; then
  echo "!! docker is not installed or not on PATH." >&2
  exit 1
fi

echo "==> Building worker image: ${IMAGE_TAG}"
docker build \
  -t "${IMAGE_TAG}" \
  -f "${ROOT_DIR}/worker/Dockerfile" \
  "${ROOT_DIR}/worker"

echo "==> Built ${IMAGE_TAG}"
docker image inspect "${IMAGE_TAG}" --format '    id={{.Id}} size={{.Size}}' || true
