import { RunTimeline } from "../../../components/RunTimeline.js";
import { SafetyEvents } from "../../../components/SafetyEvents.js";
import { TraceViewer } from "../../../components/TraceViewer.js";
import { formatCost, formatTokens } from "../../../lib/format-cost.js";
import { durationBetween } from "../../../lib/format-duration.js";
import { api } from "../../../lib/api.js";

/** Full run detail: timeline + trace link + safety events. */
export default async function RunPage({ params }: { params: { runId: string } }) {
  const run = await api.getRun(params.runId);
  return (
    <div className="grid">
      <header className="panel">
        <h1>
          Run {run.runId} <span className="badge">{run.state}</span>
        </h1>
        <div className="muted">
          {run.job.repo.owner}/{run.job.repo.name} · {formatTokens(run.usage.total)} tokens ·{" "}
          {formatCost(run.dollars)} · {durationBetween(run.startedAt, run.finishedAt)}
        </div>
        <div style={{ marginTop: 8 }}>
          <TraceViewer traceUrl={run.traceUrl} />
        </div>
      </header>

      <section className="grid">
        <h2>Timeline</h2>
        <RunTimeline events={run.timeline} />
      </section>

      <section className="grid">
        <h2>Safety</h2>
        <SafetyEvents events={run.safetyEvents} refusal={run.refusal} />
      </section>
    </div>
  );
}
