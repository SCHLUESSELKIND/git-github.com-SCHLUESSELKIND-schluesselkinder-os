import { finding, readTextFiles, type GovernanceFinding } from "./boundary-checks.js";
import {
  allowedNegativeControls,
  frozenRuntimeTerms,
  hiddenDeliveryFieldTerms,
  protectedRuntimeExclusions,
  protectedRuntimeRoots
} from "./forbidden-terminology.js";

const positiveAuthorityPatterns = [
  "approvalAuthority: true",
  "publishAuthority: true",
  "automationAllowed: true",
  "externalDelivery: true",
  "distributionAuthority: true",
  "publishReady: true",
  "reviewRequired: false",
  "humanCommitRequired: false",
  "manualExportPrepared: false",
  "portableArtifactOnly: false",
  "usableWithoutReview: true",
  "passImpliesApproval: true",
  "snapshotImpliesApproval: true",
  "snapshotImpliesTruth: true"
] as const;

const semanticLeakPatterns = [
  /PASS.{0,40}(means|equals|grants|creates).{0,20}approval/i,
  /score.{0,40}truth/i,
  /score.{0,40}authority/i,
  /export.{0,40}external action/i,
  /package.{0,40}permission/i
] as const;

export function auditAuthorityLeaks(root: string): GovernanceFinding[] {
  const files = readTextFiles(root, protectedRuntimeRoots, protectedRuntimeExclusions);
  const findings: GovernanceFinding[] = [];

  for (const file of files) {
    findings.push(...auditPositiveAuthority(file.path, file.text));
    findings.push(...auditHiddenDeliveryFields(file.path, file.text));
    findings.push(...auditRuntimeTerminology(file.path, file.text));
    findings.push(...auditSemanticLeaks(file.path, file.text));
  }

  return findings;
}

function auditPositiveAuthority(filePath: string, text: string): GovernanceFinding[] {
  return positiveAuthorityPatterns
    .filter((pattern) => text.includes(pattern))
    .map((pattern) =>
      finding({
        code: "AUTHORITY_FLAG_LEAK",
        detail: `Positive authority literal is not allowed: ${pattern}`,
        filePath,
        severity: "BLOCKER"
      })
    );
}

function auditHiddenDeliveryFields(filePath: string, text: string): GovernanceFinding[] {
  return hiddenDeliveryFieldTerms
    .filter((term) => text.includes(term))
    .map((term) =>
      finding({
        code: "HIDDEN_DELIVERY_FIELD",
        detail: `Hidden delivery or storage field is not allowed: ${term}`,
        filePath,
        severity: "BLOCKER"
      })
    );
}

function auditRuntimeTerminology(filePath: string, text: string): GovernanceFinding[] {
  const normalizedText = removeAllowedNegativeControls(text).toLowerCase();

  return frozenRuntimeTerms
    .filter((term) => normalizedText.includes(term.toLowerCase()))
    .map((term) =>
      finding({
        code: "FROZEN_TERMINOLOGY_RUNTIME_LEAK",
        detail: `Frozen operational term is not allowed in runtime surface: ${term}`,
        filePath,
        severity: "BLOCKER"
      })
    );
}

function auditSemanticLeaks(filePath: string, text: string): GovernanceFinding[] {
  return semanticLeakPatterns
    .filter((pattern) => pattern.test(text))
    .map((pattern) =>
      finding({
        code: "AUTHORITY_SEMANTIC_LEAK",
        detail: `Potential authority semantic leak matched: ${pattern.source}`,
        filePath,
        severity: "BLOCKER"
      })
    );
}

function removeAllowedNegativeControls(text: string): string {
  return allowedNegativeControls.reduce((current, literal) => current.split(literal).join(""), text);
}
