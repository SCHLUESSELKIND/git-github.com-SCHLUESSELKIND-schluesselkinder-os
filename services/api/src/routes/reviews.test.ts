import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-10T00:00:00.000Z");

const decision = {
  createdAt: now,
  decidedBy: "SYSTEM_SEED",
  id: "decision-1",
  note: "Seeded historical decision to demonstrate append-only review history.",
  reviewItemId: "review-1",
  type: "REQUEST_REVISION" as const
};

const comment = {
  author: "SYSTEM_SEED",
  body: "Needs revision is represented as current materialized status; decision history remains append-only.",
  createdAt: now,
  id: "comment-1",
  reviewItemId: "review-1"
};

const violation = {
  active: true,
  createdAt: now,
  detail: "Archive content must keep radical reduction.",
  id: "violation-1",
  reviewItemId: "review-1",
  ruleCode: "CORE_RADICAL_REDUCTION",
  severity: "REQUIRED" as const,
  source: "BRAND_RULE" as const,
  title: "Radical reduction required"
};

const reviewItem = {
  asset: null,
  assetId: null,
  campaignWorld: {
    code: "COLD_ARCHIVE",
    id: "world-1",
    name: "Cold archive"
  },
  campaignWorldId: "world-1",
  channelFragment: null,
  channelFragmentId: null,
  comments: [comment],
  createdAt: now,
  decisions: [decision],
  id: "review-1",
  musicRelease: null,
  musicReleaseId: null,
  releaseFragment: null,
  releaseFragmentId: null,
  reviewKey: "SKR-CONTENT-COLD-ARCHIVE",
  stage: "CONTENT_REVIEW" as const,
  status: "NEEDS_REVISION" as const,
  subjectKey: "COLD_ARCHIVE",
  subjectType: "CAMPAIGN_WORLD" as const,
  summary: "Content review shell for COLD_ARCHIVE.",
  title: "COLD_ARCHIVE content review",
  track: null,
  trackId: null,
  updatedAt: now,
  violations: [violation]
};

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
    listAudiencePersonas: async () => [],
    listBrandRules: async () => [],
    listChannelRules: async () => [],
    listForbiddenEnergy: async () => [],
    listLanguageRules: async () => [],
    listScoringRules: async () => [],
    listVisualRules: async () => [],
    listVoiceProfiles: async () => []
  },
  contentGraph: {
    findMusicReleaseGraph: async () => null,
    listAssets: async () => [],
    listAssetTags: async () => [],
    listCampaignWorlds: async () => [],
    listChannelFragments: async () => [],
    listCompatibility: async () => [],
    listMoodReferences: async () => [],
    listReleaseFragments: async () => [],
    listVisualEnvironments: async () => []
  },
  reviews: {
    findByReviewKey: async (reviewKey) => (reviewKey === reviewItem.reviewKey ? reviewItem : null),
    list: async () => [reviewItem],
    listComments: async (reviewKey) => (reviewKey === reviewItem.reviewKey ? [comment] : null),
    listDecisions: async (reviewKey) => (reviewKey === reviewItem.reviewKey ? [decision] : null),
    listViolations: async (reviewKey) => (reviewKey === reviewItem.reviewKey ? [violation] : null)
  }
};

test("GET /reviews returns read-only review items", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/reviews"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].reviewKey, "SKR-CONTENT-COLD-ARCHIVE");
  assert.equal(body[0].status, "NEEDS_REVISION");
  assert.equal(body[0].decisions[0].type, "REQUEST_REVISION");
});

test("GET /reviews/:reviewKey/decisions exposes append-only history records", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/reviews/SKR-CONTENT-COLD-ARCHIVE/decisions"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].type, "REQUEST_REVISION");
  assert.equal("status" in body[0], false);
});

test("GET /reviews/:reviewKey/violations returns source and ruleCode without hard rule joins", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/reviews/SKR-CONTENT-COLD-ARCHIVE/violations"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].source, "BRAND_RULE");
  assert.equal(body[0].ruleCode, "CORE_RADICAL_REDUCTION");
});

test("review routes do not expose write endpoints", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "POST",
    url: "/reviews"
  });

  assert.equal(response.statusCode, 404);
});
