import type { FastifyInstance } from "fastify";
import { z } from "zod";
import {
  artistListResponseSchema,
  artistResponseSchema
} from "../contracts/artist.js";
import type { ApiRepositories } from "../repositories.js";
import { mapArtist } from "./mappers.js";

const artistParamsSchema = z.object({
  slug: z.string().min(1)
});

export async function registerArtistRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/artists", async () => {
    const artists = await repositories.artists.list();

    return artistListResponseSchema.parse(artists.map(mapArtist));
  });

  server.get<{ Params: { slug: string } }>("/artists/:slug", async (request, reply) => {
    const params = artistParamsSchema.parse(request.params);
    const artist = await repositories.artists.findBySlug(params.slug);

    if (!artist) {
      return reply.code(404).send({ error: "artist_not_found" });
    }

    return artistResponseSchema.parse(mapArtist(artist));
  });
}
