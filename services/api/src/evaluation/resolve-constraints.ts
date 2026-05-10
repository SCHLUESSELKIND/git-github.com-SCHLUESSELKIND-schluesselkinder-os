import type {
  ConstraintBundleInput,
  EvaluationFinding,
  ResolvedConstraint,
  RuleInput,
  ScoringRuleInput
} from "./types.js";

type ResolveConstraintsInput = Readonly<{
  bundle: ConstraintBundleInput | null;
  rules: RuleInput[];
  scoringRules: ScoringRuleInput[];
}>;

type ResolveConstraintsResult = Readonly<{
  constraints: ResolvedConstraint[];
  findings: EvaluationFinding[];
}>;

export function resolveConstraints(input: ResolveConstraintsInput): ResolveConstraintsResult {
  if (!input.bundle) {
    return {
      constraints: [],
      findings: [
        {
          code: "CONSTRAINT_BUNDLE_MISSING",
          detail: "No active constraint bundle is available for this evaluation subject.",
          ruleCode: null,
          severity: "BLOCKER",
          source: "REVIEW_GOVERNANCE",
          title: "Constraint bundle missing"
        }
      ]
    };
  }

  const activeConstraints = input.bundle.constraints.filter((constraint) => constraint.active);
  const knownRuleCodes = new Set([
    ...input.rules.map((rule) => rule.code),
    ...input.scoringRules.map((rule) => rule.code)
  ]);

  return {
    constraints: activeConstraints,
    findings: activeConstraints
      .filter((constraint) => constraint.required && constraint.ruleCode && !knownRuleCodes.has(constraint.ruleCode))
      .map((constraint) => ({
        code: "CONSTRAINT_RULE_UNRESOLVED",
        detail: `Required constraint ${constraint.title} references ruleCode ${constraint.ruleCode}, but no active rule record was resolved.`,
        ruleCode: constraint.ruleCode,
        severity: "WARNING" as const,
        source: constraint.source,
        title: "Constraint rule unresolved"
      }))
  };
}
