export default function RunPage({ params }: { params: { runId: string } }) {
  return (
    <div className="grid">
      <h1>Run {params.runId}</h1>
      <p className="muted">Timeline, cost, trace, and safety events for this run.</p>
    </div>
  );
}
