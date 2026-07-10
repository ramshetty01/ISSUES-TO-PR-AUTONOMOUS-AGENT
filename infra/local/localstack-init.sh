#!/usr/bin/env sh
# ---------------------------------------------------------------------------
# LocalStack init hook (runs from /etc/localstack/init/ready.d/ on boot).
# Provisions the $0 local backbone: SQS jobs queue + DLQ (with redrive),
# a DynamoDB budget ledger table, and an S3 artifacts bucket.
#
# Fully idempotent: every create is guarded so re-runs are no-ops.
# Uses `awslocal` (bundled in the localstack image) which targets the
# in-container endpoint with the fixed 000000000000 dev account.
# ---------------------------------------------------------------------------
set -eu

REGION="us-east-1"
QUEUE_NAME="itpr-jobs"
DLQ_NAME="itpr-jobs-dlq"
BUDGET_TABLE="itpr-budget-ledger"
ARTIFACTS_BUCKET="itpr-artifacts"

echo "[localstack-init] provisioning itpr local resources in ${REGION}..."

# --- SQS: dead-letter queue first, then the main queue wired to redrive -----
create_queue() {
  name="$1"
  if awslocal sqs get-queue-url --region "${REGION}" --queue-name "${name}" >/dev/null 2>&1; then
    echo "[localstack-init] sqs queue ${name} already exists"
  else
    awslocal sqs create-queue --region "${REGION}" --queue-name "${name}" >/dev/null
    echo "[localstack-init] created sqs queue ${name}"
  fi
}

create_queue "${DLQ_NAME}"
create_queue "${QUEUE_NAME}"

# Resolve the DLQ ARN and attach a redrive policy to the main queue.
DLQ_URL="$(awslocal sqs get-queue-url --region "${REGION}" --queue-name "${DLQ_NAME}" --output text --query 'QueueUrl')"
DLQ_ARN="$(awslocal sqs get-queue-attributes --region "${REGION}" --queue-url "${DLQ_URL}" --attribute-names QueueArn --output text --query 'Attributes.QueueArn')"
MAIN_URL="$(awslocal sqs get-queue-url --region "${REGION}" --queue-name "${QUEUE_NAME}" --output text --query 'QueueUrl')"

awslocal sqs set-queue-attributes \
  --region "${REGION}" \
  --queue-url "${MAIN_URL}" \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}" >/dev/null
echo "[localstack-init] wired redrive ${QUEUE_NAME} -> ${DLQ_NAME} (maxReceiveCount=5)"

# --- DynamoDB: budget ledger (pk/sk keeps per-repo + per-window records) -----
if awslocal dynamodb describe-table --region "${REGION}" --table-name "${BUDGET_TABLE}" >/dev/null 2>&1; then
  echo "[localstack-init] dynamodb table ${BUDGET_TABLE} already exists"
else
  awslocal dynamodb create-table \
    --region "${REGION}" \
    --table-name "${BUDGET_TABLE}" \
    --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
    --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST >/dev/null
  echo "[localstack-init] created dynamodb table ${BUDGET_TABLE}"
fi

# --- S3: artifacts bucket ----------------------------------------------------
if awslocal s3api head-bucket --region "${REGION}" --bucket "${ARTIFACTS_BUCKET}" >/dev/null 2>&1; then
  echo "[localstack-init] s3 bucket ${ARTIFACTS_BUCKET} already exists"
else
  awslocal s3api create-bucket --region "${REGION}" --bucket "${ARTIFACTS_BUCKET}" >/dev/null
  echo "[localstack-init] created s3 bucket ${ARTIFACTS_BUCKET}"
fi

echo "[localstack-init] done."
