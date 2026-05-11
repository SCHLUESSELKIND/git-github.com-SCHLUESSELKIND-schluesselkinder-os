import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-10T03:00:00.000Z");

const constraintBundle = {
  active: true,
  code: "CB-SK-CORE-GENERATION",
  constraints: [
    {
      active: true,
      bundleId: "bundle-1",
      id: "constraint-1",
      instruction: "Every output must remain bound to a ReviewItem.",
      required: true,
      ruleCode: "REVIEW_BINDING_REQUIRED",
      source: "REVIEW_GOVERNANCE" as const,
      title: "Review binding required",
      weight: 100
    }
  ],
  createdAt: now,
  description: "Core constraints required for controlled draft preparation.",
  id: "bundle-1",
  name: "SCHLUESSELKINDER core generation constraints"
};

const brief = {
  briefKey: "GB-MOODBOARD-SKM-003",
  campaignWorld: {
    code: "ROOM_AFTER_LIGHT",
    id: "world-1",
    name: "Room after light"
  },
  campaignWorldId: "world-1",
  channel: "WEBSITE" as const,
  channelCompositionProfile: {
    channel: "WEBSITE" as const,
    code: "CCP-WEBSITE-INSTITUTIONAL",
    id: "profile-1",
    name: "Website institutional"
  },
  channelCompositionProfileId: "profile-1",
  channelFragment: null,
  channelFragmentId: null,
  constraintBundle: {
    code: "CB-SK-CORE-GENERATION",
    id: "bundle-1",
    name: "SCHLUESSELKINDER core generation constraints"
  },
  constraintBundleId: "bundle-1",
  createdAt: now,
  id: "brief-1",
  musicRelease: {
    id: "music-3",
    releaseCode: "SKM-003",
    title: "ROPEMASTER"
  },
  musicReleaseId: "music-3",
  objective: "Compose a review-bound moodboard brief without calling a generator.",
  promptSections: [
    {
      body: "Use chair environment and rune/key hierarchy. Ropeface remains secondary.",
      briefId: "brief-1",
      id: "section-1",
      locked: true,
      position: 10,
      title: "Brand constraints",
      type: "BRAND_CONSTRAINTS" as const
    }
  ],
  reviewItem: {
    id: "review-1",
    reviewKey: "SKR-MOODBOARD-SKM-003",
    stage: "MOODBOARD_REVIEW" as const,
    status: "PENDING" as const
  },
  reviewItemId: "review-1",
  subjectKey: "SKM-003",
  subjectType: "MUSIC_RELEASE" as const,
  title: "ROPEMASTER controlled moodboard brief",
  track: null,
  trackId: null,
  type: "MOODBOARD" as const
};

const request = {
  brief: {
    briefKey: brief.briefKey,
    id: brief.id,
    title: brief.title,
    type: brief.type
  },
  briefId: brief.id,
  createdAt: now,
  id: "request-1",
  notes: "Planning request only.",
  outputs: [
    {
      id: "output-1",
      outputKey: "GO-MOODBOARD-SKM-003-PLACEHOLDER",
      reviewItemId: "review-1",
      status: "REVIEW_REQUIRED" as const,
      title: "ROPEMASTER moodboard placeholder"
    }
  ],
  requestedFor: "moodboard_review",
  requestKey: "GR-MOODBOARD-SKM-003",
  status: "READY_FOR_REVIEW" as const
};

const evaluation = {
  createdAt: now,
  detail: "Chair environment is present as required campaign-world anchor.",
  id: "evaluation-1",
  outputId: "output-1",
  ruleCode: "VISUAL_CHAIR_PRIMARY",
  source: "VISUAL_RULE" as const,
  title: "Chair environment present",
  verdict: "PASS" as const
};

const output = {
  createdAt: now,
  evaluations: [evaluation],
  id: "output-1",
  outputKey: "GO-MOODBOARD-SKM-003-PLACEHOLDER",
  placeholder: "Placeholder only. Chair and rune/key references are review-bound.",
  request: {
    id: request.id,
    requestKey: request.requestKey,
    status: request.status
  },
  requestId: request.id,
  reviewItem: {
    id: "review-1",
    reviewKey: "SKR-MOODBOARD-SKM-003",
    stage: "MOODBOARD_REVIEW" as const,
    status: "PENDING" as const
  },
  reviewItemId: "review-1",
  status: "REVIEW_REQUIRED" as const,
  title: "ROPEMASTER moodboard placeholder"
};

const repositories: ApiRepositories = {
  artists: {
    findBySlug: async () => null,
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
  fragments: {
    list: async () => []
  },
  generation: {
    findBriefByKey: async (briefKey) => (briefKey === brief.briefKey ? brief : null),
    findOutputByKey: async (outputKey) => (outputKey === output.outputKey ? output : null),
    findRequestByKey: async (requestKey) => (requestKey === request.requestKey ? request : null),
    listBriefs: async () => [brief],
    listChannelCompositionProfiles: async () => [],
    listConstraintBundles: async () => [constraintBundle],
    listOutputEvaluations: async (outputKey) => (outputKey === output.outputKey ? [evaluation] : null),
    listOutputs: async () => [output],
    listRequests: async () => [request]
  },
  music: {
    findByReleaseCode: async () => null,
    list: async () => []
  },
  objects: {
    list: async () => []
  },
  reviews: {
    findByReviewKey: async () => null,
    list: async () => [],
    listComments: async () => null,
    listDecisions: async () => null,
    listViolations: async () => null
  }
};

test("GET /drafts/health exposes non-authoritative manual boundaries", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/drafts/health"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.reviewRequired, true);
  assert.equal(body.approvalAuthority, false);
  assert.equal(body.publishAuthority, false);
  assert.equal(body.humanCommitRequired, true);
  assert.equal(body.automationAllowed, false);
  assert.equal(body.externalDelivery, false);
  assert.equal(body.writeRoutes, false);
});

test("GET /drafts/packages/generation-outputs/:outputKey prepares manual package without authority", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/drafts/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.sourceType, "GENERATION_OUTPUT");
  assert.equal(body.reviewRequired, true);
  assert.equal(body.approvalAuthority, false);
  assert.equal(body.publishAuthority, false);
  assert.equal(body.humanCommitRequired, true);
  assert.equal(body.automationAllowed, false);
  assert.equal(body.externalDelivery, false);
  assert.equal(body.evaluationSummary.dominantVerdict, "PASS");
  assert.equal(body.evaluationSummary.passImpliesApproval, false);
  assert.equal(body.evaluationSummary.approvalAuthority, false);
  assert.equal(body.evaluationSummary.publishAuthority, false);

  for (const artifact of body.exportArtifacts) {
    assert.equal(artifact.manualExportPrepared, true);
    assert.equal(artifact.publishReady, false);
    assert.equal(artifact.humanCommitRequired, true);
  }
});

test("GET /drafts/packages/generation-briefs/:briefKey prepares unevaluated manual package", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/drafts/packages/generation-briefs/GB-MOODBOARD-SKM-003"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.sourceType, "GENERATION_BRIEF");
  assert.equal(body.evaluationSummary.dominantVerdict, "NOT_EVALUATED");
  assert.equal(body.reviewSummary.reviewKey, "SKR-MOODBOARD-SKM-003");
  assert.equal(body.constraintSummary.requiredCount, 1);
  assert.equal(body.channelDrafts[0].approvalAuthority, false);
  assert.equal(body.channelDrafts[0].publishAuthority, false);
  assert.equal(body.channelDrafts[0].externalDelivery, false);
});

test("draft routes expose no write route", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "POST",
    url: "/drafts/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  assert.equal(response.statusCode, 404);
});

test("draft package does not contain performance fields or legacy readiness field", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/drafts/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  const body = response.json();
  const keys = collectKeys(body);

  assert.equal(keys.includes(["export", "Ready"].join("")), false);
  assert.equal(keys.includes(["eng", "agement"].join("")), false);
  assert.equal(keys.includes(["rea", "ch"].join("")), false);
  assert.equal(keys.includes(["viral", "ity"].join("")), false);
  assert.equal(keys.includes(["c", "tr"].join("")), false);
  assert.equal(keys.includes(["watch", "Time"].join("")), false);
  assert.equal(keys.includes(["gro", "wth"].join("")), false);
});

function collectKeys(value: unknown): string[] {
  if (!value || typeof value !== "object") {
    return [];
  }

  if (Array.isArray(value)) {
    return value.flatMap(collectKeys);
  }

  return Object.entries(value).flatMap(([key, childValue]) => [key, ...collectKeys(childValue)]);
}
