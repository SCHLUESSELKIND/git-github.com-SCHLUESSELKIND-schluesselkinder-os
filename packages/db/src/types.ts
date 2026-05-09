import type {
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

export type ArtistRecord = Artist;
export type AudiencePersonaRecord = AudiencePersona;
export type BrandRuleRecord = BrandRule;
export type ChannelRuleRecord = ChannelRule;
export type ForbiddenEnergyRecord = ForbiddenEnergy;
export type FragmentRecord = Fragment;
export type LanguageRuleRecord = LanguageRule;
export type MusicReleaseRecord = MusicRelease & {
  artist?: Artist;
  tracks?: Track[];
};
export type ObjectReleaseRecord = ObjectRelease & {
  artist?: Artist | null;
};
export type SignalScoringRuleRecord = SignalScoringRule;
export type TrackRecord = Track;
export type VisualRuleRecord = VisualRule;
export type VoiceProfileRecord = VoiceProfile;
