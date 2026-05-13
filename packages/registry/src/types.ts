export type RegistryVisibility = "public" | "internal";

export type RegistryLifecycleState = "active-signal" | "active-archive" | "closed" | "on-hold";

export type ArtistKey = `ARTIST-${string}`;
export type ReleaseKey = `RELEASE-${string}`;
export type TrackKey = `TRACK-${string}`;
export type ObjectKey = `OBJ-${string}`;
export type WorldKey = `WORLD-${string}`;
export type ReferenceKey = `REF-${string}`;
export type DistributionKey = `DIST-${string}`;
export type LineageKey = `LINEAGE-${string}`;

export type ArtistRecord = Readonly<{
  artistKey: ArtistKey;
  canonicalName: string;
  slug: string;
  state: RegistryLifecycleState;
  visibility: RegistryVisibility;
}>;

export type ReleaseRecord = Readonly<{
  releaseKey: ReleaseKey;
  releaseCode: string;
  title: string;
  displayTitle: string;
  artistKey: ArtistKey;
  role: "album-anchor" | "preview-signal";
  state: RegistryLifecycleState;
  visibility: RegistryVisibility;
}>;

export type TrackSignalRecord = Readonly<{
  trackKey: TrackKey;
  trackCode: string;
  title: string;
  releaseKey: ReleaseKey;
  role: "preview-signal";
  state: RegistryLifecycleState;
  visibility: RegistryVisibility;
}>;

export type ObjectRecord = Readonly<{
  objectKey: ObjectKey;
  objectCode: string;
  title: string;
  objectClass: "archive-object" | "release-object";
  mark: string;
  releaseKey?: ReleaseKey;
  state: RegistryLifecycleState;
  visibility: RegistryVisibility;
}>;

export type WorldRecord = Readonly<{
  worldKey: WorldKey;
  title: string;
  visibility: RegistryVisibility;
}>;

export type ExternalReferenceRecord = Readonly<{
  referenceKey: ReferenceKey;
  targetKey: ArtistKey | ReleaseKey | TrackKey | ObjectKey;
  platform: "SOUNDCLOUD" | "SPOTIFY" | "YOUTUBE" | "INSTAGRAM" | "TIKTOK";
  sourceAuthority: false;
  visibility: RegistryVisibility;
}>;

export type DistributionReferenceRecord = Readonly<{
  distributionKey: DistributionKey;
  targetKey: ReleaseKey | TrackKey;
  platform: "SOUNDCLOUD" | "SPOTIFY" | "YOUTUBE";
  sourceAuthority: false;
  visibility: RegistryVisibility;
}>;

export type LineageRecord = Readonly<{
  lineageKey: LineageKey;
  parentKey: ReleaseKey | TrackKey | ObjectKey;
  childKey: ReleaseKey | TrackKey | ObjectKey;
  relation: "contextual" | "release-object";
  visibility: RegistryVisibility;
}>;

export type PublicArtistDossier = Readonly<{
  artistKey: ArtistKey;
  canonicalName: string;
  slug: string;
}>;

export type PublicReleaseProjection = Readonly<{
  releaseKey: ReleaseKey;
  releaseCode: string;
  title: string;
  displayTitle: string;
  role: ReleaseRecord["role"];
  signals: PublicTrackSignalProjection[];
}>;

export type PublicTrackSignalProjection = Readonly<{
  trackKey: TrackKey;
  trackCode: string;
  title: string;
  releaseKey: ReleaseKey;
}>;

export type PublicObjectProjection = Readonly<{
  objectKey: ObjectKey;
  objectCode: string;
  title: string;
  objectClass: ObjectRecord["objectClass"];
  releaseKey: ReleaseKey | null;
}>;
