/**
 * Obtain an installation-scoped REST client for a given installation. Wraps the
 * github-client package with this app's App instance.
 */
import type { App } from "@octokit/app";
import { installationClient, type GhRest } from "@itpr/github-client";
import { getApp } from "./app-auth.js";

/** Installation-scoped client, using the app singleton unless one is provided. */
export function clientForInstallation(
  installationId: number,
  app: App = getApp(),
): Promise<GhRest> {
  return installationClient(app, installationId);
}
