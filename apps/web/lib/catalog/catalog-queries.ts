import { readCatalogJson, type CatalogClientOptions } from "./catalog-client";
import type { CatalogArtistProjection, CatalogReleaseProjection, CatalogTrackProjection } from "./catalog-types";

export async function listCatalogArtists(options?: CatalogClientOptions) {
  return (await readCatalogJson<CatalogArtistProjection[]>("/catalog/artists", options)) ?? [];
}

export async function getCatalogArtist(artistKey: string, options?: CatalogClientOptions) {
  return readCatalogJson<CatalogArtistProjection>(`/catalog/artists/${encodeURIComponent(artistKey)}`, options);
}

export async function listCatalogMusicReleases(options?: CatalogClientOptions) {
  return (await readCatalogJson<CatalogReleaseProjection[]>("/catalog/music-releases", options)) ?? [];
}

export async function getCatalogMusicRelease(releaseCode: string, options?: CatalogClientOptions) {
  return readCatalogJson<CatalogReleaseProjection>(
    `/catalog/music-releases/${encodeURIComponent(releaseCode)}`,
    options
  );
}

export async function listCatalogTracks(options?: CatalogClientOptions) {
  return (await readCatalogJson<CatalogTrackProjection[]>("/catalog/tracks", options)) ?? [];
}

export async function getCatalogTrack(trackKey: string, options?: CatalogClientOptions) {
  return readCatalogJson<CatalogTrackProjection>(`/catalog/tracks/${encodeURIComponent(trackKey)}`, options);
}
