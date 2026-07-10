import Link from "next/link";

import { RateLimitBanner } from "../components/RateLimitBanner.js";
import { formatCost } from "../lib/format-cost.js";
import { api } from "../lib/api.js";

// Backed by a runtime API; render per-request rather than prerendering at build.
export const dynamic = "force-dynamic";

/** Overview of recent runs. */
export default async function HomePage() {
  const [runs, rateLimit] = await Promise.all([
    api.listRuns(),
    api.getRateLimit(),
  ]);
  return (
    <div className="grid">
      <RateLimitBanner status={rateLimit} />
      <section className="panel">
        <h1>Recent runs</h1>
        <p className="muted">Newest agent runs across all repos.</p>
      </section>
      {runs.length === 0 ? (
        <p className="muted">No runs yet.</p>
      ) : (
        <table aria-label="recent runs">
          <thead>
            <tr>
              <th>Run</th>
              <th>Repo</th>
              <th>State</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.runId}>
                <td>
                  <Link href={`/runs/${run.runId}`}>{run.runId}</Link>
                </td>
                <td>
                  {run.job.repo.owner}/{run.job.repo.name}
                </td>
                <td>
                  <span className="badge">{run.state}</span>
                </td>
                <td>{formatCost(run.dollars)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <nav className="panel">
        <Link href="/budgets">Budgets →</Link>
      </nav>
    </div>
  );
}
