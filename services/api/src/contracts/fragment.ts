import { z } from "zod";
import { fragmentTypeSchema } from "./status.js";

export const fragmentResponseSchema = z.object({
  active: z.boolean(),
  content: z.string(),
  createdAt: z.string(),
  id: z.string(),
  language: z.string(),
  type: fragmentTypeSchema,
  weight: z.number().int()
});

export const fragmentListResponseSchema = z.array(fragmentResponseSchema);

export type FragmentResponse = z.infer<typeof fragmentResponseSchema>;
