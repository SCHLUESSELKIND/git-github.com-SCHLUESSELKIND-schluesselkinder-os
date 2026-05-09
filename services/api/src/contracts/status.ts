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
