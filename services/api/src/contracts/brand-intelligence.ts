import { z } from "zod";
import {
  channelSchema,
  ruleCategorySchema,
  ruleSeveritySchema
} from "./status.js";

export const brandRuleResponseSchema = z.object({
  active: z.boolean(),
  category: ruleCategorySchema,
  code: z.string(),
  createdAt: z.string(),
  id: z.string(),
  severity: ruleSeveritySchema,
  statement: z.string(),
  title: z.string(),
  weight: z.number().int()
});

export const visualRuleResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  id: z.string(),
  rule: z.string(),
  severity: ruleSeveritySchema,
  title: z.string(),
  weight: z.number().int()
});

export const languageRuleResponseSchema = visualRuleResponseSchema;

export const forbiddenEnergyResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  id: z.string(),
  label: z.string(),
  reason: z.string(),
  severity: ruleSeveritySchema,
  weight: z.number().int()
});

export const audiencePersonaResponseSchema = z.object({
  active: z.boolean(),
  aestheticAttraction: z.string(),
  behavioralPattern: z.string(),
  code: z.string(),
  createdAt: z.string(),
  emotionalState: z.string(),
  id: z.string(),
  name: z.string(),
  rejectionPattern: z.string(),
  resonanceReason: z.string()
});

export const voiceProfileResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  description: z.string(),
  id: z.string(),
  name: z.string()
});

export const channelRuleResponseSchema = z.object({
  active: z.boolean(),
  channel: channelSchema,
  code: z.string(),
  createdAt: z.string(),
  id: z.string(),
  rule: z.string(),
  severity: ruleSeveritySchema,
  title: z.string(),
  weight: z.number().int()
});

export const signalScoringRuleResponseSchema = z.object({
  active: z.boolean(),
  code: z.string(),
  createdAt: z.string(),
  description: z.string(),
  id: z.string(),
  maxScore: z.number().int(),
  title: z.string(),
  weight: z.number().int()
});

export const brandIntelligenceResponseSchema = z.object({
  audiencePersonas: z.array(audiencePersonaResponseSchema),
  brandRules: z.array(brandRuleResponseSchema),
  channelRules: z.array(channelRuleResponseSchema),
  forbiddenEnergy: z.array(forbiddenEnergyResponseSchema),
  languageRules: z.array(languageRuleResponseSchema),
  scoringRules: z.array(signalScoringRuleResponseSchema),
  visualRules: z.array(visualRuleResponseSchema),
  voiceProfiles: z.array(voiceProfileResponseSchema)
});

export const brandRuleListResponseSchema = z.array(brandRuleResponseSchema);
export const visualRuleListResponseSchema = z.array(visualRuleResponseSchema);
export const languageRuleListResponseSchema = z.array(languageRuleResponseSchema);
export const forbiddenEnergyListResponseSchema = z.array(forbiddenEnergyResponseSchema);
export const audiencePersonaListResponseSchema = z.array(audiencePersonaResponseSchema);
export const voiceProfileListResponseSchema = z.array(voiceProfileResponseSchema);
export const channelRuleListResponseSchema = z.array(channelRuleResponseSchema);
export const signalScoringRuleListResponseSchema = z.array(signalScoringRuleResponseSchema);

export type BrandIntelligenceResponse = z.infer<typeof brandIntelligenceResponseSchema>;
