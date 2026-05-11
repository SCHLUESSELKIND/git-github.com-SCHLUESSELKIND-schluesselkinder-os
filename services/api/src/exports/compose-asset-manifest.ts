import type { CompatibilityRecord } from "../repositories.js";
import { manualExportSurfaceBoundary, type AssetManifest } from "./types.js";

export function composeAssetManifest(input: {
  campaignWorldCode: string | null;
  compatibility: CompatibilityRecord[];
  manifestKey: string;
}): AssetManifest {
  return {
    ...manualExportSurfaceBoundary,
    assets: input.compatibility
      .filter((compatibility) => compatibility.kind === "CAMPAIGN_WORLD_ASSET")
      .filter((compatibility) => {
        if (!input.campaignWorldCode) {
          return true;
        }

        return compatibility.record.campaignWorld.code === input.campaignWorldCode;
      })
      .map((compatibility) => ({
        ...manualExportSurfaceBoundary,
        campaignWorldRelation: compatibility.record.campaignWorld.code,
        code: compatibility.record.asset.code,
        compatibilityVerdict: compatibility.record.verdict,
        referenceKey: compatibility.record.asset.referenceKey,
        sourceType: compatibility.record.asset.sourceType,
        title: compatibility.record.asset.title
      })),
    manifestKey: input.manifestKey,
    symbolicOnly: true
  };
}
