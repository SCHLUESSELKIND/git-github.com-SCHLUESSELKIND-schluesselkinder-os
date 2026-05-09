import { z } from "zod";
import { releaseStatusSchema } from "./status.js";

export const trackResponseSchema = z.object({
  duration: z.number().int().nullable(),
  id: z.string(),
  moodFragment: z.string().nullable(),
  title: z.string()
});

export const musicReleaseResponseSchema = z.object({
  artist: z.object({
    name: z.string(),
    slug: z.string()
  }),
  coverImage: z.string().nullable(),
  createdAt: z.string(),
  id: z.string(),
  releaseCode: z.string(),
  status: releaseStatusSchema,
  title: z.string(),
  tracks: z.array(trackResponseSchema)
});

export const musicReleaseListResponseSchema = z.array(musicReleaseResponseSchema);

export type MusicReleaseResponse = z.infer<typeof musicReleaseResponseSchema>;
