import { auditAuthorityLeaks } from "./authority-leak-audit.js";
import { auditBoundaryLiterals, type GovernanceFinding } from "./boundary-checks.js";
import { auditDependencies } from "./dependency-audit.js";
import { auditRouteSurface } from "./route-surface-audit.js";

export type CapabilityDiff = Readonly<{
  findings: GovernanceFinding[];
  current: {
    apiMutations: false;
    backgroundExecution: false;
    externalDelivery: false;
    providerIntegrations: false;
    schemaExpansion: false;
  };
  escalationRequiredBefore: readonly string[];
}>;

export function buildCapabilityDiff(root: string): CapabilityDiff {
  return {
    current: {
      apiMutations: false,
      backgroundExecution: false,
      externalDelivery: false,
      providerIntegrations: false,
      schemaExpansion: false
    },
    escalationRequiredBefore: [
      "write routes",
      "provider adapters",
      "background execution",
      "external delivery",
      "authority persistence",
      "auth workflows",
      "storage or file transfer"
    ],
    findings: [
      ...auditRouteSurface(root),
      ...auditDependencies(root),
      ...auditAuthorityLeaks(root),
      ...auditBoundaryLiterals(root)
    ]
  };
}
