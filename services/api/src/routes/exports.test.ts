import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-10T04:00:00.000Z");

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
  description: "Core constraints required for controlled manual export.",
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
  status: "DRAFT" as const
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

const reviewItem = {
  asset: null,
  assetId: null,
  campaignWorld: {
    code: "ROOM_AFTER_LIGHT",
    id: "world-1",
    name: "Room after light"
  },
  campaignWorldId: "world-1",
  channelFragment: null,
  channelFragmentId: null,
  comments: [
    {
      author: "operator",
      body: "Keep rune/key hierarchy primary.",
      createdAt: now,
      id: "comment-1",
      reviewItemId: "review-1"
    }
  ],
  createdAt: now,
  decisions: [
    {
      createdAt: now,
      decidedBy: "operator",
      id: "decision-1",
      note: "Inspection continues.",
      reviewItemId: "review-1",
      type: "REQUEST_REVISION" as const
    }
  ],
  id: "review-1",
  musicRelease: {
    id: "music-3",
    releaseCode: "SKM-003",
    title: "ROPEMASTER"
  },
  musicReleaseId: "music-3",
  releaseFragment: null,
  releaseFragmentId: null,
  reviewKey: "SKR-MOODBOARD-SKM-003",
  stage: "MOODBOARD_REVIEW" as const,
  status: "PENDING" as const,
  subjectKey: "SKM-003",
  subjectType: "MUSIC_RELEASE" as const,
  summary: "Manual review required before any further boundary crossing.",
  title: "ROPEMASTER moodboard review",
  track: null,
  trackId: null,
  updatedAt: now,
  violations: [
    {
      active: true,
      createdAt: now,
      detail: "Ropeface must not replace rune/key hierarchy.",
      id: "violation-1",
      reviewItemId: "review-1",
      ruleCode: "ROPEFACE_SECONDARY_ONLY",
      severity: "WARNING" as const,
      source: "VISUAL_RULE" as const,
      title: "Artist stamp hierarchy"
    }
  ]
};

const compatibility = [
  {
    kind: "CAMPAIGN_WORLD_ASSET" as const,
    record: {
      asset: {
        active: true,
        code: "CHAIR_CAMPAIGN_ENVIRONMENT",
        createdAt: now,
        description: "Primary chair environment.",
        id: "asset-chair",
        referenceKey: "brand/chair",
        sourceType: "SYMBOLIC_REFERENCE" as const,
        title: "Chair campaign environment",
        type: "IMAGE" as const,
        weight: 100
      },
      assetId: "asset-chair",
      campaignWorld: {
        active: true,
        code: "ROOM_AFTER_LIGHT",
        createdAt: now,
        description: "Primary campaign world.",
        id: "world-1",
        name: "Room after light",
        weight: 100
      },
      campaignWorldId: "world-1",
      id: "compat-1",
      reason: "Chair environment is required.",
      verdict: "REQUIRED" as const,
      weight: 100
    }
  }
];

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
    listCompatibility: async () => compatibility,
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
    findByReviewKey: async (reviewKey) => (reviewKey === reviewItem.reviewKey ? reviewItem : null),
    list: async () => [reviewItem],
    listComments: async () => reviewItem.comments,
    listDecisions: async () => reviewItem.decisions,
    listViolations: async () => reviewItem.violations
  }
};

test("GET /exports/health exposes manual-only boundaries", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/exports/health"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assertManualExportBoundary(body);
  assert.equal(body.writeRoutes, false);
  assert.equal(body.dbMutation, false);
  assert.equal(body.fileWriting, false);
  assert.equal(body.providerIntegration, false);
});

test("GET /exports/packages/generation-outputs/:outputKey composes portable inspection package", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/exports/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.sourceType, "GENERATION_OUTPUT");
  assertManualExportBoundary(body);
  assertManualExportBoundary(body.reviewSnapshot);
  assertManualExportBoundary(body.evaluationSnapshot);
  assertManualExportBoundary(body.assetManifest);
  assert.equal(body.reviewSnapshot.snapshotImpliesApproval, false);
  assert.equal(body.evaluationSnapshot.snapshotImpliesTruth, false);
  assert.equal(body.evaluationSnapshot.passImpliesApproval, false);
  assert.equal(body.evaluationSnapshot.dominantVerdict, "PASS");

  for (const artifact of body.manualArtifacts) {
    assertManualExportBoundary(artifact);
  }

  for (const bundle of body.portableBundles) {
    assertManualExportBoundary(bundle);
  }
});

test("GET /exports/packages/generation-briefs/:briefKey keeps unevaluated material non-authoritative", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/exports/packages/generation-briefs/GB-MOODBOARD-SKM-003"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.sourceType, "GENERATION_BRIEF");
  assert.equal(body.evaluationSnapshot.dominantVerdict, "NOT_EVALUATED");
  assert.equal(body.reviewSnapshot.snapshotImpliesApproval, false);
  assert.equal(body.constraintSnapshot.requiredCount, 1);
  assertManualExportBoundary(body.constraintSnapshot.constraints[0]);
});

test("GET /exports/review-snapshots/:reviewKey does not turn review history into approval authority", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/exports/review-snapshots/SKR-MOODBOARD-SKM-003"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.reviewKey, "SKR-MOODBOARD-SKM-003");
  assert.equal(body.snapshotImpliesApproval, false);
  assertManualExportBoundary(body);
  assertManualExportBoundary(body.decisions[0]);
  assertManualExportBoundary(body.comments[0]);
  assertManualExportBoundary(body.violations[0]);
});

test("export routes expose no write route", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "POST",
    url: "/exports/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  assert.equal(response.statusCode, 404);
});

test("asset manifest stays symbolic and contains no transfer mechanics", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/exports/packages/generation-outputs/GO-MOODBOARD-SKM-003-PLACEHOLDER"
  });

  const body = response.json();
  const asset = body.assetManifest.assets[0];
  const keys = collectKeys(body);

  assert.equal(asset.code, "CHAIR_CAMPAIGN_ENVIRONMENT");
  assert.equal(asset.title, "Chair campaign environment");
  assert.equal(asset.sourceType, "SYMBOLIC_REFERENCE");
  assert.equal(asset.referenceKey, "brand/chair");
  assert.equal(asset.campaignWorldRelation, "ROOM_AFTER_LIGHT");
  assert.equal(asset.compatibilityVerdict, "REQUIRED");
  assertManualExportBoundary(asset);
  assertForbiddenKeysAbsent(keys);
});

test("export source files contain no mutation or external handoff code", () => {
  const source = readSourceTree("src/exports") + readFileSync("src/routes/exports.ts", "utf8");

  for (const term of [
    ["pris", "ma."].join(""),
    [".cre", "ate("].join(""),
    [".upd", "ate("].join(""),
    [".ups", "ert("].join(""),
    [".del", "ete("].join(""),
    ["write", "File"].join(""),
    ["append", "File"].join(""),
    ["open", "ai"].join(""),
    ["anth", "ropic"].join(""),
    ["stripe"].join(""),
    ["print", "ful"].join(""),
    ["up", "load"].join(""),
    ["qu", "eue"].join(""),
    ["re", "try"].join("")
  ]) {
    assert.equal(source.toLowerCase().includes(term.toLowerCase()), false);
  }
});

function assertManualExportBoundary(value: Record<string, unknown>) {
  assert.equal(value.reviewRequired, true);
  assert.equal(value.approvalAuthority, false);
  assert.equal(value.publishAuthority, false);
  assert.equal(value.humanCommitRequired, true);
  assert.equal(value.automationAllowed, false);
  assert.equal(value.externalDelivery, false);
  assert.equal(value.manualExportPrepared, true);
  assert.equal(value.portableArtifactOnly, true);
  assert.equal(value.distributionAuthority, false);
  assert.equal(value.publishReady, false);
}

function assertForbiddenKeysAbsent(keys: string[]) {
  for (const key of [
    ["file", "Path"].join(""),
    ["up", "load", "Target"].join(""),
    ["cdn", "Url"].join(""),
    ["storage", "Provider"].join(""),
    ["dim", "ensions"].join(""),
    ["binary", "Metadata"].join(""),
    ["delivery", "Destination"].join(""),
    ["qu", "eue", "Id"].join(""),
    ["re", "try", "State"].join(""),
    ["platform", "Action"].join(""),
    ["eng", "agement"].join(""),
    ["per", "formance"].join("")
  ]) {
    assert.equal(keys.includes(key), false);
  }
}

function collectKeys(value: unknown): string[] {
  if (!value || typeof value !== "object") {
    return [];
  }

  if (Array.isArray(value)) {
    return value.flatMap(collectKeys);
  }

  return Object.entries(value).flatMap(([key, childValue]) => [key, ...collectKeys(childValue)]);
}

function readSourceTree(path: string): string {
  return readdirSync(path, { withFileTypes: true })
    .map((entry) => {
      const childPath = join(path, entry.name);
      return entry.isDirectory() ? readSourceTree(childPath) : readFileSync(childPath, "utf8");
    })
    .join("\n");
}
