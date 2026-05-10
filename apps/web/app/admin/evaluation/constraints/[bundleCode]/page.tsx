import { ConsoleReadError, ConsoleShell, ConsoleUnavailable } from "../../_components/ConsoleShell";
import { ConstraintTable, FindingList, RawJsonBlock } from "../../_components/ReportPanels";
import { fetchConstraintBundle, isInternalConsoleEnabled } from "../../_lib/api";

export const dynamic = "force-dynamic";

export default async function EvaluationConstraintPage({
  params
}: Readonly<{
  params: Promise<{ bundleCode: string }>;
}>) {
  if (!isInternalConsoleEnabled()) {
    return <ConsoleUnavailable />;
  }

  const { bundleCode } = await params;

  try {
    const report = await fetchConstraintBundle(bundleCode);

    return (
      <ConsoleShell eyebrow="INTERNAL / CONSTRAINT TRACE" title={report.bundle.code}>
        <div className="grid gap-8">
          <section className="border border-stone-800 bg-black/30 p-5">
            <p className="text-xs font-black uppercase text-stone-500">bundle</p>
            <h2 className="mt-4 text-3xl font-black uppercase text-stone-100">{report.bundle.name}</h2>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-stone-400">{report.bundle.description}</p>
            <div className="mt-6 grid gap-2 font-mono text-xs uppercase text-stone-500 md:grid-cols-3">
              <span>reviewRequired: {String(report.reviewRequired)}</span>
              <span>usableWithoutReview: {String(report.usableWithoutReview)}</span>
              <span>approvalAuthority: {String(report.approvalAuthority)}</span>
            </div>
          </section>
          <FindingList findings={report.findings} />
          <ConstraintTable constraints={report.resolvedConstraints} />
          <RawJsonBlock data={report} />
        </div>
      </ConsoleShell>
    );
  } catch (error) {
    return <ConsoleReadError message={error instanceof Error ? error.message : "unknown read failure"} />;
  }
}
