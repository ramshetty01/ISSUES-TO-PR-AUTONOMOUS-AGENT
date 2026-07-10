/** Handle installation created/deleted/suspend/unsuspend — record + acknowledge. */
import type { InstallationEvent } from "@itpr/shared-types";
import { logger } from "../logging/logger.js";
import type { HandlerResult } from "./issue-labeled.handler.js";

export function handleInstallation(event: InstallationEvent): HandlerResult {
  logger.info("installation event", {
    action: event.action,
    installationId: event.installationId,
  });
  return { action: "recorded", detail: `installation.${event.action}` };
}
