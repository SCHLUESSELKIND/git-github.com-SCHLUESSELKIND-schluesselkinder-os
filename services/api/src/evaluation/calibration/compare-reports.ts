import { explainEvaluationReport } from "./explain-report.js";
import type { CalibrationFailure, CalibrationFixture } from "./fixture-schema.js";
import type { EvaluationAxis, EvaluationReport } from "../types.js";

export function compareReportToFixture(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  return [
    ...compareAuthorityBoundary(report),
    ...compareVerdict(fixture, report),
    ...compareFindingCodes(fixture, report),
    ...compareDominantRule(fixture, report),
    ...compareScoreRange(fixture, report),
    ...compareDegradedAxes(fixture, report),
    ...compareForbiddenTerms(fixture, report)
  ];
}

function compareAuthorityBoundary(report: EvaluationReport): CalibrationFailure[] {
  const failures: CalibrationFailure[] = [];

  if (!report.reviewRequired) {
    failures.push(failure("REPORT_REVIEW_REQUIRED", true, report.reviewRequired));
  }

  if (report.usableWithoutReview) {
    failures.push(failure("REPORT_USABLE_WITHOUT_REVIEW", false, report.usableWithoutReview));
  }

  if (report.approvalAuthority) {
    failures.push(failure("REPORT_APPROVAL_AUTHORITY", false, report.approvalAuthority));
  }

  return failures;
}

function compareVerdict(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  if (report.verdict === fixture.expectation.expectedVerdict) {
    return [];
  }

  return [
    {
      code: "VERDICT_MISMATCH",
      detail: `${fixture.key} expected ${fixture.expectation.expectedVerdict} but received ${report.verdict}.`,
      expected: fixture.expectation.expectedVerdict,
      actual: report.verdict
    }
  ];
}

function compareFindingCodes(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  const actualCodes = new Set(report.findings.map((finding) => finding.code));

  return fixture.expectation.expectedFindingCodes
    .filter((code) => !actualCodes.has(code))
    .map((code) => ({
      code: "EXPECTED_FINDING_MISSING",
      detail: `${fixture.key} expected finding ${code}.`,
      expected: code,
      actual: [...actualCodes]
    }));
}

function compareDominantRule(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  const explanation = explainEvaluationReport(report);

  if (explanation.dominantRule === fixture.expectation.expectedDominantRule) {
    return [];
  }

  return [
    {
      code: "DOMINANT_RULE_MISMATCH",
      detail: `${fixture.key} expected dominant rule ${fixture.expectation.expectedDominantRule ?? "none"}.`,
      expected: fixture.expectation.expectedDominantRule,
      actual: explanation.dominantRule
    }
  ];
}

function compareScoreRange(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  const { max, min } = fixture.expectation.expectedScoreRange;

  if (report.score.normalized >= min && report.score.normalized <= max) {
    return [];
  }

  return [
    {
      code: "SCORE_RANGE_MISMATCH",
      detail: `${fixture.key} score ${report.score.normalized} is outside ${min}-${max}.`,
      expected: fixture.expectation.expectedScoreRange,
      actual: report.score.normalized
    }
  ];
}

function compareDegradedAxes(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  const degraded = new Set(report.score.axes.filter((axis) => axis.score < axis.maxScore).map((axis) => axis.axis));

  return fixture.expectation.expectedDegradedAxes
    .filter((axis) => !degraded.has(axis))
    .map((axis) => ({
      code: "EXPECTED_AXIS_NOT_DEGRADED",
      detail: `${fixture.key} expected degraded axis ${axis}.`,
      expected: axis,
      actual: [...degraded] as EvaluationAxis[]
    }));
}

function compareForbiddenTerms(fixture: CalibrationFixture, report: EvaluationReport): CalibrationFailure[] {
  const serialized = JSON.stringify(report).toLowerCase();

  return fixture.expectation.mustNotContain
    .map((term) => term.toLowerCase())
    .filter((term) => serialized.includes(term))
    .map((term) => ({
      code: "FORBIDDEN_REPORT_TERM",
      detail: `${fixture.key} report contains forbidden calibration term "${term}".`,
      expected: `absence of ${term}`,
      actual: term
    }));
}

function failure(code: string, expected: unknown, actual: unknown): CalibrationFailure {
  return {
    code,
    detail: `${code} failed.`,
    expected,
    actual
  };
}
