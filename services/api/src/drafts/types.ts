import type { ConstraintSource, EvaluationVerdict, Channel } from "@schluesselkinder/db";

export const draftBoundary = {
  approvalAuthority: false,
  automationAllowed: false,
  externalDelivery: false,
  humanCommitRequired: true,
  publishAuthority: false,
  reviewRequired: true
} as const;

export const manualExportBoundary = {
  humanCommitRequired: true,
  manualExportPrepared: true,
  publishReady: false
} as const;

export type DraftSourceType = "GENERATION_BRIEF" | "GENERATION_OUTPUT";

export type DraftBoundary = typeof draftBoundary;

export type ManualExportBoundary = typeof manualExportBoundary;

export type DraftReviewSummary = Readonly<
  DraftBoundary & {
    reviewKey: string | null;
    stage: string | null;
    status: string | null;
    summary: string;
  }
>;

export type DraftConstraintSummary = Readonly<{
  bundleCode: string;
  bundleName: string;
  requiredCount: number;
  constraints: ReadonlyArray<{
    instruction: string;
    required: boolean;
    ruleCode: string | null;
    source: ConstraintSource;
    title: string;
    weight: number;
  }>;
}>;

export type DraftEvaluationSummary = Readonly<
  DraftBoundary & {
    dominantVerdict: EvaluationVerdict | "NOT_EVALUATED";
    passImpliesApproval: false;
    verdicts: EvaluationVerdict[];
    findings: ReadonlyArray<{
      detail: string;
      ruleCode: string | null;
      source: ConstraintSource;
      title: string;
      verdict: EvaluationVerdict;
    }>;
  }
>;

export type ChannelDraft = Readonly<
  DraftBoundary & {
    body: string;
    channel: Channel | null;
    draftKey: string;
    format: "CHANNEL_PROPOSAL" | "REVIEW_SUMMARY" | "CONSTRAINT_SUMMARY";
    title: string;
  }
>;

export type ExportArtifact = Readonly<
  ManualExportBoundary & {
    artifactKey: string;
    artifactType: "JSON_PACKAGE" | "TEXT_BUNDLE" | "REVIEW_SUMMARY";
    content: string;
    title: string;
  }
>;

export type DraftPackage = Readonly<
  DraftBoundary & {
    channel: Channel | null;
    channelDrafts: ChannelDraft[];
    constraintSummary: DraftConstraintSummary;
    evaluationSummary: DraftEvaluationSummary;
    exportArtifacts: ExportArtifact[];
    packageKey: string;
    reviewSummary: DraftReviewSummary;
    sourceKey: string;
    sourceType: DraftSourceType;
    subjectKey: string;
    title: string;
  }
>;
