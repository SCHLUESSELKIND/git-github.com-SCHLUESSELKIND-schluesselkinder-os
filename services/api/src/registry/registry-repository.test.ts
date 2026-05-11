import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createRegistryRepository } from "./registry-repository.js";
import type {
  RegistryArtistRow,
  RegistryChannelPresenceRow,
  RegistryDistributionReferenceRow,
  RegistryExternalReferenceRow,
  RegistryMusicReleaseRow,
  RegistryTrackRow,
  RegistryTrackWithReleaseRow
} from "./registry-types.js";

const now = new Date("2026-05-11T00:00:00.000Z");

const artistRow = {
  artistKey: "artist_shibari_kawaii",
  bioFragment: "Kalte Naehe.",
  createdAt: now,
  id: "artist-1",
  name: "SHIBARI KAWAII",
  slug: "shibari-kawaii",
  status: "ACTIVE",
  symbol: "ROPEFACE"
} satisfies RegistryArtistRow;

const trackRow = {
  duration: 188,
  id: "track-1",
  moodFragment: "ritual force",
  releaseId: "release-1",
  title: "ROPEMASTER",
  trackKey: "track_sk_0001_01"
} satisfies RegistryTrackRow;

const trackWithReleaseRow = {
  ...trackRow,
  release: {
    artist: {
      artistKey: artistRow.artistKey,
      id: artistRow.id,
      name: artistRow.name,
      slug: artistRow.slug
    },
    id: "release-1",
    releaseCode: "SKM-003",
    title: "ROPEMASTER"
  }
} satisfies RegistryTrackWithReleaseRow;

const musicReleaseRow = {
  artist: {
    artistKey: artistRow.artistKey,
    id: artistRow.id,
    name: artistRow.name,
    slug: artistRow.slug
  },
  artistId: artistRow.id,
  coverImage: null,
  createdAt: now,
  id: "release-1",
  releaseCode: "SKM-003",
  status: "ACTIVE",
  title: "ROPEMASTER",
  tracks: [trackRow]
} satisfies RegistryMusicReleaseRow;

const channelPresenceRow = {
  artist: {
    artistKey: artistRow.artistKey,
    id: artistRow.id,
    name: artistRow.name,
    slug: artistRow.slug
  },
  artistId: artistRow.id,
  createdAt: now,
  handle: null,
  id: "presence-1",
  platform: "SOUNDCLOUD",
  presenceKey: "presence_shibari_kawaii_soundcloud",
  profileUrl: null,
  verifiedState: "UNVERIFIED",
  visibility: "INTERNAL"
} satisfies RegistryChannelPresenceRow;

const externalReferenceRow = {
  artist: null,
  artistId: null,
  channelPresence: {
    id: channelPresenceRow.id,
    platform: channelPresenceRow.platform,
    presenceKey: channelPresenceRow.presenceKey
  },
  channelPresenceId: channelPresenceRow.id,
  createdAt: now,
  externalId: null,
  id: "external-reference-1",
  musicRelease: null,
  musicReleaseId: null,
  objectRelease: null,
  objectReleaseId: null,
  platform: "SOUNDCLOUD",
  referenceKey: "external_ref_soundcloud_presence_1",
  sourceAuthority: false,
  track: null,
  trackId: null,
  url: "urn:schluesselkinder:test:external-reference",
  verifiedState: "UNVERIFIED"
} satisfies RegistryExternalReferenceRow;

const distributionReferenceRow = {
  createdAt: now,
  distributionKey: "distribution_ref_track_1",
  externalId: null,
  id: "distribution-reference-1",
  musicRelease: null,
  musicReleaseId: null,
  platform: "SPOTIFY",
  sourceAuthority: false,
  track: {
    id: trackRow.id,
    title: trackRow.title,
    trackKey: trackRow.trackKey
  },
  trackId: trackRow.id,
  url: null,
  verifiedState: "UNVERIFIED"
} satisfies RegistryDistributionReferenceRow;

type ReadCall = Readonly<{
  args: unknown;
  delegate: string;
  method: "findFirst" | "findMany";
}>;

function readOnlyDelegate<Row>(
  delegate: string,
  rows: Row[],
  calls: ReadCall[],
  writeCalls: string[],
  first: Row | null = rows[0] ?? null
) {
  const failWrite = (method: string) => async () => {
    writeCalls.push(`${delegate}.${method}`);
    throw new Error(`registry repository attempted write method ${delegate}.${method}`);
  };

  return {
    create: failWrite("create"),
    createMany: failWrite("createMany"),
    delete: failWrite("delete"),
    deleteMany: failWrite("deleteMany"),
    findFirst: async (args?: unknown) => {
      calls.push({ args, delegate, method: "findFirst" });
      return first;
    },
    findMany: async (args?: unknown) => {
      calls.push({ args, delegate, method: "findMany" });
      return rows;
    },
    update: failWrite("update"),
    updateMany: failWrite("updateMany"),
    upsert: failWrite("upsert")
  };
}

test("registry repository reads and maps canonical registry records without writes", async () => {
  const calls: ReadCall[] = [];
  const writeCalls: string[] = [];
  const repository = createRegistryRepository({
    artist: readOnlyDelegate("artist", [artistRow], calls, writeCalls),
    channelPresence: readOnlyDelegate("channelPresence", [channelPresenceRow], calls, writeCalls),
    distributionReference: readOnlyDelegate("distributionReference", [distributionReferenceRow], calls, writeCalls),
    externalReference: readOnlyDelegate("externalReference", [externalReferenceRow], calls, writeCalls),
    musicRelease: readOnlyDelegate("musicRelease", [musicReleaseRow], calls, writeCalls),
    track: readOnlyDelegate("track", [trackWithReleaseRow], calls, writeCalls)
  });

  const artists = await repository.listArtists();
  const artist = await repository.getArtistByKeyOrSlug("artist_shibari_kawaii");
  const releases = await repository.listMusicReleases();
  const release = await repository.getMusicReleaseByCode("SKM-003");
  const tracks = await repository.listTracks();
  const track = await repository.getTrackByKey("track_sk_0001_01");
  const channelPresences = await repository.listChannelPresences();
  const externalReferences = await repository.listExternalReferences();
  const distributionReferences = await repository.listDistributionReferences();

  assert.equal(artists[0]?.canonicalName, "SHIBARI KAWAII");
  assert.equal(artist?.artistKey, "artist_shibari_kawaii");
  assert.equal(releases[0]?.artist.canonicalName, "SHIBARI KAWAII");
  assert.equal(release?.tracks[0]?.trackKey, "track_sk_0001_01");
  assert.equal(tracks[0]?.release?.releaseCode, "SKM-003");
  assert.equal(track?.release?.artist?.canonicalName, "SHIBARI KAWAII");
  assert.equal(channelPresences[0]?.platform, "SOUNDCLOUD");
  assert.equal(externalReferences[0]?.targetCount, 1);
  assert.equal(externalReferences[0]?.sourceAuthority, false);
  assert.equal(distributionReferences[0]?.targetCount, 1);
  assert.equal(distributionReferences[0]?.sourceAuthority, false);

  assert.deepEqual(writeCalls, []);
  assert.ok(calls.length >= 9);
  assert.ok(calls.every((call) => call.method === "findMany" || call.method === "findFirst"));
});

test("registry repository source contains no Prisma write calls or route registration", () => {
  const source = readFileSync(new URL("./registry-repository.ts", import.meta.url), "utf8");

  assert.equal(/\.(create|createMany|update|updateMany|upsert|delete|deleteMany)\s*\(/.test(source), false);
  assert.equal(/from\s+["']fastify["']|buildServer|\.route\s*\(|\.register\s*\(/.test(source), false);
});
