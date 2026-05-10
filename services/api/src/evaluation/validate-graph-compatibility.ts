import type {
  CompatibilityInput,
  EvaluationFinding,
  EvaluationInput,
  GraphCompatibilityCheck
} from "./types.js";

type GraphValidationResult = Readonly<{
  checks: GraphCompatibilityCheck[];
  findings: EvaluationFinding[];
}>;

export function validateGraphCompatibility(input: EvaluationInput): GraphValidationResult {
  const relevantCompatibility = input.compatibility.filter((record) => isRelevant(record, input));
  const checks = relevantCompatibility.map((record) => toCheck(record));
  const findings = relevantCompatibility.flatMap((record) => toFindings(record, input));

  return { checks, findings };
}

function isRelevant(record: CompatibilityInput, input: EvaluationInput): boolean {
  const declaredCampaignWorld = input.declared.campaignWorldCode;
  const declaredAssets = new Set(input.text.detectedAssetCodes);
  const declaredMoods = new Set(input.declared.moodReferenceCodes);
  const releaseCode = input.declared.releaseCode;

  if (record.kind === "CAMPAIGN_WORLD_ASSET") {
    return record.sourceCode === declaredCampaignWorld || declaredAssets.has(record.targetCode);
  }

  if (record.kind === "CAMPAIGN_WORLD_MOOD_REFERENCE") {
    return record.sourceCode === declaredCampaignWorld || declaredMoods.has(record.targetCode);
  }

  if (record.kind === "MUSIC_RELEASE_CAMPAIGN_WORLD") {
    return record.sourceCode === releaseCode || record.targetCode === declaredCampaignWorld;
  }

  if (record.kind === "TRACK_MOOD_REFERENCE") {
    return declaredMoods.has(record.targetCode);
  }

  if (record.kind === "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT") {
    return record.sourceCode === declaredCampaignWorld;
  }

  return false;
}

function toCheck(record: CompatibilityInput): GraphCompatibilityCheck {
  return {
    detail: `${record.kind}: ${record.sourceCode} -> ${record.targetCode} is ${record.verdict}.`,
    kind: record.kind,
    reason: record.reason,
    sourceCode: record.sourceCode,
    targetCode: record.targetCode,
    verdict: record.verdict,
    weight: record.weight
  };
}

function toFindings(record: CompatibilityInput, input: EvaluationInput): EvaluationFinding[] {
  const declaredAssets = new Set(input.text.detectedAssetCodes);
  const declaredMoods = new Set(input.declared.moodReferenceCodes);
  const declaredCampaignWorld = input.declared.campaignWorldCode;

  if (record.kind === "CAMPAIGN_WORLD_ASSET") {
    const assetUsed = declaredAssets.has(record.targetCode);

    if (record.verdict === "REQUIRED" && record.sourceCode === declaredCampaignWorld && !assetUsed) {
      return [
        {
          code: "GRAPH_REQUIRED_ASSET_MISSING",
          detail: `${record.targetCode} is required for ${record.sourceCode}, but it is not present in the evaluated material.`,
          ruleCode: record.targetCode,
          severity: "BLOCKER",
          source: "CONTENT_GRAPH_COMPATIBILITY",
          title: "Required asset missing"
        }
      ];
    }

    if (record.verdict === "FORBIDDEN" && assetUsed) {
      return [
        {
          code: "GRAPH_FORBIDDEN_ASSET_USED",
          detail: `${record.targetCode} is forbidden in ${record.sourceCode}, but it is present in the evaluated material.`,
          ruleCode: record.targetCode,
          severity: "BLOCKER",
          source: "CONTENT_GRAPH_COMPATIBILITY",
          title: "Forbidden asset used"
        }
      ];
    }

    if (record.verdict === "DISCOURAGED" && assetUsed) {
      return [
        {
          code: "GRAPH_DISCOURAGED_ASSET_USED",
          detail: `${record.targetCode} is discouraged in ${record.sourceCode}; keep it secondary and review-bound.`,
          ruleCode: record.targetCode,
          severity: "WARNING",
          source: "CONTENT_GRAPH_COMPATIBILITY",
          title: "Discouraged asset used"
        }
      ];
    }
  }

  if (record.kind === "CAMPAIGN_WORLD_MOOD_REFERENCE") {
    const moodUsed = declaredMoods.has(record.targetCode);

    if (record.verdict === "REQUIRED" && record.sourceCode === declaredCampaignWorld && !moodUsed) {
      return [
        {
          code: "GRAPH_REQUIRED_MOOD_MISSING",
          detail: `${record.targetCode} is required for ${record.sourceCode}, but no matching mood reference is present.`,
          ruleCode: record.targetCode,
          severity: "BLOCKER",
          source: "CONTENT_GRAPH_COMPATIBILITY",
          title: "Required mood reference missing"
        }
      ];
    }
  }

  return [];
}
