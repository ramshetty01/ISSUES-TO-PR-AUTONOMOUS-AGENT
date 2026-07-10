export interface RateLimitState {
  /** Whether a free-tier provider is currently throttling us. */
  throttled: boolean;
  /** The provider being throttled (e.g. "groq", "gemini"). */
  provider?: string;
  /** ISO-8601 time the limit is expected to reset. */
  resetsAt?: string;
}

export interface RateLimitBannerProps {
  status: RateLimitState;
}

/** Surfaces free-tier rate-limit throttling; renders nothing when clear. */
export function RateLimitBanner({ status }: RateLimitBannerProps) {
  if (!status.throttled) {
    return null;
  }
  const who = status.provider ? `${status.provider} ` : "";
  return (
    <div
      role="alert"
      className="panel"
      style={{ borderColor: "var(--warn)", color: "var(--warn)" }}
    >
      ⏳ {who}free-tier rate limit reached — requests are being throttled
      {status.resetsAt ? `; resets at ${status.resetsAt}` : ""}.
    </div>
  );
}

export default RateLimitBanner;
