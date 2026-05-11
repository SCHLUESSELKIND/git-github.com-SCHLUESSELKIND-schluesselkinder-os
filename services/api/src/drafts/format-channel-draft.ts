import type { GenerationBriefRecord, GenerationOutputRecord } from "../repositories.js";
import { draftBoundary, type ChannelDraft, type DraftConstraintSummary, type DraftReviewSummary } from "./types.js";

export function formatChannelDraft(input: {
  brief: GenerationBriefRecord;
  constraintSummary: DraftConstraintSummary;
  output?: GenerationOutputRecord | null;
  reviewSummary: DraftReviewSummary;
}): ChannelDraft {
  const sourceKey = input.output?.outputKey ?? input.brief.briefKey;
  const title = input.output?.title ?? input.brief.title;
  const material = input.output?.placeholder ?? input.brief.objective;

  return {
    ...draftBoundary,
    body: [
      `Source: ${sourceKey}`,
      `Subject: ${input.brief.subjectKey}`,
      `Channel: ${input.brief.channel ?? "UNSPECIFIED"}`,
      `Review: ${input.reviewSummary.reviewKey ?? "MISSING"}`,
      `Constraint bundle: ${input.constraintSummary.bundleCode}`,
      "",
      material,
      "",
      "Manual commit required. External delivery is false."
    ].join("\n"),
    channel: input.brief.channel,
    draftKey: `DRAFT-${sourceKey}`,
    format: "CHANNEL_PROPOSAL",
    title
  };
}
