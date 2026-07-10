import { describe, it, expect, vi } from "vitest";
import type { App } from "@octokit/app";
import {
  getInstallationToken,
  installationClient,
  getInstallationPermissions,
  createIssueComment,
  getBranchProtection,
  getBranchProtectionSafe,
  createBranch,
  type GhRest,
} from "../src/index.js";

const REPO = { owner: "acme", repo: "widgets" };

/** Build a mock GhRest with only the methods a given test exercises. */
function mockGh(overrides: Partial<GhRest> = {}): GhRest {
  return overrides as GhRest;
}

describe("auth", () => {
  it("mints an installation token via the App", async () => {
    const octokit = {
      auth: vi.fn().mockResolvedValue({
        token: "ghs_abc",
        expiresAt: "2026-07-09T01:00:00Z",
      }),
      rest: {},
    };
    const app = {
      getInstallationOctokit: vi.fn().mockResolvedValue(octokit),
    } as unknown as App;

    const tok = await getInstallationToken(app, 99);
    expect(app.getInstallationOctokit).toHaveBeenCalledWith(99);
    expect(tok).toEqual({ token: "ghs_abc", expiresAt: "2026-07-09T01:00:00Z" });
  });

  it("fetches installation permissions via the app octokit", async () => {
    const request = vi.fn().mockResolvedValue({
      data: { permissions: { issues: "write", contents: "read" } },
    });
    const app = { octokit: { request } } as unknown as App;
    const perms = await getInstallationPermissions(app, 7);
    expect(request).toHaveBeenCalledWith(
      "GET /app/installations/{installation_id}",
      { installation_id: 7 },
    );
    expect(perms).toEqual({ issues: "write", contents: "read" });
  });

  it("returns an installation-scoped rest client built from the token", async () => {
    const octokit = {
      auth: vi
        .fn()
        .mockResolvedValue({ token: "ghs_x", expiresAt: "2026-07-09T01:00:00Z" }),
    };
    const app = {
      getInstallationOctokit: vi.fn().mockResolvedValue(octokit),
    } as unknown as App;
    const gh = await installationClient(app, 1);
    // A real @octokit/rest surface exposes the endpoints our GhRest subset uses.
    expect(typeof gh.repos.get).toBe("function");
    expect(typeof gh.issues.createComment).toBe("function");
  });
});

describe("issues", () => {
  it("posts a comment and returns id + url", async () => {
    const createComment = vi.fn().mockResolvedValue({
      data: { id: 5, html_url: "https://github.com/acme/widgets/issues/1#c5" },
    });
    const gh = mockGh({ issues: { createComment } as unknown as GhRest["issues"] });
    const res = await createIssueComment(gh, REPO, 1, "on it");
    expect(createComment).toHaveBeenCalledWith({
      ...REPO,
      issue_number: 1,
      body: "on it",
    });
    expect(res).toEqual({ id: 5, url: "https://github.com/acme/widgets/issues/1#c5" });
  });
});

describe("protection", () => {
  it("maps the API shape to a BranchProtectionSnapshot", async () => {
    const getBranchProtectionApi = vi.fn().mockResolvedValue({
      data: {
        required_pull_request_reviews: { required_approving_review_count: 2 },
        allow_force_pushes: { enabled: false },
        restrictions: {},
        enforce_admins: { enabled: true },
      },
    });
    const gh = mockGh({
      repos: {
        getBranchProtection: getBranchProtectionApi,
      } as unknown as GhRest["repos"],
    });
    const snap = await getBranchProtection(gh, REPO, "main");
    expect(snap).toEqual({
      branch: "main",
      requiresPullRequest: true,
      requiredApprovingReviews: 2,
      allowsForcePush: false,
      restrictsDirectPush: true,
      enforcesForAdmins: true,
    });
  });

  it("safe variant returns an unprotected snapshot on 404", async () => {
    const gh = mockGh({
      repos: {
        getBranchProtection: vi.fn().mockRejectedValue(new Error("Not Found")),
      } as unknown as GhRest["repos"],
    });
    const snap = await getBranchProtectionSafe(gh, REPO, "main");
    expect(snap.requiresPullRequest).toBe(false);
    expect(snap.allowsForcePush).toBe(true);
  });
});

describe("refs", () => {
  it("creates a branch under refs/heads", async () => {
    const createRef = vi
      .fn()
      .mockResolvedValue({ data: { ref: "refs/heads/fix/bug" } });
    const gh = mockGh({ git: { createRef } as unknown as GhRest["git"] });
    const ref = await createBranch(gh, REPO, "fix/bug", "deadbeef");
    expect(createRef).toHaveBeenCalledWith({
      ...REPO,
      ref: "refs/heads/fix/bug",
      sha: "deadbeef",
    });
    expect(ref).toBe("refs/heads/fix/bug");
  });
});
