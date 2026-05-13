import type { ReleaseRecord } from "./types.js";

export const releases = [
  {
    artistKey: "ARTIST-SHIBARI-KAWAII",
    displayTitle: "ROPEMASTER LP",
    releaseCode: "SKR-LP-001",
    releaseKey: "RELEASE-ROPEMASTER-LP",
    role: "album-anchor",
    state: "active-signal",
    title: "ROPEMASTER",
    visibility: "public"
  }
] as const satisfies readonly ReleaseRecord[];
