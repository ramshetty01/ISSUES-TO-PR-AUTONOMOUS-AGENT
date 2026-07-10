/** Budget ledger error taxonomy. */

/** Raised when a spend/reservation would exceed the repo's budget window. */
export class BudgetExceeded extends Error {
  constructor(
    public readonly detail: {
      kind: "tokens" | "dollars";
      cap: number;
      spent: number;
      requested: number;
    },
  ) {
    super(
      `Budget exceeded (${detail.kind}): cap=${detail.cap} spent=${detail.spent} requested=${detail.requested}`,
    );
    this.name = "BudgetExceeded";
  }
}

/** Raised when the primary (DynamoDB) backend is unreachable. */
export class LedgerUnavailable extends Error {
  constructor(cause?: unknown) {
    super("Budget ledger backend unavailable");
    this.name = "LedgerUnavailable";
    if (cause !== undefined) this.cause = cause;
  }
}
