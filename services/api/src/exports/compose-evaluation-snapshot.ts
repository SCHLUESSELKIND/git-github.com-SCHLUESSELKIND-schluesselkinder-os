import type { GenerationOutputEvaluationRecord } from "../repositories.js";
import { manualExportSurfaceBoundary, type EvaluationSnapshot } from "./types.js";

export function composeEvaluationSnapshot(evaluations: GenerationOutputEvaluationRecord[]): EvaluationSnapshot {
  const verdicts = evaluations.map((evaluation) => evaluation.verdict);
  const dominantVerdict =
    verdicts.includes("FAIL") ? "FAIL" : verdicts.includes("WARNING") ? "WARNING" : verdicts.includes("PASS") ? "PASS" : "NOT_EVALUATED";

  return {
    ...manualExportSurfaceBoundary,
    dominantVerdict,
    findings: evaluations.map((evaluation) => ({
      ...manualExportSurfaceBoundary,
      detail: evaluation.detail,
      ruleCode: evaluation.ruleCode,
      source: evaluation.source,
      title: evaluation.title,
      verdict: evaluation.verdict
    })),
    passImpliesApproval: false,
    snapshotImpliesTruth: false,
    verdicts
  };
}
