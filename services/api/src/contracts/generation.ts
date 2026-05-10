import { z } from "zod";
import {
  channelSchema,
  constraintSourceSchema,
  evaluationVerdictSchema,
  generationBriefTypeSchema,
  generationOutputStatusSchema,
  generationRequestStatusSchema,
  promptSectionTypeSchema,
  reviewStageSchema,
  reviewStatusSchema,
  reviewSubjectTypeSchema
} from "./status.js";

export const generationBriefConstraintResponseSchema = z.object({
  active: z.boolean(),
  id: z.string(),
  instruction: z.string(),
  required: z.boolean(),
  ruleCode: z.string().nullable(),
  source: constraintSourceSchema,
  title: z.string(),
  weight: z.number().int()
});

export const constraintBundleResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  constraints: z.array(generationBriefConstraintResponseSchema),
  createdAt: z.string(),
  description: z.string(),
  id: z.string(),
  name: z.string()
});

export const channelCompositionProfileResponseSchema = z.object({
  active: z.boolean(),
  channel: channelSchema,
  code: z.string(),
  createdAt: z.string(),
  description: z.string(),
  id: z.string(),
  name: z.string(),
  outputShape: z.string()
});

export const promptSectionResponseSchema = z.object({
  body: z.string(),
  id: z.string(),
  locked: z.boolean(),
  position: z.number().int(),
  title: z.string(),
  type: promptSectionTypeSchema
});

const reviewBindingSchema = z
  .object({
    id: z.string(),
    reviewKey: z.string(),
    stage: reviewStageSchema,
    status: reviewStatusSchema
  })
  .nullable();

export const generationBriefResponseSchema = z.object({
  briefKey: z.string(),
  campaignWorld: z
    .object({
      code: z.string(),
      id: z.string(),
      name: z.string()
    })
    .nullable(),
  channel: channelSchema.nullable(),
  channelCompositionProfile: z
    .object({
      channel: channelSchema,
      code: z.string(),
      id: z.string(),
      name: z.string()
    })
    .nullable(),
  channelFragment: z
    .object({
      channel: channelSchema,
      id: z.string(),
      placement: z.string()
    })
    .nullable(),
  constraintBundle: z.object({
    code: z.string(),
    id: z.string(),
    name: z.string()
  }),
  createdAt: z.string(),
  id: z.string(),
  musicRelease: z
    .object({
      id: z.string(),
      releaseCode: z.string(),
      title: z.string()
    })
    .nullable(),
  objective: z.string(),
  promptSections: z.array(promptSectionResponseSchema),
  reviewItem: reviewBindingSchema,
  subjectKey: z.string(),
  subjectType: reviewSubjectTypeSchema,
  title: z.string(),
  track: z
    .object({
      id: z.string(),
      title: z.string()
    })
    .nullable(),
  type: generationBriefTypeSchema
});

export const generationRequestResponseSchema = z.object({
  brief: z.object({
    briefKey: z.string(),
    id: z.string(),
    title: z.string(),
    type: generationBriefTypeSchema
  }),
  createdAt: z.string(),
  id: z.string(),
  notes: z.string().nullable(),
  outputs: z.array(
    z.object({
      id: z.string(),
      outputKey: z.string(),
      reviewItemId: z.string(),
      status: generationOutputStatusSchema,
      title: z.string()
    })
  ),
  requestedFor: z.string().nullable(),
  requestKey: z.string(),
  status: generationRequestStatusSchema
});

export const generationOutputEvaluationResponseSchema = z.object({
  createdAt: z.string(),
  detail: z.string(),
  id: z.string(),
  outputId: z.string(),
  ruleCode: z.string().nullable(),
  source: constraintSourceSchema,
  title: z.string(),
  verdict: evaluationVerdictSchema
});

export const generationOutputResponseSchema = z.object({
  createdAt: z.string(),
  evaluations: z.array(generationOutputEvaluationResponseSchema),
  id: z.string(),
  outputKey: z.string(),
  placeholder: z.string(),
  request: z.object({
    id: z.string(),
    requestKey: z.string(),
    status: generationRequestStatusSchema
  }),
  reviewItemId: z.string(),
  reviewItem: z.object({
    id: z.string(),
    reviewKey: z.string(),
    stage: reviewStageSchema,
    status: reviewStatusSchema
  }),
  status: generationOutputStatusSchema,
  title: z.string()
});

export const generationResponseSchema = z.object({
  briefs: z.array(generationBriefResponseSchema),
  channelCompositionProfiles: z.array(channelCompositionProfileResponseSchema),
  constraintBundles: z.array(constraintBundleResponseSchema),
  outputs: z.array(generationOutputResponseSchema),
  requests: z.array(generationRequestResponseSchema)
});

export const constraintBundleListResponseSchema = z.array(constraintBundleResponseSchema);
export const channelCompositionProfileListResponseSchema = z.array(channelCompositionProfileResponseSchema);
export const generationBriefListResponseSchema = z.array(generationBriefResponseSchema);
export const generationRequestListResponseSchema = z.array(generationRequestResponseSchema);
export const generationOutputListResponseSchema = z.array(generationOutputResponseSchema);
export const generationOutputEvaluationListResponseSchema = z.array(generationOutputEvaluationResponseSchema);

export type GenerationResponse = z.infer<typeof generationResponseSchema>;
