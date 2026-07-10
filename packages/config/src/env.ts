/**
 * Load + validate configuration from an environment source. Fails fast with a
 * readable, aggregated error listing every missing/invalid key.
 */
import { configSchema, type Config } from "./schema.js";
import { DEV_DEFAULTS } from "./defaults.js";

export type EnvSource = Record<string, string | undefined>;

/** Thrown when the environment fails validation. Message lists all problems. */
export class ConfigError extends Error {
  constructor(public readonly issues: string[]) {
    super(
      `Invalid configuration:\n${issues.map((i) => `  - ${i}`).join("\n")}`,
    );
    this.name = "ConfigError";
  }
}

/**
 * Parse + validate config. In development/test, dev defaults backfill any key
 * not present in the source, so only real secrets must be supplied.
 */
export function loadConfig(source: EnvSource = process.env): Config {
  const useDefaults = (source.NODE_ENV ?? "development") !== "production";
  const merged: EnvSource = useDefaults
    ? { ...DEV_DEFAULTS, ...stripUndefined(source) }
    : source;

  const result = configSchema.safeParse(merged);
  if (!result.success) {
    const issues = result.error.issues.map(
      (i) => `${i.path.join(".") || "(root)"}: ${i.message}`,
    );
    throw new ConfigError(issues);
  }
  return result.data;
}

function stripUndefined(source: EnvSource): EnvSource {
  const out: EnvSource = {};
  for (const [k, v] of Object.entries(source)) {
    if (v !== undefined) out[k] = v;
  }
  return out;
}
