import type { TrackSignalRecord } from "./types.js";

export const trackSignals = [
  {
    releaseKey: "RELEASE-ROPEMASTER-LP",
    role: "preview-signal",
    state: "active-signal",
    title: "TINDERMATCH",
    trackCode: "SKR-001",
    trackKey: "TRACK-TINDERMATCH",
    visibility: "public"
  },
  {
    releaseKey: "RELEASE-ROPEMASTER-LP",
    role: "preview-signal",
    state: "active-signal",
    title: "ROPEMASTER",
    trackCode: "SKR-002",
    trackKey: "TRACK-ROPEMASTER",
    visibility: "public"
  }
] as const satisfies readonly TrackSignalRecord[];
