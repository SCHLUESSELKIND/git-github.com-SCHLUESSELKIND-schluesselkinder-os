export { prisma } from "./client.js";
export {
  ArtistStatus,
  Channel,
  FragmentType,
  Prisma,
  PrismaClient,
  ReleaseStatus,
  RuleCategory,
  RuleSeverity
} from "@prisma/client";
export type {
  Artist,
  AudiencePersona,
  BrandRule,
  ChannelRule,
  ForbiddenEnergy,
  Fragment,
  LanguageRule,
  MusicRelease,
  ObjectRelease,
  SignalScoringRule,
  Track,
  VisualRule,
  VoiceProfile
} from "@prisma/client";

export const dbReadiness = {
  migrationsEnabled: true,
  prismaSchema: "packages/db/prisma/schema.prisma"
} as const;
