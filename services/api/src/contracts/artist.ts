import { z } from "zod";
import { artistStatusSchema } from "./status.js";

export const artistResponseSchema = z.object({
  bioFragment: z.string().nullable(),
  createdAt: z.string(),
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  status: artistStatusSchema,
  symbol: z.string()
});

export const artistListResponseSchema = z.array(artistResponseSchema);

export type ArtistResponse = z.infer<typeof artistResponseSchema>;
