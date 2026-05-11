import type {
  AssetSourceType,
  Channel,
  CompatibilityVerdict,
  ConstraintSource,
  EvaluationVerdict,
  RuleSeverity,
  RuleViolationSource
} from "@schluesselkinder/db";

export const manualExportSurfaceBoundary = {
  approvalAuthority: false,
  automationAllowed: false,
  distributionAuthority: false,
  externalDelivery: false,
  humanCommitRequired: true,
  manualExportPrepared: true,
  portableArtifactOnly: true,
  publishAuthority: false,
  publishReady: false,
  reviewRequired: true
} as const;

export type ManualExportSurfaceBoundary = typeof manualExportSurfaceBoundary;

export type ExportSourceType = "GENERATION_BRIEF" | "GENERATION_OUTPUT" | "REVIEW_ITEM";

export type ReviewDecisionSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    createdAt: string;
    decidedBy: string | null;
    note: string | null;
    type: string;
  }
>;

export type ReviewCommentSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    author: string | null;
    body: string;
    createdAt: string;
  }
>;

export type ReviewViolationSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    active: boolean;
    detail: string;
    ruleCode: string | null;
    severity: RuleSeverity;
    source: RuleViolationSource;
    title: string;
  }
>;

export type ReviewSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    comments: ReviewCommentSnapshot[];
    decisions: ReviewDecisionSnapshot[];
    reviewKey: string | null;
    snapshotImpliesApproval: false;
    stage: string | null;
    status: string | null;
    subjectKey: string | null;
    subjectType: string | null;
    summary: string | null;
    title: string;
    violations: ReviewViolationSnapshot[];
  }
>;

export type EvaluationFindingSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    detail: string;
    ruleCode: string | null;
    source: ConstraintSource;
    title: string;
    verdict: EvaluationVerdict;
  }
>;

export type EvaluationSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    dominantVerdict: EvaluationVerdict | "NOT_EVALUATED";
    findings: EvaluationFindingSnapshot[];
    passImpliesApproval: false;
    snapshotImpliesTruth: false;
    verdicts: EvaluationVerdict[];
  }
>;

export type ConstraintSnapshot = Readonly<
  ManualExportSurfaceBoundary & {
    bundleCode: string | null;
    bundleName: string | null;
    constraints: ReadonlyArray<
      ManualExportSurfaceBoundary & {
        instruction: string;
        required: boolean;
        ruleCode: string | null;
        source: ConstraintSource;
        title: string;
        weight: number;
      }
    >;
    requiredCount: number;
  }
>;

export type AssetManifestItem = Readonly<
  ManualExportSurfaceBoundary & {
    campaignWorldRelation: string;
    code: string;
    compatibilityVerdict: CompatibilityVerdict;
    referenceKey: string | null;
    sourceType: AssetSourceType;
    title: string;
  }
>;

export type AssetManifest = Readonly<
  ManualExportSurfaceBoundary & {
    assets: AssetManifestItem[];
    manifestKey: string;
    symbolicOnly: true;
  }
>;

export type PortableBundle = Readonly<
  ManualExportSurfaceBoundary & {
    bundleKey: string;
    content: string;
    format: "JSON" | "TEXT";
    title: string;
  }
>;

export type ManualExportArtifact = Readonly<
  ManualExportSurfaceBoundary & {
    artifactKey: string;
    artifactType: "PORTABLE_JSON" | "PORTABLE_TEXT" | "ASSET_MANIFEST" | "REVIEW_SNAPSHOT" | "EVALUATION_SNAPSHOT";
    content: string;
    title: string;
  }
>;

export type ExportPackage = Readonly<
  ManualExportSurfaceBoundary & {
    assetManifest: AssetManifest;
    channel: Channel | null;
    constraintSnapshot: ConstraintSnapshot;
    evaluationSnapshot: EvaluationSnapshot;
    manualArtifacts: ManualExportArtifact[];
    packageKey: string;
    portableBundles: PortableBundle[];
    reviewSnapshot: ReviewSnapshot;
    sourceKey: string;
    sourceType: ExportSourceType;
    subjectKey: string;
    title: string;
  }
>;
