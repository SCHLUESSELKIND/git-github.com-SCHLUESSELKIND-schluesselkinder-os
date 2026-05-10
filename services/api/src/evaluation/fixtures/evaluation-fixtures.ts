import type { ApiRepositories } from "../../repositories.js";
import type { EvaluationInput } from "../types.js";

const now = new Date("2026-05-10T02:00:00.000Z");

export const cleanEvaluationInput: EvaluationInput = {
  channel: "WEBSITE",
  compatibility: [
    {
      kind: "CAMPAIGN_WORLD_ASSET",
      reason: "Chair environment is required for the primary campaign world.",
      sourceCode: "ROOM_AFTER_LIGHT",
      sourceLabel: "Room after light",
      targetCode: "CHAIR_CAMPAIGN_ENVIRONMENT",
      targetLabel: "Chair campaign environment",
      verdict: "REQUIRED",
      weight: 100
    },
    {
      kind: "CAMPAIGN_WORLD_ASSET",
      reason: "Rune/key remains the institutional punctuation mark.",
      sourceCode: "ROOM_AFTER_LIGHT",
      sourceLabel: "Room after light",
      targetCode: "RUNE_KEY_SYMBOL",
      targetLabel: "Rune/key symbol",
      verdict: "REQUIRED",
      weight: 95
    }
  ],
  constraintBundle: {
    code: "CB-SK-CORE-GENERATION",
    constraints: [
      {
        active: true,
        instruction: "Every output must remain bound to a ReviewItem.",
        required: true,
        ruleCode: "REVIEW_BINDING_REQUIRED",
        source: "REVIEW_GOVERNANCE",
        title: "Review binding required",
        weight: 100
      },
      {
        active: true,
        instruction: "Reject cyberpunk overload before review.",
        required: true,
        ruleCode: "CYBERPUNK_OVERLOAD",
        source: "FORBIDDEN_ENERGY",
        title: "Cyberpunk overload guard",
        weight: 100
      }
    ],
    description: "Core constraints required for controlled generation planning.",
    name: "SCHLUESSELKINDER core generation constraints"
  },
  declared: {
    campaignWorldCode: "ROOM_AFTER_LIGHT",
    moodReferenceCodes: [],
    releaseCode: "SKM-003"
  },
  forbiddenEnergy: [
    {
      code: "CYBERPUNK_OVERLOAD",
      label: "Cyberpunk overload",
      reason: "Adds generic neon dystopia instead of controlled techno-industrial emptiness.",
      severity: "REQUIRED",
      weight: 100
    }
  ],
  reviewBinding: {
    id: "review-1",
    reviewKey: "SKR-MOODBOARD-SKM-003",
    status: "PENDING"
  },
  rules: [
    {
      code: "REVIEW_BINDING_REQUIRED",
      severity: "REQUIRED",
      text: "Every output must remain bound to a ReviewItem.",
      title: "Review binding required",
      weight: 100
    }
  ],
  scoringRules: [
    {
      code: "SCORE_FORBIDDEN_ENERGY_AVOIDANCE",
      description: "Penalizes forbidden energy.",
      maxScore: 10,
      title: "Forbidden energy avoidance",
      weight: 4
    }
  ],
  subject: {
    key: "GO-MOODBOARD-SKM-003-PLACEHOLDER",
    type: "GENERATION_OUTPUT"
  },
  text: {
    body: ["ROPEMASTER uses chair environment and rune/key system as controlled archive material."],
    detectedAssetCodes: ["CHAIR_CAMPAIGN_ENVIRONMENT", "RUNE_KEY_SYMBOL"]
  }
};

export const failingEvaluationInput: EvaluationInput = {
  ...cleanEvaluationInput,
  compatibility: [
    ...cleanEvaluationInput.compatibility,
    {
      kind: "CAMPAIGN_WORLD_ASSET",
      reason: "Ropeface cannot replace the rune/key as institutional archive language.",
      sourceCode: "ROOM_AFTER_LIGHT",
      sourceLabel: "Room after light",
      targetCode: "ROPEFACE_ARTIST_STAMP",
      targetLabel: "Ropeface artist stamp",
      verdict: "FORBIDDEN",
      weight: 100
    }
  ],
  text: {
    body: ["Use neon gradient hype language and make Ropeface the masterbrand hero."],
    detectedAssetCodes: ["ROPEFACE_ARTIST_STAMP"]
  }
};

const constraintBundle = {
  active: true,
  code: "CB-SK-CORE-GENERATION",
  constraints: cleanEvaluationInput.constraintBundle?.constraints.map((constraint, index) => ({
    ...constraint,
    bundleId: "bundle-1",
    id: `constraint-${index + 1}`
  })) ?? [],
  createdAt: now,
  description: "Core constraints required for controlled generation planning.",
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

const output = {
  createdAt: now,
  evaluations: [],
  id: "output-1",
  outputKey: "GO-MOODBOARD-SKM-003-PLACEHOLDER",
  placeholder: "Placeholder only. Chair and rune/key references are review-bound.",
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

export const evaluationRepositories: ApiRepositories = {
  artists: {
    findBySlug: async () => null,
    list: async () => []
  },
  brandIntelligence: {
    listAudiencePersonas: async () => [],
    listBrandRules: async () => [],
    listChannelRules: async () => [],
    listForbiddenEnergy: async () => cleanEvaluationInput.forbiddenEnergy.map((energy) => ({
      active: true,
      createdAt: now,
      id: `energy-${energy.code}`,
      ...energy
    })),
    listLanguageRules: async () => [],
    listScoringRules: async () => cleanEvaluationInput.scoringRules.map((rule) => ({
      active: true,
      createdAt: now,
      id: `score-${rule.code}`,
      ...rule
    })),
    listVisualRules: async () => [],
    listVoiceProfiles: async () => []
  },
  contentGraph: {
    findMusicReleaseGraph: async () => null,
    listAssets: async () => [],
    listAssetTags: async () => [],
    listCampaignWorlds: async () => [],
    listChannelFragments: async () => [],
    listCompatibility: async () => [
      {
        kind: "CAMPAIGN_WORLD_ASSET",
        record: {
          asset: {
            active: true,
            code: "CHAIR_CAMPAIGN_ENVIRONMENT",
            createdAt: now,
            description: "Primary chair environment.",
            id: "asset-chair",
            referenceKey: "brand/chair",
            sourceType: "SYMBOLIC_REFERENCE",
            title: "Chair campaign environment",
            type: "IMAGE",
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
          verdict: "REQUIRED",
          weight: 100
        }
      }
    ],
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
    listOutputEvaluations: async () => [],
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
