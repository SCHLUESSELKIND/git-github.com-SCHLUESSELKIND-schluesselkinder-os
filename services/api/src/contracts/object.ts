import { z } from "zod";
import { releaseStatusSchema } from "./status.js";

export const objectReleaseResponseSchema = z.object({
  archiveFragment: z.string().nullable(),
  artist: z
    .object({
      name: z.string(),
      slug: z.string()
    })
    .nullable(),
  createdAt: z.string(),
  id: z.string(),
  mark: z.string(),
  materialNote: z.string().nullable(),
  releaseId: z.string(),
  status: releaseStatusSchema,
  title: z.string(),
  type: z.string()
});

export const objectReleaseListResponseSchema = z.array(objectReleaseResponseSchema);

export type ObjectReleaseResponse = z.infer<typeof objectReleaseResponseSchema>;
