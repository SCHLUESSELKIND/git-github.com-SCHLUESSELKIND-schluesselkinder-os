import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { RegistryRepository } from "../registry/registry-types.js";

const artistParamsSchema = z.object({
  artistKey: z.string().min(1)
});

const releaseParamsSchema = z.object({
  releaseKey: z.string().min(1)
});

const trackParamsSchema = z.object({
  trackKey: z.string().min(1)
});

export async function registerRegistryRoutes(server: FastifyInstance, registry: RegistryRepository) {
  server.get("/registry/artists", async () => registry.listArtists());

  server.get<{ Params: { artistKey: string } }>("/registry/artists/:artistKey", async (request, reply) => {
    const params = artistParamsSchema.parse(request.params);
    const artist = await registry.getArtistByKeyOrSlug(params.artistKey);

    if (!artist) {
      return reply.code(404).send({ error: "registry_artist_not_found" });
    }

    return artist;
  });

  server.get("/registry/music-releases", async () => registry.listMusicReleases());

  server.get<{ Params: { releaseKey: string } }>("/registry/music-releases/:releaseKey", async (request, reply) => {
    const params = releaseParamsSchema.parse(request.params);
    const release = await registry.getMusicReleaseByCode(params.releaseKey);

    if (!release) {
      return reply.code(404).send({ error: "registry_music_release_not_found" });
    }

    return release;
  });

  server.get<{ Params: { trackKey: string } }>("/registry/tracks/:trackKey", async (request, reply) => {
    const params = trackParamsSchema.parse(request.params);
    const track = await registry.getTrackByKey(params.trackKey);

    if (!track) {
      return reply.code(404).send({ error: "registry_track_not_found" });
    }

    return track;
  });

  server.get("/registry/channel-presences", async () => registry.listChannelPresences());
  server.get("/registry/external-references", async () => registry.listExternalReferences());
  server.get("/registry/distribution-references", async () => registry.listDistributionReferences());
}
