/**
 * Actor gate: ignore bots and the app's own identity, and optionally restrict
 * to an explicit set of permitted actors.
 */
import type { Actor } from "@itpr/shared-types";

export interface ActorPolicy {
  /** Logins to always ignore (the app's own bot login, known automations). */
  ignoreLogins?: string[];
  /**
   * When set, only these logins are permitted. When omitted, any non-bot,
   * non-ignored actor is permitted.
   */
  allowLogins?: string[];
}

export function isAllowedActor(actor: Actor, policy: ActorPolicy = {}): boolean {
  if (actor.type === "Bot") return false;
  const ignore = new Set(policy.ignoreLogins ?? []);
  if (ignore.has(actor.login)) return false;
  if (policy.allowLogins) {
    return new Set(policy.allowLogins).has(actor.login);
  }
  return true;
}
