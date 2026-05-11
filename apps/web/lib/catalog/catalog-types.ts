export type CatalogArtistState = "ACTIVE" | "ARCHIVED" | "HIDDEN";

export type CatalogReleaseState = "SIGNAL_PENDING" | "ACTIVE" | "CLOSED" | "ARCHIVED" | "HIDDEN";

export type CatalogArtistProjection = Readonly<{
  artistKey: string;
  displayName: string;
  primaryImage: string | null;
  primaryWorld: string | null;
  state: CatalogArtistState;
}>;

export type CatalogReleaseProjection = Readonly<{
  canonicalArtwork: string | null;
  publicFragments: string[];
  releaseCode: string;
  releaseType: string | null;
  state: CatalogReleaseState;
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
