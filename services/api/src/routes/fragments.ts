import type { FastifyInstance } from "fastify";
import { fragmentListResponseSchema } from "../contracts/fragment.js";
import type { ApiRepositories } from "../repositories.js";
import { mapFragment } from "./mappers.js";

export async function registerFragmentRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/fragments", async () => {
    const fragments = await repositories.fragments.list();

    return fragmentListResponseSchema.parse(fragments.map(mapFragment));
  });
}
