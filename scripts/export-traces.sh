#!/usr/bin/env bash
#
# export-traces.sh — pull run trace archives out of the S3 artifacts bucket
# (LocalStack in dev) into a local directory, then scrub them of secrets/PII so
# they are safe to share or attach to an eval report.
#
#   ./scripts/export-traces.sh [OUTPUT_DIR]
#
# Requires the AWS CLI. Endpoint + bucket come from .env (LocalStack defaults).
# Scrubbing is delegated to scripts/scrub-trace-archives.py (stdlib only).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
OUT_DIR="${1:-${ROOT_DIR}/traces-export}"

# Load AWS_* / S3_ARTIFACTS_BUCKET from .env if present (without leaking to caller).
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^[A-Z_]+=.*' "${ENV_FILE}" || true)
  set +a
fi

ENDPOINT="${AWS_ENDPOINT_URL:-http://localhost:4566}"
BUCKET="${S3_ARTIFACTS_BUCKET:-itpr-artifacts}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_REGION="${AWS_REGION:-us-east-1}"

if ! command -v aws >/dev/null 2>&1; then
  echo "!! aws CLI not found. Install it or export traces manually." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
echo "==> Syncing s3://${BUCKET}/traces -> ${OUT_DIR} (endpoint ${ENDPOINT})"
aws --endpoint-url "${ENDPOINT}" s3 sync "s3://${BUCKET}/traces" "${OUT_DIR}" || {
  echo "!! sync failed (is LocalStack up and the bucket seeded?)" >&2
  exit 1
}

echo "==> Scrubbing exported archives in place"
python3 "${ROOT_DIR}/scripts/scrub-trace-archives.py" --pii --in-place "${OUT_DIR}"

echo "==> Done. Scrubbed traces in ${OUT_DIR}"
