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
      // Verified 2026-06-10 on the canonical artist profile (1jzZXWDrVb0…):
      // "Grünlichtbezirk" is live as a SINGLE. The locked 3-track EP shape
      // has not appeared as one album yet — if it lands on T-0, swap this
      // album ID for the EP's.
      spotify: "https://open.spotify.com/album/4tzxhyGZNEPs2kES3wydfO",
      appleMusic: undefined,
      soundcloud: undefined,
      bandcamp: undefined,
      youtubeMusic: undefined,
      // shop.schluesselkinder.de currently redirects to the apex domain
      // (Shopify Admin primary-domain config). A relative path would 404 on
      // the apex after T-0. Set the absolute collection URL once the
      // storefront resolves: https://shop.schluesselkinder.de/collections/gruenlichtbezirk
      shopCollection: undefined
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
 * no fluff. e.g. "12.06.2026 · 00:00 CEST".
 *
 * Parses every component DIRECTLY from the ISO 8601 source string. Going
 * through `new Date()` + `getUTC*()` would shift the display into UTC and
 * silently break the cutover (e.g. "2026-06-12T00:00:00+02:00" → UTC
 * June 11 22:00 → displays "11.06" instead of "12.06"). That bug shipped
 * once in the first prerender — it stays caught here.
 *
 * The timezone label is picked from the offset:
 *   +01:00 → "CET"  (winter)
 *   +02:00 → "CEST" (summer, DST)
 *   anything else → raw offset string, never silently mis-labeled.
 */
export function formatReleaseDate(release: Release): string {
  const match = release.releaseAt.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}([+-]\d{2}):?(\d{2})$/
  );
  if (!match) {
    return release.releaseAt;
  }
  const [, year, month, day, hh, mm, offsetHours] = match;
  let tzLabel: string;
  if (offsetHours === "+01") {
    tzLabel = "CET";
  } else if (offsetHours === "+02") {
    tzLabel = "CEST";
  } else {
    tzLabel = `UTC${offsetHours}`;
  }
  return `${day}.${month}.${year} · ${hh}:${mm} ${tzLabel}`;
}
