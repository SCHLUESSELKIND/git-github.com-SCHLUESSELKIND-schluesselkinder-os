import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import type { RegistryRepository } from "../registry/registry-types.js";
import { createCatalogService } from "./catalog-service.js";

const now = "2026-05-11T00:00:00.000Z";

const artist = {
  artistKey: "artist_shibari_kawaii",
  bioFragment: "Kalte Naehe.",
  canonicalName: "SHIBARI KAWAII",
  createdAt: now,
  id: "artist-1",
  slug: "shibari-kawaii",
  status: "ACTIVE",
  symbol: "ROPEFACE"
} as const;

const artistWithoutKey = {
  ...artist,
  artistKey: null,
  id: "artist-2",
  slug: "slug-is-not-a-canonical-key"
} as const;

const track = {
  duration: 188,
  id: "track-1",
  moodFragment: "ritual force",
  release: {
    artist: {
      artistKey: artist.artistKey,
      canonicalName: artist.canonicalName,
      id: artist.id,
      slug: artist.slug
    },
    id: "release-1",
    releaseCode: "SKM-003",
    title: "ROPEMASTER"
  },
  releaseId: "release-1",
  title: "ROPEMASTER",
  trackKey: "track_sk_0001_01"
} as const;

const trackWithoutKey = {
  ...track,
  id: "track-2",
  title: "TITLE IS NOT A CANONICAL KEY",
  trackKey: null
} as const;

const musicRelease = {
  artist: {
    artistKey: artist.artistKey,
    canonicalName: artist.canonicalName,
    id: artist.id,
    slug: artist.slug
  },
  coverImage: "/images/ropemaster-cover.jpg",
  createdAt: now,
  id: "release-1",
  releaseCode: "SKM-003",
  status: "ACTIVE" as const,
  title: "ROPEMASTER",
  tracks: [
    {
      ...track,
      release: null
    }
  ]
};

function createRegistryRepositoryStub(): RegistryRepository {
  return {
    getArtistByKeyOrSlug: async (artistKey) =>
      artistKey === artist.artistKey || artistKey === artist.slug ? artist : null,
    getMusicReleaseByCode: async (releaseCode) => (releaseCode === musicRelease.releaseCode ? musicRelease : null),
    getTrackByKey: async (trackKey) => (trackKey === track.trackKey ? track : null),
    listArtists: async () => [artist, artistWithoutKey],
    listChannelPresences: async () => [],
    listDistributionReferences: async () => [],
    listExternalReferences: async () => [],
    listMusicReleases: async () => [musicRelease],
    listTracks: async () => [track, trackWithoutKey]
  };
}

test("catalog service projects a narrow public catalog shape from registry records", async () => {
  const service = createCatalogService(createRegistryRepositoryStub());
  const catalog = await service.readCatalogProjectionSet();

  assert.deepEqual(catalog.artists, [
    {
      artistKey: "artist_shibari_kawaii",
      displayName: "SHIBARI KAWAII",
      primaryImage: null,
      primaryWorld: null,
      state: "ACTIVE"
    }
  ]);
  assert.deepEqual(catalog.releases, [
    {
      canonicalArtwork: "/images/ropemaster-cover.jpg",
      publicFragments: [],
      releaseCode: "SKM-003",
      releaseType: null,
      state: "ACTIVE",
      title: "ROPEMASTER"
    }
  ]);
  assert.deepEqual(catalog.tracks, [
    {
      moods: [],
      runtime: 188,
      title: "ROPEMASTER",
      trackKey: "track_sk_0001_01",
      worlds: []
    }
  ]);
});

test("catalog projection does not create authority from slugs, titles, or free-text fragments", async () => {
  const service = createCatalogService(createRegistryRepositoryStub());
  const artists = await service.listArtistProjections();
  const releases = await service.listReleaseProjections();
  const tracks = await service.listTrackProjections();

  assert.equal(artists.some((projection) => projection.artistKey === artistWithoutKey.slug), false);
  assert.equal(tracks.some((projection) => projection.trackKey === trackWithoutKey.title), false);
  assert.equal("releaseKey" in releases[0]!, false);
  assert.deepEqual(tracks[0]?.moods, []);
  assert.deepEqual(tracks[0]?.worlds, []);
});

test("catalog projection source remains internal, read-only, and non-persistent", () => {
  const serviceSource = readFileSync(new URL("./catalog-service.ts", import.meta.url), "utf8");
  const mapperSource = readFileSync(new URL("./catalog-mappers.ts", import.meta.url), "utf8");
  const source = `${serviceSource}\n${mapperSource}`;

  assert.equal(/from\s+["']fastify["']|server\.|\.route\s*\(|\.register\s*\(/.test(source), false);
  assert.equal(/\.(create|createMany|update|updateMany|upsert|delete|deleteMany)\s*\(/.test(source), false);
  assert.equal(/prisma|redis|cache|persist|provider|oembed|oauth|webhook|worker|queue/i.test(source), false);
});
