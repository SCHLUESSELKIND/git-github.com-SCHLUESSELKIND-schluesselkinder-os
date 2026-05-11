import type { RegistryArtist, RegistryMusicRelease, RegistryTrack } from "../registry/registry-types.js";
import type { CatalogArtistProjection, CatalogReleaseProjection, CatalogTrackProjection } from "./catalog-types.js";

export function mapCatalogArtistProjection(artist: RegistryArtist): CatalogArtistProjection | null {
  if (!artist.artistKey) {
    return null;
  }

  return {
    artistKey: artist.artistKey,
    displayName: artist.canonicalName,
    primaryImage: null,
    primaryWorld: null,
    state: artist.status
  };
}

export function mapCatalogReleaseProjection(release: RegistryMusicRelease): CatalogReleaseProjection {
  return {
    canonicalArtwork: release.coverImage,
    publicFragments: [],
    releaseCode: release.releaseCode,
    releaseType: null,
    state: release.status,
    title: release.title
  };
}

export function mapCatalogTrackProjection(track: RegistryTrack): CatalogTrackProjection | null {
  if (!track.trackKey) {
    return null;
  }

  return {
    moods: [],
    runtime: track.duration,
    title: track.title,
    trackKey: track.trackKey,
    worlds: []
  };
}

export function filterCatalogProjection<T>(projection: T | null): projection is T {
  return projection !== null;
}
