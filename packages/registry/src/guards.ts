import { artists } from "./artists";
import { objects } from "./objects";
import { releases } from "./releases";
import { trackSignals } from "./tracks";

type KeyedRecord = Readonly<{
  code?: string;
  key: string;
  visibility: "public" | "internal";
}>;

function countValues(values: readonly string[]) {
  const counts = new Map<string, number>();

  for (const value of values) {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }

  return counts;
}

function duplicates(values: readonly string[]) {
  return [...countValues(values).entries()].filter(([, count]) => count > 1).map(([value]) => value);
}

function collectRecords(): KeyedRecord[] {
  return [
    ...artists.map((artist) => ({ key: artist.artistKey, visibility: artist.visibility })),
    ...releases.map((release) => ({ code: release.releaseCode, key: release.releaseKey, visibility: release.visibility })),
    ...trackSignals.map((track) => ({ code: track.trackCode, key: track.trackKey, visibility: track.visibility })),
    ...objects.map((object) => ({ code: object.objectCode, key: object.objectKey, visibility: object.visibility }))
  ];
}

export function auditStaticRegistry() {
  const records = collectRecords();
  const duplicateKeys = duplicates(records.map((record) => record.key));
  const duplicateCodes = duplicates(records.flatMap((record) => (record.code ? [record.code] : [])));
  const publicCodesMatchingInternalKeys = records.filter((record) => record.code === record.key).map((record) => record.key);
  const publicText = records
    .filter((record) => record.visibility === "public")
    .map((record) => `${record.key} ${record.code ?? ""}`)
    .join(" ");

  return {
    duplicateCodes,
    duplicateKeys,
    onHoldPublic: /PICK ME UP|TUESDAY MORNING COMEDOWN/.test(publicText),
    publicCodesMatchingInternalKeys,
    ropemasterReleaseAndTrackAreDistinct:
      releases.some((release) => release.releaseKey === "RELEASE-ROPEMASTER-LP" && release.title === "ROPEMASTER") &&
      trackSignals.some((track) => track.trackKey === "TRACK-ROPEMASTER" && track.title === "ROPEMASTER")
  };
}
