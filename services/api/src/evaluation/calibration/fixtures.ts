import type { CalibrationFixture } from "./fixture-schema.js";
import { createEvaluationTextInput } from "../evaluate-generation-output.js";
import { cleanEvaluationInput } from "../fixtures/evaluation-fixtures.js";
import type { EvaluationInput, ForbiddenEnergyInput } from "../types.js";

const blockedScoreRange = { min: 65, max: 75 };
const globalForbiddenReportTerms = ["ctr", "reach", "virality", "watchtime", "watch time", "follower growth"];
const forbiddenEnergyCatalog: ForbiddenEnergyInput[] = [
  forbiddenEnergy("AI_MOODBOARD", "AI moodboard", "Detects prompt-aesthetic and collage drift."),
  forbiddenEnergy("CYBERPUNK_OVERLOAD", "Cyberpunk overload", "Detects generic neon dystopia."),
  forbiddenEnergy("FAKE_LUXURY", "Fake luxury", "Detects status-flex language and fake premium claims."),
  forbiddenEnergy("HYPE_LANGUAGE", "Hype language", "Detects promotional hype vocabulary."),
  forbiddenEnergy("ARCHIVE_INCOHERENCE", "Archive incoherence", "Detects mixed-system object archive drift."),
  forbiddenEnergy("CREATOR_ECONOMY_LANGUAGE", "Creator economy language", "Detects audience-building and monetization language."),
  forbiddenEnergy("EXCESSIVE_EXPLANATION", "Excessive explanation", "Detects explanatory copy that weakens restraint."),
  forbiddenEnergy("MEME_IRONY", "Meme irony", "Detects internet irony and meme phrasing."),
  forbiddenEnergy("MOTIVATIONAL_FASHION", "Motivational fashion", "Detects self-help fashion copy."),
  forbiddenEnergy("OVER_LOGOING", "Over-logoing", "Detects logo repetition as visual noise."),
  forbiddenEnergy("ROPEFACE_DOMINANCE", "Ropeface dominance", "Detects artist stamp promoted into masterbrand hierarchy."),
  forbiddenEnergy("SHOPIFY_MERCH", "Shopify merch language", "Detects generic store language."),
  forbiddenEnergy("STARTUP_SAAS", "Startup SaaS", "Detects platform and growth-product language."),
  forbiddenEnergy("TIKTOK_BAIT", "TikTok bait", "Detects short-form bait structures."),
  forbiddenEnergy("TREND_CHASING", "Trend chasing", "Detects algorithmic trend language.")
];

export const cleanCalibrationFixture: CalibrationFixture = {
  category: "GOVERNANCE_BOUNDARY",
  description: "A clean, review-bound baseline must pass without approval authority.",
  expectation: {
    expectedDegradedAxes: [],
    expectedDominantRule: null,
    expectedFindingCodes: [],
    expectedScoreRange: { min: 100, max: 100 },
    expectedVerdict: "PASS",
    mustNotContain: globalForbiddenReportTerms
  },
  input: {
    ...cleanEvaluationInput,
    forbiddenEnergy: forbiddenEnergyCatalog
  },
  key: "CAL-CLEAN-REVIEW-BOUND",
  title: "Clean review-bound material"
};

export const redTeamFixtures: CalibrationFixture[] = [
  driftFixture({
    category: "CYBERPUNK_OVERLOAD",
    key: "CAL-RED-CYBERPUNK-OVERLOAD",
    title: "Cyberpunk overload",
    driftCode: "CYBERPUNK_OVERLOAD",
    body: "Use chair environment and rune/key system, then add a neon gradient cyberpunk layer."
  }),
  driftFixture({
    category: "STARTUP_SAAS_LANGUAGE",
    key: "CAL-RED-STARTUP-SAAS",
    title: "Startup SaaS language",
    driftCode: "STARTUP_SAAS",
    body: "Use chair environment and rune/key system. Join us to unlock the community platform."
  }),
  driftFixture({
    category: "FAKE_LUXURY",
    key: "CAL-RED-FAKE-LUXURY",
    title: "Fake luxury",
    driftCode: "FAKE_LUXURY",
    body: "Use chair environment and rune/key system as a premium lifestyle status symbol."
  }),
  driftFixture({
    category: "MEME_IRONY",
    key: "CAL-RED-MEME-IRONY",
    title: "Meme irony",
    driftCode: "MEME_IRONY",
    body: "Use chair environment and rune/key system. It is giving basement vibes only."
  }),
  driftFixture({
    category: "TIKTOK_BAIT",
    key: "CAL-RED-TIKTOK-BAIT",
    title: "TikTok bait",
    driftCode: "TIKTOK_BAIT",
    body: "Use chair environment and rune/key system. POV: watch till the end with a viral sound."
  }),
  driftFixture({
    category: "OVER_LOGOING",
    key: "CAL-RED-OVER-LOGOING",
    title: "Over-logoing",
    driftCode: "OVER_LOGOING",
    body: "Use chair environment and rune/key system, then build a logo wall with all-over logo treatment."
  }),
  driftFixture({
    category: "ROPEFACE_DOMINANCE",
    key: "CAL-RED-ROPEFACE-DOMINANCE",
    title: "Ropeface dominance",
    driftCode: "ROPEFACE_DOMINANCE",
    body: "Use chair environment and rune/key system, then make ropeface hero logo the institutional mark."
  }),
  driftFixture({
    category: "AI_MOODBOARD_SLUDGE",
    key: "CAL-RED-AI-MOODBOARD-SLUDGE",
    title: "AI moodboard sludge",
    driftCode: "AI_MOODBOARD",
    body: "Use chair environment and rune/key system, then assemble it as a midjourney moodboard collage."
  }),
  driftFixture({
    category: "HYPE_LANGUAGE",
    key: "CAL-RED-HYPE-LANGUAGE",
    title: "Hype language",
    driftCode: "HYPE_LANGUAGE",
    body: "Use chair environment and rune/key system. This insane drop is a must cop."
  }),
  driftFixture({
    category: "TREND_CHASING",
    key: "CAL-RED-TREND-CHASING",
    title: "Trend chasing",
    driftCode: "TREND_CHASING",
    body: "Use chair environment and rune/key system as a trend alert for the current trend."
  }),
  driftFixture({
    category: "CREATOR_ECONOMY_LANGUAGE",
    key: "CAL-RED-CREATOR-ECONOMY",
    title: "Creator economy language",
    driftCode: "CREATOR_ECONOMY_LANGUAGE",
    body: "Use chair environment and rune/key system to build your audience as a content creator."
  }),
  driftFixture({
    category: "MOTIVATIONAL_FASHION_LANGUAGE",
    key: "CAL-RED-MOTIVATIONAL-FASHION",
    title: "Motivational fashion language",
    driftCode: "MOTIVATIONAL_FASHION",
    body: "Use chair environment and rune/key system to empower your style and be your best self."
  }),
  driftFixture({
    category: "EXCESSIVE_EXPLANATION",
    key: "CAL-RED-EXCESSIVE-EXPLANATION",
    title: "Excessive explanation",
    driftCode: "EXCESSIVE_EXPLANATION",
    body: "Use chair environment and rune/key system. Let us explain what this means is restraint and identity."
  }),
  driftFixture({
    category: "ARCHIVE_INCOHERENCE",
    key: "CAL-RED-ARCHIVE-INCOHERENCE",
    title: "Archive incoherence",
    driftCode: "ARCHIVE_INCOHERENCE",
    body: "Use chair environment and rune/key system, then frame the objects as a random capsule of assorted vibes."
  })
];

export const calibrationFixtures: CalibrationFixture[] = [cleanCalibrationFixture, ...redTeamFixtures];

function driftFixture(input: {
  body: string;
  category: CalibrationFixture["category"];
  driftCode: string;
  key: string;
  title: string;
}): CalibrationFixture {
  return {
    category: input.category,
    description: `${input.title} must be blocked before review while preserving the no-approval boundary.`,
    expectation: {
      expectedDegradedAxes: [
        "IDENTITY_PROTECTION",
        "CULTURAL_CREDIBILITY",
        "PRESSURE_WITHOUT_NOISE",
        "RULE_ADHERENCE"
      ],
      expectedDominantRule: input.driftCode,
      expectedFindingCodes: [`FORBIDDEN_ENERGY_${input.driftCode}`],
      expectedScoreRange: blockedScoreRange,
      expectedVerdict: "FAIL",
      mustNotContain: globalForbiddenReportTerms
    },
    input: buildInput(input.key, input.body),
    key: input.key,
    title: input.title
  };
}

function buildInput(key: string, body: string): EvaluationInput {
  return {
    ...cleanEvaluationInput,
    forbiddenEnergy: forbiddenEnergyCatalog,
    subject: {
      key,
      type: "GENERATION_OUTPUT"
    },
    text: createEvaluationTextInput([body])
  };
}

function forbiddenEnergy(code: string, label: string, reason: string): ForbiddenEnergyInput {
  return {
    code,
    label,
    reason,
    severity: "REQUIRED",
    weight: 100
  };
}
