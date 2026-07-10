#!/usr/bin/env sh
# ---------------------------------------------------------------------------
# Enqueue a single sample job onto itpr-jobs so the dispatcher has something
# to pick up on a fresh local stack. Optional + idempotent: it first checks
# for an existing sample marker and skips if one is already queued.
#
# Runs against LocalStack via `awslocal`. Intended to be invoked either on the
# host (with awslocal installed) or inside the localstack container via
# `docker compose exec`.
# ---------------------------------------------------------------------------
set -eu

REGION="us-east-1"
QUEUE_NAME="itpr-jobs"

QUEUE_URL="$(awslocal sqs get-queue-url --region "${REGION}" --queue-name "${QUEUE_NAME}" --output text --query 'QueueUrl')"

# Idempotency guard: if any message with our sample marker is already visible,
# do not enqueue a duplicate.
EXISTING="$(awslocal sqs receive-message \
  --region "${REGION}" \
  --queue-url "${QUEUE_URL}" \
  --visibility-timeout 0 \
  --max-number-of-messages 10 \
  --message-attribute-names All \
  --output text 2>/dev/null | grep -c 'itpr-sample-seed' || true)"

if [ "${EXISTING}" != "0" ]; then
  echo "[seed] sample job already present on ${QUEUE_NAME}; skipping"
  exit 0
fi

BODY='{"schemaVersion":1,"jobId":"sample-0001","source":"seed","repo":{"owner":"itpr","name":"demo","defaultBranch":"main"},"issue":{"number":1,"title":"Sample seeded job","body":"Boot smoke test job for the local stack."}}'

awslocal sqs send-message \
  --region "${REGION}" \
  --queue-url "${QUEUE_URL}" \
  --message-body "${BODY}" \
  --message-attributes 'seed={DataType=String,StringValue=itpr-sample-seed}' >/dev/null

echo "[seed] enqueued sample job onto ${QUEUE_NAME}"
