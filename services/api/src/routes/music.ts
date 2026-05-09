import type { FastifyInstance } from "fastify";
import { z } from "zod";
import {
  musicReleaseListResponseSchema,
  musicReleaseResponseSchema
} from "../contracts/music.js";
import type { ApiRepositories } from "../repositories.js";
import { mapMusicRelease } from "./mappers.js";

const musicParamsSchema = z.object({
  releaseCode: z.string().min(1)
});

export async function registerMusicRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/music", async () => {
    const releases = await repositories.music.list();

    return musicReleaseListResponseSchema.parse(releases.map(mapMusicRelease));
  });

  server.get<{ Params: { releaseCode: string } }>("/music/:releaseCode", async (request, reply) => {
    const params = musicParamsSchema.parse(request.params);
    const release = await repositories.music.findByReleaseCode(params.releaseCode);

    if (!release) {
      return reply.code(404).send({ error: "music_release_not_found" });
    }

    return musicReleaseResponseSchema.parse(mapMusicRelease(release));
  });
}
