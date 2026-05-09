import type { FastifyInstance } from "fastify";
import { objectReleaseListResponseSchema } from "../contracts/object.js";
import type { ApiRepositories } from "../repositories.js";
import { mapObjectRelease } from "./mappers.js";

export async function registerObjectRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/objects", async () => {
    const objects = await repositories.objects.list();

    return objectReleaseListResponseSchema.parse(objects.map(mapObjectRelease));
  });
}
