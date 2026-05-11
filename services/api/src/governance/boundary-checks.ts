import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";

export type GovernanceFinding = Readonly<{
  code: string;
  detail: string;
  filePath: string | null;
  severity: "BLOCKER" | "WARNING";
}>;

export type TextFile = Readonly<{
  path: string;
  text: string;
}>;

export function getRepositoryRoot(): string {
  return resolve(process.cwd(), "../..");
}

export function finding(input: GovernanceFinding): GovernanceFinding {
  return input;
}

export function readTextFile(root: string, relativePath: string): TextFile | null {
  const absolutePath = resolve(root, relativePath);

  if (!existsSync(absolutePath)) {
    return null;
  }

  return {
    path: relativePath,
    text: readFileSync(absolutePath, "utf8")
  };
}

export function readTextFiles(root: string, relativeRoots: readonly string[], exclusions: readonly string[] = []): TextFile[] {
  return relativeRoots.flatMap((relativeRoot) => readTextTree(root, relativeRoot, exclusions));
}

export function auditBoundaryLiterals(root: string): GovernanceFinding[] {
  const findings: GovernanceFinding[] = [];

  findings.push(
    ...requireFileLiterals(root, "services/api/src/contracts/evaluation.ts", [
      "approvalAuthority: z.literal(false)",
      "reviewRequired: z.literal(true)",
      "usableWithoutReview: z.literal(false)"
    ])
  );
  findings.push(
    ...requireFileLiterals(root, "services/api/src/contracts/drafts.ts", [
      "approvalAuthority: z.literal(false)",
      "automationAllowed: z.literal(false)",
      "externalDelivery: z.literal(false)",
      "humanCommitRequired: z.literal(true)",
      "publishAuthority: z.literal(false)",
      "reviewRequired: z.literal(true)",
      "manualExportPrepared: z.literal(true)",
      "publishReady: z.literal(false)"
    ])
  );
  findings.push(
    ...requireFileLiterals(root, "services/api/src/contracts/exports.ts", [
      "approvalAuthority: z.literal(false)",
      "automationAllowed: z.literal(false)",
      "distributionAuthority: z.literal(false)",
      "externalDelivery: z.literal(false)",
      "humanCommitRequired: z.literal(true)",
      "manualExportPrepared: z.literal(true)",
      "portableArtifactOnly: z.literal(true)",
      "publishAuthority: z.literal(false)",
      "publishReady: z.literal(false)",
      "reviewRequired: z.literal(true)"
    ])
  );

  return findings;
}

export function formatFindings(findings: readonly GovernanceFinding[]): string {
  return findings
    .map((item) => `${item.code}${item.filePath ? ` ${item.filePath}` : ""}: ${item.detail}`)
    .join("\n");
}

function requireFileLiterals(root: string, relativePath: string, literals: readonly string[]): GovernanceFinding[] {
  const file = readTextFile(root, relativePath);

  if (!file) {
    return [
      finding({
        code: "BOUNDARY_FILE_MISSING",
        detail: "Required boundary contract file is missing.",
        filePath: relativePath,
        severity: "BLOCKER"
      })
    ];
  }

  return literals
    .filter((literal) => !file.text.includes(literal))
    .map((literal) =>
      finding({
        code: "BOUNDARY_LITERAL_MISSING",
        detail: `Missing required literal: ${literal}`,
        filePath: relativePath,
        severity: "BLOCKER"
      })
    );
}

function readTextTree(root: string, relativePath: string, exclusions: readonly string[]): TextFile[] {
  const absolutePath = resolve(root, relativePath);

  if (!existsSync(absolutePath)) {
    return [];
  }

  const stat = statSync(absolutePath);

  if (stat.isFile()) {
    if (!absolutePath.endsWith(".ts") && !absolutePath.endsWith(".tsx") && !absolutePath.endsWith(".json")) {
      return [];
    }

    if (exclusions.some((exclusion) => relativePath.endsWith(exclusion) || relativePath.includes(exclusion))) {
      return [];
    }

    return [
      {
        path: relativePath,
        text: readFileSync(absolutePath, "utf8")
      }
    ];
  }

  return readdirSync(absolutePath).flatMap((entry) => {
    if (entry === "node_modules" || entry === ".next" || entry === "dist") {
      return [];
    }

    return readTextTree(root, `${relativePath}/${entry}`, exclusions);
  });
}
