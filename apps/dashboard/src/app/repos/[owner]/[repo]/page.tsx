export default function RepoPage({
  params,
}: {
  params: { owner: string; repo: string };
}) {
  return (
    <div className="grid">
      <h1>
        {params.owner}/{params.repo}
      </h1>
      <p className="muted">Budget and spend ledger for this repository.</p>
    </div>
  );
}
