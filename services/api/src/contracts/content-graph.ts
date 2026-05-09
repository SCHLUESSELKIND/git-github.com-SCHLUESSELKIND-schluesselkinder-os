import { z } from "zod";
import {
  assetSourceTypeSchema,
  assetTypeSchema,
  channelSchema,
  compatibilityVerdictSchema,
  fragmentPlacementSchema
} from "./status.js";

const graphNodeBaseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  description: z.string(),
  id: z.string(),
  name: z.string(),
  weight: z.number().int()
});

export const campaignWorldResponseSchema = graphNodeBaseSchema;
export const visualEnvironmentResponseSchema = graphNodeBaseSchema;
export const moodReferenceResponseSchema = graphNodeBaseSchema;

export const assetResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  description: z.string().nullable(),
  id: z.string(),
  referenceKey: z.string().nullable(),
  sourceType: assetSourceTypeSchema,
  title: z.string(),
  type: assetTypeSchema,
  weight: z.number().int()
});

export const assetTagResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  id: z.string(),
  label: z.string()
});

export const compatibilityResponseSchema = z.object({
  kind: z.enum([
    "ARTIST_CAMPAIGN_WORLD",
    "MUSIC_RELEASE_CAMPAIGN_WORLD",
    "TRACK_MOOD_REFERENCE",
    "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT",
    "CAMPAIGN_WORLD_MOOD_REFERENCE",
    "CAMPAIGN_WORLD_ASSET"
  ]),
  reason: z.string().nullable(),
  source: z.object({
    code: z.string(),
    id: z.string(),
    label: z.string()
  }),
  target: z.object({
    code: z.string(),
    id: z.string(),
    label: z.string()
  }),
  verdict: compatibilityVerdictSchema,
  weight: z.number().int()
});

const fragmentSummarySchema = z.object({
  content: z.string(),
  id: z.string(),
  language: z.string(),
  type: z.string()
});

export const releaseFragmentResponseSchema = z.object({
  active: z.boolean(),
  fragment: fragmentSummarySchema,
  id: z.string(),
  musicRelease: z
    .object({
      id: z.string(),
      releaseCode: z.string(),
      title: z.string()
    })
    .nullable(),
  placement: fragmentPlacementSchema,
  track: z
    .object({
      id: z.string(),
      title: z.string()
    })
    .nullable(),
  weight: z.number().int()
});

export const channelFragmentResponseSchema = z.object({
  active: z.boolean(),
  campaignWorld: z
    .object({
      code: z.string(),
      id: z.string(),
      name: z.string()
    })
    .nullable(),
  channel: channelSchema,
  fragment: fragmentSummarySchema,
  id: z.string(),
  moodReference: z
    .object({
      code: z.string(),
      id: z.string(),
      name: z.string()
    })
    .nullable(),
  placement: fragmentPlacementSchema,
  weight: z.number().int()
});

export const contentGraphMusicReleaseResponseSchema = z.object({
  campaignWorlds: z.array(compatibilityResponseSchema),
  release: z.object({
    artist: z.object({
      name: z.string(),
      slug: z.string()
    }),
    id: z.string(),
    releaseCode: z.string(),
    status: z.string(),
    title: z.string()
  }),
  releaseFragments: z.array(releaseFragmentResponseSchema),
  trackMoodReferences: z.array(compatibilityResponseSchema)
});

export const contentGraphResponseSchema = z.object({
  assets: z.array(assetResponseSchema),
  assetTags: z.array(assetTagResponseSchema),
  campaignWorlds: z.array(campaignWorldResponseSchema),
  channelFragments: z.array(channelFragmentResponseSchema),
  compatibility: z.array(compatibilityResponseSchema),
  moodReferences: z.array(moodReferenceResponseSchema),
  releaseFragments: z.array(releaseFragmentResponseSchema),
  visualEnvironments: z.array(visualEnvironmentResponseSchema)
});

export const campaignWorldListResponseSchema = z.array(campaignWorldResponseSchema);
export const visualEnvironmentListResponseSchema = z.array(visualEnvironmentResponseSchema);
export const moodReferenceListResponseSchema = z.array(moodReferenceResponseSchema);
export const assetListResponseSchema = z.array(assetResponseSchema);
export const assetTagListResponseSchema = z.array(assetTagResponseSchema);
export const compatibilityListResponseSchema = z.array(compatibilityResponseSchema);
export const releaseFragmentListResponseSchema = z.array(releaseFragmentResponseSchema);
export const channelFragmentListResponseSchema = z.array(channelFragmentResponseSchema);

export type ContentGraphResponse = z.infer<typeof contentGraphResponseSchema>;
