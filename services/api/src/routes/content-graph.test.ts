import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-09T02:00:00.000Z");

const campaignWorld = {
  active: true,
  code: "ROOM_AFTER_LIGHT",
  createdAt: now,
  description: "Primary campaign world for chair, concrete, low light, and after-room pressure.",
  id: "world-1",
  name: "Room after light",
  weight: 100
};

const moodReference = {
  active: true,
  code: "EMPTY_ROOM_PRESSURE",
  createdAt: now,
  description: "After-room pressure, silence, and spatial absence.",
  id: "mood-1",
  name: "Empty room pressure",
  weight: 95
};

const asset = {
  active: true,
  code: "RUNE_KEY_SYMBOL",
  createdAt: now,
  description: "Institutional rune/key mark.",
  id: "asset-1",
  referenceKey: "brand/rune-key-symbol",
  sourceType: "SYMBOLIC_REFERENCE" as const,
  title: "Rune/key symbol",
  type: "SYMBOL" as const,
  weight: 100
};

const fragment = {
  content: "NACHT BLEIBT MATERIAL.",
  id: "fragment-1",
  language: "de",
  type: "HERO" as const
};

const releaseFragment = {
  active: true,
  fragment,
  fragmentId: "fragment-1",
  id: "release-fragment-1",
  musicRelease: {
    id: "music-3",
    releaseCode: "SKM-003",
    title: "ROPEMASTER"
  },
  musicReleaseId: "music-3",
  placement: "RELEASE_NOTE" as const,
  track: null,
  trackId: null,
  weight: 90
};

const trackMoodReference = {
  kind: "TRACK_MOOD_REFERENCE" as const,
  record: {
    id: "track-mood-1",
    moodReference,
    moodReferenceId: "mood-1",
    reason: "ROPEMASTER uses EMPTY_ROOM_PRESSURE as an operational mood reference.",
    track: {
      id: "track-3",
      title: "ROPEMASTER"
    },
    trackId: "track-3",
    verdict: "REQUIRED" as const,
    weight: 100
  }
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
    findMusicReleaseGraph: async (releaseCode) =>
      releaseCode === "SKM-003"
        ? {
            campaignWorlds: [
              {
                kind: "MUSIC_RELEASE_CAMPAIGN_WORLD",
                record: {
                  campaignWorld,
                  campaignWorldId: "world-1",
                  id: "music-world-1",
                  musicRelease: {
                    id: "music-3",
                    releaseCode: "SKM-003",
                    title: "ROPEMASTER"
                  },
                  musicReleaseId: "music-3",
                  reason: "ROPEMASTER belongs to ROOM_AFTER_LIGHT.",
                  verdict: "REQUIRED",
                  weight: 100
                }
              }
            ],
            release: {
              artist: {
                name: "SHIBARI KAWAII",
                slug: "shibari-kawaii"
              },
              artistId: "artist-1",
              coverImage: null,
              createdAt: now,
              id: "music-3",
              releaseCode: "SKM-003",
              status: "ACTIVE",
              title: "ROPEMASTER"
            },
            releaseFragments: [releaseFragment],
            trackMoodReferences: [trackMoodReference]
          }
        : null,
    listAssets: async () => [asset],
    listAssetTags: async () => [
      {
        active: true,
        code: "RUNE_KEY",
        createdAt: now,
        id: "tag-1",
        label: "Rune/key"
      }
    ],
    listCampaignWorlds: async () => [campaignWorld],
    listChannelFragments: async () => [
      {
        active: true,
        campaignWorld: {
          code: "ROOM_AFTER_LIGHT",
          id: "world-1",
          name: "Room after light"
        },
        campaignWorldId: "world-1",
        channel: "WEBSITE",
        fragment,
        fragmentId: "fragment-1",
        id: "channel-fragment-1",
        moodReference: null,
        moodReferenceId: null,
        placement: "HERO",
        weight: 100
      }
    ],
    listCompatibility: async () => [
      {
        kind: "CAMPAIGN_WORLD_ASSET",
        record: {
          asset,
          assetId: "asset-1",
          campaignWorld,
          campaignWorldId: "world-1",
          id: "world-asset-1",
          reason: "Rune/key remains the institutional punctuation mark.",
          verdict: "REQUIRED",
          weight: 95
        }
      },
      {
        kind: "CAMPAIGN_WORLD_ASSET",
        record: {
          asset: {
            active: true,
            code: "ROPEFACE_ARTIST_STAMP",
            createdAt: now,
            description: "SHIBARI KAWAII secondary artist stamp.",
            id: "asset-2",
            referenceKey: "brand/ropeface-artist-stamp",
            sourceType: "SYMBOLIC_REFERENCE",
            title: "Ropeface artist stamp",
            type: "SYMBOL",
            weight: 60
          },
          assetId: "asset-2",
          campaignWorld,
          campaignWorldId: "world-1",
          id: "world-asset-2",
          reason: "Ropeface cannot replace the rune/key as institutional archive language.",
          verdict: "FORBIDDEN",
          weight: 100
        }
      },
      trackMoodReference
    ],
    listMoodReferences: async () => [moodReference],
    listReleaseFragments: async () => [releaseFragment],
    listVisualEnvironments: async () => [
      {
        active: true,
        code: "DUNGEON_CHAIR_PRIMARY",
        createdAt: now,
        description: "Primary recurring campaign environment.",
        id: "visual-1",
        name: "Dungeon chair primary",
        weight: 100
      }
    ]
  }
};

test("GET /content-graph returns semantic graph groups without a live database", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/content-graph"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.campaignWorlds[0].code, "ROOM_AFTER_LIGHT");
  assert.equal(body.assets[0].referenceKey, "brand/rune-key-symbol");
  assert.equal(body.compatibility[0].verdict, "REQUIRED");
  assert.equal(body.compatibility.some((item: { verdict: string }) => item.verdict === "FORBIDDEN"), true);
});

test("GET /content-graph/assets stays symbolic and avoids storage metadata", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/content-graph/assets"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].referenceKey, "brand/rune-key-symbol");
  assert.equal("url" in body[0], false);
  assert.equal("width" in body[0], false);
  assert.equal("storageProvider" in body[0], false);
});

test("GET /content-graph/music/:releaseCode returns release orchestration", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/content-graph/music/SKM-003"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body.release.releaseCode, "SKM-003");
  assert.equal(body.campaignWorlds[0].target.code, "ROOM_AFTER_LIGHT");
  assert.equal(body.trackMoodReferences[0].target.code, "EMPTY_ROOM_PRESSURE");
});
