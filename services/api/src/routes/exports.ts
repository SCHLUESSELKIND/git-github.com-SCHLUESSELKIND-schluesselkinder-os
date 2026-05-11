import type { FastifyInstance } from "fastify";
import {
  exportHealthResponseSchema,
  exportPackageResponseSchema,
  reviewSnapshotResponseSchema
} from "../contracts/exports.js";
import { composeExportPackage } from "../exports/compose-export-package.js";
import { composeReviewSnapshot } from "../exports/compose-review-snapshot.js";
import { manualExportSurfaceBoundary } from "../exports/types.js";
import type {
  ApiRepositories,
  ConstraintBundleRecord,
  GenerationBriefRecord,
  GenerationOutputRecord,
  ReviewItemRecord
} from "../repositories.js";

export async function registerExportRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/exports/health", async () =>
    exportHealthResponseSchema.parse({
      ...manualExportSurfaceBoundary,
      dbMutation: false,
      externalIntegration: false,
      fileWriting: false,
      providerIntegration: false,
      status: "ok",
      writeRoutes: false
    })
  );

  server.get("/exports/packages/generation-outputs/:outputKey", async (request, reply) => {
    const { outputKey } = request.params as { outputKey: string };
    const output = await repositories.generation.findOutputByKey(outputKey);

    if (!output) {
      return reply.code(404).send({ error: "generation_output_not_found" });
    }

    const brief = await findBriefForOutput(repositories, output);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const [constraintBundle, compatibility, storedEvaluations, review] = await Promise.all([
      findConstraintBundle(repositories, brief),
      repositories.contentGraph.listCompatibility(),
      repositories.generation.listOutputEvaluations(output.outputKey),
      repositories.reviews.findByReviewKey(output.reviewItem.reviewKey)
    ]);

    return exportPackageResponseSchema.parse(
      composeExportPackage({
        brief,
        compatibility,
        constraintBundle,
        evaluations: storedEvaluations ?? output.evaluations,
        output,
        review,
        sourceType: "GENERATION_OUTPUT"
      })
    );
  });

  server.get("/exports/packages/generation-briefs/:briefKey", async (request, reply) => {
    const { briefKey } = request.params as { briefKey: string };
    const brief = await repositories.generation.findBriefByKey(briefKey);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const [constraintBundle, compatibility, review] = await Promise.all([
      findConstraintBundle(repositories, brief),
      repositories.contentGraph.listCompatibility(),
      brief.reviewItem ? repositories.reviews.findByReviewKey(brief.reviewItem.reviewKey) : Promise.resolve(null)
    ]);

    return exportPackageResponseSchema.parse(
      composeExportPackage({
        brief,
        compatibility,
        constraintBundle,
        review,
        sourceType: "GENERATION_BRIEF"
      })
    );
  });

  server.get("/exports/review-snapshots/:reviewKey", async (request, reply) => {
    const { reviewKey } = request.params as { reviewKey: string };
    const review = await repositories.reviews.findByReviewKey(reviewKey);

    if (!review) {
      return reply.code(404).send({ error: "review_item_not_found" });
    }

    return reviewSnapshotResponseSchema.parse(
      composeReviewSnapshot({
        review,
        subjectKey: review.subjectKey,
        title: review.title
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
