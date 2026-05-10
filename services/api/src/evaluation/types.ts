export type EvaluationVerdict = "PASS" | "WARNING" | "FAIL";

export type EvaluationGrade = "BLOCKED" | "WEAK" | "VIABLE" | "STRONG";

export type EvaluationFindingSeverity = "BLOCKER" | "WARNING" | "INFO";

export type EvaluationAxis =
  | "IDENTITY_PROTECTION"
  | "SYMBOLIC_RESTRAINT"
  | "INSTITUTIONAL_CONSISTENCY"
  | "CULTURAL_CREDIBILITY"
  | "PRESSURE_WITHOUT_NOISE"
  | "ARCHIVE_COHERENCE"
  | "RULE_ADHERENCE"
  | "REVIEW_READINESS";

export type EvaluationSource =
  | "BRAND_RULE"
  | "VISUAL_RULE"
  | "LANGUAGE_RULE"
  | "FORBIDDEN_ENERGY"
  | "CHANNEL_RULE"
  | "SIGNAL_SCORING_RULE"
  | "CONTENT_GRAPH_COMPATIBILITY"
  | "REVIEW_GOVERNANCE"
  | "MANUAL";

export type CompatibilityVerdict = "ALLOWED" | "DISCOURAGED" | "FORBIDDEN" | "REQUIRED";

export type RuleSeverity = "REQUIRED" | "WARNING" | "DISCOURAGED";

export type EvaluationSubject = Readonly<{
  key: string;
  type: "GENERATION_BRIEF" | "GENERATION_OUTPUT";
}>;

export type EvaluationFinding = Readonly<{
  code: string;
  detail: string;
  ruleCode: string | null;
  severity: EvaluationFindingSeverity;
  source: EvaluationSource;
  title: string;
}>;

export type ResolvedConstraint = Readonly<{
  active: boolean;
  instruction: string;
  required: boolean;
  ruleCode: string | null;
  source: EvaluationSource;
  title: string;
  weight: number;
}>;

export type ConstraintBundleInput = Readonly<{
  code: string;
  constraints: ResolvedConstraint[];
  description: string;
  name: string;
}>;

export type RuleInput = Readonly<{
  code: string;
  severity?: RuleSeverity;
  text: string;
  title: string;
  weight: number;
}>;

export type ForbiddenEnergyInput = Readonly<{
  code: string;
  label: string;
  reason: string;
  severity: RuleSeverity;
  weight: number;
}>;

export type ScoringRuleInput = Readonly<{
  code: string;
  description: string;
  maxScore: number;
  title: string;
  weight: number;
}>;

export type CompatibilityInput = Readonly<{
  kind: string;
  reason: string | null;
  sourceCode: string;
  sourceLabel: string;
  targetCode: string;
  targetLabel: string;
  verdict: CompatibilityVerdict;
  weight: number;
}>;

export type GraphCompatibilityCheck = Readonly<{
  detail: string;
  kind: string;
  reason: string | null;
  sourceCode: string;
  targetCode: string;
  verdict: CompatibilityVerdict;
  weight: number;
}>;

export type EvaluationAxisScore = Readonly<{
  axis: EvaluationAxis;
  maxScore: number;
  score: number;
}>;

export type SignalScore = Readonly<{
  axes: EvaluationAxisScore[];
  grade: EvaluationGrade;
  max: number;
  normalized: number;
  total: number;
}>;

export type EvaluationTextInput = Readonly<{
  body: string[];
  detectedAssetCodes: string[];
}>;

export type EvaluationInput = Readonly<{
  channel: string | null;
  compatibility: CompatibilityInput[];
  constraintBundle: ConstraintBundleInput | null;
  forbiddenEnergy: ForbiddenEnergyInput[];
  rules: RuleInput[];
  reviewBinding: {
    id: string;
    reviewKey: string;
    status: string;
  } | null;
  scoringRules: ScoringRuleInput[];
  subject: EvaluationSubject;
  text: EvaluationTextInput;
  declared: {
    campaignWorldCode: string | null;
    moodReferenceCodes: string[];
    releaseCode: string | null;
  };
}>;

export type EvaluationReport = Readonly<{
  approvalAuthority: false;
  findings: EvaluationFinding[];
  graphChecks: GraphCompatibilityCheck[];
  reportKey: string;
  resolvedConstraints: ResolvedConstraint[];
  reviewRequired: true;
  score: SignalScore;
  subject: EvaluationSubject;
  usableWithoutReview: false;
  verdict: EvaluationVerdict;
  verdictMeaning: string;
}>;
