import type {
  EvaluationFinding,
  EvaluationReport,
  GraphCompatibilityCheck,
  ResolvedConstraint
} from "../_lib/api";

export function VerdictPanel({ report }: Readonly<{ report: EvaluationReport }>) {
  const tone = report.verdict === "FAIL" ? "border-red-950 text-red-300" : report.verdict === "WARNING" ? "border-stone-600 text-stone-200" : "border-stone-800 text-stone-300";

  return (
    <section className={`border ${tone} bg-black/30 p-5`}>
      <div className="grid gap-6 md:grid-cols-[0.32fr_1fr]">
        <div>
          <p className="text-[0.68rem] font-black uppercase text-stone-500">verdict</p>
          <p className="mt-3 text-5xl font-black uppercase leading-none">{report.verdict}</p>
        </div>
        <div className="space-y-4">
          <p className="max-w-3xl text-sm leading-7 text-stone-300">{report.verdictMeaning}</p>
          <div className="grid gap-2 font-mono text-xs uppercase text-stone-500 md:grid-cols-3">
            <span>reviewRequired: {String(report.reviewRequired)}</span>
            <span>usableWithoutReview: {String(report.usableWithoutReview)}</span>
            <span>approvalAuthority: {String(report.approvalAuthority)}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export function FindingList({ findings }: Readonly<{ findings: EvaluationFinding[] }>) {
  return (
    <section className="border border-stone-800 bg-black/30">
      <PanelHeader label="findings" count={findings.length} />
      {findings.length === 0 ? (
        <p className="p-4 font-mono text-xs uppercase text-stone-500">no blocking findings in this report; review still required.</p>
      ) : (
        <div className="divide-y divide-stone-900">
          {findings.map((finding) => (
            <div className="grid gap-3 p-4 md:grid-cols-[0.2fr_0.2fr_1fr]" key={`${finding.code}-${finding.ruleCode}`}>
              <p className="font-mono text-xs uppercase text-stone-400">{finding.severity}</p>
              <p className="font-mono text-xs uppercase text-stone-500">{finding.source}</p>
              <div>
                <p className="text-sm font-black uppercase text-stone-200">{finding.title}</p>
                <p className="mt-2 font-mono text-xs leading-6 text-stone-400">{finding.detail}</p>
                <p className="mt-2 font-mono text-[0.68rem] uppercase text-stone-600">{finding.ruleCode ?? "no ruleCode"}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export function ConstraintTable({ constraints }: Readonly<{ constraints: ResolvedConstraint[] }>) {
  return (
    <section className="border border-stone-800 bg-black/30">
      <PanelHeader label="resolved constraints" count={constraints.length} />
      <div className="divide-y divide-stone-900">
        {constraints.map((constraint) => (
          <div className="grid gap-3 p-4 md:grid-cols-[0.18fr_0.18fr_1fr_0.12fr]" key={`${constraint.source}-${constraint.ruleCode}-${constraint.title}`}>
            <p className="font-mono text-xs uppercase text-stone-500">{constraint.source}</p>
            <p className="font-mono text-xs uppercase text-stone-500">{constraint.required ? "required" : "optional"}</p>
            <div>
              <p className="text-sm font-black uppercase text-stone-200">{constraint.title}</p>
              <p className="mt-2 font-mono text-xs leading-6 text-stone-400">{constraint.instruction}</p>
            </div>
            <p className="font-mono text-xs uppercase text-stone-500">w:{constraint.weight}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function GraphCheckTable({ checks }: Readonly<{ checks: GraphCompatibilityCheck[] }>) {
  return (
    <section className="border border-stone-800 bg-black/30">
      <PanelHeader label="graph checks" count={checks.length} />
      <div className="divide-y divide-stone-900">
        {checks.map((check) => (
          <div className="grid gap-3 p-4 md:grid-cols-[0.22fr_0.2fr_1fr_0.12fr]" key={`${check.kind}-${check.sourceCode}-${check.targetCode}`}>
            <p className="font-mono text-xs uppercase text-stone-500">{check.kind}</p>
            <p className="font-mono text-xs uppercase text-stone-300">{check.verdict}</p>
            <div>
              <p className="font-mono text-xs uppercase text-stone-400">
                {check.sourceCode} -&gt; {check.targetCode}
              </p>
              <p className="mt-2 font-mono text-xs leading-6 text-stone-500">{check.reason ?? check.detail}</p>
            </div>
            <p className="font-mono text-xs uppercase text-stone-500">w:{check.weight}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function ScoreAxisList({ report }: Readonly<{ report: EvaluationReport }>) {
  return (
    <section className="border border-stone-800 bg-black/30">
      <PanelHeader label={`score / ${report.score.grade}`} count={report.score.axes.length} />
      <div className="divide-y divide-stone-900">
        {report.score.axes.map((axis) => (
          <div className="grid gap-3 p-4 md:grid-cols-[0.42fr_1fr_0.12fr]" key={axis.axis}>
            <p className="font-mono text-xs uppercase text-stone-400">{axis.axis}</p>
            <div className="h-1 self-center bg-stone-900">
              <div
                className="h-1 bg-stone-500"
                style={{ width: `${Math.max(0, Math.min(100, (axis.score / axis.maxScore) * 100))}%` }}
              />
            </div>
            <p className="font-mono text-xs uppercase text-stone-500">
              {axis.score}/{axis.maxScore}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function RawJsonBlock({ data }: Readonly<{ data: unknown }>) {
  return (
    <details className="border border-stone-800 bg-black/30">
      <summary className="cursor-pointer px-4 py-3 text-xs font-black uppercase text-stone-500">
        raw json
      </summary>
      <pre className="max-h-[42rem] overflow-auto border-t border-stone-900 p-4 text-xs leading-6 text-stone-400">
        {JSON.stringify(data, null, 2)}
      </pre>
    </details>
  );
}

function PanelHeader({ count, label }: Readonly<{ count: number; label: string }>) {
  return (
    <div className="flex items-center justify-between border-b border-stone-800 px-4 py-3">
      <p className="text-xs font-black uppercase text-stone-500">{label}</p>
      <p className="font-mono text-xs text-stone-600">{count}</p>
    </div>
  );
}
