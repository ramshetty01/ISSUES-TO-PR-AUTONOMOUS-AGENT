/**
 * verify-branch-protection.ts — check that a repo's default branch has the
 * protection the agent requires before it will operate on that repo. This is
 * the same gate the dispatcher applies (see docs/branch-protection-requirements.md
 * and policies/branch-protection-required.yaml); running it standalone lets an
 * operator confirm a repo is ready without pushing a job through the queue.
 *
 *   pnpm dlx tsx scripts/verify-branch-protection.ts owner/repo [branch]
 *
 * Requires GitHub App credentials in the environment (.env). Exits non-zero if
 * protection is missing or weaker than required.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { parse as parseYaml } from "yaml";
import { loadConfig } from "@itpr/config";
import {
  createApp,
  listInstallations,
  installationClient,
  getDefaultBranch,
  getBranchProtection,
} from "@itpr/github-client";
import type { BranchProtectionSnapshot } from "@itpr/shared-types";

interface RequiredProtection {
  requirePullRequest: boolean;
  minApprovals: number;
  disallowForcePush: boolean;
  restrictDirectPush: boolean;
}

const here = dirname(fileURLToPath(import.meta.url));
const POLICY = resolve(here, "../policies/branch-protection-required.yaml");

function loadRequired(): RequiredProtection {
  return parseYaml(readFileSync(POLICY, "utf8")) as RequiredProtection;
}

function violations(
  snap: BranchProtectionSnapshot,
  req: RequiredProtection,
): string[] {
  const out: string[] = [];
  if (req.requirePullRequest && !snap.requiresPullRequest)
    out.push("pull request reviews are not required");
  if (snap.requiredApprovingReviews < req.minApprovals)
    out.push(
      `requires ${snap.requiredApprovingReviews} approvals, need >= ${req.minApprovals}`,
    );
  if (req.disallowForcePush && snap.allowsForcePush)
    out.push("force pushes are allowed");
  if (req.restrictDirectPush && !snap.restrictsDirectPush)
    out.push("direct pushes are not restricted");
  return out;
}

async function main(): Promise<void> {
  const target = process.argv[2];
  if (!target || !target.includes("/")) {
    console.error("usage: tsx scripts/verify-branch-protection.ts owner/repo [branch]");
    process.exit(2);
  }
  const [owner, name] = target.split("/");
  const cfg = loadConfig();
  const app = createApp(cfg);

  const installs = await listInstallations(app);
  if (installs.length === 0) {
    console.error("no App installations found — is the App installed on the org?");
    process.exit(1);
  }
  // Use the first installation; a multi-tenant setup would match by account.
  const gh = await installationClient(app, installs[0].id);

  const branch = process.argv[3] ?? (await getDefaultBranch(gh, { owner, repo: name }));
  const snap = await getBranchProtection(gh, { owner, repo: name }, branch);
  const req = loadRequired();
  const problems = violations(snap, req);

  console.log(`branch protection for ${owner}/${name}@${branch}:`);
  console.log(JSON.stringify(snap, null, 2));

  if (problems.length > 0) {
    console.error("\nFAIL — required protection missing:");
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log("\nOK — branch protection satisfies policy.");
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
