import type { FastifyInstance } from "fastify";
import {
  audiencePersonaListResponseSchema,
  brandIntelligenceResponseSchema,
  brandRuleListResponseSchema,
  channelRuleListResponseSchema,
  forbiddenEnergyListResponseSchema,
  languageRuleListResponseSchema,
  signalScoringRuleListResponseSchema,
  visualRuleListResponseSchema,
  voiceProfileListResponseSchema
} from "../contracts/brand-intelligence.js";
import type { ApiRepositories } from "../repositories.js";
import {
  mapAudiencePersona,
  mapBrandRule,
  mapChannelRule,
  mapForbiddenEnergy,
  mapLanguageRule,
  mapSignalScoringRule,
  mapVisualRule,
  mapVoiceProfile
} from "./mappers.js";

export async function registerBrandIntelligenceRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/brand-intelligence", async () => {
    const [
      audiencePersonas,
      brandRules,
      channelRules,
      forbiddenEnergy,
      languageRules,
      scoringRules,
      visualRules,
      voiceProfiles
    ] = await Promise.all([
      repositories.brandIntelligence.listAudiencePersonas(),
      repositories.brandIntelligence.listBrandRules(),
      repositories.brandIntelligence.listChannelRules(),
      repositories.brandIntelligence.listForbiddenEnergy(),
      repositories.brandIntelligence.listLanguageRules(),
      repositories.brandIntelligence.listScoringRules(),
      repositories.brandIntelligence.listVisualRules(),
      repositories.brandIntelligence.listVoiceProfiles()
    ]);

    return brandIntelligenceResponseSchema.parse({
      audiencePersonas: audiencePersonas.map(mapAudiencePersona),
      brandRules: brandRules.map(mapBrandRule),
      channelRules: channelRules.map(mapChannelRule),
      forbiddenEnergy: forbiddenEnergy.map(mapForbiddenEnergy),
      languageRules: languageRules.map(mapLanguageRule),
      scoringRules: scoringRules.map(mapSignalScoringRule),
      visualRules: visualRules.map(mapVisualRule),
      voiceProfiles: voiceProfiles.map(mapVoiceProfile)
    });
  });

  server.get("/brand-intelligence/rules", async () =>
    brandRuleListResponseSchema.parse((await repositories.brandIntelligence.listBrandRules()).map(mapBrandRule))
  );

  server.get("/brand-intelligence/visual-rules", async () =>
    visualRuleListResponseSchema.parse((await repositories.brandIntelligence.listVisualRules()).map(mapVisualRule))
  );

  server.get("/brand-intelligence/language-rules", async () =>
    languageRuleListResponseSchema.parse((await repositories.brandIntelligence.listLanguageRules()).map(mapLanguageRule))
  );

  server.get("/brand-intelligence/forbidden-energy", async () =>
    forbiddenEnergyListResponseSchema.parse(
      (await repositories.brandIntelligence.listForbiddenEnergy()).map(mapForbiddenEnergy)
    )
  );

  server.get("/brand-intelligence/audience-personas", async () =>
    audiencePersonaListResponseSchema.parse(
      (await repositories.brandIntelligence.listAudiencePersonas()).map(mapAudiencePersona)
    )
  );

  server.get("/brand-intelligence/voice-profiles", async () =>
    voiceProfileListResponseSchema.parse((await repositories.brandIntelligence.listVoiceProfiles()).map(mapVoiceProfile))
  );

  server.get("/brand-intelligence/channel-rules", async () =>
    channelRuleListResponseSchema.parse((await repositories.brandIntelligence.listChannelRules()).map(mapChannelRule))
  );

  server.get("/brand-intelligence/scoring-rules", async () =>
    signalScoringRuleListResponseSchema.parse(
      (await repositories.brandIntelligence.listScoringRules()).map(mapSignalScoringRule)
    )
  );
}
