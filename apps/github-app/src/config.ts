/** github-app configuration, derived from the validated shared config. */
import { loadConfig, type Config } from "@itpr/config";

export interface AppConfig {
  port: number;
  smeeUrl: string | undefined;
  webhookSecret: string;
  nodeEnv: Config["NODE_ENV"];
}

export function loadAppConfig(source?: NodeJS.ProcessEnv): AppConfig {
  const cfg = loadConfig(source);
  return {
    port: cfg.PORT,
    smeeUrl: cfg.SMEE_URL,
    webhookSecret: cfg.GITHUB_WEBHOOK_SECRET,
    nodeEnv: cfg.NODE_ENV,
  };
}
