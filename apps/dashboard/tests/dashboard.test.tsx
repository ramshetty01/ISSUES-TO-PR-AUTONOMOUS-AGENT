import type {
  BudgetWindow,
  LedgerEntry,
  Refusal,
  SafetyEvent,
  TimelineEvent,
} from "@itpr/shared-types";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BudgetCard } from "../src/components/BudgetCard.js";
import { CostChart } from "../src/components/CostChart.js";
import { RateLimitBanner } from "../src/components/RateLimitBanner.js";
import { RepoBudgetTable } from "../src/components/RepoBudgetTable.js";
import { RunTimeline } from "../src/components/RunTimeline.js";
import { SafetyEvents } from "../src/components/SafetyEvents.js";
import { TraceViewer, resolveTraceHref } from "../src/components/TraceViewer.js";

const budget: BudgetWindow = {
  repo: { owner: "acme", name: "widgets" },
  periodStart: "2026-01-01T00:00:00Z",
  periodEnd: "2026-01-02T00:00:00Z",
  tokenCap: 100_000,
  dollarCap: 5,
  tokensSpent: 90_000,
  dollarsSpent: 4.5,
};

const events: TimelineEvent[] = [
  { at: "2026-01-01T00:00:00Z", kind: "plan", message: "Planned the fix" },
  { at: "2026-01-01T00:01:00Z", kind: "pr_opened", message: "Opened PR #12" },
];

const ledger: LedgerEntry[] = [
  {
    id: "e1",
    repo: { owner: "acme", name: "widgets" },
    runId: "r1",
    provider: "groq",
    tokens: { input: 100, output: 50, total: 150 },
    dollars: 0,
    at: "2026-01-01T00:00:00Z",
  },
];

describe("RunTimeline", () => {
  it("renders events from typed props", () => {
    render(<RunTimeline events={events} />);
    expect(screen.getByText("Opened PR #12")).toBeInTheDocument();
  });
  it("handles empty", () => {
    render(<RunTimeline events={[]} />);
    expect(screen.getByText(/no timeline events/i)).toBeInTheDocument();
  });
});

describe("BudgetCard + RepoBudgetTable", () => {
  it("renders a budget card with the repo and a meter", () => {
    render(<BudgetCard budget={budget} />);
    expect(screen.getByText("acme/widgets")).toBeInTheDocument();
    expect(screen.getAllByRole("meter").length).toBe(2);
  });
  it("renders a table row linking to the repo page", () => {
    render(<RepoBudgetTable budgets={[budget]} />);
    const link = screen.getByRole("link", { name: "acme/widgets" });
    expect(link).toHaveAttribute("href", "/repos/acme/widgets");
  });
});

describe("CostChart", () => {
  it("renders a bar per provider", () => {
    render(<CostChart entries={ledger} />);
    expect(screen.getByRole("img", { name: /cost by provider/i })).toBeInTheDocument();
    expect(screen.getByText("groq")).toBeInTheDocument();
  });
});

describe("TraceViewer", () => {
  it("uses an explicit traceUrl", () => {
    render(<TraceViewer traceUrl="http://localhost:3000/trace/r1" />);
    expect(screen.getByRole("link", { name: /langfuse trace/i })).toHaveAttribute(
      "href",
      "http://localhost:3000/trace/r1",
    );
  });
  it("builds the href from host + id", () => {
    expect(
      resolveTraceHref({ traceId: "r1", langfuseHost: "http://localhost:3000/" }),
    ).toBe("http://localhost:3000/trace/r1");
  });
  it("shows a fallback when nothing links", () => {
    render(<TraceViewer />);
    expect(screen.getByText(/no trace recorded/i)).toBeInTheDocument();
  });
});

describe("RateLimitBanner reflects throttle state", () => {
  it("renders nothing when not throttled", () => {
    const { container } = render(<RateLimitBanner status={{ throttled: false }} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("alerts when throttled", () => {
    render(<RateLimitBanner status={{ throttled: true, provider: "groq" }} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/groq.*rate limit/i);
  });
});

describe("SafetyEvents", () => {
  const safetyEvents: SafetyEvent[] = [
    { at: "2026-01-01T00:00:00Z", reason: "secret_detected", message: "blocked a token" },
  ];
  it("renders events and a pinned refusal", () => {
    const refusal: Refusal = { reason: "forbidden_path", message: "cannot touch .github" };
    render(<SafetyEvents events={safetyEvents} refusal={refusal} />);
    expect(screen.getByText(/refused: forbidden_path/i)).toBeInTheDocument();
    expect(screen.getByText(/blocked a token/i)).toBeInTheDocument();
  });
  it("renders a clean-run message", () => {
    render(<SafetyEvents events={[]} />);
    expect(screen.getByText(/clean run/i)).toBeInTheDocument();
  });
});
