import type {
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
  ChannelCompositionProfile,
  ChannelFragment,
  ChannelRule,
  ConstraintBundle,
  ForbiddenEnergy,
  Fragment,
  GenerationBrief,
  GenerationBriefConstraint,
  GenerationOutput,
  GenerationOutputEvaluation,
  GenerationRequest,
  LanguageRule,
  MusicRelease,
  MusicReleaseCampaignWorld,
  MoodReference,
  ObjectRelease,
  PromptSection,
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

export type ApprovalCommentRecord = ApprovalComment;
export type ApprovalDecisionRecord = ApprovalDecision;
export type AssetRecord = Asset;
export type AssetTagAssignmentRecord = AssetTagAssignment;
export type AssetTagRecord = AssetTag;
export type ArtistRecord = Artist;
export type ArtistCampaignWorldRecord = ArtistCampaignWorld;
export type AudiencePersonaRecord = AudiencePersona;
export type BrandRuleRecord = BrandRule;
export type CampaignWorldAssetRecord = CampaignWorldAsset;
export type CampaignWorldMoodReferenceRecord = CampaignWorldMoodReference;
export type CampaignWorldRecord = CampaignWorld;
export type CampaignWorldVisualEnvironmentRecord = CampaignWorldVisualEnvironment;
export type ChannelCompositionProfileRecord = ChannelCompositionProfile;
export type ChannelFragmentRecord = ChannelFragment;
export type ChannelRuleRecord = ChannelRule;
export type ConstraintBundleRecord = ConstraintBundle;
export type ForbiddenEnergyRecord = ForbiddenEnergy;
export type FragmentRecord = Fragment;
export type GenerationBriefConstraintRecord = GenerationBriefConstraint;
export type GenerationBriefRecord = GenerationBrief;
export type GenerationOutputEvaluationRecord = GenerationOutputEvaluation;
export type GenerationOutputRecord = GenerationOutput;
export type GenerationRequestRecord = GenerationRequest;
export type LanguageRuleRecord = LanguageRule;
export type MoodReferenceRecord = MoodReference;
export type MusicReleaseCampaignWorldRecord = MusicReleaseCampaignWorld;
export type MusicReleaseRecord = MusicRelease & {
  artist?: Artist;
  tracks?: Track[];
};
export type ObjectReleaseRecord = ObjectRelease & {
  artist?: Artist | null;
};
export type PromptSectionRecord = PromptSection;
export type ReleaseFragmentRecord = ReleaseFragment;
export type ReviewItemRecord = ReviewItem;
export type RuleViolationRecord = RuleViolation;
export type SignalScoringRuleRecord = SignalScoringRule;
export type TrackRecord = Track;
export type TrackMoodReferenceRecord = TrackMoodReference;
export type VisualRuleRecord = VisualRule;
export type VisualEnvironmentRecord = VisualEnvironment;
export type VoiceProfileRecord = VoiceProfile;
