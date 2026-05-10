import { ConsoleReadError, ConsoleShell, ConsoleUnavailable } from "../../_components/ConsoleShell";
import {
  ConstraintTable,
  FindingList,
  GraphCheckTable,
  RawJsonBlock,
  ScoreAxisList,
  VerdictPanel
} from "../../_components/ReportPanels";
import { fetchEvaluationBrief, isInternalConsoleEnabled } from "../../_lib/api";

export const dynamic = "force-dynamic";

export default async function EvaluationBriefPage({
  params
}: Readonly<{
  params: Promise<{ briefKey: string }>;
}>) {
  if (!isInternalConsoleEnabled()) {
    return <ConsoleUnavailable />;
  }

  const { briefKey } = await params;

  try {
    const report = await fetchEvaluationBrief(briefKey);

    return (
      <ConsoleShell eyebrow="INTERNAL / BRIEF TRACE" title={report.subject.key}>
        <div className="grid gap-8">
          <VerdictPanel report={report} />
          <FindingList findings={report.findings} />
          <ScoreAxisList report={report} />
          <ConstraintTable constraints={report.resolvedConstraints} />
          <GraphCheckTable checks={report.graphChecks} />
          <RawJsonBlock data={report} />
        </div>
      </ConsoleShell>
    );
  } catch (error) {
    return <ConsoleReadError message={error instanceof Error ? error.message : "unknown read failure"} />;
  }
}
