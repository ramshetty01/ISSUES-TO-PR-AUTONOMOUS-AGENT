/**
 * Budget gate: before dispatching a job, estimate its cost and atomically
 * check-and-reserve against the per-repo budget window. Over-budget jobs are
 * refused before any worker is spawned.
 */
import type { Job, BudgetVerdict } from "@itpr/shared-types";
import {
  resolveCaps,
  type Ledger,
  type BudgetDefaults,
  type SpendEstimate,
} from "@itpr/budget-ledger";
import { estimateJobCost, type EstimatorOptions } from "./cost-estimator.js";

export interface BudgetServiceOptions {
  ledger: Ledger;
  defaults: BudgetDefaults;
  estimator?: EstimatorOptions;
  now?: () => Date;
}

export class BudgetService {
  constructor(private readonly opts: BudgetServiceOptions) {}

  /** Estimate + reserve. Returns the verdict; allowed=false means do not dispatch. */
  async checkAndReserve(job: Job): Promise<BudgetVerdict> {
    const est = estimateJobCost(job, this.opts.estimator);
    const caps = resolveCaps(job.repo, this.opts.defaults);
    const estimate: SpendEstimate = {
      id: `reserve:${job.id}`,
      runId: job.id,
      provider: "estimate",
      tokens: est.tokens,
      dollars: est.dollars,
    };
    return this.opts.ledger.checkAndReserve(
      job.repo,
      estimate,
      caps,
      this.opts.now ? this.opts.now() : undefined,
    );
  }
}
