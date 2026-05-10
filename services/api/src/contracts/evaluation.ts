import { z } from "zod";

const evaluationVerdictSchema = z.enum(["PASS", "WARNING", "FAIL"]);
const evaluationGradeSchema = z.enum(["BLOCKED", "WEAK", "VIABLE", "STRONG"]);
const findingSeveritySchema = z.enum(["BLOCKER", "WARNING", "INFO"]);
const evaluationSourceSchema = z.enum([
  "BRAND_RULE",
  "VISUAL_RULE",
  "LANGUAGE_RULE",
  "FORBIDDEN_ENERGY",
  "CHANNEL_RULE",
  "SIGNAL_SCORING_RULE",
  "CONTENT_GRAPH_COMPATIBILITY",
  "REVIEW_GOVERNANCE",
  "MANUAL"
]);

const compatibilityVerdictSchema = z.enum(["ALLOWED", "DISCOURAGED", "FORBIDDEN", "REQUIRED"]);

export const evaluationSubjectResponseSchema = z.object({
  key: z.string(),
  type: z.enum(["GENERATION_BRIEF", "GENERATION_OUTPUT"])
});

export const evaluationFindingResponseSchema = z.object({
  code: z.string(),
  detail: z.string(),
  ruleCode: z.string().nullable(),
  severity: findingSeveritySchema,
  source: evaluationSourceSchema,
  title: z.string()
});

export const resolvedConstraintResponseSchema = z.object({
  active: z.boolean(),
  instruction: z.string(),
  required: z.boolean(),
  ruleCode: z.string().nullable(),
  source: evaluationSourceSchema,
  title: z.string(),
  weight: z.number().int()
});

export const graphCompatibilityCheckResponseSchema = z.object({
  detail: z.string(),
  kind: z.string(),
  reason: z.string().nullable(),
  sourceCode: z.string(),
  targetCode: z.string(),
  verdict: compatibilityVerdictSchema,
  weight: z.number().int()
});

export const signalScoreResponseSchema = z.object({
  axes: z.array(
    z.object({
      axis: z.enum([
        "IDENTITY_PROTECTION",
        "SYMBOLIC_RESTRAINT",
        "INSTITUTIONAL_CONSISTENCY",
        "CULTURAL_CREDIBILITY",
        "PRESSURE_WITHOUT_NOISE",
        "ARCHIVE_COHERENCE",
        "RULE_ADHERENCE",
        "REVIEW_READINESS"
      ]),
      maxScore: z.number().int(),
      score: z.number().int()
    })
  ),
  grade: evaluationGradeSchema,
  max: z.number().int(),
  normalized: z.number().int(),
  total: z.number().int()
});

export const evaluationReportResponseSchema = z.object({
  approvalAuthority: z.literal(false),
  findings: z.array(evaluationFindingResponseSchema),
  graphChecks: z.array(graphCompatibilityCheckResponseSchema),
  reportKey: z.string(),
  resolvedConstraints: z.array(resolvedConstraintResponseSchema),
  reviewRequired: z.literal(true),
  score: signalScoreResponseSchema,
  subject: evaluationSubjectResponseSchema,
  usableWithoutReview: z.literal(false),
  verdict: evaluationVerdictSchema,
  verdictMeaning: z.string()
});

export const resolvedConstraintBundleResponseSchema = z.object({
  approvalAuthority: z.literal(false),
  bundle: z.object({
    code: z.string(),
    description: z.string(),
    name: z.string()
  }),
  findings: z.array(evaluationFindingResponseSchema),
  resolvedConstraints: z.array(resolvedConstraintResponseSchema),
  reviewRequired: z.literal(true),
  usableWithoutReview: z.literal(false)
});

export const evaluationHealthResponseSchema = z.object({
  approvalAuthority: z.literal(false),
  dbMutation: z.literal(false),
  execution: z.literal(false),
  providerIntegration: z.literal(false),
  reviewRequired: z.literal(true),
  status: z.literal("ok"),
  usableWithoutReview: z.literal(false),
  writeRoutes: z.literal(false)
});

export type EvaluationReportResponse = z.infer<typeof evaluationReportResponseSchema>;
