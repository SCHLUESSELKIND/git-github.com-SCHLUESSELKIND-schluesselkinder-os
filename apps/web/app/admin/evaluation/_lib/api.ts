export type EvaluationVerdict = "PASS" | "WARNING" | "FAIL";
export type EvaluationGrade = "BLOCKED" | "WEAK" | "VIABLE" | "STRONG";
export type FindingSeverity = "BLOCKER" | "WARNING" | "INFO";

export type EvaluationFinding = Readonly<{
  code: string;
  detail: string;
  ruleCode: string | null;
  severity: FindingSeverity;
  source: string;
  title: string;
}>;

export type ResolvedConstraint = Readonly<{
  active: boolean;
  instruction: string;
  required: boolean;
  ruleCode: string | null;
  source: string;
  title: string;
  weight: number;
}>;

export type GraphCompatibilityCheck = Readonly<{
  detail: string;
  kind: string;
  reason: string | null;
  sourceCode: string;
  targetCode: string;
  verdict: "ALLOWED" | "DISCOURAGED" | "FORBIDDEN" | "REQUIRED";
  weight: number;
}>;

export type EvaluationReport = Readonly<{
  approvalAuthority: false;
  findings: EvaluationFinding[];
  graphChecks: GraphCompatibilityCheck[];
  reportKey: string;
  resolvedConstraints: ResolvedConstraint[];
  reviewRequired: true;
  score: {
    axes: Array<{
      axis: string;
      maxScore: number;
      score: number;
    }>;
    grade: EvaluationGrade;
    max: number;
    normalized: number;
    total: number;
  };
  subject: {
    key: string;
    type: "GENERATION_BRIEF" | "GENERATION_OUTPUT";
  };
  usableWithoutReview: false;
  verdict: EvaluationVerdict;
  verdictMeaning: string;
}>;

export type EvaluationHealth = Readonly<{
  approvalAuthority: false;
  dbMutation: false;
  execution: false;
  providerIntegration: false;
  reviewRequired: true;
  status: "ok";
  usableWithoutReview: false;
  writeRoutes: false;
}>;

export type ConstraintBundleReport = Readonly<{
  approvalAuthority: false;
  bundle: {
    code: string;
    description: string;
    name: string;
  };
  findings: EvaluationFinding[];
  resolvedConstraints: ResolvedConstraint[];
  reviewRequired: true;
  usableWithoutReview: false;
}>;

export type GenerationSummary = Readonly<{
  briefs: Array<{
    briefKey: string;
    id: string;
    reviewItem: {
      reviewKey: string;
      status: string;
    } | null;
    subjectKey: string;
    title: string;
    type: string;
  }>;
  constraintBundles: Array<{
    code: string;
    constraints: ResolvedConstraint[];
    description: string;
    id: string;
    name: string;
  }>;
  outputs: Array<{
    outputKey: string;
    reviewItemId: string;
    reviewItem: {
      reviewKey: string;
      status: string;
    };
    status: string;
    title: string;
  }>;
}>;

export class ConsoleApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConsoleApiError";
  }
}

// Single source of truth lives in `app/admin/_lib/admin-gate.ts`.
export { isInternalConsoleEnabled } from "../../_lib/admin-gate";

export async function fetchEvaluationHealth() {
  return readJson<EvaluationHealth>("/evaluation/health");
}

export async function fetchGenerationSummary() {
  return readJson<GenerationSummary>("/generation");
}

export async function fetchEvaluationOutput(outputKey: string) {
  return readJson<EvaluationReport>(`/evaluation/generation/outputs/${encodeURIComponent(outputKey)}`);
}

export async function fetchEvaluationBrief(briefKey: string) {
  return readJson<EvaluationReport>(`/evaluation/generation/briefs/${encodeURIComponent(briefKey)}`);
}

export async function fetchConstraintBundle(bundleCode: string) {
  return readJson<ConstraintBundleReport>(`/evaluation/rules/constraints/${encodeURIComponent(bundleCode)}`);
}

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ConsoleApiError(`Read failed for ${path}: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:3001").replace(/\/$/, "");
}
