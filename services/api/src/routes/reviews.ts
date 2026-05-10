import type { FastifyInstance } from "fastify";
import {
  approvalCommentListResponseSchema,
  approvalDecisionListResponseSchema,
  reviewItemListResponseSchema,
  reviewItemResponseSchema,
  reviewStageListResponseSchema,
  reviewStatusListResponseSchema,
  ruleViolationListResponseSchema
} from "../contracts/reviews.js";
import type { ApiRepositories } from "../repositories.js";
import {
  mapApprovalComment,
  mapApprovalDecision,
  mapReviewItem,
  mapRuleViolation
} from "./mappers.js";

const reviewStages = ["MOODBOARD_REVIEW", "CONTENT_REVIEW", "SCHEDULE_REVIEW"] as const;
const reviewStatuses = ["PENDING", "APPROVED", "REJECTED", "NEEDS_REVISION", "ARCHIVED"] as const;

export async function registerReviewRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/reviews", async () =>
    reviewItemListResponseSchema.parse((await repositories.reviews.list()).map(mapReviewItem))
  );

  server.get("/reviews/stages", async () => reviewStageListResponseSchema.parse(reviewStages));

  server.get("/reviews/statuses", async () => reviewStatusListResponseSchema.parse(reviewStatuses));

  server.get("/reviews/:reviewKey", async (request, reply) => {
    const { reviewKey } = request.params as { reviewKey: string };
    const reviewItem = await repositories.reviews.findByReviewKey(reviewKey);

    if (!reviewItem) {
      return reply.code(404).send({ error: "review_item_not_found" });
    }

    return reviewItemResponseSchema.parse(mapReviewItem(reviewItem));
  });

  server.get("/reviews/:reviewKey/decisions", async (request, reply) => {
    const { reviewKey } = request.params as { reviewKey: string };
    const decisions = await repositories.reviews.listDecisions(reviewKey);

    if (!decisions) {
      return reply.code(404).send({ error: "review_item_not_found" });
    }

    return approvalDecisionListResponseSchema.parse(decisions.map(mapApprovalDecision));
  });

  server.get("/reviews/:reviewKey/comments", async (request, reply) => {
    const { reviewKey } = request.params as { reviewKey: string };
    const comments = await repositories.reviews.listComments(reviewKey);

    if (!comments) {
      return reply.code(404).send({ error: "review_item_not_found" });
    }

    return approvalCommentListResponseSchema.parse(comments.map(mapApprovalComment));
  });

  server.get("/reviews/:reviewKey/violations", async (request, reply) => {
    const { reviewKey } = request.params as { reviewKey: string };
    const violations = await repositories.reviews.listViolations(reviewKey);

    if (!violations) {
      return reply.code(404).send({ error: "review_item_not_found" });
    }

    return ruleViolationListResponseSchema.parse(violations.map(mapRuleViolation));
  });
}
