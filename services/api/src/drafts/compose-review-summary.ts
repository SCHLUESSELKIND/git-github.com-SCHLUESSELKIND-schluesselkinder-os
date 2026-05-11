import type { GenerationBriefRecord, GenerationOutputRecord } from "../repositories.js";
import { draftBoundary, type DraftReviewSummary } from "./types.js";

type ReviewBinding = NonNullable<GenerationBriefRecord["reviewItem"]> | GenerationOutputRecord["reviewItem"];

export function composeReviewSummary(input: {
  brief: GenerationBriefRecord;
  output?: GenerationOutputRecord | null;
}): DraftReviewSummary {
  const review = input.output?.reviewItem ?? input.brief.reviewItem;

  return {
    ...draftBoundary,
    reviewKey: review?.reviewKey ?? null,
    stage: review?.stage ?? null,
    status: review?.status ?? null,
    summary: buildReviewSummary(review, input.brief.subjectKey)
  };
}

function buildReviewSummary(review: ReviewBinding | null | undefined, subjectKey: string): string {
  if (!review) {
    return `Manual review binding is missing for ${subjectKey}. The draft package remains inspection-only.`;
  }

  return `Manual review binding ${review.reviewKey} is required for ${subjectKey}. This package has no approval authority.`;
}
