/**
 * Zod schema for all environment variables. Single source of truth for config
 * shape + validation; the inferred `Config` type is consumed across TS services.
 */
import { z } from "zod";

/** Coerce common truthy/falsy strings to boolean. */
const boolish = z
  .enum(["true", "false", "1", "0"])
  .transform((v) => v === "true" || v === "1");

export const configSchema = z.object({
  NODE_ENV: z
    .enum(["development", "test", "production"])
    .default("development"),
  PORT: z.coerce.number().int().positive().default(3001),

  // --- GitHub App (real secrets; required) ---
  GITHUB_APP_ID: z.string().min(1, "GITHUB_APP_ID is required"),
  GITHUB_APP_PRIVATE_KEY: z
    .string()
    .min(1, "GITHUB_APP_PRIVATE_KEY is required"),
  GITHUB_WEBHOOK_SECRET: z
    .string()
    .min(1, "GITHUB_WEBHOOK_SECRET is required"),

  // --- smee.io webhook forwarding ---
  SMEE_URL: z.string().url().optional(),

  // --- LocalStack / AWS-compatible ---
  AWS_ENDPOINT_URL: z.string().url(),
  AWS_REGION: z.string().min(1),
  AWS_ACCESS_KEY_ID: z.string().min(1),
  AWS_SECRET_ACCESS_KEY: z.string().min(1),
  SQS_QUEUE_URL: z.string().url(),
  SQS_DLQ_URL: z.string().url(),
  DYNAMODB_BUDGET_TABLE: z.string().min(1),
  S3_ARTIFACTS_BUCKET: z.string().min(1),

  // --- Observability ---
  LANGFUSE_HOST: z.string().url(),
  LANGFUSE_PUBLIC_KEY: z.string().optional(),
  LANGFUSE_SECRET_KEY: z.string().optional(),

  // --- LLM providers (free tier; all optional, at least mock always works) ---
  LLM_PROVIDER_ORDER: z
    .string()
    .transform((s) => s.split(",").map((x) => x.trim()).filter(Boolean)),
  NVIDIA_NIM_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  GROQ_API_KEY: z.string().optional(),
  OLLAMA_HOST: z.string().url(),

  // --- Feature flags ---
  BUDGET_LEDGER_FALLBACK_SQLITE: boolish.default("true"),
});

/** Fully validated, typed configuration object. */
export type Config = z.infer<typeof configSchema>;
