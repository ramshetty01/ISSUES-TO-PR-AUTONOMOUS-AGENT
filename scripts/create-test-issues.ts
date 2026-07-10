/**
 * create-test-issues.ts — seed a repo with a few labeled issues that exercise
 * the agent end-to-end (a failing test, a small bug, a typo). Each is opened
 * and then tagged with the trigger label so the github-app enqueues a job.
 *
 *   pnpm dlx tsx scripts/create-test-issues.ts owner/repo [label]
 *
 * Uses the GitHub App installation token (creds from .env). The default trigger
 * label matches policies/allowed-labels.yaml ("agent-fix").
 */
import { Octokit } from "@octokit/rest";
import { loadConfig } from "@itpr/config";
import {
  createApp,
  listInstallations,
  getInstallationToken,
} from "@itpr/github-client";

interface SeedIssue {
  title: string;
  body: string;
}

const SEED_ISSUES: SeedIssue[] = [
  {
    title: "[test] add() returns wrong result for negative numbers",
    body:
      "`add(-2, 1)` returns `-3` but should return `-1`.\n\n" +
      "Reproduce:\n```\nassert add(-2, 1) == -1\n```\n" +
      "Please fix the implementation and keep the existing tests green.",
  },
  {
    title: "[test] README references a renamed CLI flag",
    body:
      "The README documents `--out-dir` but the CLI now accepts `--output`.\n" +
      "Update the docs so the example runs as written.",
  },
  {
    title: "[test] guard against empty input in parse()",
    body:
      "`parse('')` raises IndexError. It should return an empty result instead.\n" +
      "Add a small guard and a regression test.",
  },
];

async function main(): Promise<void> {
  const target = process.argv[2];
  if (!target || !target.includes("/")) {
    console.error("usage: tsx scripts/create-test-issues.ts owner/repo [label]");
    process.exit(2);
  }
  const [owner, repo] = target.split("/");
  const label = process.argv[3] ?? "agent-fix";

  const cfg = loadConfig();
  const app = createApp(cfg);
  const installs = await listInstallations(app);
  if (installs.length === 0) {
    console.error("no App installations found");
    process.exit(1);
  }
  const { token } = await getInstallationToken(app, installs[0].id);
  const octokit = new Octokit({ auth: token });

  for (const issue of SEED_ISSUES) {
    const { data } = await octokit.rest.issues.create({
      owner,
      repo,
      title: issue.title,
      body: issue.body,
    });
    await octokit.rest.issues.addLabels({
      owner,
      repo,
      issue_number: data.number,
      labels: [label],
    });
    console.log(`created #${data.number} (${label}): ${data.html_url}`);
  }
  console.log(`\nSeeded ${SEED_ISSUES.length} labeled issues on ${owner}/${repo}.`);
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
