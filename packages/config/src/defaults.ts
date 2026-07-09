/**
 * Development defaults for the $0 local stack. These let the stack boot with a
 * minimal .env (only real secrets — GitHub App keys, provider keys — must be set).
 */
export const DEV_DEFAULTS = {
  NODE_ENV: "development",
  PORT: "3001",

  /** LocalStack unified endpoint (SQS + DynamoDB + S3). */
  AWS_ENDPOINT_URL: "http://localhost:4566",
  AWS_REGION: "us-east-1",
  AWS_ACCESS_KEY_ID: "test",
  AWS_SECRET_ACCESS_KEY: "test",

  SQS_QUEUE_URL: "http://localhost:4566/000000000000/itpr-jobs",
  SQS_DLQ_URL: "http://localhost:4566/000000000000/itpr-jobs-dlq",
  DYNAMODB_BUDGET_TABLE: "itpr-budget-ledger",
  S3_ARTIFACTS_BUCKET: "itpr-artifacts",

  /** Self-hosted Langfuse. */
  LANGFUSE_HOST: "http://localhost:3000",

  /** Local Ollama daemon. */
  OLLAMA_HOST: "http://localhost:11434",

  /** Default provider fallback order (comma-separated). */
  LLM_PROVIDER_ORDER: "mock",
} as const satisfies Record<string, string>;
