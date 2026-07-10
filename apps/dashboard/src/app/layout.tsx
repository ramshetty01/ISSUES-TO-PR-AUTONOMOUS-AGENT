import type { Metadata } from "next";
import type { ReactNode } from "react";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "issue-to-PR agent — dashboard",
  description: "Runs, budgets, and safety events for the issue-to-PR agent.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="container">
          <strong>issue-to-PR agent</strong>{" "}
          <span className="muted">· dashboard</span>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
