/**
 * Express server for the GitHub App. Captures the raw request body (needed for
 * HMAC webhook verification in a later phase), attaches a per-request context,
 * and mounts the health + webhook routes.
 */
import express, { type Express, type Request } from "express";
import { healthRouter } from "./routes/health.js";
import { withRequestContext } from "./logging/request-context.js";
import { logger } from "./logging/logger.js";

/** A stub webhook sink; the real routing/verification lands in later phases. */
export type WebhookSink = (args: {
  event: string;
  deliveryId: string;
  body: unknown;
  rawBody: Buffer;
}) => Promise<void> | void;

export interface ServerOptions {
  /** Handles a verified-later webhook. Defaults to a no-op that logs. */
  onWebhook?: WebhookSink;
}

interface RawBodyRequest extends Request {
  rawBody?: Buffer;
}

export function createServer(opts: ServerOptions = {}): Express {
  const app = express();

  // Capture the raw body so signature verification can hash the exact bytes.
  app.use(
    express.json({
      verify: (req, _res, buf) => {
        (req as RawBodyRequest).rawBody = Buffer.from(buf);
      },
    }),
  );

  // Per-request correlation context.
  app.use((req, _res, next) => {
    const ctx: { deliveryId?: string; event?: string } = {};
    const deliveryId = req.header("x-github-delivery");
    const event = req.header("x-github-event");
    if (deliveryId) ctx.deliveryId = deliveryId;
    if (event) ctx.event = event;
    withRequestContext(ctx, () => next());
  });

  app.use(healthRouter());

  const onWebhook: WebhookSink =
    opts.onWebhook ??
    (({ event, deliveryId }) =>
      logger.info("webhook received (stub)", { event, deliveryId }));

  app.post("/webhook", async (req, res) => {
    const event = req.header("x-github-event") ?? "unknown";
    const deliveryId = req.header("x-github-delivery") ?? "unknown";
    try {
      await onWebhook({
        event,
        deliveryId,
        body: req.body,
        rawBody: (req as RawBodyRequest).rawBody ?? Buffer.alloc(0),
      });
      res.status(202).json({ accepted: true });
    } catch (err) {
      logger.error("webhook handler failed", { error: String(err) });
      res.status(500).json({ accepted: false });
    }
  });

  return app;
}
