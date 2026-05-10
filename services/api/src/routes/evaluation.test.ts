import assert from "node:assert/strict";
import { test } from "node:test";
import { evaluationRepositories } from "../evaluation/fixtures/evaluation-fixtures.js";
import { buildServer } from "../server.js";

test("GET /evaluation/health exposes non-execution boundaries", async () => {
  const server = buildServer({ repositories: evaluationRepositories });

  const response = await server.inject({
    method: "GET",
    url: "/evaluation/health"
  });
  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.execution, false);
  assert.equal(body.writeRoutes, false);
  assert.equal(body.providerIntegration, false);
  assert.equal(body.approvalAuthority, false);
});

test("GET /evaluation/generation/outputs/:outputKey returns report without approval authority", async () => {
  const server = buildServer({ repositories: evaluationRepositories });

  const response = await server.inject({
    method: "GET",
    url: "/evaluation/generation/outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });
  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.subject.type, "GENERATION_OUTPUT");
  assert.equal(body.reviewRequired, true);
  assert.equal(body.usableWithoutReview, false);
  assert.equal(body.approvalAuthority, false);
  assert.equal(body.verdictMeaning.includes("No verdict equals approval."), true);
});

test("GET /evaluation/generation/briefs/:briefKey evaluates brief material only", async () => {
  const server = buildServer({ repositories: evaluationRepositories });

  const response = await server.inject({
    method: "GET",
    url: "/evaluation/generation/briefs/GB-MOODBOARD-SKM-003"
  });
  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.subject.type, "GENERATION_BRIEF");
  assert.equal(body.approvalAuthority, false);
  assert.equal(Array.isArray(body.resolvedConstraints), true);
});

test("GET /evaluation/rules/constraints/:bundleCode resolves constraints without writing", async () => {
  const server = buildServer({ repositories: evaluationRepositories });

  const response = await server.inject({
    method: "GET",
    url: "/evaluation/rules/constraints/CB-SK-CORE-GENERATION"
  });
  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.bundle.code, "CB-SK-CORE-GENERATION");
  assert.equal(body.reviewRequired, true);
  assert.equal(body.usableWithoutReview, false);
  assert.equal(body.approvalAuthority, false);
  assert.equal(
    body.findings.some((finding: { code: string }) => finding.code === "CONSTRAINT_RULE_UNRESOLVED"),
    false
  );
});

test("evaluation routes do not expose write endpoints", async () => {
  const server = buildServer({ repositories: evaluationRepositories });

  const response = await server.inject({
    method: "POST",
    url: "/evaluation/generation/outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  assert.equal(response.statusCode, 404);
});
