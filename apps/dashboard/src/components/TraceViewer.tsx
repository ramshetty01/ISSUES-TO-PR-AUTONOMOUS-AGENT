export interface TraceViewerProps {
  /** Full trace URL (from RunSummary.traceUrl), if already known. */
  traceUrl?: string | undefined;
  /** Trace id, used with langfuseHost to build the link when traceUrl is absent. */
  traceId?: string | undefined;
  /** Self-hosted Langfuse base, e.g. http://localhost:3000. */
  langfuseHost?: string | undefined;
}

/** Builds a deep-link into the self-hosted Langfuse trace (matches the worker). */
export function resolveTraceHref(props: TraceViewerProps): string | null {
  if (props.traceUrl) return props.traceUrl;
  if (props.traceId && props.langfuseHost) {
    return `${props.langfuseHost.replace(/\/$/, "")}/trace/${props.traceId}`;
  }
  return null;
}

/** Link out to the run's Langfuse trace. */
export function TraceViewer(props: TraceViewerProps) {
  const href = resolveTraceHref(props);
  if (!href) {
    return <p className="muted">No trace recorded for this run.</p>;
  }
  return (
    <a
      className="badge"
      href={href}
      target="_blank"
      rel="noreferrer"
      aria-label="open langfuse trace"
    >
      View Langfuse trace ↗
    </a>
  );
}

export default TraceViewer;
