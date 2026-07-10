import { describe, it, expect, vi } from "vitest";
import request from "supertest";
import { createServer } from "../src/server.js";

describe("github-app server", () => {
  it("GET /health returns 200 ok", async () => {
    const app = createServer();
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  it("POST /webhook routes to the sink and returns 202", async () => {
    const sink = vi.fn();
    const app = createServer({ onWebhook: sink });
    const res = await request(app)
      .post("/webhook")
      .set("x-github-event", "issues")
      .set("x-github-delivery", "delivery-123")
      .send({ action: "labeled" });

    expect(res.status).toBe(202);
    expect(res.body.accepted).toBe(true);
    expect(sink).toHaveBeenCalledOnce();
    const arg = sink.mock.calls[0]![0];
    expect(arg.event).toBe("issues");
    expect(arg.deliveryId).toBe("delivery-123");
    expect(arg.body).toEqual({ action: "labeled" });
    // raw body captured for later HMAC verification
    expect(Buffer.isBuffer(arg.rawBody)).toBe(true);
    expect(arg.rawBody.length).toBeGreaterThan(0);
  });

  it("returns 500 when the sink throws", async () => {
    const app = createServer({
      onWebhook: () => {
        throw new Error("boom");
      },
    });
    const res = await request(app)
      .post("/webhook")
      .set("x-github-event", "issues")
      .send({});
    expect(res.status).toBe(500);
    expect(res.body.accepted).toBe(false);
  });
});
