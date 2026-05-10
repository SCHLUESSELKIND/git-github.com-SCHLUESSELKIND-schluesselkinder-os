import { computeSignalScore } from "./compute-signal-score.js";
import { detectForbiddenEnergy } from "./detect-forbidden-energy.js";
import { resolveConstraints } from "./resolve-constraints.js";
import { validateGraphCompatibility } from "./validate-graph-compatibility.js";
import type {
  EvaluationFinding,
  EvaluationInput,
  EvaluationReport,
  EvaluationTextInput,
  EvaluationVerdict,
  RuleInput
} from "./types.js";

export function evaluateGenerationOutput(input: EvaluationInput): EvaluationReport {
  return evaluate(input);
}

export function evaluateGenerationBrief(input: EvaluationInput): EvaluationReport {
  return evaluate(input);
}

export function createEvaluationTextInput(body: string[]): EvaluationTextInput {
  return {
    body,
    detectedAssetCodes: detectAssetCodes(body.join(" "))
  };
}

function evaluate(input: EvaluationInput): EvaluationReport {
  const rules = constraintsAsRules(input);
  const resolved = resolveConstraints({
    bundle: input.constraintBundle,
    rules,
    scoringRules: input.scoringRules
  });
  const forbiddenFindings = detectForbiddenEnergy({
    forbiddenEnergy: input.forbiddenEnergy,
    text: input.text
  });
  const graph = validateGraphCompatibility(input);
  const governanceFindings = validateReviewBinding(input);
  const findings = [...resolved.findings, ...forbiddenFindings, ...graph.findings, ...governanceFindings];
  const score = computeSignalScore(findings, input.scoringRules);
  const verdict = verdictFromFindings(findings);

  return {
    approvalAuthority: false,
    findings,
    graphChecks: graph.checks,
    reportKey: `EV-${input.subject.key}`,
    resolvedConstraints: resolved.constraints,
    reviewRequired: true,
    score,
    subject: input.subject,
    usableWithoutReview: false,
    verdict,
    verdictMeaning: verdictMeaning(verdict)
  };
}

function constraintsAsRules(input: EvaluationInput): RuleInput[] {
  return [
    ...input.rules,
    ...input.forbiddenEnergy.map((energy) => ({
      code: energy.code,
      severity: energy.severity,
      text: energy.reason,
      title: energy.label,
      weight: energy.weight
    }))
  ];
}

function validateReviewBinding(input: EvaluationInput): EvaluationFinding[] {
  if (!input.reviewBinding) {
    return [
      {
        code: "REVIEW_BINDING_MISSING",
        detail: `${input.subject.type} ${input.subject.key} is not bound to a ReviewItem.`,
        ruleCode: "REVIEW_BINDING_REQUIRED",
        severity: "BLOCKER",
        source: "REVIEW_GOVERNANCE",
        title: "Review binding missing"
      }
    ];
  }

  return [];
}

function verdictFromFindings(findings: EvaluationFinding[]): EvaluationVerdict {
  if (findings.some((finding) => finding.severity === "BLOCKER")) {
    return "FAIL";
  }

  if (findings.some((finding) => finding.severity === "WARNING")) {
    return "WARNING";
  }

  return "PASS";
}

function verdictMeaning(verdict: EvaluationVerdict): string {
  if (verdict === "FAIL") {
    return "Blocked before approval review. No verdict equals approval.";
  }

  if (verdict === "WARNING") {
    return "Non-blocking concerns found. Human review is still required. No verdict equals approval.";
  }

  return "No blocking findings. Human review is still required. No verdict equals approval.";
}

function detectAssetCodes(text: string): string[] {
  const normalized = text.toLowerCase();
  const matches = new Set<string>();

  if (normalized.includes("chair") || normalized.includes("dungeon") || normalized.includes("room_after_light")) {
    matches.add("CHAIR_CAMPAIGN_ENVIRONMENT");
  }

  if (normalized.includes("rune/key") || normalized.includes("rune") || normalized.includes("key symbol")) {
    matches.add("RUNE_KEY_SYMBOL");
  }

  if (normalized.includes("ropeface")) {
    matches.add("ROPEFACE_ARTIST_STAMP");
  }

  return [...matches];
}
