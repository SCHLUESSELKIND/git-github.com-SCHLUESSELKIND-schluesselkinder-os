import type { WorldRecord } from "./types";

export const worlds = [
  {
    title: "Post Club Silence",
    visibility: "internal",
    worldKey: "WORLD-POST-CLUB-SILENCE"
  },
  {
    title: "Room After Light",
    visibility: "internal",
    worldKey: "WORLD-ROOM-AFTER-LIGHT"
  },
  {
    title: "Cold Archive",
    visibility: "internal",
    worldKey: "WORLD-COLD-ARCHIVE"
  }
] as const satisfies readonly WorldRecord[];
