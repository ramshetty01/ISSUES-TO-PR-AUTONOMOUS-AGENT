/**
 * smee.io client: forwards GitHub webhook deliveries to the local Express
 * server. Replaces the public AWS webhook Lambda in the $0 local build.
 */
import SmeeClient from "smee-client";
import { logger } from "./logging/logger.js";

export interface SmeeHandle {
  close(): void;
}

/**
 * Start forwarding from a smee channel to a local target URL. No-ops (returns
 * undefined) when no smee URL is configured — useful in production or tests.
 */
export function startSmee(
  smeeUrl: string | undefined,
  targetUrl: string,
): SmeeHandle | undefined {
  if (!smeeUrl) {
    logger.info("smee disabled (no SMEE_URL)");
    return undefined;
  }
  const smee = new SmeeClient({ source: smeeUrl, target: targetUrl, logger });
  const events = smee.start();
  logger.info("smee forwarding started", { smeeUrl, targetUrl });
  return {
    close: () => events.close(),
  };
}
