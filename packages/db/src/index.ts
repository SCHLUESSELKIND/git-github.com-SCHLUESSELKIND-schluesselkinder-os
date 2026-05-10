export { prisma } from "./client.js";
export {
  AssetSourceType,
  AssetType,
  ArtistStatus,
  Channel,
  CompatibilityVerdict,
  DecisionType,
  FragmentPlacement,
  FragmentType,
  Prisma,
  PrismaClient,
  ReleaseStatus,
  ReviewStage,
  ReviewStatus,
  ReviewSubjectType,
  RuleCategory,
  RuleViolationSource,
  RuleSeverity
} from "@prisma/client";
export type {
  ApprovalComment,
  ApprovalDecision,
  Asset,
  AssetTag,
  AssetTagAssignment,
  Artist,
  ArtistCampaignWorld,
  AudiencePersona,
  BrandRule,
  CampaignWorld,
  CampaignWorldAsset,
  CampaignWorldMoodReference,
  CampaignWorldVisualEnvironment,
  ChannelFragment,
  ChannelRule,
  ForbiddenEnergy,
  Fragment,
  LanguageRule,
  MusicRelease,
  MusicReleaseCampaignWorld,
  MoodReference,
  ObjectRelease,
  ReleaseFragment,
  ReviewItem,
  RuleViolation,
  SignalScoringRule,
  Track,
  TrackMoodReference,
  VisualRule,
  VisualEnvironment,
  VoiceProfile
} from "@prisma/client";

export const dbReadiness = {
  migrationsEnabled: true,
  prismaSchema: "packages/db/prisma/schema.prisma"
} as const;
