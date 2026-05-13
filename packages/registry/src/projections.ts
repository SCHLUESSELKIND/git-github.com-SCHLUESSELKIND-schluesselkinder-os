import { artists } from "./artists";
import { objects } from "./objects";
import { releases } from "./releases";
import { trackSignals } from "./tracks";
import type {
  PublicArtistDossier,
  PublicObjectProjection,
  PublicReleaseProjection,
  PublicTrackSignalProjection
} from "./types";

function isPublic<T extends { visibility: "public" | "internal" }>(record: T) {
  return record.visibility === "public";
}

function toPublicTrackSignal(track: (typeof trackSignals)[number]): PublicTrackSignalProjection {
  return {
    releaseKey: track.releaseKey,
    title: track.title,
    trackCode: track.trackCode,
    trackKey: track.trackKey
  };
}

export function getArtistDossier(): PublicArtistDossier {
  const artist = artists.find(isPublic);

  if (!artist) {
    throw new Error("No public artist dossier is available.");
  }

  return {
    artistKey: artist.artistKey,
    canonicalName: artist.canonicalName,
    slug: artist.slug
  };
}

export function getPublicReleaseSignals(): PublicReleaseProjection[] {
  return releases.filter(isPublic).map((release) => ({
    displayTitle: release.displayTitle,
    releaseCode: release.releaseCode,
    releaseKey: release.releaseKey,
    role: release.role,
    signals: trackSignals.filter((track) => isPublic(track) && track.releaseKey === release.releaseKey).map(toPublicTrackSignal),
    title: release.title
  }));
}

export function getReleaseByCode(code: string): PublicReleaseProjection | null {
  return getPublicReleaseSignals().find((release) => release.releaseCode === code) ?? null;
}

export function getPublicObjects(): PublicObjectProjection[] {
  return objects.filter(isPublic).map((object) => ({
    objectClass: object.objectClass,
    objectCode: object.objectCode,
    objectKey: object.objectKey,
    releaseKey: object.releaseKey ?? null,
    title: object.title
  }));
}

export function getObjectByCode(code: string): PublicObjectProjection | null {
  return getPublicObjects().find((object) => object.objectCode === code) ?? null;
}
