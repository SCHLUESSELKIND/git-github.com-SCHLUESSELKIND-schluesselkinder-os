import type {
  EvaluationAxis,
  EvaluationAxisScore,
  EvaluationFinding,
  EvaluationGrade,
  ScoringRuleInput,
  SignalScore
} from "./types.js";

const axes: EvaluationAxis[] = [
  "IDENTITY_PROTECTION",
  "SYMBOLIC_RESTRAINT",
  "INSTITUTIONAL_CONSISTENCY",
  "CULTURAL_CREDIBILITY",
  "PRESSURE_WITHOUT_NOISE",
  "ARCHIVE_COHERENCE",
  "RULE_ADHERENCE",
  "REVIEW_READINESS"
];

export function computeSignalScore(findings: EvaluationFinding[], scoringRules: ScoringRuleInput[]): SignalScore {
  const axisScores = axes.map((axis) => scoreAxis(axis, findings, scoringRules));
  const total = axisScores.reduce((sum, axis) => sum + axis.score, 0);
  const max = axisScores.reduce((sum, axis) => sum + axis.maxScore, 0);
  const normalized = max === 0 ? 0 : Math.round((total / max) * 100);

  return {
    axes: axisScores,
    grade: gradeScore(normalized, findings),
    max,
    normalized,
    total
  };
}

function scoreAxis(axis: EvaluationAxis, findings: EvaluationFinding[], scoringRules: ScoringRuleInput[]): EvaluationAxisScore {
  const activeRuleWeight = scoringRules.reduce((sum, rule) => sum + Math.max(rule.weight, 0), 0);
  const maxScore = 10;
  const baseline = activeRuleWeight > 0 ? 10 : 8;
  const penalty = findings
    .filter((finding) => affectsAxis(finding, axis))
    .reduce((sum, finding) => sum + findingPenalty(finding), 0);

  return {
    axis,
    maxScore,
    score: Math.max(0, baseline - penalty)
  };
}

function affectsAxis(finding: EvaluationFinding, axis: EvaluationAxis): boolean {
  if (finding.source === "FORBIDDEN_ENERGY") {
    return ["IDENTITY_PROTECTION", "CULTURAL_CREDIBILITY", "PRESSURE_WITHOUT_NOISE", "RULE_ADHERENCE"].includes(axis);
  }

  if (finding.source === "CONTENT_GRAPH_COMPATIBILITY") {
    return ["SYMBOLIC_RESTRAINT", "ARCHIVE_COHERENCE", "RULE_ADHERENCE"].includes(axis);
  }

  if (finding.source === "REVIEW_GOVERNANCE") {
    return axis === "REVIEW_READINESS" || axis === "RULE_ADHERENCE";
  }

  if (finding.source === "LANGUAGE_RULE") {
    return axis === "INSTITUTIONAL_CONSISTENCY" || axis === "PRESSURE_WITHOUT_NOISE";
  }

  if (finding.source === "VISUAL_RULE") {
    return axis === "SYMBOLIC_RESTRAINT" || axis === "ARCHIVE_COHERENCE";
  }

  return axis === "RULE_ADHERENCE";
}

function findingPenalty(finding: EvaluationFinding): number {
  if (finding.severity === "BLOCKER") {
    return 6;
  }

  if (finding.severity === "WARNING") {
    return 2;
  }

  return 0;
}

function gradeScore(normalized: number, findings: EvaluationFinding[]): EvaluationGrade {
  if (findings.some((finding) => finding.severity === "BLOCKER")) {
    return "BLOCKED";
  }

  if (normalized < 60) {
    return "WEAK";
  }

  if (normalized < 85) {
    return "VIABLE";
  }

  return "STRONG";
}
