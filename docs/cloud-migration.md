# Cloud Migration (LocalStack → AWS)

The stack is developed against [LocalStack](https://localstack.cloud) so the
whole pipeline runs on a laptop with zero cloud cost. Because every service uses
the AWS SDK against a single configurable endpoint, moving to real AWS is an
**endpoint + credentials swap**, not a rewrite. The service APIs are identical.

## Service mapping

| Concern | Local (LocalStack) | AWS (production) | Code change |
| --- | --- | --- | --- |
| Job queue | SQS on `:4566` | Amazon SQS | none — same API |
| Dead-letter queue | SQS on `:4566` | Amazon SQS (redrive policy) | none |
| Budget ledger | DynamoDB on `:4566` (or SQLite fallback) | Amazon DynamoDB | none — same API |
| Artifact / trace store | S3 on `:4566` | Amazon S3 | none — same API |
| Compute (worker) | local Docker | ECS/Fargate task or Firecracker microVM | runner target |
| Traces / observability | self-hosted Langfuse | self-hosted Langfuse or hosted | endpoint only |

## The endpoint swap

Every AWS client reads `AWS_ENDPOINT_URL` from validated config
([`packages/config`](../packages/config), `boto3` in the worker). Local dev sets
it to `http://localhost:4566`; production **omits it**, so the SDK resolves the
real regional endpoint. Concretely, in `.env`:

```diff
-AWS_ENDPOINT_URL=http://localhost:4566
-AWS_ACCESS_KEY_ID=test
-AWS_SECRET_ACCESS_KEY=test
+# AWS_ENDPOINT_URL unset — use the real endpoint
+AWS_REGION=us-east-1
+# credentials come from the task/instance IAM role, not static keys
```

Resource identifiers (`SQS_QUEUE_URL`, `SQS_DLQ_URL`, `DYNAMODB_BUDGET_TABLE`,
`S3_ARTIFACTS_BUCKET`) point at real ARNs/names instead of the LocalStack ones.
See [`.env.example`](../.env.example) for the full list.

## Local baseline before migrating

Before swapping endpoints, prove the exact same workflow locally:

```bash
make up
make seed
docker compose exec localstack awslocal sqs list-queues
docker compose exec localstack awslocal dynamodb list-tables
docker compose exec localstack awslocal s3 ls
make worker-image
```

LocalStack should expose:

- `itpr-jobs` and its DLQ.
- `itpr-budget-ledger`.
- `itpr-artifacts`.

Then run a labeled-issue flow through the GitHub App, or run one normalized job
through the same worker image:

```bash
./scripts/run-local-worker.sh path/to/job.json
```

This keeps cloud migration focused on infrastructure and credentials. If Track A
or the local worker path is failing, fix that before introducing real AWS.

## What must change for real AWS

1. **Credentials.** Drop the static `test`/`test` keys; grant the compute role
   least-privilege IAM: `sqs:{ReceiveMessage,DeleteMessage,SendMessage}` on the
   two queues, `dynamodb:{PutItem,Query}` on the ledger table, `s3:{PutObject,
   GetObject}` on the artifact bucket.
2. **Provisioning.** Create the queues/table/bucket with the same names, plus a
   DLQ redrive policy and DynamoDB point-in-time recovery. (Infra templates are
   owned by `infra/**`, out of scope here.)
3. **Worker compute.** Swap the dispatcher's Docker runner for an ECS/Fargate
   `RunTask`, or better, a Firecracker microVM for stronger isolation — see
   [sandbox design](sandbox-design.md) and
   [residual risks](../security/threat-model/residual-risks.md).
4. **Egress.** Restrict the worker's network to GitHub, the LLM providers, and
   the artifact bucket.
5. **Secrets.** Move GitHub App keys, Langfuse keys, provider keys, and webhook
   secrets out of `.env` and into the target secret manager for the compute
   platform.
6. **Webhook ingress.** Replace smee.io with the production GitHub App webhook
   URL. Keep the same `GITHUB_WEBHOOK_SECRET` validation behavior.
7. **Policy data.** Carry over `policies/repo-allowlist.yaml`,
   `policies/allowed-labels.yaml`, and budget policy values. Production remains
   deny-by-default.

## Production readiness checklist

- Track A smoke eval passes locally with the `mock` provider.
- A local worker-image run succeeds against LocalStack.
- Target repositories are allowlisted and have branch protection.
- GitHub App permissions match
  [github-app-permissions.md](github-app-permissions.md).
- AWS queues, table, bucket, IAM roles, and redrive policy are provisioned.
- `AWS_ENDPOINT_URL` is unset in production.
- Langfuse is reachable from the worker and dashboard.
- Dashboard is served on a port or domain that does not collide with Langfuse.

## Why it stays cheap

DynamoDB/SQS/S3 all have generous free tiers, and the agent runs on
[free-tier LLM providers](llm-provider-strategy.md), so a modest production
deployment can approach zero marginal cost while enforcing the same
[budget policy](budget-policy.md). See the [architecture](architecture.md)
overview for how the pieces connect.
