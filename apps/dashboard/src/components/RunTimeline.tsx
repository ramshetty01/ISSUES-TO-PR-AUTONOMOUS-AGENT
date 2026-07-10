import type { TimelineEvent } from "@itpr/shared-types";

export interface RunTimelineProps {
  events: TimelineEvent[];
}

/** Ordered feed of a run's timeline events (plan, edit, test, pr_opened, …). */
export function RunTimeline({ events }: RunTimelineProps) {
  if (events.length === 0) {
    return <p className="muted">No timeline events yet.</p>;
  }
  return (
    <ol className="panel grid" aria-label="run timeline" style={{ listStyle: "none", margin: 0 }}>
      {events.map((event, i) => (
        <li key={`${event.at}-${i}`} className="grid" style={{ gap: 2 }}>
          <div>
            <span className="badge">{event.kind}</span>{" "}
            <span>{event.message}</span>
          </div>
          <time className="muted" dateTime={event.at} style={{ fontSize: 12 }}>
            {event.at}
          </time>
        </li>
      ))}
    </ol>
  );
}

export default RunTimeline;
