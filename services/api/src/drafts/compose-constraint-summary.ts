import type { ConstraintBundleRecord, GenerationBriefRecord } from "../repositories.js";
import type { DraftConstraintSummary } from "./types.js";

export function composeConstraintSummary(input: {
  brief: GenerationBriefRecord;
  constraintBundle: ConstraintBundleRecord | null;
}): DraftConstraintSummary {
  const constraints = input.constraintBundle?.constraints ?? [];

  return {
    bundleCode: input.brief.constraintBundle.code,
    bundleName: input.brief.constraintBundle.name,
    constraints: constraints.map((constraint) => ({
      instruction: constraint.instruction,
      required: constraint.required,
      ruleCode: constraint.ruleCode,
      source: constraint.source,
      title: constraint.title,
      weight: constraint.weight
    })),
    requiredCount: constraints.filter((constraint) => constraint.required).length
  };
}
