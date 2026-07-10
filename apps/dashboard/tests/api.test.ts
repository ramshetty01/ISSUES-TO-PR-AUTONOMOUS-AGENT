import { describe, expect, it, vi } from "vitest";

import { ApiClient, ApiError } from "../src/lib/api.js";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("ApiClient", () => {
  it("fetches runs from the configured base with the right path", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse([{ runId: "r1" }]));
    const client = new ApiClient({ baseUrl: "http://api/", fetchImpl });
    const runs = await client.listRuns();
    expect(runs).toEqual([{ runId: "r1" }]);
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api/api/runs",
      expect.objectContaining({ headers: { accept: "application/json" } }),
    );
  });

  it("encodes path params", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ owner: "a b" }));
    const client = new ApiClient({ baseUrl: "http://api", fetchImpl });
    await client.getRepoBudget("a b", "c/d");
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api/api/repos/a%20b/c%2Fd/budget",
      expect.anything(),
    );
  });

  it("throws ApiError on non-2xx", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({}, 503));
    const client = new ApiClient({ baseUrl: "http://api", fetchImpl });
    await expect(client.listBudgets()).rejects.toBeInstanceOf(ApiError);
  });
});
