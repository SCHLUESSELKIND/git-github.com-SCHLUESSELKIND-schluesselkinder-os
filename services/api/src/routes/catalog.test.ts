import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import type { CatalogService } from "../catalog/catalog-types.js";
import { buildServer } from "../server.js";

const artistProjection = {
  artistKey: "artist_shibari_kawaii",
  displayName: "SHIBARI KAWAII",
  primaryImage: null,
  primaryWorld: null,
  state: "ACTIVE"
} as const;

const releaseProjection = {
  canonicalArtwork: null,
  publicFragments: [],
  releaseCode: "SKM-003",
  releaseType: null,
  state: "ACTIVE",
  title: "ROPEMASTER"
} as const;

const trackProjection = {
  moods: [],
  runtime: 188,
  title: "ROPEMASTER",
  trackKey: "track_sk_0001_01",
  worlds: []
} as const;

function createCatalogServiceStub(): CatalogService {
  return {
    listArtistProjections: async () => [artistProjection],
    listReleaseProjections: async () => [releaseProjection],
    listTrackProjections: async () => [trackProjection],
    readCatalogProjectionSet: async () => ({
      artists: [artistProjection],
      releases: [releaseProjection],
      tracks: [trackProjection]
    })
  };
}

test("catalog routes expose projection-only records", async () => {
  const server = buildServer({ catalogService: createCatalogServiceStub() });

  const artistsResponse = await server.inject({ method: "GET", url: "/catalog/artists" });
  const artistResponse = await server.inject({ method: "GET", url: "/catalog/artists/artist_shibari_kawaii" });
  const releasesResponse = await server.inject({ method: "GET", url: "/catalog/music-releases" });
  const releaseResponse = await server.inject({ method: "GET", url: "/catalog/music-releases/SKM-003" });
  const tracksResponse = await server.inject({ method: "GET", url: "/catalog/tracks" });
  const trackResponse = await server.inject({ method: "GET", url: "/catalog/tracks/track_sk_0001_01" });

  assert.equal(artistsResponse.statusCode, 200);
  assert.deepEqual(artistsResponse.json(), [artistProjection]);
  assert.equal(artistResponse.statusCode, 200);
  assert.equal(artistResponse.json().displayName, "SHIBARI KAWAII");
  assert.equal("slug" in artistResponse.json(), false);
  assert.equal(releasesResponse.statusCode, 200);
  assert.deepEqual(releasesResponse.json(), [releaseProjection]);
  assert.equal(releaseResponse.statusCode, 200);
  assert.equal(releaseResponse.json().releaseCode, "SKM-003");
  assert.equal("releaseKey" in releaseResponse.json(), false);
  assert.equal(tracksResponse.statusCode, 200);
  assert.deepEqual(tracksResponse.json(), [trackProjection]);
  assert.equal(trackResponse.statusCode, 200);
  assert.equal(trackResponse.json().trackKey, "track_sk_0001_01");
  assert.equal("sourceAuthority" in trackResponse.json(), false);
});

test("catalog detail routes return 404 for unknown projection identifiers", async () => {
  const server = buildServer({ catalogService: createCatalogServiceStub() });

  const artistResponse = await server.inject({ method: "GET", url: "/catalog/artists/missing" });
  const releaseResponse = await server.inject({ method: "GET", url: "/catalog/music-releases/missing" });
  const trackResponse = await server.inject({ method: "GET", url: "/catalog/tracks/missing" });

  assert.equal(artistResponse.statusCode, 404);
  assert.equal(artistResponse.json().error, "catalog_artist_not_found");
  assert.equal(releaseResponse.statusCode, 404);
  assert.equal(releaseResponse.json().error, "catalog_music_release_not_found");
  assert.equal(trackResponse.statusCode, 404);
  assert.equal(trackResponse.json().error, "catalog_track_not_found");
});

test("catalog route surface remains GET-only and projection-only", async () => {
  const server = buildServer({ catalogService: createCatalogServiceStub() });
  const postResponse = await server.inject({ method: "POST", url: "/catalog/artists" });
  const source = readFileSync(new URL("./catalog.ts", import.meta.url), "utf8");

  assert.equal(postResponse.statusCode, 404);
  assert.equal(/server\.(post|put|patch|delete)\s*\(/.test(source), false);
  assert.equal(/\.(create|createMany|update|updateMany|upsert|delete|deleteMany)\s*\(/.test(source), false);
  assert.equal(/prisma|redis|cache|persist|provider|oembed|oauth|webhook|worker|queue/i.test(source), false);
});
