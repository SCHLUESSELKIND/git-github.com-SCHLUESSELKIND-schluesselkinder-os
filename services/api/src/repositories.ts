import { prisma } from "@schluesselkinder/db";
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
} from "@schluesselkinder/db";

export type ArtistRecord = Artist;
export type AudiencePersonaRecord = AudiencePersona;
export type BrandRuleRecord = BrandRule;
export type ChannelRuleRecord = ChannelRule;
export type ForbiddenEnergyRecord = ForbiddenEnergy;
export type LanguageRuleRecord = LanguageRule;
export type SignalScoringRuleRecord = SignalScoringRule;
export type VisualRuleRecord = VisualRule;
export type VoiceProfileRecord = VoiceProfile;

export type ObjectReleaseRecord = ObjectRelease & {
  artist: Pick<Artist, "name" | "slug"> | null;
};

export type MusicReleaseRecord = MusicRelease & {
  artist: Pick<Artist, "name" | "slug">;
  tracks: Track[];
};

export type FragmentRecord = Fragment;

export type ApiRepositories = Readonly<{
  artists: {
    findBySlug(slug: string): Promise<ArtistRecord | null>;
    list(): Promise<ArtistRecord[]>;
  };
  fragments: {
    list(): Promise<FragmentRecord[]>;
  };
  music: {
    findByReleaseCode(releaseCode: string): Promise<MusicReleaseRecord | null>;
    list(): Promise<MusicReleaseRecord[]>;
  };
  objects: {
    list(): Promise<ObjectReleaseRecord[]>;
  };
  brandIntelligence: {
    listAudiencePersonas(): Promise<AudiencePersonaRecord[]>;
    listBrandRules(): Promise<BrandRuleRecord[]>;
    listChannelRules(): Promise<ChannelRuleRecord[]>;
    listForbiddenEnergy(): Promise<ForbiddenEnergyRecord[]>;
    listLanguageRules(): Promise<LanguageRuleRecord[]>;
    listScoringRules(): Promise<SignalScoringRuleRecord[]>;
    listVisualRules(): Promise<VisualRuleRecord[]>;
    listVoiceProfiles(): Promise<VoiceProfileRecord[]>;
  };
}>;

export function createPrismaRepositories(): ApiRepositories {
  return {
    artists: {
      findBySlug: (slug) =>
        prisma.artist.findUnique({
          where: { slug }
        }),
      list: () =>
        prisma.artist.findMany({
          orderBy: { createdAt: "asc" }
        })
    },
    fragments: {
      list: () =>
        prisma.fragment.findMany({
          orderBy: [{ weight: "desc" }, { createdAt: "asc" }],
          where: { active: true }
        })
    },
    music: {
      findByReleaseCode: (releaseCode) =>
        prisma.musicRelease.findUnique({
          include: {
            artist: {
              select: {
                name: true,
                slug: true
              }
            },
            tracks: true
          },
          where: { releaseCode }
        }),
      list: () =>
        prisma.musicRelease.findMany({
          include: {
            artist: {
              select: {
                name: true,
                slug: true
              }
            },
            tracks: true
          },
          orderBy: { releaseCode: "asc" }
        })
    },
    objects: {
      list: () =>
        prisma.objectRelease.findMany({
          include: {
            artist: {
              select: {
                name: true,
                slug: true
              }
            }
          },
          orderBy: { releaseId: "asc" }
        })
    },
    brandIntelligence: {
      listAudiencePersonas: () =>
        prisma.audiencePersona.findMany({
          orderBy: { code: "asc" },
          where: { active: true }
        }),
      listBrandRules: () =>
        prisma.brandRule.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listChannelRules: () =>
        prisma.channelRule.findMany({
          orderBy: [{ channel: "asc" }, { weight: "desc" }],
          where: { active: true }
        }),
      listForbiddenEnergy: () =>
        prisma.forbiddenEnergy.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listLanguageRules: () =>
        prisma.languageRule.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listScoringRules: () =>
        prisma.signalScoringRule.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listVisualRules: () =>
        prisma.visualRule.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listVoiceProfiles: () =>
        prisma.voiceProfile.findMany({
          orderBy: { code: "asc" },
          where: { active: true }
        })
    }
  };
}
