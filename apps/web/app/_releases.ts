// Release constants — single source of truth for cross-page release state.
//
// Edit when locking the next release. The ReleaseStatus component reads from
// here. Order matters — index 0 is the latest / most-foregrounded release.
//
// Dates are ISO 8601 with explicit timezone. Do NOT use local-time strings
// like "2026-06-12 00:00" — Next.js renders in UTC on the server and
// timezone slippage at the cutover moment is the single most expensive bug
// in release tooling.

export type ReleaseStatus = "incoming" | "in_transmission" | "archived";

export interface Release {
  /** Stable release ID, matches docs/release-log.md and docs/releases/<id>/. */
  id: string;
  /** Artist slug used in /artists/[slug]. */
  artist: string;
  /** EP / album title as it appears on streaming + cover. */
  title: string;
  /** Release moment, ISO 8601 with explicit zone offset (CET = +01:00, CEST = +02:00). */
  releaseAt: string;
  /** Streaming + shop URLs. All optional — render whichever resolve. */
  links: {
    spotify?: string;
    appleMusic?: string;
    soundcloud?: string;
    bandcamp?: string;
    youtubeMusic?: string;
    shopCollection?: string;
  };
  /** Tracklist for display. */
  tracks: string[];
  /** When the release rolls off the foreground onto the archive list. */
  archivesAfterDays?: number;
}

/**
 * 2026-06-12 00:00 CEST is +02:00 (Germany is on CEST in June).
 * Spelt out as ISO 8601: "2026-06-12T00:00:00+02:00".
 */
export const RELEASES: readonly Release[] = [
  {
    id: "RELEASE-001",
    artist: "snuffragga",
    title: "GRÜNLICHTBEZIRK",
    releaseAt: "2026-06-12T00:00:00+02:00",
    links: {
      // Real URLs populated as part of the T-2 / T-1 production tasks. Empty
      // until then — the page renders the "incoming" state until releaseAt anyway.
      spotify: undefined,
      appleMusic: undefined,
      soundcloud: undefined,
      bandcamp: undefined,
      youtubeMusic: undefined,
      shopCollection: "/collections/gruenlichtbezirk"
    },
    tracks: ["GRÜNLICHTBEZIRK", "DISTRICT PRESSURE", "NACHTFREQUENZ"],
    archivesAfterDays: 90
  }
] as const;

/**
 * Compute the live status of a release at a given moment. Tests can pass a
 * fixed `now` to keep snapshots deterministic.
 */
export function statusOf(release: Release, now: Date = new Date()): ReleaseStatus {
  const releaseTime = new Date(release.releaseAt).getTime();
  const nowTime = now.getTime();
  if (nowTime < releaseTime) {
    return "incoming";
  }
  const archiveTime = release.archivesAfterDays
    ? releaseTime + release.archivesAfterDays * 24 * 60 * 60 * 1000
    : Number.POSITIVE_INFINITY;
  if (nowTime >= archiveTime) {
    return "archived";
  }
  return "in_transmission";
}

/**
 * Find the latest release for a given artist slug. Returns null if the artist
 * has no releases. Order in RELEASES decides "latest" — keep newest at index 0.
 */
export function latestReleaseFor(artist: string): Release | null {
  for (const release of RELEASES) {
    if (release.artist === artist) {
      return release;
    }
  }
  return null;
}

/**
 * Format the release date for display in the brand voice: cold, ISO-leaning,
 * no fluff. e.g. "12.06.2026 · 00:00 CET".
 */
export function formatReleaseDate(release: Release): string {
  const d = new Date(release.releaseAt);
  const day = String(d.getUTCDate()).padStart(2, "0");
  const month = String(d.getUTCMonth() + 1).padStart(2, "0");
  const year = d.getUTCFullYear();
  // Construct from the ISO string to keep CET/CEST exact rather than the
  // server's local zone, which on Hetzner is UTC.
  const isoTimeMatch = release.releaseAt.match(/T(\d{2}):(\d{2})/);
  const hh = isoTimeMatch ? isoTimeMatch[1] : "00";
  const mm = isoTimeMatch ? isoTimeMatch[2] : "00";
  return `${day}.${month}.${year} · ${hh}:${mm} CET`;
}
