import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { finding, type GovernanceFinding } from "./boundary-checks.js";
import { providerDependencyTerms, storageDependencyTerms, workerDependencyTerms } from "./forbidden-terminology.js";

const packageFiles = [
  "package.json",
  "apps/web/package.json",
  "services/api/package.json",
  "packages/db/package.json",
  "packages/brand/package.json",
  "packages/ui/package.json"
] as const;

export function auditDependencies(root: string): GovernanceFinding[] {
  const findings: GovernanceFinding[] = [];

  for (const packageFile of packageFiles) {
    const absolutePath = resolve(root, packageFile);

    if (!existsSync(absolutePath)) {
      continue;
    }

    const manifest = JSON.parse(readFileSync(absolutePath, "utf8")) as {
      dependencies?: Record<string, string>;
      devDependencies?: Record<string, string>;
      optionalDependencies?: Record<string, string>;
    };
    const dependencyNames = [
      ...Object.keys(manifest.dependencies ?? {}),
      ...Object.keys(manifest.devDependencies ?? {}),
      ...Object.keys(manifest.optionalDependencies ?? {})
    ];

    for (const dependencyName of dependencyNames) {
      const normalized = dependencyName.toLowerCase();
      const category = classifyDependency(normalized);

      if (!category) {
        continue;
      }

      findings.push(
        finding({
          code: "DISALLOWED_DEPENDENCY",
          detail: `${dependencyName} adds ${category} capability and requires governance escalation first.`,
          filePath: packageFile,
          severity: "BLOCKER"
        })
      );
    }
  }

  return findings;
}

function classifyDependency(dependencyName: string): string | null {
  if (providerDependencyTerms.some((term) => dependencyName.includes(term))) {
    return "provider or platform integration";
  }

  if (workerDependencyTerms.some((term) => dependencyName === term || dependencyName.includes(term))) {
    return "background execution";
  }

  if (storageDependencyTerms.some((term) => dependencyName.includes(term))) {
    return "storage or transfer";
  }

  return null;
}
