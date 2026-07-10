import type { Refusal, SafetyEvent } from "@itpr/shared-types";

export interface SafetyEventsProps {
  events: SafetyEvent[];
  /** Populated when the run terminated in a refusal. */
  refusal?: Refusal | undefined;
}

/** Feed of safety events, with the terminal refusal (if any) pinned on top. */
export function SafetyEvents({ events, refusal }: SafetyEventsProps) {
  if (!refusal && events.length === 0) {
    return <p className="muted">No safety events — clean run.</p>;
  }
  return (
    <div className="grid" aria-label="safety events">
      {refusal ? (
        <div
          role="alert"
          className="panel"
          style={{ borderColor: "var(--danger)" }}
        >
          <strong style={{ color: "var(--danger)" }}>Refused: {refusal.reason}</strong>
          <div>{refusal.message}</div>
          {refusal.detail ? <div className="muted">{refusal.detail}</div> : null}
        </div>
      ) : null}
      <ul className="panel" style={{ listStyle: "none", margin: 0 }}>
        {events.map((e, i) => (
          <li key={`${e.at}-${i}`}>
            <span className="badge">{e.reason}</span> {e.message}
            {e.path ? <code className="muted"> {e.path}</code> : null}{" "}
            <time className="muted" dateTime={e.at} style={{ fontSize: 12 }}>
              {e.at}
            </time>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SafetyEvents;
