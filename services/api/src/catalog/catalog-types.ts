import type { RegistryArtistStatus, RegistryReleaseStatus } from "../registry/registry-types.js";

export type CatalogArtistProjection = Readonly<{
  artistKey: string;
  displayName: string;
  primaryImage: string | null;
  primaryWorld: string | null;
  state: RegistryArtistStatus;
}>;

export type CatalogReleaseProjection = Readonly<{
  canonicalArtwork: string | null;
  publicFragments: string[];
  releaseCode: string;
  releaseType: string | null;
  state: RegistryReleaseStatus;
  title: string;
}>;

export type CatalogTrackProjection = Readonly<{
  moods: string[];
  runtime: number | null;
  title: string;
  trackKey: string;
  worlds: string[];
}>;

export type CatalogProjectionSet = Readonly<{
  artists: CatalogArtistProjection[];
  releases: CatalogReleaseProjection[];
  tracks: CatalogTrackProjection[];
}>;

export type CatalogService = Readonly<{
  listArtistProjections(): Promise<CatalogArtistProjection[]>;
  listReleaseProjections(): Promise<CatalogReleaseProjection[]>;
  listTrackProjections(): Promise<CatalogTrackProjection[]>;
  readCatalogProjectionSet(): Promise<CatalogProjectionSet>;
}>;
