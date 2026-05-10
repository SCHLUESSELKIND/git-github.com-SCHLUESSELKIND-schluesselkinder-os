import { z } from "zod";
import {
  decisionTypeSchema,
  reviewStageSchema,
  reviewStatusSchema,
  reviewSubjectTypeSchema,
  ruleSeveritySchema,
  ruleViolationSourceSchema
} from "./status.js";

export const approvalDecisionResponseSchema = z.object({
  createdAt: z.string(),
  decidedBy: z.string().nullable(),
  id: z.string(),
  note: z.string().nullable(),
  reviewItemId: z.string(),
  type: decisionTypeSchema
});

export const approvalCommentResponseSchema = z.object({
  author: z.string().nullable(),
  body: z.string(),
  createdAt: z.string(),
  id: z.string(),
  reviewItemId: z.string()
});

export const ruleViolationResponseSchema = z.object({
  active: z.boolean(),
  createdAt: z.string(),
  detail: z.string(),
  id: z.string(),
  reviewItemId: z.string(),
  ruleCode: z.string().nullable(),
  severity: ruleSeveritySchema,
  source: ruleViolationSourceSchema,
  title: z.string()
});

export const reviewItemResponseSchema = z.object({
  asset: z
    .object({
      code: z.string(),
      id: z.string(),
      title: z.string()
    })
    .nullable(),
  campaignWorld: z
    .object({
      code: z.string(),
      id: z.string(),
      name: z.string()
    })
    .nullable(),
  channelFragment: z
    .object({
      channel: z.string(),
      id: z.string(),
      placement: z.string()
    })
    .nullable(),
  comments: z.array(approvalCommentResponseSchema),
  createdAt: z.string(),
  decisions: z.array(approvalDecisionResponseSchema),
  id: z.string(),
  musicRelease: z
    .object({
      id: z.string(),
      releaseCode: z.string(),
      title: z.string()
    })
    .nullable(),
  releaseFragment: z
    .object({
      id: z.string(),
      placement: z.string()
    })
    .nullable(),
  reviewKey: z.string(),
  stage: reviewStageSchema,
  status: reviewStatusSchema,
  subjectKey: z.string(),
  subjectType: reviewSubjectTypeSchema,
  summary: z.string().nullable(),
  title: z.string(),
  track: z
    .object({
      id: z.string(),
      title: z.string()
    })
    .nullable(),
  updatedAt: z.string(),
  violations: z.array(ruleViolationResponseSchema)
});

export const reviewItemListResponseSchema = z.array(reviewItemResponseSchema);
export const approvalDecisionListResponseSchema = z.array(approvalDecisionResponseSchema);
export const approvalCommentListResponseSchema = z.array(approvalCommentResponseSchema);
export const ruleViolationListResponseSchema = z.array(ruleViolationResponseSchema);

export const reviewStageListResponseSchema = z.array(reviewStageSchema);
export const reviewStatusListResponseSchema = z.array(reviewStatusSchema);

export type ReviewItemResponse = z.infer<typeof reviewItemResponseSchema>;
