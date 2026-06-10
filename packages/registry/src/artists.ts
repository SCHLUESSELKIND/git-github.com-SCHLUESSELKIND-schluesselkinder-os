import type { ArtistRecord } from "./types";

export const artists = [
  {
    artistKey: "ARTIST-SHIBARI-KAWAII",
    canonicalName: "SHIBARI KAWAII",
    slug: "shibari-kawaii",
    state: "active-signal",
    visibility: "public"
  },
  {
    artistKey: "ARTIST-SNUFFRAGGA-SOUNDSYSTEM",
    canonicalName: "SNUFFRAGGA SOUNDSYSTEM",
    slug: "snuffragga",
    state: "active-signal",
    visibility: "public"
  }
] as const satisfies readonly ArtistRecord[];
