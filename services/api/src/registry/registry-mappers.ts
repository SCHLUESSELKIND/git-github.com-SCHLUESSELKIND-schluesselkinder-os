import type {
  RegistryArtist,
  RegistryArtistRow,
  RegistryArtistSummary,
  RegistryArtistSummaryRow,
  RegistryChannelPresence,
  RegistryChannelPresenceRow,
  RegistryDistributionReference,
  RegistryDistributionReferenceRow,
  RegistryExternalReference,
  RegistryExternalReferenceRow,
  RegistryMusicRelease,
  RegistryMusicReleaseRow,
  RegistryTrack,
  RegistryTrackRow,
  RegistryTrackWithReleaseRow
} from "./registry-types.js";

function mapRegistryArtistSummary(artist: RegistryArtistSummaryRow): RegistryArtistSummary {
  return {
    artistKey: artist.artistKey,
    canonicalName: artist.name,
    id: artist.id,
    slug: artist.slug
  };
}

export function mapRegistryArtist(artist: RegistryArtistRow): RegistryArtist {
  return {
    artistKey: artist.artistKey,
    bioFragment: artist.bioFragment,
    canonicalName: artist.name,
    createdAt: artist.createdAt.toISOString(),
    id: artist.id,
    slug: artist.slug,
    status: artist.status,
    symbol: artist.symbol
  };
}

export function mapRegistryMusicRelease(release: RegistryMusicReleaseRow): RegistryMusicRelease {
  return {
    artist: mapRegistryArtistSummary(release.artist),
    coverImage: release.coverImage,
    createdAt: release.createdAt.toISOString(),
    id: release.id,
    releaseCode: release.releaseCode,
    status: release.status,
    title: release.title,
    tracks: release.tracks.map((track) => mapRegistryTrack(track, { release: null }))
  };
}

export function mapRegistryTrack(
  track: RegistryTrackRow,
  context: { release: RegistryTrack["release"] }
): RegistryTrack {
  return {
    duration: track.duration,
    id: track.id,
    moodFragment: track.moodFragment,
    release: context.release,
    releaseId: track.releaseId,
    title: track.title,
    trackKey: track.trackKey
  };
}

export function mapRegistryTrackWithRelease(track: RegistryTrackWithReleaseRow): RegistryTrack {
  return mapRegistryTrack(track, {
    release: {
      ...track.release,
      artist: mapRegistryArtistSummary(track.release.artist)
    }
  });
}

export function mapRegistryChannelPresence(presence: RegistryChannelPresenceRow): RegistryChannelPresence {
  return {
    artist: presence.artist ? mapRegistryArtistSummary(presence.artist) : null,
    createdAt: presence.createdAt.toISOString(),
    handle: presence.handle,
    id: presence.id,
    platform: presence.platform,
    presenceKey: presence.presenceKey,
    profileUrl: presence.profileUrl,
    verifiedState: presence.verifiedState,
    visibility: presence.visibility
  };
}

export function mapRegistryExternalReference(reference: RegistryExternalReferenceRow): RegistryExternalReference {
  const targets = {
    artist: reference.artist ? mapRegistryArtistSummary(reference.artist) : null,
    channelPresence: reference.channelPresence,
    musicRelease: reference.musicRelease,
    objectRelease: reference.objectRelease,
    track: reference.track
  };

  return {
    createdAt: reference.createdAt.toISOString(),
    externalId: reference.externalId,
    id: reference.id,
    platform: reference.platform,
    referenceKey: reference.referenceKey,
    sourceAuthority: reference.sourceAuthority,
    targetCount: Object.values(targets).filter(Boolean).length,
    targets,
    url: reference.url,
    verifiedState: reference.verifiedState
  };
}

export function mapRegistryDistributionReference(
  reference: RegistryDistributionReferenceRow
): RegistryDistributionReference {
  return {
    createdAt: reference.createdAt.toISOString(),
    distributionKey: reference.distributionKey,
    externalId: reference.externalId,
    id: reference.id,
    musicRelease: reference.musicRelease,
    platform: reference.platform,
    sourceAuthority: reference.sourceAuthority,
    targetCount: [reference.musicRelease, reference.track].filter(Boolean).length,
    track: reference.track,
    url: reference.url,
    verifiedState: reference.verifiedState
  };
}
