import { z } from "zod";
import { channelSchema, constraintSourceSchema, evaluationVerdictSchema } from "./status.js";

const manualExportSurfaceBoundarySchema = z.object({
  approvalAuthority: z.literal(false),
  automationAllowed: z.literal(false),
  distributionAuthority: z.literal(false),
  externalDelivery: z.literal(false),
  humanCommitRequired: z.literal(true),
  manualExportPrepared: z.literal(true),
  portableArtifactOnly: z.literal(true),
  publishAuthority: z.literal(false),
  publishReady: z.literal(false),
  reviewRequired: z.literal(true)
});

export const reviewDecisionSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  createdAt: z.string(),
  decidedBy: z.string().nullable(),
  note: z.string().nullable(),
  type: z.string()
});

export const reviewCommentSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  author: z.string().nullable(),
  body: z.string(),
  createdAt: z.string()
});

export const reviewViolationSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  active: z.boolean(),
  detail: z.string(),
  ruleCode: z.string().nullable(),
  severity: z.string(),
  source: z.string(),
  title: z.string()
});

export const reviewSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  comments: z.array(reviewCommentSnapshotResponseSchema),
  decisions: z.array(reviewDecisionSnapshotResponseSchema),
  reviewKey: z.string().nullable(),
  snapshotImpliesApproval: z.literal(false),
  stage: z.string().nullable(),
  status: z.string().nullable(),
  subjectKey: z.string().nullable(),
  subjectType: z.string().nullable(),
  summary: z.string().nullable(),
  title: z.string(),
  violations: z.array(reviewViolationSnapshotResponseSchema)
});

export const evaluationFindingSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  detail: z.string(),
  ruleCode: z.string().nullable(),
  source: constraintSourceSchema,
  title: z.string(),
  verdict: evaluationVerdictSchema
});

export const evaluationSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  dominantVerdict: z.union([evaluationVerdictSchema, z.literal("NOT_EVALUATED")]),
  findings: z.array(evaluationFindingSnapshotResponseSchema),
  passImpliesApproval: z.literal(false),
  snapshotImpliesTruth: z.literal(false),
  verdicts: z.array(evaluationVerdictSchema)
});

export const constraintSnapshotResponseSchema = manualExportSurfaceBoundarySchema.extend({
  bundleCode: z.string().nullable(),
  bundleName: z.string().nullable(),
  constraints: z.array(
    manualExportSurfaceBoundarySchema.extend({
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

export const assetManifestItemResponseSchema = manualExportSurfaceBoundarySchema.extend({
  campaignWorldRelation: z.string(),
  code: z.string(),
  compatibilityVerdict: z.string(),
  referenceKey: z.string().nullable(),
  sourceType: z.string(),
  title: z.string()
});

export const assetManifestResponseSchema = manualExportSurfaceBoundarySchema.extend({
  assets: z.array(assetManifestItemResponseSchema),
  manifestKey: z.string(),
  symbolicOnly: z.literal(true)
});

export const portableBundleResponseSchema = manualExportSurfaceBoundarySchema.extend({
  bundleKey: z.string(),
  content: z.string(),
  format: z.enum(["JSON", "TEXT"]),
  title: z.string()
});

export const manualExportArtifactResponseSchema = manualExportSurfaceBoundarySchema.extend({
  artifactKey: z.string(),
  artifactType: z.enum(["PORTABLE_JSON", "PORTABLE_TEXT", "ASSET_MANIFEST", "REVIEW_SNAPSHOT", "EVALUATION_SNAPSHOT"]),
  content: z.string(),
  title: z.string()
});

export const exportPackageResponseSchema = manualExportSurfaceBoundarySchema.extend({
  assetManifest: assetManifestResponseSchema,
  channel: channelSchema.nullable(),
  constraintSnapshot: constraintSnapshotResponseSchema,
  evaluationSnapshot: evaluationSnapshotResponseSchema,
  manualArtifacts: z.array(manualExportArtifactResponseSchema),
  packageKey: z.string(),
  portableBundles: z.array(portableBundleResponseSchema),
  reviewSnapshot: reviewSnapshotResponseSchema,
  sourceKey: z.string(),
  sourceType: z.enum(["GENERATION_BRIEF", "GENERATION_OUTPUT", "REVIEW_ITEM"]),
  subjectKey: z.string(),
  title: z.string()
});

export const exportHealthResponseSchema = manualExportSurfaceBoundarySchema.extend({
  dbMutation: z.literal(false),
  externalIntegration: z.literal(false),
  fileWriting: z.literal(false),
  providerIntegration: z.literal(false),
  status: z.literal("ok"),
  writeRoutes: z.literal(false)
});

export type ExportPackageResponse = z.infer<typeof exportPackageResponseSchema>;
