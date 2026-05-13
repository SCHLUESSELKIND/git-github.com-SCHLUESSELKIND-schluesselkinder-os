import type { ObjectRecord } from "./types.js";

export const objects: readonly ObjectRecord[] = [
  {
    mark: "KEY",
    objectClass: "archive-object",
    objectCode: "SK-001",
    objectKey: "OBJ-SK-001",
    state: "closed",
    title: "BLACK HOODIE / KEY",
    visibility: "public"
  },
  {
    mark: "ROPEMASTER",
    objectClass: "release-object",
    objectCode: "SK-002",
    objectKey: "OBJ-SK-002",
    releaseKey: "RELEASE-ROPEMASTER-LP",
    state: "active-archive",
    title: "SHIBARI KAWAII ROPEMASTER HOODIE",
    visibility: "public"
  }
] as const satisfies readonly ObjectRecord[];
