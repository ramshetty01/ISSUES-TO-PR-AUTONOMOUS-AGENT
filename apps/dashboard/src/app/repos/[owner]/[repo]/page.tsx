import { BudgetCard } from "../../../../components/BudgetCard.js";
import { CostChart } from "../../../../components/CostChart.js";
import { api } from "../../../../lib/api.js";

/** Per-repo view: budget window + spend ledger. */
export default async function RepoPage({
  params,
}: {
  params: { owner: string; repo: string };
}) {
  const [budget, ledger] = await Promise.all([
    api.getRepoBudget(params.owner, params.repo),
    api.listRepoLedger(params.owner, params.repo),
  ]);
  return (
    <div className="grid">
      <h1>
        {params.owner}/{params.repo}
      </h1>
      <BudgetCard budget={budget} />
      <section className="panel grid">
        <h2>Spend by provider</h2>
        <CostChart entries={ledger} />
      </section>
    </div>
  );
}
