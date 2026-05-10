import type { EvaluationHealth } from "../_lib/api";

export function BoundaryStatus({ health }: Readonly<{ health: EvaluationHealth }>) {
  const rows = [
    ["review required", health.reviewRequired],
    ["usable without review", health.usableWithoutReview],
    ["approval authority", health.approvalAuthority],
    ["db mutation", health.dbMutation],
    ["write routes", health.writeRoutes],
    ["provider integration", health.providerIntegration],
    ["execution", health.execution]
  ] as const;

  return (
    <section className="border border-stone-800 bg-black/30">
      <div className="border-b border-stone-800 px-4 py-3 text-xs font-black uppercase text-stone-500">
        boundary status
      </div>
      <div className="grid md:grid-cols-2">
        {rows.map(([label, value]) => (
          <div className="flex items-center justify-between border-b border-stone-900 px-4 py-3 last:border-b-0 md:odd:border-r" key={label}>
            <span className="font-mono text-xs uppercase text-stone-500">{label}</span>
            <span className="font-mono text-xs uppercase text-stone-200">{String(value)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
