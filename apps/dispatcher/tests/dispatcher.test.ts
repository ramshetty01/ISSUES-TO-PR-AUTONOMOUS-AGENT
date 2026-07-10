import { describe, it, expect, vi } from "vitest";
import type { Job } from "@itpr/shared-types";
import { Dispatcher, type DispatcherDeps } from "../src/dispatcher.js";
import { Poller } from "../src/poller.js";
import { AuditLog } from "../src/observability/audit-log.js";
import { Metrics } from "../src/observability/metrics.js";
import { normalizeJob } from "../src/job-normalizer.js";
import type { ReceivedJob } from "../src/queue/sqs-client.js";

const job: Job = {
  id: "d-1",
  repo: { owner: "acme", name: "widgets" },
  installationId: 42,
  trigger: "issue_labeled",
  issueNumber: 7,
  headSha: "",
  labels: ["agent-fix"],
  createdAt: "2026-07-10T12:00:00.000Z",
};

function received(overrides: Partial<ReceivedJob> = {}): ReceivedJob {
  return { messageId: "m1", receiptHandle: "rh1", job, receiveCount: 1, ...overrides };
}

function mkDeps(over: Partial<DispatcherDeps> = {}): {
  deps: DispatcherDeps;
  spies: {
    ack: ReturnType<typeof vi.fn>;
    nack: ReturnType<typeof vi.fn>;
    deadLetter: ReturnType<typeof vi.fn>;
    runWorker: ReturnType<typeof vi.fn>;
  };
  metrics: Metrics;
} {
  const ack = vi.fn().mockResolvedValue(undefined);
  const nack = vi.fn().mockResolvedValue(undefined);
  const deadLetter = vi.fn().mockResolvedValue(undefined);
  const runWorker = vi.fn().mockResolvedValue({ exitCode: 0, timedOut: false });
  const metrics = new Metrics();
  const deps: DispatcherDeps = {
    checkBudget: vi
      .fn()
      .mockResolvedValue({ allowed: true, remainingTokens: 1, remainingDollars: 1 }),
    checkRepoPolicy: vi.fn().mockResolvedValue({ ok: true }),
    runWorker,
    ack,
    nack,
    deadLetter,
    maxReceives: 5,
    audit: new AuditLog(),
    metrics,
    ...over,
  };
  return { deps, spies: { ack, nack, deadLetter, runWorker }, metrics };
}

describe("job-normalizer", () => {
  it("accepts a valid job, rejects malformed", () => {
    expect(normalizeJob(job).ok).toBe(true);
    expect(normalizeJob({ id: "x" }).ok).toBe(false);
    expect(normalizeJob({ ...job, trigger: "bogus" }).ok).toBe(false);
  });
});

describe("Dispatcher.handle", () => {
  it("dispatches a valid job and acks", async () => {
    const { deps, spies, metrics } = mkDeps();
    const res = await new Dispatcher(deps).handle(received());
    expect(res).toBe("dispatched");
    expect(spies.runWorker).toHaveBeenCalledOnce();
    expect(spies.ack).toHaveBeenCalledOnce();
    expect(spies.nack).not.toHaveBeenCalled();
    expect(metrics.get("succeeded")).toBe(1);
  });

  it("refuses + acks (no retry) when over budget; worker not spawned", async () => {
    const { deps, spies, metrics } = mkDeps({
      checkBudget: vi.fn().mockResolvedValue({
        allowed: false,
        reason: "daily token cap reached",
        remainingTokens: 0,
        remainingDollars: 0,
      }),
    });
    const res = await new Dispatcher(deps).handle(received());
    expect(res).toBe("refused");
    expect(spies.ack).toHaveBeenCalledOnce();
    expect(spies.runWorker).not.toHaveBeenCalled();
    expect(metrics.get("refused")).toBe(1);
  });

  it("refuses when repo policy fails", async () => {
    const { deps, spies } = mkDeps({
      checkRepoPolicy: vi.fn().mockResolvedValue({ ok: false, reason: "no protection" }),
    });
    const res = await new Dispatcher(deps).handle(received());
    expect(res).toBe("refused");
    expect(spies.ack).toHaveBeenCalledOnce();
    expect(spies.runWorker).not.toHaveBeenCalled();
  });

  it("nacks on non-zero worker exit (transient failure)", async () => {
    const { deps, spies, metrics } = mkDeps({
      runWorker: vi.fn().mockResolvedValue({ exitCode: 1, timedOut: false }),
    });
    const res = await new Dispatcher(deps).handle(received());
    expect(res).toBe("failed");
    expect(spies.nack).toHaveBeenCalledOnce();
    expect(spies.ack).not.toHaveBeenCalled();
    expect(metrics.get("failed")).toBe(1);
  });

  it("nacks when the worker throws", async () => {
    const { deps, spies } = mkDeps({
      runWorker: vi.fn().mockRejectedValue(new Error("spawn failed")),
    });
    const res = await new Dispatcher(deps).handle(received());
    expect(res).toBe("failed");
    expect(spies.nack).toHaveBeenCalledOnce();
  });

  it("dead-letters past the max receive count", async () => {
    const { deps, spies, metrics } = mkDeps();
    const res = await new Dispatcher(deps).handle(received({ receiveCount: 6 }));
    expect(res).toBe("dead_lettered");
    expect(spies.deadLetter).toHaveBeenCalledOnce();
    expect(metrics.get("dead_lettered")).toBe(1);
  });

  it("dead-letters a malformed job", async () => {
    const { deps, spies } = mkDeps();
    const bad = received({ job: { id: "d-1" } as unknown as Job });
    const res = await new Dispatcher(deps).handle(bad);
    expect(res).toBe("malformed");
    expect(spies.deadLetter).toHaveBeenCalledOnce();
  });
});

describe("Poller.tick", () => {
  it("dispatches every message in a batch", async () => {
    const { deps } = mkDeps();
    const dispatcher = new Dispatcher(deps);
    const handle = vi.spyOn(dispatcher, "handle").mockResolvedValue("dispatched");
    const poller = new Poller({
      receive: vi
        .fn()
        .mockResolvedValue([received(), received({ receiptHandle: "rh2" })]),
      dispatcher,
    });
    const n = await poller.tick();
    expect(n).toBe(2);
    expect(handle).toHaveBeenCalledTimes(2);
  });
});
