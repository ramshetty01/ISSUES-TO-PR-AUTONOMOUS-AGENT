/**
 * Assemble the environment the worker container needs. Secret values are placed
 * in the env MAP (passed via the child process' environment), never in argv —
 * the runner passes only variable NAMES to `docker run -e`.
 */
import type { Job } from "@itpr/shared-types";
import { loadConfig } from "@itpr/config";

export interface WorkerEnv {
  /** name -> value, injected into the runner's child-process env. */
  env: Record<string, string>;
  /** variable names to forward via `docker run -e NAME`. */
  keys: string[];
}

export interface WorkerEnvInput {
  job: Job;
  /** Short-lived installation token minted just before dispatch. */
  installationToken: string;
  source?: NodeJS.ProcessEnv;
}

export function buildWorkerEnv(input: WorkerEnvInput): WorkerEnv {
  const cfg = loadConfig(input.source);
  const env: Record<string, string> = {
    ITPR_JOB: JSON.stringify(input.job),
    ITPR_JOB_ID: input.job.id,
    ITPR_SANDBOX_MODE: "process",
    GITHUB_INSTALLATION_TOKEN: input.installationToken,
    AWS_ENDPOINT_URL: cfg.AWS_ENDPOINT_URL,
    AWS_REGION: cfg.AWS_REGION,
    AWS_ACCESS_KEY_ID: cfg.AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY: cfg.AWS_SECRET_ACCESS_KEY,
    S3_ARTIFACTS_BUCKET: cfg.S3_ARTIFACTS_BUCKET,
    LANGFUSE_HOST: cfg.LANGFUSE_HOST,
    OLLAMA_HOST: cfg.OLLAMA_HOST,
    LLM_PROVIDER_ORDER: cfg.LLM_PROVIDER_ORDER.join(","),
    OPENROUTER_MODEL: cfg.OPENROUTER_MODEL ?? "tencent/hy3:free",
    NVIDIA_NIM_MODEL: cfg.NVIDIA_NIM_MODEL ?? "qwen/qwen3.5-122b-a10b",
  };
  // Forward optional provider keys only when present.
  for (const k of ["OPENROUTER_API_KEY", "NVIDIA_NIM_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"] as const) {
    const v = input.source?.[k] ?? process.env[k];
    if (v) env[k] = v;
  }
  return { env, keys: Object.keys(env) };
}
