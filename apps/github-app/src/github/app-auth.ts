/** Build + cache the GitHub App instance from validated config. */
import type { App } from "@octokit/app";
import { createApp } from "@itpr/github-client";
import { loadConfig } from "@itpr/config";

let cached: App | undefined;

/** Lazily construct the App (singleton). */
export function getApp(): App {
  if (!cached) cached = createApp(loadConfig());
  return cached;
}

/** Reset the cached App (tests). */
export function resetApp(): void {
  cached = undefined;
}
