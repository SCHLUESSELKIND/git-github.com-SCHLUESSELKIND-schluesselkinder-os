import type { DistributionReferenceRecord, ExternalReferenceRecord } from "./types.js";

export const externalReferences = [] as const satisfies readonly ExternalReferenceRecord[];

export const distributionReferences = [] as const satisfies readonly DistributionReferenceRecord[];
