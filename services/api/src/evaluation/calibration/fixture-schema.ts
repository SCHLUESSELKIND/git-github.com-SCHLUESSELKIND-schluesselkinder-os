import type { EvaluationAxis, EvaluationInput, EvaluationReport, EvaluationVerdict } from "../types.js";

export type RedTeamCategory =
  | "CYBERPUNK_OVERLOAD"
  | "STARTUP_SAAS_LANGUAGE"
  | "FAKE_LUXURY"
  | "MEME_IRONY"
  | "TIKTOK_BAIT"
  | "OVER_LOGOING"
  | "ROPEFACE_DOMINANCE"
  | "AI_MOODBOARD_SLUDGE"
  | "HYPE_LANGUAGE"
  | "TREND_CHASING"
  | "CREATOR_ECONOMY_LANGUAGE"
  | "MOTIVATIONAL_FASHION_LANGUAGE"
  | "EXCESSIVE_EXPLANATION"
  | "ARCHIVE_INCOHERENCE"
  | "GOVERNANCE_BOUNDARY";

export type CalibrationScoreRange = Readonly<{
  max: number;
  min: number;
}>;

export type CalibrationExpectation = Readonly<{
  expectedDegradedAxes: EvaluationAxis[];
  expectedDominantRule: string | null;
  expectedFindingCodes: string[];
  expectedScoreRange: CalibrationScoreRange;
  expectedVerdict: EvaluationVerdict;
  mustNotContain: string[];
}>;

export type CalibrationFixture = Readonly<{
  category: RedTeamCategory;
  description: string;
  expectation: CalibrationExpectation;
  input: EvaluationInput;
  key: string;
  title: string;
}>;

export type CalibrationFailure = Readonly<{
  code: string;
  detail: string;
  expected: unknown;
  actual: unknown;
}>;

export type CalibrationFixtureResult = Readonly<{
  failures: CalibrationFailure[];
  fixture: CalibrationFixture;
  passed: boolean;
  report: EvaluationReport;
}>;

export type CalibrationSuiteResult = Readonly<{
  failed: number;
  failures: CalibrationFailure[];
  passed: number;
  results: CalibrationFixtureResult[];
  total: number;
}>;
