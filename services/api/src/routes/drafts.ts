import type { FastifyInstance } from "fastify";
import { draftHealthResponseSchema, draftPackageResponseSchema } from "../contracts/drafts.js";
import { composeDraftPackage } from "../drafts/compose-draft-package.js";
import type {
  ApiRepositories,
  ConstraintBundleRecord,
  GenerationBriefRecord,
  GenerationOutputRecord
} from "../repositories.js";

export async function registerDraftRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/drafts/health", async () =>
    draftHealthResponseSchema.parse({
      approvalAuthority: false,
      automationAllowed: false,
      dbMutation: false,
      externalDelivery: false,
      externalIntegration: false,
      humanCommitRequired: true,
      providerIntegration: false,
      publishAuthority: false,
      reviewRequired: true,
      status: "ok",
      writeRoutes: false
    })
  );

  server.get("/drafts/packages/generation-outputs/:outputKey", async (request, reply) => {
    const { outputKey } = request.params as { outputKey: string };
    const output = await repositories.generation.findOutputByKey(outputKey);

    if (!output) {
      return reply.code(404).send({ error: "generation_output_not_found" });
    }

    const brief = await findBriefForOutput(repositories, output);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const [constraintBundle, storedEvaluations] = await Promise.all([
      findConstraintBundle(repositories, brief),
      repositories.generation.listOutputEvaluations(output.outputKey)
    ]);

    return draftPackageResponseSchema.parse(
      composeDraftPackage({
        brief,
        constraintBundle,
        evaluations: storedEvaluations ?? output.evaluations,
        output,
        sourceType: "GENERATION_OUTPUT"
      })
    );
  });

  server.get("/drafts/packages/generation-briefs/:briefKey", async (request, reply) => {
    const { briefKey } = request.params as { briefKey: string };
    const brief = await repositories.generation.findBriefByKey(briefKey);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const constraintBundle = await findConstraintBundle(repositories, brief);

    return draftPackageResponseSchema.parse(
      composeDraftPackage({
        brief,
        constraintBundle,
        sourceType: "GENERATION_BRIEF"
      })
    );
  });
}

async function findBriefForOutput(
  repositories: ApiRepositories,
  output: GenerationOutputRecord
): Promise<GenerationBriefRecord | null> {
  const requestRecord = await repositories.generation.findRequestByKey(output.request.requestKey);
  const briefKey = requestRecord?.brief.briefKey;

  if (briefKey) {
    return repositories.generation.findBriefByKey(briefKey);
  }

  const requests = await repositories.generation.listRequests();
  const fallbackRequest = requests.find((candidate) => candidate.id === output.requestId);
  const fallbackBriefKey = fallbackRequest?.brief.briefKey;

  return fallbackBriefKey ? repositories.generation.findBriefByKey(fallbackBriefKey) : null;
}

async function findConstraintBundle(
  repositories: ApiRepositories,
  brief: GenerationBriefRecord
): Promise<ConstraintBundleRecord | null> {
  const bundles = await repositories.generation.listConstraintBundles();

  return bundles.find((candidate) => candidate.id === brief.constraintBundle.id || candidate.code === brief.constraintBundle.code) ?? null;
}
