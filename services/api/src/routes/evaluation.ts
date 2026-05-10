import type { FastifyInstance } from "fastify";
import {
  evaluationHealthResponseSchema,
  evaluationReportResponseSchema,
  resolvedConstraintBundleResponseSchema
} from "../contracts/evaluation.js";
import { createEvaluationTextInput, evaluateGenerationBrief, evaluateGenerationOutput } from "../evaluation/evaluate-generation-output.js";
import { resolveConstraints } from "../evaluation/resolve-constraints.js";
import type {
  CompatibilityInput,
  ConstraintBundleInput,
  EvaluationInput,
  ForbiddenEnergyInput,
  RuleInput,
  ScoringRuleInput
} from "../evaluation/types.js";
import type {
  ApiRepositories,
  CompatibilityRecord,
  ConstraintBundleRecord,
  GenerationBriefRecord,
  GenerationOutputRecord
} from "../repositories.js";

export async function registerEvaluationRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/evaluation/health", async () =>
    evaluationHealthResponseSchema.parse({
      approvalAuthority: false,
      dbMutation: false,
      execution: false,
      providerIntegration: false,
      reviewRequired: true,
      status: "ok",
      usableWithoutReview: false,
      writeRoutes: false
    })
  );

  server.get("/evaluation/rules/constraints/:bundleCode", async (request, reply) => {
    const { bundleCode } = request.params as { bundleCode: string };
    const context = await loadEvaluationContext(repositories);
    const bundle = context.bundles.find((candidate) => candidate.code === bundleCode);

    if (!bundle) {
      return reply.code(404).send({ error: "constraint_bundle_not_found" });
    }

    const resolved = resolveConstraints({
      bundle: mapConstraintBundle(bundle),
      rules: context.rules,
      scoringRules: context.scoringRules
    });

    return resolvedConstraintBundleResponseSchema.parse({
      approvalAuthority: false,
      bundle: {
        code: bundle.code,
        description: bundle.description,
        name: bundle.name
      },
      findings: resolved.findings,
      resolvedConstraints: resolved.constraints,
      reviewRequired: true,
      usableWithoutReview: false
    });
  });

  server.get("/evaluation/generation/briefs/:briefKey", async (request, reply) => {
    const { briefKey } = request.params as { briefKey: string };
    const brief = await repositories.generation.findBriefByKey(briefKey);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const context = await loadEvaluationContext(repositories);
    const report = evaluateGenerationBrief(buildBriefEvaluationInput(brief, context));

    return evaluationReportResponseSchema.parse(report);
  });

  server.get("/evaluation/generation/outputs/:outputKey", async (request, reply) => {
    const { outputKey } = request.params as { outputKey: string };
    const output = await repositories.generation.findOutputByKey(outputKey);

    if (!output) {
      return reply.code(404).send({ error: "generation_output_not_found" });
    }

    const requests = await repositories.generation.listRequests();
    const requestRecord = requests.find((candidate) => candidate.id === output.requestId);
    const briefKey = requestRecord?.brief.briefKey;

    if (!briefKey) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const brief = await repositories.generation.findBriefByKey(briefKey);

    if (!brief) {
      return reply.code(404).send({ error: "generation_brief_not_found" });
    }

    const context = await loadEvaluationContext(repositories);
    const report = evaluateGenerationOutput(buildOutputEvaluationInput(output, brief, context));

    return evaluationReportResponseSchema.parse(report);
  });
}

type EvaluationContext = Readonly<{
  bundles: ConstraintBundleRecord[];
  compatibility: CompatibilityInput[];
  forbiddenEnergy: ForbiddenEnergyInput[];
  moodReferenceCodes: string[];
  rules: RuleInput[];
  scoringRules: ScoringRuleInput[];
}>;

async function loadEvaluationContext(repositories: ApiRepositories): Promise<EvaluationContext> {
  const [
    brandRules,
    visualRules,
    languageRules,
    channelRules,
    forbiddenEnergy,
    scoringRules,
    compatibility,
    bundles,
    moodReferences
  ] = await Promise.all([
    repositories.brandIntelligence.listBrandRules(),
    repositories.brandIntelligence.listVisualRules(),
    repositories.brandIntelligence.listLanguageRules(),
    repositories.brandIntelligence.listChannelRules(),
    repositories.brandIntelligence.listForbiddenEnergy(),
    repositories.brandIntelligence.listScoringRules(),
    repositories.contentGraph.listCompatibility(),
    repositories.generation.listConstraintBundles(),
    repositories.contentGraph.listMoodReferences()
  ]);

  return {
    bundles,
    compatibility: compatibility.map(mapCompatibility),
    forbiddenEnergy: forbiddenEnergy.map((energy) => ({
      code: energy.code,
      label: energy.label,
      reason: energy.reason,
      severity: energy.severity,
      weight: energy.weight
    })),
    moodReferenceCodes: moodReferences.map((mood) => mood.code),
    rules: [
      {
        code: "REVIEW_BINDING_REQUIRED",
        severity: "REQUIRED",
        text: "Every evaluated generation output must remain bound to a ReviewItem and must not imply approval authority.",
        title: "Review binding required",
        weight: 100
      },
      ...brandRules.map((rule) => ({
        code: rule.code,
        severity: rule.severity,
        text: rule.statement,
        title: rule.title,
        weight: rule.weight
      })),
      ...visualRules.map((rule) => ({
        code: rule.code,
        severity: rule.severity,
        text: rule.rule,
        title: rule.title,
        weight: rule.weight
      })),
      ...languageRules.map((rule) => ({
        code: rule.code,
        severity: rule.severity,
        text: rule.rule,
        title: rule.title,
        weight: rule.weight
      })),
      ...channelRules.map((rule) => ({
        code: rule.code,
        severity: rule.severity,
        text: rule.rule,
        title: rule.title,
        weight: rule.weight
      })),
      ...forbiddenEnergy.map((energy) => ({
        code: energy.code,
        severity: energy.severity,
        text: energy.reason,
        title: energy.label,
        weight: energy.weight
      }))
    ],
    scoringRules: scoringRules.map((rule) => ({
      code: rule.code,
      description: rule.description,
      maxScore: rule.maxScore,
      title: rule.title,
      weight: rule.weight
    }))
  };
}

function buildBriefEvaluationInput(brief: GenerationBriefRecord, context: EvaluationContext): EvaluationInput {
  const body = [
    brief.title,
    brief.objective,
    brief.subjectKey,
    brief.campaignWorld?.code ?? "",
    brief.channelCompositionProfile?.code ?? "",
    ...brief.promptSections.map((section) => `${section.title}: ${section.body}`)
  ];
  const text = createEvaluationTextInput(body);

  return {
    channel: brief.channel,
    compatibility: context.compatibility,
    constraintBundle: findBundle(brief, context),
    declared: {
      campaignWorldCode: brief.campaignWorld?.code ?? null,
      moodReferenceCodes: detectMoodReferences(body, context.moodReferenceCodes),
      releaseCode: brief.musicRelease?.releaseCode ?? null
    },
    forbiddenEnergy: context.forbiddenEnergy,
    reviewBinding: brief.reviewItem
      ? {
          id: brief.reviewItem.id,
          reviewKey: brief.reviewItem.reviewKey,
          status: brief.reviewItem.status
        }
      : null,
    rules: context.rules,
    scoringRules: context.scoringRules,
    subject: {
      key: brief.briefKey,
      type: "GENERATION_BRIEF"
    },
    text
  };
}

function buildOutputEvaluationInput(
  output: GenerationOutputRecord,
  brief: GenerationBriefRecord,
  context: EvaluationContext
): EvaluationInput {
  const body = [
    output.title,
    output.placeholder,
    output.status,
    brief.title,
    brief.objective,
    brief.subjectKey,
    brief.campaignWorld?.code ?? "",
    brief.channelCompositionProfile?.code ?? "",
    ...brief.promptSections.map((section) => `${section.title}: ${section.body}`),
    ...output.evaluations.map((evaluation) => `${evaluation.title}: ${evaluation.detail}`)
  ];
  const text = createEvaluationTextInput(body);

  return {
    channel: brief.channel,
    compatibility: context.compatibility,
    constraintBundle: findBundle(brief, context),
    declared: {
      campaignWorldCode: brief.campaignWorld?.code ?? null,
      moodReferenceCodes: detectMoodReferences(body, context.moodReferenceCodes),
      releaseCode: brief.musicRelease?.releaseCode ?? null
    },
    forbiddenEnergy: context.forbiddenEnergy,
    reviewBinding: {
      id: output.reviewItem.id,
      reviewKey: output.reviewItem.reviewKey,
      status: output.reviewItem.status
    },
    rules: context.rules,
    scoringRules: context.scoringRules,
    subject: {
      key: output.outputKey,
      type: "GENERATION_OUTPUT"
    },
    text
  };
}

function findBundle(brief: GenerationBriefRecord, context: EvaluationContext): ConstraintBundleInput | null {
  const bundle = context.bundles.find((candidate) => candidate.id === brief.constraintBundle.id);
  return bundle ? mapConstraintBundle(bundle) : null;
}

function mapConstraintBundle(bundle: ConstraintBundleRecord): ConstraintBundleInput {
  return {
    code: bundle.code,
    constraints: bundle.constraints.map((constraint) => ({
      active: constraint.active,
      instruction: constraint.instruction,
      required: constraint.required,
      ruleCode: constraint.ruleCode,
      source: constraint.source,
      title: constraint.title,
      weight: constraint.weight
    })),
    description: bundle.description,
    name: bundle.name
  };
}

function mapCompatibility(record: CompatibilityRecord): CompatibilityInput {
  if (record.kind === "ARTIST_CAMPAIGN_WORLD") {
    return {
      kind: record.kind,
      reason: record.record.reason,
      sourceCode: record.record.artist.slug,
      sourceLabel: record.record.artist.name,
      targetCode: record.record.campaignWorld.code,
      targetLabel: record.record.campaignWorld.name,
      verdict: record.record.verdict,
      weight: record.record.weight
    };
  }

  if (record.kind === "MUSIC_RELEASE_CAMPAIGN_WORLD") {
    return {
      kind: record.kind,
      reason: record.record.reason,
      sourceCode: record.record.musicRelease.releaseCode,
      sourceLabel: record.record.musicRelease.title,
      targetCode: record.record.campaignWorld.code,
      targetLabel: record.record.campaignWorld.name,
      verdict: record.record.verdict,
      weight: record.record.weight
    };
  }

  if (record.kind === "TRACK_MOOD_REFERENCE") {
    return {
      kind: record.kind,
      reason: record.record.reason,
      sourceCode: record.record.track.title,
      sourceLabel: record.record.track.title,
      targetCode: record.record.moodReference.code,
      targetLabel: record.record.moodReference.name,
      verdict: record.record.verdict,
      weight: record.record.weight
    };
  }

  if (record.kind === "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT") {
    return {
      kind: record.kind,
      reason: record.record.reason,
      sourceCode: record.record.campaignWorld.code,
      sourceLabel: record.record.campaignWorld.name,
      targetCode: record.record.visualEnvironment.code,
      targetLabel: record.record.visualEnvironment.name,
      verdict: record.record.verdict,
      weight: record.record.weight
    };
  }

  if (record.kind === "CAMPAIGN_WORLD_MOOD_REFERENCE") {
    return {
      kind: record.kind,
      reason: record.record.reason,
      sourceCode: record.record.campaignWorld.code,
      sourceLabel: record.record.campaignWorld.name,
      targetCode: record.record.moodReference.code,
      targetLabel: record.record.moodReference.name,
      verdict: record.record.verdict,
      weight: record.record.weight
    };
  }

  return {
    kind: record.kind,
    reason: record.record.reason,
    sourceCode: record.record.campaignWorld.code,
    sourceLabel: record.record.campaignWorld.name,
    targetCode: record.record.asset.code,
    targetLabel: record.record.asset.title,
    verdict: record.record.verdict,
    weight: record.record.weight
  };
}

function detectMoodReferences(body: string[], moodReferenceCodes: string[]): string[] {
  const normalized = body.join(" ").toLowerCase();

  return moodReferenceCodes.filter((code) => normalized.includes(code.toLowerCase()));
}
