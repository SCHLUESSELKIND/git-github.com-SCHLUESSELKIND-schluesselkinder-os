import type { LineageRecord } from "./types.js";

export const lineage = [
  {
    childKey: "OBJ-SK-002",
    lineageKey: "LINEAGE-RELEASE-ROPEMASTER-LP-OBJ-SK-002",
    parentKey: "RELEASE-ROPEMASTER-LP",
    relation: "release-object",
    visibility: "public"
  }
] as const satisfies readonly LineageRecord[];
