import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-10T01:00:00.000Z");

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
  description: "Core constraints required for controlled generation planning.",
  id: "bundle-1",
  name: "SCHLUESSELKINDER core generation constraints"
};

const channelCompositionProfile = {
  active: true,
  channel: "WEBSITE" as const,
  code: "CCP-WEBSITE-INSTITUTIONAL",
  createdAt: now,
  description: "Website composition profile.",
  id: "profile-1",
  name: "Website institutional",
  outputShape: "One dominant statement, metadata fragments, no CTA pressure."
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
  channelCompositionProfile,
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
      body: "Subject: SKM-003 ROPEMASTER.",
      briefId: "brief-1",
      id: "section-1",
      locked: true,
      position: 10,
      title: "Subject context",
      type: "CONTEXT" as const
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
    briefKey: "GB-MOODBOARD-SKM-003",
    id: "brief-1",
    title: "ROPEMASTER controlled moodboard brief",
    type: "MOODBOARD" as const
  },
  briefId: "brief-1",
  createdAt: now,
  id: "request-1",
  notes: "Planning request only. No AI provider exists.",
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
  placeholder: "Placeholder only. No model output, media file, prompt execution, or publishable asset exists.",
  request: {
    id: "request-1",
    requestKey: "GR-MOODBOARD-SKM-003",
    status: "READY_FOR_REVIEW" as const
  },
  requestId: "request-1",
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
    findByReviewKey: async () => null,
    list: async () => [],
    listComments: async () => null,
    listDecisions: async () => null,
    listViolations: async () => null
  },
  generation: {
    findBriefByKey: async (briefKey) => (briefKey === brief.briefKey ? brief : null),
    findOutputByKey: async (outputKey) => (outputKey === output.outputKey ? output : null),
    findRequestByKey: async (requestKey) => (requestKey === request.requestKey ? request : null),
    listBriefs: async () => [brief],
    listChannelCompositionProfiles: async () => [channelCompositionProfile],
    listConstraintBundles: async () => [constraintBundle],
    listOutputEvaluations: async (outputKey) => (outputKey === output.outputKey ? [evaluation] : null),
    listOutputs: async () => [output],
    listRequests: async () => [request]
  }
};

test("GET /generation returns controlled planning records without execution", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/generation"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.briefs[0].briefKey, "GB-MOODBOARD-SKM-003");
  assert.equal(body.requests[0].status, "READY_FOR_REVIEW");
  assert.equal(body.outputs[0].status, "REVIEW_REQUIRED");
  assert.equal(body.outputs[0].reviewItemId, "review-1");
  assert.equal(body.outputs[0].reviewItem.reviewKey, "SKR-MOODBOARD-SKM-003");
});

test("GET /generation/outputs/:outputKey keeps approval truth out of output status", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/generation/outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.status, "REVIEW_REQUIRED");
  assert.equal(body.status === "APPROVED", false);
  assert.equal(body.reviewItemId, "review-1");
  assert.equal(body.reviewItem.reviewKey, "SKR-MOODBOARD-SKM-003");
});

test("GET /generation/outputs/:outputKey/evaluations returns stored evaluations only", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/generation/outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER/evaluations"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].source, "VISUAL_RULE");
  assert.equal(body[0].verdict, "PASS");
});

test("generation routes do not expose write or execution endpoints", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "POST",
    url: "/generation/requests"
  });

  assert.equal(response.statusCode, 404);
});
