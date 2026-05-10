import { forbiddenEnergyOperationalTerms } from "../detect-forbidden-energy.js";
import type { CompatibilityVerdict, EvaluationInput, EvaluationSource } from "../types.js";

export type RuleConflictSeverity = "BLOCKER" | "WARNING" | "INFO";

export type RuleConflict = Readonly<{
  code: string;
  detail: string;
  referenceKey: string;
  severity: RuleConflictSeverity;
  source: EvaluationSource;
}>;

export function detectRuleConflicts(input: EvaluationInput): RuleConflict[] {
  return [
    ...detectCompatibilityConflicts(input),
    ...detectUnresolvedConstraintReferences(input),
    ...detectUncoveredForbiddenEnergy(input),
    ...detectMissingScoringRules(input)
  ];
}

function detectCompatibilityConflicts(input: EvaluationInput): RuleConflict[] {
  const grouped = new Map<string, Set<CompatibilityVerdict>>();

  for (const record of input.compatibility) {
    const key = `${record.kind}:${record.sourceCode}->${record.targetCode}`;
    grouped.set(key, (grouped.get(key) ?? new Set<CompatibilityVerdict>()).add(record.verdict));
  }

  return [...grouped.entries()].flatMap<RuleConflict>(([referenceKey, verdicts]) => {
    if (verdicts.has("REQUIRED") && verdicts.has("FORBIDDEN")) {
      return [
        {
          code: "COMPATIBILITY_REQUIRED_AND_FORBIDDEN",
          detail: `${referenceKey} is marked REQUIRED and FORBIDDEN.`,
          referenceKey,
          severity: "BLOCKER" as const,
          source: "CONTENT_GRAPH_COMPATIBILITY" as const
        }
      ];
    }

    if (verdicts.has("REQUIRED") && verdicts.has("DISCOURAGED")) {
      return [
        {
          code: "COMPATIBILITY_REQUIRED_AND_DISCOURAGED",
          detail: `${referenceKey} is marked REQUIRED and DISCOURAGED.`,
          referenceKey,
          severity: "WARNING" as const,
          source: "CONTENT_GRAPH_COMPATIBILITY" as const
        }
      ];
    }

    return [];
  });
}

function detectUnresolvedConstraintReferences(input: EvaluationInput): RuleConflict[] {
  if (!input.constraintBundle) {
    return [
      {
        code: "CONFLICT_CHECK_CONSTRAINT_BUNDLE_MISSING",
        detail: "No constraint bundle is available for conflict detection.",
        referenceKey: input.subject.key,
        severity: "BLOCKER",
        source: "REVIEW_GOVERNANCE"
      }
    ];
  }

  const knownRuleCodes = new Set([
    ...input.rules.map((rule) => rule.code),
    ...input.forbiddenEnergy.map((energy) => energy.code),
    ...input.scoringRules.map((rule) => rule.code)
  ]);

  return input.constraintBundle.constraints
    .filter((constraint) => constraint.active && constraint.required && constraint.ruleCode && !knownRuleCodes.has(constraint.ruleCode))
    .map((constraint) => ({
      code: "CONSTRAINT_REFERENCES_MISSING_RULE",
      detail: `Constraint ${constraint.title} references missing ruleCode ${constraint.ruleCode}.`,
      referenceKey: `${input.constraintBundle?.code}:${constraint.title}`,
      severity: "WARNING" as const,
      source: constraint.source
    }));
}

function detectUncoveredForbiddenEnergy(input: EvaluationInput): RuleConflict[] {
  return input.forbiddenEnergy
    .filter((energy) => (forbiddenEnergyOperationalTerms[energy.code] ?? []).length === 0)
    .map((energy) => ({
      code: "FORBIDDEN_ENERGY_WITHOUT_OPERATIONAL_TERMS",
      detail: `Forbidden energy ${energy.code} has no deterministic detector terms.`,
      referenceKey: energy.code,
      severity: "WARNING" as const,
      source: "FORBIDDEN_ENERGY" as const
    }));
}

function detectMissingScoringRules(input: EvaluationInput): RuleConflict[] {
  if (input.scoringRules.length > 0) {
    return [];
  }

  return [
    {
      code: "SCORING_RULES_MISSING",
      detail: "No scoring rules are available; score calibration would use fallback baselines.",
      referenceKey: input.subject.key,
      severity: "WARNING",
      source: "SIGNAL_SCORING_RULE"
    }
  ];
}
