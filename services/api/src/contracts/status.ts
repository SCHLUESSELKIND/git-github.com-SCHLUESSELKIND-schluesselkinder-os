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
