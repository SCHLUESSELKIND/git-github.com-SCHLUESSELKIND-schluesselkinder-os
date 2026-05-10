import { compareReportToFixture } from "./compare-reports.js";
import type { CalibrationFixture, CalibrationFixtureResult, CalibrationSuiteResult } from "./fixture-schema.js";
import { evaluateGenerationBrief, evaluateGenerationOutput } from "../evaluate-generation-output.js";

export function runCalibrationFixture(fixture: CalibrationFixture): CalibrationFixtureResult {
  const report =
    fixture.input.subject.type === "GENERATION_BRIEF"
      ? evaluateGenerationBrief(fixture.input)
      : evaluateGenerationOutput(fixture.input);
  const failures = compareReportToFixture(fixture, report);

  return {
    failures,
    fixture,
    passed: failures.length === 0,
    report
  };
}

export function runCalibrationFixtureSuite(fixtures: readonly CalibrationFixture[]): CalibrationSuiteResult {
  const results = fixtures.map(runCalibrationFixture);
  const failures = results.flatMap((result) => result.failures);

  return {
    failed: results.filter((result) => !result.passed).length,
    failures,
    passed: results.filter((result) => result.passed).length,
    results,
    total: results.length
  };
}
