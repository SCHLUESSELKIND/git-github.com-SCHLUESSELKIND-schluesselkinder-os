import assert from "node:assert/strict";
import { test } from "node:test";
import type { ApiRepositories } from "../repositories.js";
import { buildServer } from "../server.js";

const now = new Date("2026-05-09T00:00:00.000Z");

const repositories: ApiRepositories = {
  artists: {
    findBySlug: async (slug) =>
      slug === "shibari-kawaii"
        ? {
            bioFragment: "Kalte Nähe.",
            createdAt: now,
            id: "artist-1",
            name: "SHIBARI KAWAII",
            slug: "shibari-kawaii",
            status: "ACTIVE",
            symbol: "ROPEFACE"
          }
        : null,
    list: async () => [
      {
        bioFragment: "Kalte Nähe.",
        createdAt: now,
        id: "artist-1",
        name: "SHIBARI KAWAII",
        slug: "shibari-kawaii",
        status: "ACTIVE",
        symbol: "ROPEFACE"
      }
    ]
  },
  fragments: {
    list: async () => [
      {
        active: true,
        content: "NACHT BLEIBT MATERIAL.",
        createdAt: now,
        id: "fragment-1",
        language: "de",
        type: "HERO",
        weight: 100
      }
    ]
  },
  music: {
    findByReleaseCode: async (releaseCode) =>
      releaseCode === "SKM-003"
        ? {
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
            title: "ROPEMASTER",
            tracks: [
              {
                duration: null,
                id: "track-3",
                moodFragment: "ritual force",
                releaseId: "music-3",
                title: "ROPEMASTER"
              }
            ]
          }
        : null,
    list: async () => [
      {
        artist: {
          name: "SHIBARI KAWAII",
          slug: "shibari-kawaii"
        },
        artistId: "artist-1",
        coverImage: null,
        createdAt: now,
        id: "music-1",
        releaseCode: "SKM-001",
        status: "ACTIVE",
        title: "PICK ME UP",
        tracks: []
      }
    ]
  },
  objects: {
    list: async () => [
      {
        archiveFragment: "Archiv offen. Store geschlossen.",
        artist: {
          name: "SHIBARI KAWAII",
          slug: "shibari-kawaii"
        },
        artistId: "artist-1",
        createdAt: now,
        id: "object-1",
        mark: "KEY",
        materialNote: "Black cotton study. Key mark.",
        releaseId: "SK-001",
        status: "CLOSED",
        title: "BLACK HOODIE / KEY",
        type: "GARMENT_STUDY"
      }
    ]
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
  }
};

test("GET /artists returns typed artist records without a live database", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/artists"
  });

  assert.equal(response.statusCode, 200);
  assert.equal(response.json()[0].slug, "shibari-kawaii");
});

test("GET /objects returns archive-only object releases", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/objects"
  });

  const body = response.json();

  assert.equal(response.statusCode, 200);
  assert.equal(body[0].releaseId, "SK-001");
  assert.equal(body[0].status, "CLOSED");
  assert.equal("price" in body[0], false);
  assert.equal("stock" in body[0], false);
  assert.equal("sku" in body[0], false);
});

test("GET /music/:releaseCode includes ROPEMASTER contract coverage", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/music/SKM-003"
  });

  assert.equal(response.statusCode, 200);
  assert.equal(response.json().title, "ROPEMASTER");
});

test("GET /fragments returns active institutional fragments", async () => {
  const server = buildServer({ repositories });

  const response = await server.inject({
    method: "GET",
    url: "/fragments"
  });

  assert.equal(response.statusCode, 200);
  assert.equal(response.json()[0].content, "NACHT BLEIBT MATERIAL.");
});
