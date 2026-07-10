/**
 * GitHub App construction + the minimal REST surface (`GhRest`) the rest of
 * this package depends on. Helpers accept a `GhRest`, so tests inject a mock
 * instead of a live Octokit — no network, no real credentials required.
 */
import { App } from "@octokit/app";
import type { Config } from "@itpr/config";

/** A repository reference used throughout the client. */
export interface Repo {
  owner: string;
  repo: string;
}

/**
 * The subset of the Octokit REST client this package uses. Structurally typed
 * so both a real Octokit and a test mock satisfy it.
 */
export interface GhRest {
  repos: {
    get(p: Repo): Promise<{ data: { default_branch: string; private: boolean } }>;
    getBranchProtection(
      p: Repo & { branch: string },
    ): Promise<{ data: BranchProtectionApi }>;
  };
  issues: {
    get(
      p: Repo & { issue_number: number },
    ): Promise<{ data: { title: string; body: string | null; state: string } }>;
    createComment(
      p: Repo & { issue_number: number; body: string },
    ): Promise<{ data: { id: number; html_url: string } }>;
    addLabels(
      p: Repo & { issue_number: number; labels: string[] },
    ): Promise<{ data: unknown }>;
    removeLabel(
      p: Repo & { issue_number: number; name: string },
    ): Promise<{ data: unknown }>;
    listLabelsOnIssue(
      p: Repo & { issue_number: number },
    ): Promise<{ data: Array<{ name: string }> }>;
  };
  pulls: {
    create(
      p: Repo & { title: string; head: string; base: string; body?: string },
    ): Promise<{ data: { number: number; html_url: string } }>;
    get(
      p: Repo & { pull_number: number },
    ): Promise<{ data: { number: number; state: string; merged: boolean } }>;
    listFiles(
      p: Repo & { pull_number: number },
    ): Promise<{ data: Array<{ filename: string; status: string }> }>;
  };
  git: {
    getRef(p: Repo & { ref: string }): Promise<{ data: { object: { sha: string } } }>;
    createRef(
      p: Repo & { ref: string; sha: string },
    ): Promise<{ data: { ref: string } }>;
    updateRef(
      p: Repo & { ref: string; sha: string; force?: boolean },
    ): Promise<{ data: { ref: string } }>;
  };
  apps: {
    listInstallations(): Promise<{ data: Array<{ id: number; account: unknown }> }>;
  };
}

/** Shape returned by GitHub's getBranchProtection endpoint (fields we read). */
export interface BranchProtectionApi {
  required_pull_request_reviews?: {
    required_approving_review_count?: number;
  } | null;
  allow_force_pushes?: { enabled: boolean } | null;
  restrictions?: unknown | null;
  enforce_admins?: { enabled: boolean } | null;
}

/** Build an App-authenticated GitHub App from validated config. */
export function createApp(config: Config): App {
  return new App({
    appId: config.GITHUB_APP_ID,
    privateKey: config.GITHUB_APP_PRIVATE_KEY,
    webhooks: { secret: config.GITHUB_WEBHOOK_SECRET },
  });
}
