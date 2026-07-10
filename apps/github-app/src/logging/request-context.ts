/**
 * Per-request correlation context propagated via AsyncLocalStorage, so any log
 * emitted while handling a request carries its id + delivery id.
 */
import { AsyncLocalStorage } from "node:async_hooks";
import { randomUUID } from "node:crypto";

export interface RequestContext {
  requestId: string;
  /** X-GitHub-Delivery id, when present. */
  deliveryId?: string;
  event?: string;
}

const storage = new AsyncLocalStorage<RequestContext>();

/** Run `fn` with a fresh request context. */
export function withRequestContext<T>(
  ctx: Partial<RequestContext>,
  fn: () => T,
): T {
  const full: RequestContext = {
    requestId: ctx.requestId ?? randomUUID(),
    ...(ctx.deliveryId !== undefined ? { deliveryId: ctx.deliveryId } : {}),
    ...(ctx.event !== undefined ? { event: ctx.event } : {}),
  };
  return storage.run(full, fn);
}

/** Current request context, if inside one. */
export function currentContext(): RequestContext | undefined {
  return storage.getStore();
}
