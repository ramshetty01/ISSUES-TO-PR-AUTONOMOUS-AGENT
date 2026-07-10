/** Handle the ping event GitHub sends when a webhook is configured. */
import type { HandlerResult } from "./issue-labeled.handler.js";

export function handlePing(): HandlerResult {
  return { action: "pong" };
}
