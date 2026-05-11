import type { GenerationBriefRecord, GenerationOutputRecord, ReviewItemRecord } from "../repositories.js";
import { manualExportSurfaceBoundary, type ReviewSnapshot } from "./types.js";

type FallbackReview = NonNullable<GenerationBriefRecord["reviewItem"]> | GenerationOutputRecord["reviewItem"];

export function composeReviewSnapshot(input: {
  fallbackReview?: FallbackReview | null;
  review: ReviewItemRecord | null;
  subjectKey: string;
  title: string;
}): ReviewSnapshot {
  if (!input.review) {
    return {
      ...manualExportSurfaceBoundary,
      comments: [],
      decisions: [],
      reviewKey: input.fallbackReview?.reviewKey ?? null,
      snapshotImpliesApproval: false,
      stage: input.fallbackReview?.stage ?? null,
      status: input.fallbackReview?.status ?? null,
      subjectKey: input.subjectKey,
      subjectType: null,
      summary: null,
      title: input.title,
      violations: []
    };
  }

  return {
    ...manualExportSurfaceBoundary,
    comments: input.review.comments.map((comment) => ({
      ...manualExportSurfaceBoundary,
      author: comment.author,
      body: comment.body,
      createdAt: comment.createdAt.toISOString()
    })),
    decisions: input.review.decisions.map((decision) => ({
      ...manualExportSurfaceBoundary,
      createdAt: decision.createdAt.toISOString(),
      decidedBy: decision.decidedBy,
      note: decision.note,
      type: decision.type
    })),
    reviewKey: input.review.reviewKey,
    snapshotImpliesApproval: false,
    stage: input.review.stage,
    status: input.review.status,
    subjectKey: input.review.subjectKey,
    subjectType: input.review.subjectType,
    summary: input.review.summary,
    title: input.review.title,
    violations: input.review.violations.map((violation) => ({
      ...manualExportSurfaceBoundary,
      active: violation.active,
      detail: violation.detail,
      ruleCode: violation.ruleCode,
      severity: violation.severity,
      source: violation.source,
      title: violation.title
    }))
  };
}
