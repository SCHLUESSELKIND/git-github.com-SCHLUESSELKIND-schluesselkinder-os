import { manualExportSurfaceBoundary, type ExportPackage, type ManualExportArtifact, type PortableBundle } from "./types.js";

type ExportPackageWithoutBundles = Omit<ExportPackage, "manualArtifacts" | "portableBundles">;

export function formatPortableBundles(input: ExportPackageWithoutBundles): PortableBundle[] {
  return [
    {
      ...manualExportSurfaceBoundary,
      bundleKey: `BUNDLE-${input.sourceKey}-JSON`,
      content: JSON.stringify(input, null, 2),
      format: "JSON",
      title: `${input.title} portable JSON`
    },
    {
      ...manualExportSurfaceBoundary,
      bundleKey: `BUNDLE-${input.sourceKey}-TEXT`,
      content: [
        `Package: ${input.packageKey}`,
        `Source: ${input.sourceKey}`,
        `Subject: ${input.subjectKey}`,
        `Review: ${input.reviewSnapshot.reviewKey ?? "NONE"}`,
        `Evaluation: ${input.evaluationSnapshot.dominantVerdict}`,
        `Assets: ${input.assetManifest.assets.length}`,
        "",
        "Human commit required.",
        "externalDelivery: false",
        "distributionAuthority: false"
      ].join("\n"),
      format: "TEXT",
      title: `${input.title} portable text`
    }
  ];
}

export function formatManualExportArtifacts(input: ExportPackageWithoutBundles, bundles: PortableBundle[]): ManualExportArtifact[] {
  const jsonBundle = bundles.find((bundle) => bundle.format === "JSON");
  const textBundle = bundles.find((bundle) => bundle.format === "TEXT");

  return [
    {
      ...manualExportSurfaceBoundary,
      artifactKey: `MANUAL-${input.sourceKey}-JSON`,
      artifactType: "PORTABLE_JSON",
      content: jsonBundle?.content ?? JSON.stringify(input, null, 2),
      title: `${input.title} JSON artifact`
    },
    {
      ...manualExportSurfaceBoundary,
      artifactKey: `MANUAL-${input.sourceKey}-TEXT`,
      artifactType: "PORTABLE_TEXT",
      content: textBundle?.content ?? input.title,
      title: `${input.title} text artifact`
    },
    {
      ...manualExportSurfaceBoundary,
      artifactKey: `MANUAL-${input.sourceKey}-ASSETS`,
      artifactType: "ASSET_MANIFEST",
      content: JSON.stringify(input.assetManifest, null, 2),
      title: `${input.title} asset manifest`
    },
    {
      ...manualExportSurfaceBoundary,
      artifactKey: `MANUAL-${input.sourceKey}-REVIEW`,
      artifactType: "REVIEW_SNAPSHOT",
      content: JSON.stringify(input.reviewSnapshot, null, 2),
      title: `${input.title} review snapshot`
    },
    {
      ...manualExportSurfaceBoundary,
      artifactKey: `MANUAL-${input.sourceKey}-EVALUATION`,
      artifactType: "EVALUATION_SNAPSHOT",
      content: JSON.stringify(input.evaluationSnapshot, null, 2),
      title: `${input.title} evaluation snapshot`
    }
  ];
}
