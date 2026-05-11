import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import type { RegistryRepository } from "../registry/registry-types.js";
import { buildServer } from "../server.js";

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

const musicRelease = {
  artist: {
    artistKey: artist.artistKey,
    canonicalName: artist.canonicalName,
    id: artist.id,
    slug: artist.slug
  },
  coverImage: null,
  createdAt: now,
  id: "release-1",
  releaseCode: "SKM-003",
  status: "ACTIVE",
  title: "ROPEMASTER",
  tracks: [
    {
      ...track,
      release: null
    }
  ]
} as const;

const channelPresence = {
  artist: {
    artistKey: artist.artistKey,
    canonicalName: artist.canonicalName,
    id: artist.id,
    slug: artist.slug
  },
  createdAt: now,
  handle: null,
  id: "presence-1",
  platform: "SOUNDCLOUD",
  presenceKey: "presence_shibari_kawaii_soundcloud",
  profileUrl: null,
  verifiedState: "UNVERIFIED",
  visibility: "INTERNAL"
} as const;

const externalReference = {
  createdAt: now,
  externalId: null,
  id: "external-reference-1",
  platform: "SOUNDCLOUD",
  referenceKey: "external_ref_soundcloud_presence_1",
  sourceAuthority: false,
  targetCount: 1,
  targets: {
    artist: null,
    channelPresence: {
      id: channelPresence.id,
      platform: channelPresence.platform,
      presenceKey: channelPresence.presenceKey
    },
    musicRelease: null,
    objectRelease: null,
    track: null
  },
  url: "urn:schluesselkinder:test:external-reference",
  verifiedState: "UNVERIFIED"
} as const;

const distributionReference = {
  createdAt: now,
  distributionKey: "distribution_ref_track_1",
  externalId: null,
  id: "distribution-reference-1",
  musicRelease: null,
  platform: "SPOTIFY",
  sourceAuthority: false,
  targetCount: 1,
  track: {
    id: track.id,
    title: track.title,
    trackKey: track.trackKey
  },
  url: null,
  verifiedState: "UNVERIFIED"
} as const;

function createRegistryRepositoryStub(): RegistryRepository {
  return {
    getArtistByKeyOrSlug: async (artistKey) =>
      artistKey === artist.artistKey || artistKey === artist.slug ? artist : null,
    getMusicReleaseByCode: async (releaseCode) => (releaseCode === musicRelease.releaseCode ? musicRelease : null),
    getTrackByKey: async (trackKey) => (trackKey === track.trackKey ? track : null),
    listArtists: async () => [artist],
    listChannelPresences: async () => [channelPresence],
    listDistributionReferences: async () => [distributionReference],
    listExternalReferences: async () => [externalReference],
    listMusicReleases: async () => [musicRelease],
    listTracks: async () => [track]
  };
}

test("registry routes expose read-only canonical registry data", async () => {
  const server = buildServer({ registryRepository: createRegistryRepositoryStub() });

  const artistsResponse = await server.inject({ method: "GET", url: "/registry/artists" });
  const artistResponse = await server.inject({ method: "GET", url: "/registry/artists/artist_shibari_kawaii" });
  const releasesResponse = await server.inject({ method: "GET", url: "/registry/music-releases" });
  const releaseResponse = await server.inject({ method: "GET", url: "/registry/music-releases/SKM-003" });
  const trackResponse = await server.inject({ method: "GET", url: "/registry/tracks/track_sk_0001_01" });
  const channelPresencesResponse = await server.inject({ method: "GET", url: "/registry/channel-presences" });
  const externalReferencesResponse = await server.inject({ method: "GET", url: "/registry/external-references" });
  const distributionReferencesResponse = await server.inject({ method: "GET", url: "/registry/distribution-references" });

  assert.equal(artistsResponse.statusCode, 200);
  assert.equal(artistsResponse.json()[0].artistKey, "artist_shibari_kawaii");
  assert.equal(artistResponse.statusCode, 200);
  assert.equal(artistResponse.json().canonicalName, "SHIBARI KAWAII");
  assert.equal(releasesResponse.statusCode, 200);
  assert.equal(releasesResponse.json()[0].releaseCode, "SKM-003");
  assert.equal(releaseResponse.statusCode, 200);
  assert.equal(releaseResponse.json().tracks[0].trackKey, "track_sk_0001_01");
  assert.equal(trackResponse.statusCode, 200);
  assert.equal(trackResponse.json().release.releaseCode, "SKM-003");
  assert.equal(channelPresencesResponse.statusCode, 200);
  assert.equal(channelPresencesResponse.json()[0].platform, "SOUNDCLOUD");
  assert.equal(externalReferencesResponse.statusCode, 200);
  assert.equal(externalReferencesResponse.json()[0].sourceAuthority, false);
  assert.equal(distributionReferencesResponse.statusCode, 200);
  assert.equal(distributionReferencesResponse.json()[0].sourceAuthority, false);
});

test("registry detail routes return 404 for unknown registry identifiers", async () => {
  const server = buildServer({ registryRepository: createRegistryRepositoryStub() });

  const artistResponse = await server.inject({ method: "GET", url: "/registry/artists/missing" });
  const releaseResponse = await server.inject({ method: "GET", url: "/registry/music-releases/missing" });
  const trackResponse = await server.inject({ method: "GET", url: "/registry/tracks/missing" });

  assert.equal(artistResponse.statusCode, 404);
  assert.equal(artistResponse.json().error, "registry_artist_not_found");
  assert.equal(releaseResponse.statusCode, 404);
  assert.equal(releaseResponse.json().error, "registry_music_release_not_found");
  assert.equal(trackResponse.statusCode, 404);
  assert.equal(trackResponse.json().error, "registry_track_not_found");
});

test("registry route surface remains GET-only and write-free", async () => {
  const server = buildServer({ registryRepository: createRegistryRepositoryStub() });
  const postResponse = await server.inject({ method: "POST", url: "/registry/artists" });
  const source = readFileSync(new URL("./registry.ts", import.meta.url), "utf8");

  assert.equal(postResponse.statusCode, 404);
  assert.equal(/server\.(post|put|patch|delete)\s*\(/.test(source), false);
  assert.equal(/\.(create|createMany|update|updateMany|upsert|delete|deleteMany)\s*\(/.test(source), false);
});
