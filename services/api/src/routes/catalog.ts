import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { CatalogService } from "../catalog/catalog-types.js";

const artistParamsSchema = z.object({
  artistKey: z.string().min(1)
});

const releaseParamsSchema = z.object({
  releaseCode: z.string().min(1)
});

const trackParamsSchema = z.object({
  trackKey: z.string().min(1)
});

export async function registerCatalogRoutes(server: FastifyInstance, catalog: CatalogService) {
  server.get("/catalog/artists", async () => catalog.listArtistProjections());

  server.get<{ Params: { artistKey: string } }>("/catalog/artists/:artistKey", async (request, reply) => {
    const params = artistParamsSchema.parse(request.params);
    const artists = await catalog.listArtistProjections();
    const artist = artists.find((projection) => projection.artistKey === params.artistKey);

    if (!artist) {
      return reply.code(404).send({ error: "catalog_artist_not_found" });
    }

    return artist;
  });

  server.get("/catalog/music-releases", async () => catalog.listReleaseProjections());

  server.get<{ Params: { releaseCode: string } }>("/catalog/music-releases/:releaseCode", async (request, reply) => {
    const params = releaseParamsSchema.parse(request.params);
    const releases = await catalog.listReleaseProjections();
    const release = releases.find((projection) => projection.releaseCode === params.releaseCode);

    if (!release) {
      return reply.code(404).send({ error: "catalog_music_release_not_found" });
    }

    return release;
  });

  server.get("/catalog/tracks", async () => catalog.listTrackProjections());

  server.get<{ Params: { trackKey: string } }>("/catalog/tracks/:trackKey", async (request, reply) => {
    const params = trackParamsSchema.parse(request.params);
    const tracks = await catalog.listTrackProjections();
    const track = tracks.find((projection) => projection.trackKey === params.trackKey);

    if (!track) {
      return reply.code(404).send({ error: "catalog_track_not_found" });
    }

    return track;
  });
}
