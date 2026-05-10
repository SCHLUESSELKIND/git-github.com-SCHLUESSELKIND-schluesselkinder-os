import { prisma } from "@schluesselkinder/db";
import type {
  ApprovalComment,
  ApprovalDecision,
  Asset,
  AssetTag,
  ArtistCampaignWorld,
  Artist,
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
} from "@schluesselkinder/db";

export type ArtistRecord = Artist;
export type ApprovalCommentRecord = ApprovalComment;
export type ApprovalDecisionRecord = ApprovalDecision;
export type AssetRecord = Asset;
export type AssetTagRecord = AssetTag;
export type AudiencePersonaRecord = AudiencePersona;
export type BrandRuleRecord = BrandRule;
export type CampaignWorldRecord = CampaignWorld;
export type ChannelCompositionProfileRecord = ChannelCompositionProfile;
export type ChannelRuleRecord = ChannelRule;
export type GenerationOutputEvaluationRecord = GenerationOutputEvaluation;
export type ForbiddenEnergyRecord = ForbiddenEnergy;
export type LanguageRuleRecord = LanguageRule;
export type MoodReferenceRecord = MoodReference;
export type SignalScoringRuleRecord = SignalScoringRule;
export type VisualRuleRecord = VisualRule;
export type VisualEnvironmentRecord = VisualEnvironment;
export type VoiceProfileRecord = VoiceProfile;

export type ObjectReleaseRecord = ObjectRelease & {
  artist: Pick<Artist, "name" | "slug"> | null;
};

export type MusicReleaseRecord = MusicRelease & {
  artist: Pick<Artist, "name" | "slug">;
  tracks: Track[];
};

export type FragmentRecord = Fragment;

type ArtistCompatibilityRecord = ArtistCampaignWorld & {
  artist: Pick<Artist, "id" | "name" | "slug">;
  campaignWorld: CampaignWorld;
};

type MusicReleaseCompatibilityRecord = MusicReleaseCampaignWorld & {
  musicRelease: Pick<MusicRelease, "id" | "releaseCode" | "title">;
  campaignWorld: CampaignWorld;
};

type TrackMoodCompatibilityRecord = TrackMoodReference & {
  track: Pick<Track, "id" | "title">;
  moodReference: MoodReference;
};

type CampaignWorldVisualCompatibilityRecord = CampaignWorldVisualEnvironment & {
  campaignWorld: CampaignWorld;
  visualEnvironment: VisualEnvironment;
};

type CampaignWorldMoodCompatibilityRecord = CampaignWorldMoodReference & {
  campaignWorld: CampaignWorld;
  moodReference: MoodReference;
};

type CampaignWorldAssetCompatibilityRecord = CampaignWorldAsset & {
  asset: Asset;
  campaignWorld: CampaignWorld;
};

export type CompatibilityRecord =
  | { kind: "ARTIST_CAMPAIGN_WORLD"; record: ArtistCompatibilityRecord }
  | { kind: "MUSIC_RELEASE_CAMPAIGN_WORLD"; record: MusicReleaseCompatibilityRecord }
  | { kind: "TRACK_MOOD_REFERENCE"; record: TrackMoodCompatibilityRecord }
  | { kind: "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT"; record: CampaignWorldVisualCompatibilityRecord }
  | { kind: "CAMPAIGN_WORLD_MOOD_REFERENCE"; record: CampaignWorldMoodCompatibilityRecord }
  | { kind: "CAMPAIGN_WORLD_ASSET"; record: CampaignWorldAssetCompatibilityRecord };

export type ReleaseFragmentRecord = ReleaseFragment & {
  fragment: Pick<Fragment, "content" | "id" | "language" | "type">;
  musicRelease: Pick<MusicRelease, "id" | "releaseCode" | "title"> | null;
  track: Pick<Track, "id" | "title"> | null;
};
export type RuleViolationRecord = RuleViolation;

export type ChannelFragmentRecord = ChannelFragment & {
  campaignWorld: Pick<CampaignWorld, "code" | "id" | "name"> | null;
  fragment: Pick<Fragment, "content" | "id" | "language" | "type">;
  moodReference: Pick<MoodReference, "code" | "id" | "name"> | null;
};

export type ContentGraphMusicReleaseRecord = Readonly<{
  campaignWorlds: CompatibilityRecord[];
  release: MusicRelease & {
    artist: Pick<Artist, "name" | "slug">;
  };
  releaseFragments: ReleaseFragmentRecord[];
  trackMoodReferences: CompatibilityRecord[];
}>;

export type ReviewItemRecord = ReviewItem & {
  asset: Pick<Asset, "code" | "id" | "title"> | null;
  campaignWorld: Pick<CampaignWorld, "code" | "id" | "name"> | null;
  channelFragment: Pick<ChannelFragment, "channel" | "id" | "placement"> | null;
  comments: ApprovalComment[];
  decisions: ApprovalDecision[];
  musicRelease: Pick<MusicRelease, "id" | "releaseCode" | "title"> | null;
  releaseFragment: Pick<ReleaseFragment, "id" | "placement"> | null;
  track: Pick<Track, "id" | "title"> | null;
  violations: RuleViolation[];
};

export type ConstraintBundleRecord = ConstraintBundle & {
  constraints: GenerationBriefConstraint[];
};

export type GenerationBriefRecord = GenerationBrief & {
  campaignWorld: Pick<CampaignWorld, "code" | "id" | "name"> | null;
  channelCompositionProfile: Pick<ChannelCompositionProfile, "channel" | "code" | "id" | "name"> | null;
  channelFragment: Pick<ChannelFragment, "channel" | "id" | "placement"> | null;
  constraintBundle: Pick<ConstraintBundle, "code" | "id" | "name">;
  musicRelease: Pick<MusicRelease, "id" | "releaseCode" | "title"> | null;
  promptSections: PromptSection[];
  reviewItem: Pick<ReviewItem, "id" | "reviewKey" | "stage" | "status"> | null;
  track: Pick<Track, "id" | "title"> | null;
};

export type GenerationRequestRecord = GenerationRequest & {
  brief: Pick<GenerationBrief, "briefKey" | "id" | "title" | "type">;
  outputs: Pick<GenerationOutput, "id" | "outputKey" | "reviewItemId" | "status" | "title">[];
};

export type GenerationOutputRecord = GenerationOutput & {
  evaluations: GenerationOutputEvaluation[];
  request: Pick<GenerationRequest, "id" | "requestKey" | "status">;
  reviewItem: Pick<ReviewItem, "id" | "reviewKey" | "stage" | "status">;
};

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
  contentGraph: {
    findMusicReleaseGraph(releaseCode: string): Promise<ContentGraphMusicReleaseRecord | null>;
    listAssets(): Promise<AssetRecord[]>;
    listAssetTags(): Promise<AssetTagRecord[]>;
    listCampaignWorlds(): Promise<CampaignWorldRecord[]>;
    listChannelFragments(): Promise<ChannelFragmentRecord[]>;
    listCompatibility(): Promise<CompatibilityRecord[]>;
    listMoodReferences(): Promise<MoodReferenceRecord[]>;
    listReleaseFragments(): Promise<ReleaseFragmentRecord[]>;
    listVisualEnvironments(): Promise<VisualEnvironmentRecord[]>;
  };
  reviews: {
    findByReviewKey(reviewKey: string): Promise<ReviewItemRecord | null>;
    list(): Promise<ReviewItemRecord[]>;
    listComments(reviewKey: string): Promise<ApprovalCommentRecord[] | null>;
    listDecisions(reviewKey: string): Promise<ApprovalDecisionRecord[] | null>;
    listViolations(reviewKey: string): Promise<RuleViolationRecord[] | null>;
  };
  generation: {
    findBriefByKey(briefKey: string): Promise<GenerationBriefRecord | null>;
    findOutputByKey(outputKey: string): Promise<GenerationOutputRecord | null>;
    findRequestByKey(requestKey: string): Promise<GenerationRequestRecord | null>;
    listBriefs(): Promise<GenerationBriefRecord[]>;
    listChannelCompositionProfiles(): Promise<ChannelCompositionProfileRecord[]>;
    listConstraintBundles(): Promise<ConstraintBundleRecord[]>;
    listOutputEvaluations(outputKey: string): Promise<GenerationOutputEvaluationRecord[] | null>;
    listOutputs(): Promise<GenerationOutputRecord[]>;
    listRequests(): Promise<GenerationRequestRecord[]>;
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
    },
    contentGraph: {
      findMusicReleaseGraph: async (releaseCode) => {
        const release = await prisma.musicRelease.findUnique({
          include: {
            artist: {
              select: {
                name: true,
                slug: true
              }
            }
          },
          where: { releaseCode }
        });

        if (!release) {
          return null;
        }

        const [campaignWorlds, releaseFragments, tracks] = await Promise.all([
          prisma.musicReleaseCampaignWorld.findMany({
            include: {
              campaignWorld: true,
              musicRelease: {
                select: {
                  id: true,
                  releaseCode: true,
                  title: true
                }
              }
            },
            orderBy: [{ weight: "desc" }],
            where: { musicReleaseId: release.id }
          }),
          prisma.releaseFragment.findMany({
            include: releaseFragmentIncludes,
            orderBy: [{ weight: "desc" }],
            where: {
              OR: [
                { musicReleaseId: release.id },
                {
                  track: {
                    releaseId: release.id
                  }
                }
              ],
              active: true
            }
          }),
          prisma.track.findMany({
            select: { id: true },
            where: { releaseId: release.id }
          })
        ]);

        const trackMoodReferences = await prisma.trackMoodReference.findMany({
          include: {
            moodReference: true,
            track: {
              select: {
                id: true,
                title: true
              }
            }
          },
          orderBy: [{ weight: "desc" }],
          where: {
            trackId: {
              in: tracks.map((track) => track.id)
            }
          }
        });

        return {
          campaignWorlds: campaignWorlds.map((record) => ({
            kind: "MUSIC_RELEASE_CAMPAIGN_WORLD",
            record
          })),
          release,
          releaseFragments,
          trackMoodReferences: trackMoodReferences.map((record) => ({
            kind: "TRACK_MOOD_REFERENCE",
            record
          }))
        };
      },
      listAssets: () =>
        prisma.asset.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listAssetTags: () =>
        prisma.assetTag.findMany({
          orderBy: { code: "asc" },
          where: { active: true }
        }),
      listCampaignWorlds: () =>
        prisma.campaignWorld.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listChannelFragments: () =>
        prisma.channelFragment.findMany({
          include: channelFragmentIncludes,
          orderBy: [{ weight: "desc" }],
          where: { active: true }
        }),
      listCompatibility: async () => {
        const [
          artistCampaignWorlds,
          musicReleaseCampaignWorlds,
          trackMoodReferences,
          campaignWorldVisualEnvironments,
          campaignWorldMoodReferences,
          campaignWorldAssets
        ] = await Promise.all([
          prisma.artistCampaignWorld.findMany({
            include: {
              artist: {
                select: {
                  id: true,
                  name: true,
                  slug: true
                }
              },
              campaignWorld: true
            },
            orderBy: [{ weight: "desc" }]
          }),
          prisma.musicReleaseCampaignWorld.findMany({
            include: {
              campaignWorld: true,
              musicRelease: {
                select: {
                  id: true,
                  releaseCode: true,
                  title: true
                }
              }
            },
            orderBy: [{ weight: "desc" }]
          }),
          prisma.trackMoodReference.findMany({
            include: {
              moodReference: true,
              track: {
                select: {
                  id: true,
                  title: true
                }
              }
            },
            orderBy: [{ weight: "desc" }]
          }),
          prisma.campaignWorldVisualEnvironment.findMany({
            include: {
              campaignWorld: true,
              visualEnvironment: true
            },
            orderBy: [{ weight: "desc" }]
          }),
          prisma.campaignWorldMoodReference.findMany({
            include: {
              campaignWorld: true,
              moodReference: true
            },
            orderBy: [{ weight: "desc" }]
          }),
          prisma.campaignWorldAsset.findMany({
            include: {
              asset: true,
              campaignWorld: true
            },
            orderBy: [{ weight: "desc" }]
          })
        ]);

        return [
          ...artistCampaignWorlds.map((record) => ({ kind: "ARTIST_CAMPAIGN_WORLD" as const, record })),
          ...musicReleaseCampaignWorlds.map((record) => ({ kind: "MUSIC_RELEASE_CAMPAIGN_WORLD" as const, record })),
          ...trackMoodReferences.map((record) => ({ kind: "TRACK_MOOD_REFERENCE" as const, record })),
          ...campaignWorldVisualEnvironments.map((record) => ({
            kind: "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT" as const,
            record
          })),
          ...campaignWorldMoodReferences.map((record) => ({
            kind: "CAMPAIGN_WORLD_MOOD_REFERENCE" as const,
            record
          })),
          ...campaignWorldAssets.map((record) => ({ kind: "CAMPAIGN_WORLD_ASSET" as const, record }))
        ];
      },
      listMoodReferences: () =>
        prisma.moodReference.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        }),
      listReleaseFragments: () =>
        prisma.releaseFragment.findMany({
          include: releaseFragmentIncludes,
          orderBy: [{ weight: "desc" }],
          where: { active: true }
        }),
      listVisualEnvironments: () =>
        prisma.visualEnvironment.findMany({
          orderBy: [{ weight: "desc" }, { code: "asc" }],
          where: { active: true }
        })
    },
    reviews: {
      findByReviewKey: (reviewKey) =>
        prisma.reviewItem.findUnique({
          include: reviewItemIncludes,
          where: { reviewKey }
        }),
      list: () =>
        prisma.reviewItem.findMany({
          include: reviewItemIncludes,
          orderBy: [{ createdAt: "asc" }]
        }),
      listComments: async (reviewKey) => {
        const reviewItem = await prisma.reviewItem.findUnique({
          select: { id: true },
          where: { reviewKey }
        });

        if (!reviewItem) {
          return null;
        }

        return prisma.approvalComment.findMany({
          orderBy: { createdAt: "asc" },
          where: { reviewItemId: reviewItem.id }
        });
      },
      listDecisions: async (reviewKey) => {
        const reviewItem = await prisma.reviewItem.findUnique({
          select: { id: true },
          where: { reviewKey }
        });

        if (!reviewItem) {
          return null;
        }

        return prisma.approvalDecision.findMany({
          orderBy: { createdAt: "asc" },
          where: { reviewItemId: reviewItem.id }
        });
      },
      listViolations: async (reviewKey) => {
        const reviewItem = await prisma.reviewItem.findUnique({
          select: { id: true },
          where: { reviewKey }
        });

        if (!reviewItem) {
          return null;
        }

        return prisma.ruleViolation.findMany({
          orderBy: { createdAt: "asc" },
          where: { reviewItemId: reviewItem.id }
        });
      }
    },
    generation: {
      findBriefByKey: (briefKey) =>
        prisma.generationBrief.findUnique({
          include: generationBriefIncludes,
          where: { briefKey }
        }),
      findOutputByKey: (outputKey) =>
        prisma.generationOutput.findUnique({
          include: generationOutputIncludes,
          where: { outputKey }
        }),
      findRequestByKey: (requestKey) =>
        prisma.generationRequest.findUnique({
          include: generationRequestIncludes,
          where: { requestKey }
        }),
      listBriefs: () =>
        prisma.generationBrief.findMany({
          include: generationBriefIncludes,
          orderBy: [{ createdAt: "asc" }]
        }),
      listChannelCompositionProfiles: () =>
        prisma.channelCompositionProfile.findMany({
          orderBy: [{ channel: "asc" }, { code: "asc" }],
          where: { active: true }
        }),
      listConstraintBundles: () =>
        prisma.constraintBundle.findMany({
          include: {
            constraints: {
              orderBy: [{ weight: "desc" }]
            }
          },
          orderBy: { code: "asc" },
          where: { active: true }
        }),
      listOutputEvaluations: async (outputKey) => {
        const output = await prisma.generationOutput.findUnique({
          select: { id: true },
          where: { outputKey }
        });

        if (!output) {
          return null;
        }

        return prisma.generationOutputEvaluation.findMany({
          orderBy: { createdAt: "asc" },
          where: { outputId: output.id }
        });
      },
      listOutputs: () =>
        prisma.generationOutput.findMany({
          include: generationOutputIncludes,
          orderBy: [{ createdAt: "asc" }]
        }),
      listRequests: () =>
        prisma.generationRequest.findMany({
          include: generationRequestIncludes,
          orderBy: [{ createdAt: "asc" }]
        })
    }
  };
}

const releaseFragmentIncludes = {
  fragment: {
    select: {
      content: true,
      id: true,
      language: true,
      type: true
    }
  },
  musicRelease: {
    select: {
      id: true,
      releaseCode: true,
      title: true
    }
  },
  track: {
    select: {
      id: true,
      title: true
    }
  }
} as const;

const channelFragmentIncludes = {
  campaignWorld: {
    select: {
      code: true,
      id: true,
      name: true
    }
  },
  fragment: {
    select: {
      content: true,
      id: true,
      language: true,
      type: true
    }
  },
  moodReference: {
    select: {
      code: true,
      id: true,
      name: true
    }
  }
} as const;

const reviewItemIncludes = {
  asset: {
    select: {
      code: true,
      id: true,
      title: true
    }
  },
  campaignWorld: {
    select: {
      code: true,
      id: true,
      name: true
    }
  },
  channelFragment: {
    select: {
      channel: true,
      id: true,
      placement: true
    }
  },
  comments: {
    orderBy: {
      createdAt: "asc"
    }
  },
  decisions: {
    orderBy: {
      createdAt: "asc"
    }
  },
  musicRelease: {
    select: {
      id: true,
      releaseCode: true,
      title: true
    }
  },
  releaseFragment: {
    select: {
      id: true,
      placement: true
    }
  },
  track: {
    select: {
      id: true,
      title: true
    }
  },
  violations: {
    orderBy: {
      createdAt: "asc"
    }
  }
} as const;

const generationBriefIncludes = {
  campaignWorld: {
    select: {
      code: true,
      id: true,
      name: true
    }
  },
  channelCompositionProfile: {
    select: {
      channel: true,
      code: true,
      id: true,
      name: true
    }
  },
  channelFragment: {
    select: {
      channel: true,
      id: true,
      placement: true
    }
  },
  constraintBundle: {
    select: {
      code: true,
      id: true,
      name: true
    }
  },
  musicRelease: {
    select: {
      id: true,
      releaseCode: true,
      title: true
    }
  },
  promptSections: {
    orderBy: {
      position: "asc"
    }
  },
  reviewItem: {
    select: {
      id: true,
      reviewKey: true,
      stage: true,
      status: true
    }
  },
  track: {
    select: {
      id: true,
      title: true
    }
  }
} as const;

const generationRequestIncludes = {
  brief: {
    select: {
      briefKey: true,
      id: true,
      title: true,
      type: true
    }
  },
  outputs: {
    select: {
      id: true,
      outputKey: true,
      reviewItemId: true,
      status: true,
      title: true
    },
    orderBy: {
      createdAt: "asc"
    }
  }
} as const;

const generationOutputIncludes = {
  evaluations: {
    orderBy: {
      createdAt: "asc"
    }
  },
  request: {
    select: {
      id: true,
      requestKey: true,
      status: true
    }
  },
  reviewItem: {
    select: {
      id: true,
      reviewKey: true,
      stage: true,
      status: true
    }
  }
} as const;
