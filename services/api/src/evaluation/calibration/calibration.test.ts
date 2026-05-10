import assert from "node:assert/strict";
import { test } from "node:test";
import { compareReportToFixture } from "./compare-reports.js";
import { detectRuleConflicts } from "./detect-rule-conflicts.js";
import { explainEvaluationReport } from "./explain-report.js";
import { calibrationFixtures, cleanCalibrationFixture, redTeamFixtures } from "./fixtures.js";
import { runCalibrationFixture, runCalibrationFixtureSuite } from "./run-fixture-suite.js";

test("calibration fixture suite remains deterministic and within expected score ranges", () => {
  const suite = runCalibrationFixtureSuite(calibrationFixtures);

  assert.equal(
    suite.failures.map((failure) => `${failure.code}: ${failure.detail}`).join("\n"),
    ""
  );
  assert.equal(suite.total, calibrationFixtures.length);
  assert.equal(suite.failed, 0);
});

test("red-team fixtures block drift without approval authority", () => {
  for (const fixture of redTeamFixtures) {
    const result = runCalibrationFixture(fixture);

    assert.equal(result.report.verdict, "FAIL");
    assert.equal(result.report.reviewRequired, true);
    assert.equal(result.report.usableWithoutReview, false);
    assert.equal(result.report.approvalAuthority, false);
    assert.equal(result.failures.length, 0);
  }
});

test("clean PASS fixture still has no approval authority", () => {
  const result = runCalibrationFixture(cleanCalibrationFixture);
  const explanation = explainEvaluationReport(result.report);

  assert.equal(result.report.verdict, "PASS");
  assert.equal(explanation.verdictReason.includes("Human review remains required."), true);
  assert.equal(explanation.reviewRequired, true);
  assert.equal(explanation.usableWithoutReview, false);
  assert.equal(explanation.approvalAuthority, false);
  assert.equal(explanation.dominantRule, null);
});

test("comparison catches score and finding drift", () => {
  const result = runCalibrationFixture(redTeamFixtures[0]);
  const failures = compareReportToFixture(
    {
      ...redTeamFixtures[0],
      expectation: {
        ...redTeamFixtures[0].expectation,
        expectedFindingCodes: ["NON_EXISTENT_FINDING"],
        expectedScoreRange: { min: 100, max: 100 }
      }
    },
    result.report
  );

  assert.equal(failures.some((failure) => failure.code === "EXPECTED_FINDING_MISSING"), true);
  assert.equal(failures.some((failure) => failure.code === "SCORE_RANGE_MISMATCH"), true);
});

test("conflict detector reports contradictory compatibility and uncovered detectors", () => {
  const baseBundle = cleanCalibrationFixture.input.constraintBundle;
  assert.ok(baseBundle);

  const conflicts = detectRuleConflicts({
    ...cleanCalibrationFixture.input,
    compatibility: [
      ...cleanCalibrationFixture.input.compatibility,
      {
        kind: "CAMPAIGN_WORLD_ASSET",
        reason: "Contradictory calibration fixture.",
        sourceCode: "ROOM_AFTER_LIGHT",
        sourceLabel: "Room after light",
        targetCode: "RUNE_KEY_SYMBOL",
        targetLabel: "Rune/key symbol",
        verdict: "FORBIDDEN",
        weight: 100
      }
    ],
    constraintBundle: {
      ...baseBundle,
      constraints: [
        ...baseBundle.constraints,
        {
          active: true,
          instruction: "Missing rule reference fixture.",
          required: true,
          ruleCode: "MISSING_RULE_CODE",
          source: "BRAND_RULE",
          title: "Missing rule reference",
          weight: 100
        }
      ]
    },
    forbiddenEnergy: [
      ...cleanCalibrationFixture.input.forbiddenEnergy,
      {
        code: "UNMAPPED_DRIFT",
        label: "Unmapped drift",
        reason: "Fixture for missing deterministic detector coverage.",
        severity: "REQUIRED",
        weight: 100
      }
    ],
    scoringRules: []
  });

  assert.equal(conflicts.some((conflict) => conflict.code === "COMPATIBILITY_REQUIRED_AND_FORBIDDEN"), true);
  assert.equal(conflicts.some((conflict) => conflict.code === "CONSTRAINT_REFERENCES_MISSING_RULE"), true);
  assert.equal(conflicts.some((conflict) => conflict.code === "FORBIDDEN_ENERGY_WITHOUT_OPERATIONAL_TERMS"), true);
  assert.equal(conflicts.some((conflict) => conflict.code === "SCORING_RULES_MISSING"), true);
});
