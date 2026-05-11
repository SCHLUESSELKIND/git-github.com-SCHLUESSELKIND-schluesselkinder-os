import { prisma } from "@schluesselkinder/db";
import {
  mapRegistryArtist,
  mapRegistryChannelPresence,
  mapRegistryDistributionReference,
  mapRegistryExternalReference,
  mapRegistryMusicRelease,
  mapRegistryTrackWithRelease
} from "./registry-mappers.js";
import type {
  RegistryArtistRow,
  RegistryChannelPresenceRow,
  RegistryDistributionReferenceRow,
  RegistryExternalReferenceRow,
  RegistryMusicReleaseRow,
  RegistryRepository,
  RegistryTrackWithReleaseRow
} from "./registry-types.js";

type ReadDelegate<Row> = Readonly<{
  findFirst(args?: unknown): Promise<Row | null>;
  findMany(args?: unknown): Promise<Row[]>;
}>;

type RegistryReadClient = Readonly<{
  artist: ReadDelegate<RegistryArtistRow>;
  channelPresence: ReadDelegate<RegistryChannelPresenceRow>;
  distributionReference: ReadDelegate<RegistryDistributionReferenceRow>;
  externalReference: ReadDelegate<RegistryExternalReferenceRow>;
  musicRelease: ReadDelegate<RegistryMusicReleaseRow>;
  track: ReadDelegate<RegistryTrackWithReleaseRow>;
}>;

const artistSummarySelect = {
  artistKey: true,
  id: true,
  name: true,
  slug: true
} as const;

const musicReleaseSummarySelect = {
  id: true,
  releaseCode: true,
  title: true
} as const;

const trackSummarySelect = {
  id: true,
  title: true,
  trackKey: true
} as const;

const objectReleaseSummarySelect = {
  id: true,
  releaseId: true,
  title: true
} as const;

const channelPresenceSummarySelect = {
  id: true,
  platform: true,
  presenceKey: true
} as const;

const musicReleaseInclude = {
  artist: {
    select: artistSummarySelect
  },
  tracks: {
    orderBy: [{ trackKey: "asc" }, { title: "asc" }]
  }
} as const;

const trackInclude = {
  release: {
    select: {
      ...musicReleaseSummarySelect,
      artist: {
        select: artistSummarySelect
      }
    }
  }
} as const;

const channelPresenceInclude = {
  artist: {
    select: artistSummarySelect
  }
} as const;

const externalReferenceInclude = {
  artist: {
    select: artistSummarySelect
  },
  channelPresence: {
    select: channelPresenceSummarySelect
  },
  musicRelease: {
    select: musicReleaseSummarySelect
  },
  objectRelease: {
    select: objectReleaseSummarySelect
  },
  track: {
    select: trackSummarySelect
  }
} as const;

const distributionReferenceInclude = {
  musicRelease: {
    select: musicReleaseSummarySelect
  },
  track: {
    select: trackSummarySelect
  }
} as const;

export function createRegistryRepository(client: RegistryReadClient = prisma as unknown as RegistryReadClient): RegistryRepository {
  return {
    getArtistByKeyOrSlug: async (keyOrSlug) => {
      const artist = await client.artist.findFirst({
        orderBy: [{ artistKey: "asc" }, { slug: "asc" }],
        where: {
          OR: [{ artistKey: keyOrSlug }, { slug: keyOrSlug }]
        }
      });

      return artist ? mapRegistryArtist(artist) : null;
    },
    getMusicReleaseByCode: async (releaseCode) => {
      const release = await client.musicRelease.findFirst({
        include: musicReleaseInclude,
        where: { releaseCode }
      });

      return release ? mapRegistryMusicRelease(release) : null;
    },
    getTrackByKey: async (trackKey) => {
      const track = await client.track.findFirst({
        include: trackInclude,
        where: { trackKey }
      });

      return track ? mapRegistryTrackWithRelease(track) : null;
    },
    listArtists: async () => {
      const artists = await client.artist.findMany({
        orderBy: [{ artistKey: "asc" }, { slug: "asc" }]
      });

      return artists.map(mapRegistryArtist);
    },
    listChannelPresences: async () => {
      const presences = await client.channelPresence.findMany({
        include: channelPresenceInclude,
        orderBy: [{ platform: "asc" }, { presenceKey: "asc" }]
      });

      return presences.map(mapRegistryChannelPresence);
    },
    listDistributionReferences: async () => {
      const references = await client.distributionReference.findMany({
        include: distributionReferenceInclude,
        orderBy: [{ platform: "asc" }, { distributionKey: "asc" }]
      });

      return references.map(mapRegistryDistributionReference);
    },
    listExternalReferences: async () => {
      const references = await client.externalReference.findMany({
        include: externalReferenceInclude,
        orderBy: [{ platform: "asc" }, { referenceKey: "asc" }]
      });

      return references.map(mapRegistryExternalReference);
    },
    listMusicReleases: async () => {
      const releases = await client.musicRelease.findMany({
        include: musicReleaseInclude,
        orderBy: { releaseCode: "asc" }
      });

      return releases.map(mapRegistryMusicRelease);
    },
    listTracks: async () => {
      const tracks = await client.track.findMany({
        include: trackInclude,
        orderBy: [{ trackKey: "asc" }, { title: "asc" }]
      });

      return tracks.map(mapRegistryTrackWithRelease);
    }
  };
}
