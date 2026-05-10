import { z } from "zod";

export const artistStatusSchema = z.enum(["ACTIVE", "ARCHIVED", "HIDDEN"]);

export const releaseStatusSchema = z.enum([
  "SIGNAL_PENDING",
  "ACTIVE",
  "CLOSED",
  "ARCHIVED",
  "HIDDEN"
]);

export const fragmentTypeSchema = z.enum([
  "HERO",
  "MANIFEST",
  "METADATA",
  "ARTIST",
  "MUSIC",
  "OBJECT",
  "SOCIAL"
]);

export const ruleSeveritySchema = z.enum(["REQUIRED", "WARNING", "DISCOURAGED"]);

export const ruleCategorySchema = z.enum([
  "CORE",
  "VISUAL",
  "LANGUAGE",
  "CHANNEL",
  "VOICE",
  "AUDIENCE",
  "SCORING"
]);

export const channelSchema = z.enum([
  "WEBSITE",
  "TIKTOK",
  "INSTAGRAM",
  "SOUNDCLOUD",
  "SPOTIFY"
]);

export const assetTypeSchema = z.enum([
  "IMAGE",
  "VIDEO",
  "AUDIO",
  "SYMBOL",
  "TEXT",
  "OBJECT",
  "MOTION"
]);

export const assetSourceTypeSchema = z.enum([
  "LOCAL_REFERENCE",
  "EXTERNAL_REFERENCE",
  "SYMBOLIC_REFERENCE"
]);

export const compatibilityVerdictSchema = z.enum([
  "ALLOWED",
  "DISCOURAGED",
  "FORBIDDEN",
  "REQUIRED"
]);

export const fragmentPlacementSchema = z.enum([
  "HERO",
  "CAPTION",
  "METADATA",
  "RELEASE_NOTE",
  "CHANNEL_COPY",
  "OBJECT_ARCHIVE"
]);

export const reviewStageSchema = z.enum([
  "MOODBOARD_REVIEW",
  "CONTENT_REVIEW",
  "SCHEDULE_REVIEW"
]);

export const reviewStatusSchema = z.enum([
  "PENDING",
  "APPROVED",
  "REJECTED",
  "NEEDS_REVISION",
  "ARCHIVED"
]);

export const decisionTypeSchema = z.enum([
  "APPROVE",
  "REJECT",
  "REQUEST_REVISION",
  "ARCHIVE"
]);

export const reviewSubjectTypeSchema = z.enum([
  "MUSIC_RELEASE",
  "TRACK",
  "CAMPAIGN_WORLD",
  "ASSET",
  "RELEASE_FRAGMENT",
  "CHANNEL_FRAGMENT",
  "FUTURE_MOODBOARD",
  "FUTURE_CONTENT_ASSET",
  "FUTURE_SCHEDULE_PLAN",
  "FUTURE_CAMPAIGN"
]);

export const ruleViolationSourceSchema = z.enum([
  "BRAND_RULE",
  "VISUAL_RULE",
  "LANGUAGE_RULE",
  "FORBIDDEN_ENERGY",
  "CHANNEL_RULE",
  "SIGNAL_SCORING_RULE",
  "CONTENT_GRAPH_COMPATIBILITY",
  "MANUAL"
]);

export const generationBriefTypeSchema = z.enum([
  "MOODBOARD",
  "CONTENT",
  "CHANNEL_COPY",
  "SCHEDULE_PLAN"
]);

export const generationRequestStatusSchema = z.enum([
  "DRAFT",
  "READY_FOR_REVIEW",
  "REJECTED",
  "REVIEW_ACCEPTED",
  "ARCHIVED"
]);

export const generationOutputStatusSchema = z.enum([
  "GENERATED_PLACEHOLDER",
  "REVIEW_REQUIRED",
  "REVIEW_REJECTED",
  "REVIEW_ARCHIVED"
]);

export const promptSectionTypeSchema = z.enum([
  "CONTEXT",
  "BRAND_CONSTRAINTS",
  "CONTENT_GRAPH",
  "CHANNEL_RULES",
  "FORBIDDEN_ENERGY",
  "OUTPUT_FORMAT",
  "REVIEW_REQUIREMENTS"
]);

export const constraintSourceSchema = z.enum([
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

export const evaluationVerdictSchema = z.enum([
  "PASS",
  "WARNING",
  "FAIL"
]);
