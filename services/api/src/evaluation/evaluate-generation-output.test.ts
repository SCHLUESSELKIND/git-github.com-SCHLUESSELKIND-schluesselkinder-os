import assert from "node:assert/strict";
import { test } from "node:test";
import { evaluateGenerationOutput } from "./evaluate-generation-output.js";
import { cleanEvaluationInput, failingEvaluationInput } from "./fixtures/evaluation-fixtures.js";

test("evaluateGenerationOutput returns PASS without approval authority for clean review-bound material", () => {
  const report = evaluateGenerationOutput(cleanEvaluationInput);

  assert.equal(report.verdict, "PASS");
  assert.equal(report.reviewRequired, true);
  assert.equal(report.usableWithoutReview, false);
  assert.equal(report.approvalAuthority, false);
  assert.equal(report.findings.length, 0);
});

test("evaluateGenerationOutput returns FAIL for forbidden energy and forbidden graph usage", () => {
  const report = evaluateGenerationOutput(failingEvaluationInput);

  assert.equal(report.verdict, "FAIL");
  assert.equal(report.findings.some((finding) => finding.code === "FORBIDDEN_ENERGY_CYBERPUNK_OVERLOAD"), true);
  assert.equal(report.findings.some((finding) => finding.code === "GRAPH_FORBIDDEN_ASSET_USED"), true);
  assert.equal(report.score.grade, "BLOCKED");
});

test("evaluateGenerationOutput fails when review binding is missing", () => {
  const report = evaluateGenerationOutput({
    ...cleanEvaluationInput,
    reviewBinding: null
  });

  assert.equal(report.verdict, "FAIL");
  assert.equal(report.findings.some((finding) => finding.code === "REVIEW_BINDING_MISSING"), true);
});

test("signal score remains brand-first and contains no engagement axis", () => {
  const report = evaluateGenerationOutput(cleanEvaluationInput);

  assert.equal(report.score.axes.some((axis) => axis.axis.includes("ENGAGEMENT")), false);
  assert.equal(report.score.axes.some((axis) => axis.axis.includes("VIRAL")), false);
  assert.equal(report.score.axes.some((axis) => axis.axis.includes("REACH")), false);
});
