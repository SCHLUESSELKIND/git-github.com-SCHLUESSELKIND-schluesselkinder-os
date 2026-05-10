import { ConsoleReadError, ConsoleShell, ConsoleUnavailable } from "../../_components/ConsoleShell";
import {
  ConstraintTable,
  FindingList,
  GraphCheckTable,
  RawJsonBlock,
  ScoreAxisList,
  VerdictPanel
} from "../../_components/ReportPanels";
import { fetchEvaluationOutput, isInternalConsoleEnabled } from "../../_lib/api";

export const dynamic = "force-dynamic";

export default async function EvaluationOutputPage({
  params
}: Readonly<{
  params: Promise<{ outputKey: string }>;
}>) {
  if (!isInternalConsoleEnabled()) {
    return <ConsoleUnavailable />;
  }

  const { outputKey } = await params;

  try {
    const report = await fetchEvaluationOutput(outputKey);

    return (
      <ConsoleShell eyebrow="INTERNAL / OUTPUT TRACE" title={report.subject.key}>
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
