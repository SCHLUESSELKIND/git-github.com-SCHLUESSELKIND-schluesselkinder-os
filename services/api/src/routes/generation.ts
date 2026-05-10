import type { FastifyInstance } from "fastify";
import {
  channelCompositionProfileListResponseSchema,
  constraintBundleListResponseSchema,
  generationBriefListResponseSchema,
  generationBriefResponseSchema,
  generationOutputEvaluationListResponseSchema,
  generationOutputListResponseSchema,
  generationOutputResponseSchema,
  generationRequestListResponseSchema,
  generationRequestResponseSchema,
  generationResponseSchema
} from "../contracts/generation.js";
import type { ApiRepositories } from "../repositories.js";
import {
  mapChannelCompositionProfile,
  mapConstraintBundle,
  mapGenerationBrief,
  mapGenerationOutput,
  mapGenerationOutputEvaluation,
  mapGenerationRequest
} from "./mappers.js";

export async function registerGenerationRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/generation", async () => {
    const [briefs, channelCompositionProfiles, constraintBundles, outputs, requests] = await Promise.all([
      repositories.generation.listBriefs(),
      repositories.generation.listChannelCompositionProfiles(),
      repositories.generation.listConstraintBundles(),
      repositories.generation.listOutputs(),
      repositories.generation.listRequests()
    ]);

    return generationResponseSchema.parse({
      briefs: briefs.map(mapGenerationBrief),
      channelCompositionProfiles: channelCompositionProfiles.map(mapChannelCompositionProfile),
      constraintBundles: constraintBundles.map(mapConstraintBundle),
      outputs: outputs.map(mapGenerationOutput),
      requests: requests.map(mapGenerationRequest)
    });
  });

  server.get("/generation/briefs", async () =>
    generationBriefListResponseSchema.parse((await repositories.generation.listBriefs()).map(mapGenerationBrief))
  );

  server.get("/generation/briefs/:briefKey", async (request, reply) => {
    const { briefKey } = request.params as { briefKey: string };
    const brief = await repositories.generation.findBriefByKey(briefKey);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    return generationBriefResponseSchema.parse(mapGenerationBrief(brief));
  });

  server.get("/generation/constraint-bundles", async () =>
    constraintBundleListResponseSchema.parse(
      (await repositories.generation.listConstraintBundles()).map(mapConstraintBundle)
    )
  );

  server.get("/generation/channel-composition-profiles", async () =>
    channelCompositionProfileListResponseSchema.parse(
      (await repositories.generation.listChannelCompositionProfiles()).map(mapChannelCompositionProfile)
    )
  );

  server.get("/generation/requests", async () =>
    generationRequestListResponseSchema.parse((await repositories.generation.listRequests()).map(mapGenerationRequest))
  );

  server.get("/generation/requests/:requestKey", async (request, reply) => {
    const { requestKey } = request.params as { requestKey: string };
    const generationRequest = await repositories.generation.findRequestByKey(requestKey);

    if (!generationRequest) {
      return reply.code(404).send({ error: "generation_request_not_found" });
    }

    return generationRequestResponseSchema.parse(mapGenerationRequest(generationRequest));
  });

  server.get("/generation/outputs", async () =>
    generationOutputListResponseSchema.parse((await repositories.generation.listOutputs()).map(mapGenerationOutput))
  );

  server.get("/generation/outputs/:outputKey", async (request, reply) => {
    const { outputKey } = request.params as { outputKey: string };
    const output = await repositories.generation.findOutputByKey(outputKey);

    if (!output) {
      return reply.code(404).send({ error: "generation_output_not_found" });
    }

    return generationOutputResponseSchema.parse(mapGenerationOutput(output));
  });

  server.get("/generation/outputs/:outputKey/evaluations", async (request, reply) => {
    const { outputKey } = request.params as { outputKey: string };
    const evaluations = await repositories.generation.listOutputEvaluations(outputKey);

    if (!evaluations) {
      return reply.code(404).send({ error: "generation_output_not_found" });
    }

    return generationOutputEvaluationListResponseSchema.parse(evaluations.map(mapGenerationOutputEvaluation));
  });
}
