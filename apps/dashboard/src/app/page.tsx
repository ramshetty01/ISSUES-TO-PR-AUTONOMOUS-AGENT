import Link from "next/link";

export default function HomePage() {
  return (
    <div className="grid">
      <section className="panel">
        <h1>Dashboard</h1>
        <p className="muted">
          Local view over runs, budgets, and safety events. Data is served by the
          dispatcher/ledger API on localhost.
        </p>
      </section>
      <nav className="panel grid">
        <Link href="/budgets">Budgets →</Link>
        <span className="muted">Runs and repo pages are linked from there.</span>
      </nav>
    </div>
  );
}
