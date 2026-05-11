import type {
  CompatibilityRecord,
  ConstraintBundleRecord,
  GenerationBriefRecord,
  GenerationOutputEvaluationRecord,
  GenerationOutputRecord,
  ReviewItemRecord
} from "../repositories.js";
import { composeAssetManifest } from "./compose-asset-manifest.js";
import { composeEvaluationSnapshot } from "./compose-evaluation-snapshot.js";
import { composeReviewSnapshot } from "./compose-review-snapshot.js";
import { formatManualExportArtifacts, formatPortableBundles } from "./format-portable-bundle.js";
import {
  manualExportSurfaceBoundary,
  type ConstraintSnapshot,
  type ExportPackage,
  type ExportSourceType
} from "./types.js";

export function composeExportPackage(input: {
  brief: GenerationBriefRecord;
  compatibility: CompatibilityRecord[];
  constraintBundle: ConstraintBundleRecord | null;
  evaluations?: GenerationOutputEvaluationRecord[];
  output?: GenerationOutputRecord | null;
  review: ReviewItemRecord | null;
  sourceType: ExportSourceType;
}): ExportPackage {
  const sourceKey = input.output?.outputKey ?? input.brief.briefKey;
  const title = input.output?.title ?? input.brief.title;
  const reviewSnapshot = composeReviewSnapshot({
    fallbackReview: input.output?.reviewItem ?? input.brief.reviewItem,
    review: input.review,
    subjectKey: input.brief.subjectKey,
    title
  });
  const evaluationSnapshot = composeEvaluationSnapshot(input.evaluations ?? input.output?.evaluations ?? []);
  const assetManifest = composeAssetManifest({
    campaignWorldCode: input.brief.campaignWorld?.code ?? null,
    compatibility: input.compatibility,
    manifestKey: `ASSET-MANIFEST-${sourceKey}`
  });
  const constraintSnapshot = composeConstraintSnapshot(input.brief, input.constraintBundle);
  const basePackage = {
    ...manualExportSurfaceBoundary,
    assetManifest,
    channel: input.brief.channel,
    constraintSnapshot,
    evaluationSnapshot,
    packageKey: `EXPORT-${sourceKey}`,
    reviewSnapshot,
    sourceKey,
    sourceType: input.sourceType,
    subjectKey: input.brief.subjectKey,
    title
  };
  const portableBundles = formatPortableBundles(basePackage);

  return {
    ...basePackage,
    manualArtifacts: formatManualExportArtifacts(basePackage, portableBundles),
    portableBundles
  };
}

function composeConstraintSnapshot(
  brief: GenerationBriefRecord,
  constraintBundle: ConstraintBundleRecord | null
): ConstraintSnapshot {
  const constraints = constraintBundle?.constraints ?? [];

  return {
    ...manualExportSurfaceBoundary,
    bundleCode: brief.constraintBundle.code,
    bundleName: brief.constraintBundle.name,
    constraints: constraints.map((constraint) => ({
      ...manualExportSurfaceBoundary,
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
