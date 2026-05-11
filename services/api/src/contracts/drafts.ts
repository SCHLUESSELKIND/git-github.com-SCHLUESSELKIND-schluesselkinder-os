import { z } from "zod";
import { channelSchema, constraintSourceSchema, evaluationVerdictSchema } from "./status.js";

const draftBoundarySchema = z.object({
  approvalAuthority: z.literal(false),
  automationAllowed: z.literal(false),
  externalDelivery: z.literal(false),
  humanCommitRequired: z.literal(true),
  publishAuthority: z.literal(false),
  reviewRequired: z.literal(true)
});

const manualExportBoundarySchema = z.object({
  humanCommitRequired: z.literal(true),
  manualExportPrepared: z.literal(true),
  publishReady: z.literal(false)
});

export const draftReviewSummaryResponseSchema = draftBoundarySchema.extend({
  reviewKey: z.string().nullable(),
  stage: z.string().nullable(),
  status: z.string().nullable(),
  summary: z.string()
});

export const draftConstraintSummaryResponseSchema = z.object({
  bundleCode: z.string(),
  bundleName: z.string(),
  constraints: z.array(
    z.object({
      instruction: z.string(),
      required: z.boolean(),
      ruleCode: z.string().nullable(),
      source: constraintSourceSchema,
      title: z.string(),
      weight: z.number().int()
    })
  ),
  requiredCount: z.number().int()
});

export const draftEvaluationSummaryResponseSchema = draftBoundarySchema.extend({
  dominantVerdict: z.union([evaluationVerdictSchema, z.literal("NOT_EVALUATED")]),
  findings: z.array(
    z.object({
      detail: z.string(),
      ruleCode: z.string().nullable(),
      source: constraintSourceSchema,
      title: z.string(),
      verdict: evaluationVerdictSchema
    })
  ),
  passImpliesApproval: z.literal(false),
  verdicts: z.array(evaluationVerdictSchema)
});

export const channelDraftResponseSchema = draftBoundarySchema.extend({
  body: z.string(),
  channel: channelSchema.nullable(),
  draftKey: z.string(),
  format: z.enum(["CHANNEL_PROPOSAL", "REVIEW_SUMMARY", "CONSTRAINT_SUMMARY"]),
  title: z.string()
});

export const exportArtifactResponseSchema = manualExportBoundarySchema.extend({
  artifactKey: z.string(),
  artifactType: z.enum(["JSON_PACKAGE", "TEXT_BUNDLE", "REVIEW_SUMMARY"]),
  content: z.string(),
  title: z.string()
});

export const draftPackageResponseSchema = draftBoundarySchema.extend({
  channel: channelSchema.nullable(),
  channelDrafts: z.array(channelDraftResponseSchema),
  constraintSummary: draftConstraintSummaryResponseSchema,
  evaluationSummary: draftEvaluationSummaryResponseSchema,
  exportArtifacts: z.array(exportArtifactResponseSchema),
  packageKey: z.string(),
  reviewSummary: draftReviewSummaryResponseSchema,
  sourceKey: z.string(),
  sourceType: z.enum(["GENERATION_BRIEF", "GENERATION_OUTPUT"]),
  subjectKey: z.string(),
  title: z.string()
});

export const draftHealthResponseSchema = draftBoundarySchema.extend({
  dbMutation: z.literal(false),
  externalIntegration: z.literal(false),
  providerIntegration: z.literal(false),
  status: z.literal("ok"),
  writeRoutes: z.literal(false)
});

export type DraftPackageResponse = z.infer<typeof draftPackageResponseSchema>;
