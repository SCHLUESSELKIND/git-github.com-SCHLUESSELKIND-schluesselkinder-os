import { finding, readTextFiles, type GovernanceFinding } from "./boundary-checks.js";

export function auditRouteSurface(root: string): GovernanceFinding[] {
  const routeFiles = readTextFiles(root, ["services/api/src/routes"], [".test.ts"]);
  const findings: GovernanceFinding[] = [];
  const disallowedMethodPattern = /server\.(post|put|patch|delete)\s*\(/g;

  for (const file of routeFiles) {
    const matches = file.text.matchAll(disallowedMethodPattern);

    for (const match of matches) {
      findings.push(
        finding({
          code: "NON_GET_ROUTE",
          detail: `Unexpected ${match[1]?.toUpperCase()} route registration.`,
          filePath: file.path,
          severity: "BLOCKER"
        })
      );
    }
  }

  return findings;
}
