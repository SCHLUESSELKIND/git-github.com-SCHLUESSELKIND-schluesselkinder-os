export type RegistryPlatform =
  | "SOUNDCLOUD"
  | "SPOTIFY"
  | "TIKTOK"
  | "INSTAGRAM"
  | "APPLE_MUSIC"
  | "YOUTUBE"
  | "MANUAL"
  | "OTHER";

export type RegistryVerificationState = "UNVERIFIED" | "MANUALLY_VERIFIED" | "EXTERNALLY_OBSERVED" | "STALE" | "UNAVAILABLE";

export type RegistryChannelVisibility = "INTERNAL" | "PUBLIC" | "HIDDEN";

export type RegistryArtistStatus = "ACTIVE" | "ARCHIVED" | "HIDDEN";

export type RegistryReleaseStatus = "SIGNAL_PENDING" | "ACTIVE" | "CLOSED" | "ARCHIVED" | "HIDDEN";

export type RegistryLineageType = "ORIGINAL" | "VARIANT" | "EDIT" | "MIX" | "REMIX" | "REMASTER" | "FRAGMENT" | "RELATED";

export type RegistryArtistRow = Readonly<{
  artistKey: string | null;
  bioFragment: string | null;
  createdAt: Date;
  id: string;
  name: string;
  slug: string;
  status: RegistryArtistStatus;
  symbol: string;
}>;

export type RegistryArtistSummary = Readonly<{
  artistKey: string | null;
  canonicalName: string;
  id: string;
  slug: string;
}>;

export type RegistryArtistSummaryRow = Readonly<{
  artistKey: string | null;
  id: string;
  name: string;
  slug: string;
}>;

export type RegistryMusicReleaseSummary = Readonly<{
  id: string;
  releaseCode: string;
  title: string;
}>;

export type RegistryTrackSummary = Readonly<{
  id: string;
  title: string;
  trackKey: string | null;
}>;

export type RegistryObjectReleaseSummary = Readonly<{
  id: string;
  releaseId: string;
  title: string;
}>;

export type RegistryChannelPresenceSummary = Readonly<{
  id: string;
  platform: RegistryPlatform;
  presenceKey: string;
}>;

export type RegistryMusicReleaseRow = Readonly<{
  artist: RegistryArtistSummaryRow;
  artistId: string;
  coverImage: string | null;
  createdAt: Date;
  id: string;
  releaseCode: string;
  status: RegistryReleaseStatus;
  title: string;
  tracks: RegistryTrackRow[];
}>;

export type RegistryTrackRow = Readonly<{
  duration: number | null;
  id: string;
  moodFragment: string | null;
  releaseId: string;
  title: string;
  trackKey: string | null;
}>;

export type RegistryTrackWithReleaseRow = RegistryTrackRow &
  Readonly<{
    release: RegistryMusicReleaseSummary & {
      artist: RegistryArtistSummaryRow;
    };
  }>;

export type RegistryChannelPresenceRow = Readonly<{
  artist: RegistryArtistSummaryRow | null;
  artistId: string | null;
  createdAt: Date;
  handle: string | null;
  id: string;
  platform: RegistryPlatform;
  presenceKey: string;
  profileUrl: string | null;
  verifiedState: RegistryVerificationState;
  visibility: RegistryChannelVisibility;
}>;

export type RegistryExternalReferenceRow = Readonly<{
  artist: RegistryArtistSummaryRow | null;
  artistId: string | null;
  channelPresence: RegistryChannelPresenceSummary | null;
  channelPresenceId: string | null;
  createdAt: Date;
  externalId: string | null;
  id: string;
  musicRelease: RegistryMusicReleaseSummary | null;
  musicReleaseId: string | null;
  objectRelease: RegistryObjectReleaseSummary | null;
  objectReleaseId: string | null;
  platform: RegistryPlatform;
  referenceKey: string;
  sourceAuthority: boolean;
  track: RegistryTrackSummary | null;
  trackId: string | null;
  url: string;
  verifiedState: RegistryVerificationState;
}>;

export type RegistryDistributionReferenceRow = Readonly<{
  createdAt: Date;
  distributionKey: string;
  externalId: string | null;
  id: string;
  musicRelease: RegistryMusicReleaseSummary | null;
  musicReleaseId: string | null;
  platform: RegistryPlatform;
  sourceAuthority: boolean;
  track: RegistryTrackSummary | null;
  trackId: string | null;
  url: string | null;
  verifiedState: RegistryVerificationState;
}>;

export type RegistryArtist = Readonly<{
  artistKey: string | null;
  bioFragment: string | null;
  canonicalName: string;
  createdAt: string;
  id: string;
  slug: string;
  status: RegistryArtistStatus;
  symbol: string;
}>;

export type RegistryMusicRelease = Readonly<{
  artist: RegistryArtistSummary;
  coverImage: string | null;
  createdAt: string;
  id: string;
  releaseCode: string;
  status: RegistryReleaseStatus;
  title: string;
  tracks: RegistryTrack[];
}>;

export type RegistryTrack = Readonly<{
  duration: number | null;
  id: string;
  moodFragment: string | null;
  release: (RegistryMusicReleaseSummary & { artist?: RegistryArtistSummary }) | null;
  releaseId: string;
  title: string;
  trackKey: string | null;
}>;

export type RegistryChannelPresence = Readonly<{
  artist: RegistryArtistSummary | null;
  createdAt: string;
  handle: string | null;
  id: string;
  platform: RegistryPlatform;
  presenceKey: string;
  profileUrl: string | null;
  verifiedState: RegistryVerificationState;
  visibility: RegistryChannelVisibility;
}>;

export type RegistryReferenceTargets = Readonly<{
  artist: RegistryArtistSummary | null;
  channelPresence: RegistryChannelPresenceSummary | null;
  musicRelease: RegistryMusicReleaseSummary | null;
  objectRelease: RegistryObjectReleaseSummary | null;
  track: RegistryTrackSummary | null;
}>;

export type RegistryExternalReference = Readonly<{
  createdAt: string;
  externalId: string | null;
  id: string;
  platform: RegistryPlatform;
  referenceKey: string;
  sourceAuthority: boolean;
  targetCount: number;
  targets: RegistryReferenceTargets;
  url: string;
  verifiedState: RegistryVerificationState;
}>;

export type RegistryDistributionReference = Readonly<{
  createdAt: string;
  distributionKey: string;
  externalId: string | null;
  id: string;
  musicRelease: RegistryMusicReleaseSummary | null;
  platform: RegistryPlatform;
  sourceAuthority: boolean;
  targetCount: number;
  track: RegistryTrackSummary | null;
  url: string | null;
  verifiedState: RegistryVerificationState;
}>;

export type RegistryRepository = Readonly<{
  getArtistByKeyOrSlug(keyOrSlug: string): Promise<RegistryArtist | null>;
  getMusicReleaseByCode(releaseCode: string): Promise<RegistryMusicRelease | null>;
  getTrackByKey(trackKey: string): Promise<RegistryTrack | null>;
  listArtists(): Promise<RegistryArtist[]>;
  listChannelPresences(): Promise<RegistryChannelPresence[]>;
  listDistributionReferences(): Promise<RegistryDistributionReference[]>;
  listExternalReferences(): Promise<RegistryExternalReference[]>;
  listMusicReleases(): Promise<RegistryMusicRelease[]>;
  listTracks(): Promise<RegistryTrack[]>;
}>;
