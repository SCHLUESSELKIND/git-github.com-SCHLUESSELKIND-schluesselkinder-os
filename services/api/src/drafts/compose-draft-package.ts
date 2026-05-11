import type {
  ConstraintBundleRecord,
  GenerationBriefRecord,
  GenerationOutputEvaluationRecord,
  GenerationOutputRecord
} from "../repositories.js";
import { composeConstraintSummary } from "./compose-constraint-summary.js";
import { composeReviewSummary } from "./compose-review-summary.js";
import { formatChannelDraft } from "./format-channel-draft.js";
import {
  draftBoundary,
  manualExportBoundary,
  type DraftEvaluationSummary,
  type DraftPackage,
  type DraftSourceType,
  type ExportArtifact
} from "./types.js";

export function composeDraftPackage(input: {
  brief: GenerationBriefRecord;
  constraintBundle: ConstraintBundleRecord | null;
  evaluations?: GenerationOutputEvaluationRecord[];
  output?: GenerationOutputRecord | null;
  sourceType: DraftSourceType;
}): DraftPackage {
  const sourceKey = input.output?.outputKey ?? input.brief.briefKey;
  const title = input.output?.title ?? input.brief.title;
  const constraintSummary = composeConstraintSummary({
    brief: input.brief,
    constraintBundle: input.constraintBundle
  });
  const reviewSummary = composeReviewSummary({
    brief: input.brief,
    output: input.output
  });
  const channelDraft = formatChannelDraft({
    brief: input.brief,
    constraintSummary,
    output: input.output,
    reviewSummary
  });
  const evaluationSummary = composeEvaluationSummary(input.evaluations ?? input.output?.evaluations ?? []);
  const basePackage = {
    ...draftBoundary,
    channel: input.brief.channel,
    constraintSummary,
    evaluationSummary,
    packageKey: `DP-${sourceKey}`,
    reviewSummary,
    sourceKey,
    sourceType: input.sourceType,
    subjectKey: input.brief.subjectKey,
    title
  };

  return {
    ...basePackage,
    channelDrafts: [channelDraft],
    exportArtifacts: composeExportArtifacts({
      basePackage,
      channelBody: channelDraft.body,
      reviewSummaryText: reviewSummary.summary,
      sourceKey,
      title
    })
  };
}

function composeEvaluationSummary(evaluations: GenerationOutputEvaluationRecord[]): DraftEvaluationSummary {
  const verdicts = evaluations.map((evaluation) => evaluation.verdict);
  const dominantVerdict =
    verdicts.includes("FAIL") ? "FAIL" : verdicts.includes("WARNING") ? "WARNING" : verdicts.includes("PASS") ? "PASS" : "NOT_EVALUATED";

  return {
    ...draftBoundary,
    dominantVerdict,
    findings: evaluations.map((evaluation) => ({
      detail: evaluation.detail,
      ruleCode: evaluation.ruleCode,
      source: evaluation.source,
      title: evaluation.title,
      verdict: evaluation.verdict
    })),
    passImpliesApproval: false,
    verdicts
  };
}

function composeExportArtifacts(input: {
  basePackage: Omit<DraftPackage, "channelDrafts" | "exportArtifacts">;
  channelBody: string;
  reviewSummaryText: string;
  sourceKey: string;
  title: string;
}): ExportArtifact[] {
  return [
    {
      ...manualExportBoundary,
      artifactKey: `ARTIFACT-${input.sourceKey}-JSON`,
      artifactType: "JSON_PACKAGE",
      content: JSON.stringify(input.basePackage, null, 2),
      title: `${input.title} manual package`
    },
    {
      ...manualExportBoundary,
      artifactKey: `ARTIFACT-${input.sourceKey}-TEXT`,
      artifactType: "TEXT_BUNDLE",
      content: input.channelBody,
      title: `${input.title} channel proposal`
    },
    {
      ...manualExportBoundary,
      artifactKey: `ARTIFACT-${input.sourceKey}-REVIEW`,
      artifactType: "REVIEW_SUMMARY",
      content: input.reviewSummaryText,
      title: `${input.title} review summary`
    }
  ];
}
