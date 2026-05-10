import type {
  EvaluationAxis,
  EvaluationFinding,
  EvaluationFindingSeverity,
  EvaluationReport,
  EvaluationSource
} from "../types.js";

export type EvaluationExplanation = Readonly<{
  approvalAuthority: false;
  degradedAxes: EvaluationAxis[];
  dominantFinding: EvaluationFinding | null;
  dominantRule: string | null;
  graphCompatibilitySummary: string[];
  reviewRequired: true;
  scoreBreakdown: Record<EvaluationAxis, number>;
  usableWithoutReview: false;
  verdictReason: string;
}>;

const severityRank: Record<EvaluationFindingSeverity, number> = {
  BLOCKER: 3,
  WARNING: 2,
  INFO: 1
};

const sourceRank: Record<EvaluationSource, number> = {
  FORBIDDEN_ENERGY: 8,
  CONTENT_GRAPH_COMPATIBILITY: 7,
  REVIEW_GOVERNANCE: 6,
  BRAND_RULE: 5,
  VISUAL_RULE: 5,
  LANGUAGE_RULE: 5,
  CHANNEL_RULE: 4,
  SIGNAL_SCORING_RULE: 3,
  MANUAL: 1
};

export function explainEvaluationReport(report: EvaluationReport): EvaluationExplanation {
  const dominantFinding = findDominantFinding(report.findings);
  const scoreBreakdown = Object.fromEntries(
    report.score.axes.map((axis) => [axis.axis, axis.score])
  ) as Record<EvaluationAxis, number>;

  return {
    approvalAuthority: false,
    degradedAxes: report.score.axes.filter((axis) => axis.score < axis.maxScore).map((axis) => axis.axis),
    dominantFinding,
    dominantRule: dominantFinding?.ruleCode ?? null,
    graphCompatibilitySummary: report.graphChecks.map(
      (check) => `${check.kind}:${check.sourceCode}->${check.targetCode}:${check.verdict}`
    ),
    reviewRequired: true,
    scoreBreakdown,
    usableWithoutReview: false,
    verdictReason: buildVerdictReason(report, dominantFinding)
  };
}

function findDominantFinding(findings: readonly EvaluationFinding[]): EvaluationFinding | null {
  const [dominant] = [...findings].sort((left, right) => {
    const severityDelta = severityRank[right.severity] - severityRank[left.severity];

    if (severityDelta !== 0) {
      return severityDelta;
    }

    const sourceDelta = sourceRank[right.source] - sourceRank[left.source];

    if (sourceDelta !== 0) {
      return sourceDelta;
    }

    return left.code.localeCompare(right.code);
  });

  return dominant ?? null;
}

function buildVerdictReason(report: EvaluationReport, dominantFinding: EvaluationFinding | null): string {
  if (!dominantFinding) {
    return `${report.verdict}: no findings detected. Human review remains required.`;
  }

  return `${report.verdict}: dominant finding ${dominantFinding.code} from ${dominantFinding.source}. Human review remains required.`;
}
