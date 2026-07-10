/** Dispatcher-side budget errors. */
export { BudgetExceeded, LedgerUnavailable } from "@itpr/budget-ledger";

/** Raised when budget cannot be evaluated (ledger + fallback both failed). */
export class BudgetCheckFailed extends Error {
  constructor(cause?: unknown) {
    super("budget check failed");
    this.name = "BudgetCheckFailed";
    if (cause !== undefined) this.cause = cause;
  }
}
