import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-09T01:00:00.000Z");

const repositories: ApiRepositories = {
  artists: {
    findBySlug: async () => null,
    list: async () => []
  },
  fragments: {
    list: async () => []
  },
  music: {
    findByReleaseCode: async () => null,
    list: async () => []
  },
  objects: {
    list: async () => []
  },
  brandIntelligence: {
    listAudiencePersonas: async () => [
      {
        active: true,
        aestheticAttraction: "Concrete, restraint, hard typography.",
        behavioralPattern: "Studies archive details before acting.",
        code: "POST_CLUB_ISOLATION",
        createdAt: now,
        emotionalState: "Afterhours distance.",
        id: "audience-1",
        name: "Post-club isolation",
        rejectionPattern: "Rejects hype.",
        resonanceReason: "Gives form to the hour after the room empties."
      }
    ],
    listBrandRules: async () => [
      {
        active: true,
        category: "CORE",
        code: "CORE_RADICAL_REDUCTION",
        createdAt: now,
        id: "brand-rule-1",
        severity: "REQUIRED",
        statement: "Use radical reduction.",
        title: "Radical reduction",
        weight: 100
      }
    ],
    listChannelRules: async () => [
      {
        active: true,
        channel: "WEBSITE",
        code: "CHANNEL_WEBSITE_INSTITUTIONAL",
        createdAt: now,
        id: "channel-rule-1",
        rule: "Website language stays institutional.",
        severity: "REQUIRED",
        title: "Website as label system",
        weight: 100
      }
    ],
    listForbiddenEnergy: async () => [
      {
        active: true,
        code: "HORROR",
        createdAt: now,
        id: "forbidden-1",
        label: "Horror",
        reason: "Pushes the label toward props.",
        severity: "REQUIRED",
        weight: 100
      }
    ],
    listLanguageRules: async () => [
      {
        active: true,
        code: "LANG_GERMAN_FIRST",
        createdAt: now,
        id: "language-rule-1",
        rule: "German first.",
        severity: "REQUIRED",
        title: "German-first fragments",
        weight: 100
      }
    ],
    listScoringRules: async () => [
      {
        active: true,
        code: "SCORE_ICONIC_RESTRAINT",
        createdAt: now,
        description: "Rewards outputs that become more iconic by removing noise.",
        id: "scoring-1",
        maxScore: 10,
        title: "Iconic restraint",
        weight: 3
      }
    ],
    listVisualRules: async () => [
      {
        active: true,
        code: "VISUAL_CHAIR_PRIMARY",
        createdAt: now,
        id: "visual-rule-1",
        rule: "The dungeon/chair image is primary.",
        severity: "REQUIRED",
        title: "Chair environment leads",
        weight: 100
      }
    ],
    listVoiceProfiles: async () => [
      {
        active: true,
        code: "MASTERBRAND",
        createdAt: now,
        description: "Institutional SCHLUESSELKINDER voice.",
        id: "voice-1",
        name: "Masterbrand"
      }
    ]
  }
};

test("GET /brand-intelligence returns all read-only intelligence groups", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/brand-intelligence"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.brandRules[0].code, "CORE_RADICAL_REDUCTION");
  assert.equal(body.voiceProfiles[0].code, "MASTERBRAND");
  assert.equal(body.audiencePersonas[0].code, "POST_CLUB_ISOLATION");
  assert.equal(body.scoringRules[0].code, "SCORE_ICONIC_RESTRAINT");
});

test("GET /brand-intelligence/audience-personas separates audience psychology from voice", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/brand-intelligence/audience-personas"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].code, "POST_CLUB_ISOLATION");
  assert.equal("description" in body[0], false);
  assert.equal("emotionalState" in body[0], true);
});

test("GET /brand-intelligence/voice-profiles returns system speech profiles", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/brand-intelligence/voice-profiles"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].code, "MASTERBRAND");
  assert.equal("emotionalState" in body[0], false);
});
