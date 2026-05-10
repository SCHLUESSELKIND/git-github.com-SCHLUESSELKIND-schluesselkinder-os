import type {
  ApprovalCommentRecord,
  ApprovalDecisionRecord,
  AssetRecord,
  AssetTagRecord,
  AudiencePersonaRecord,
  ArtistRecord,
  BrandRuleRecord,
  CampaignWorldRecord,
  ChannelRuleRecord,
  ChannelFragmentRecord,
  CompatibilityRecord,
  ForbiddenEnergyRecord,
  FragmentRecord,
  LanguageRuleRecord,
  MusicReleaseRecord,
  MoodReferenceRecord,
  ObjectReleaseRecord,
  ReleaseFragmentRecord,
  ReviewItemRecord,
  RuleViolationRecord,
  SignalScoringRuleRecord,
  VisualRuleRecord,
  VisualEnvironmentRecord,
  VoiceProfileRecord
} from "../repositories.js";

export function mapArtist(artist: ArtistRecord) {
  return {
    bioFragment: artist.bioFragment,
    createdAt: artist.createdAt.toISOString(),
    id: artist.id,
    name: artist.name,
    slug: artist.slug,
    status: artist.status,
    symbol: artist.symbol
  };
}

export function mapObjectRelease(object: ObjectReleaseRecord) {
  return {
    archiveFragment: object.archiveFragment,
    artist: object.artist,
    createdAt: object.createdAt.toISOString(),
    id: object.id,
    mark: object.mark,
    materialNote: object.materialNote,
    releaseId: object.releaseId,
    status: object.status,
    title: object.title,
    type: object.type
  };
}

export function mapMusicRelease(release: MusicReleaseRecord) {
  return {
    artist: release.artist,
    coverImage: release.coverImage,
    createdAt: release.createdAt.toISOString(),
    id: release.id,
    releaseCode: release.releaseCode,
    status: release.status,
    title: release.title,
    tracks: release.tracks.map((track) => ({
      duration: track.duration,
      id: track.id,
      moodFragment: track.moodFragment,
      title: track.title
    }))
  };
}

export function mapFragment(fragment: FragmentRecord) {
  return {
    active: fragment.active,
    content: fragment.content,
    createdAt: fragment.createdAt.toISOString(),
    id: fragment.id,
    language: fragment.language,
    type: fragment.type,
    weight: fragment.weight
  };
}

export function mapBrandRule(rule: BrandRuleRecord) {
  return {
    active: rule.active,
    category: rule.category,
    code: rule.code,
    createdAt: rule.createdAt.toISOString(),
    id: rule.id,
    severity: rule.severity,
    statement: rule.statement,
    title: rule.title,
    weight: rule.weight
  };
}

export function mapVisualRule(rule: VisualRuleRecord) {
  return {
    active: rule.active,
    code: rule.code,
    createdAt: rule.createdAt.toISOString(),
    id: rule.id,
    rule: rule.rule,
    severity: rule.severity,
    title: rule.title,
    weight: rule.weight
  };
}

export function mapLanguageRule(rule: LanguageRuleRecord) {
  return mapVisualRule(rule);
}

export function mapForbiddenEnergy(energy: ForbiddenEnergyRecord) {
  return {
    active: energy.active,
    code: energy.code,
    createdAt: energy.createdAt.toISOString(),
    id: energy.id,
    label: energy.label,
    reason: energy.reason,
    severity: energy.severity,
    weight: energy.weight
  };
}

export function mapAudiencePersona(persona: AudiencePersonaRecord) {
  return {
    active: persona.active,
    aestheticAttraction: persona.aestheticAttraction,
    behavioralPattern: persona.behavioralPattern,
    code: persona.code,
    createdAt: persona.createdAt.toISOString(),
    emotionalState: persona.emotionalState,
    id: persona.id,
    name: persona.name,
    rejectionPattern: persona.rejectionPattern,
    resonanceReason: persona.resonanceReason
  };
}

export function mapVoiceProfile(profile: VoiceProfileRecord) {
  return {
    active: profile.active,
    code: profile.code,
    createdAt: profile.createdAt.toISOString(),
    description: profile.description,
    id: profile.id,
    name: profile.name
  };
}

export function mapChannelRule(rule: ChannelRuleRecord) {
  return {
    active: rule.active,
    channel: rule.channel,
    code: rule.code,
    createdAt: rule.createdAt.toISOString(),
    id: rule.id,
    rule: rule.rule,
    severity: rule.severity,
    title: rule.title,
    weight: rule.weight
  };
}

export function mapSignalScoringRule(rule: SignalScoringRuleRecord) {
  return {
    active: rule.active,
    code: rule.code,
    createdAt: rule.createdAt.toISOString(),
    description: rule.description,
    id: rule.id,
    maxScore: rule.maxScore,
    title: rule.title,
    weight: rule.weight
  };
}

export function mapCampaignWorld(world: CampaignWorldRecord) {
  return {
    active: world.active,
    code: world.code,
    createdAt: world.createdAt.toISOString(),
    description: world.description,
    id: world.id,
    name: world.name,
    weight: world.weight
  };
}

export function mapVisualEnvironment(environment: VisualEnvironmentRecord) {
  return {
    active: environment.active,
    code: environment.code,
    createdAt: environment.createdAt.toISOString(),
    description: environment.description,
    id: environment.id,
    name: environment.name,
    weight: environment.weight
  };
}

export function mapMoodReference(mood: MoodReferenceRecord) {
  return {
    active: mood.active,
    code: mood.code,
    createdAt: mood.createdAt.toISOString(),
    description: mood.description,
    id: mood.id,
    name: mood.name,
    weight: mood.weight
  };
}

export function mapAsset(asset: AssetRecord) {
  return {
    active: asset.active,
    code: asset.code,
    createdAt: asset.createdAt.toISOString(),
    description: asset.description,
    id: asset.id,
    referenceKey: asset.referenceKey,
    sourceType: asset.sourceType,
    title: asset.title,
    type: asset.type,
    weight: asset.weight
  };
}

export function mapAssetTag(tag: AssetTagRecord) {
  return {
    active: tag.active,
    code: tag.code,
    createdAt: tag.createdAt.toISOString(),
    id: tag.id,
    label: tag.label
  };
}

export function mapCompatibility(compatibility: CompatibilityRecord) {
  const base = {
    kind: compatibility.kind,
    reason: compatibility.record.reason,
    verdict: compatibility.record.verdict,
    weight: compatibility.record.weight
  };

  switch (compatibility.kind) {
    case "ARTIST_CAMPAIGN_WORLD":
      return {
        ...base,
        source: {
          code: compatibility.record.artist.slug,
          id: compatibility.record.artist.id,
          label: compatibility.record.artist.name
        },
        target: {
          code: compatibility.record.campaignWorld.code,
          id: compatibility.record.campaignWorld.id,
          label: compatibility.record.campaignWorld.name
        }
      };
    case "MUSIC_RELEASE_CAMPAIGN_WORLD":
      return {
        ...base,
        source: {
          code: compatibility.record.musicRelease.releaseCode,
          id: compatibility.record.musicRelease.id,
          label: compatibility.record.musicRelease.title
        },
        target: {
          code: compatibility.record.campaignWorld.code,
          id: compatibility.record.campaignWorld.id,
          label: compatibility.record.campaignWorld.name
        }
      };
    case "TRACK_MOOD_REFERENCE":
      return {
        ...base,
        source: {
          code: compatibility.record.track.title,
          id: compatibility.record.track.id,
          label: compatibility.record.track.title
        },
        target: {
          code: compatibility.record.moodReference.code,
          id: compatibility.record.moodReference.id,
          label: compatibility.record.moodReference.name
        }
      };
    case "CAMPAIGN_WORLD_VISUAL_ENVIRONMENT":
      return {
        ...base,
        source: {
          code: compatibility.record.campaignWorld.code,
          id: compatibility.record.campaignWorld.id,
          label: compatibility.record.campaignWorld.name
        },
        target: {
          code: compatibility.record.visualEnvironment.code,
          id: compatibility.record.visualEnvironment.id,
          label: compatibility.record.visualEnvironment.name
        }
      };
    case "CAMPAIGN_WORLD_MOOD_REFERENCE":
      return {
        ...base,
        source: {
          code: compatibility.record.campaignWorld.code,
          id: compatibility.record.campaignWorld.id,
          label: compatibility.record.campaignWorld.name
        },
        target: {
          code: compatibility.record.moodReference.code,
          id: compatibility.record.moodReference.id,
          label: compatibility.record.moodReference.name
        }
      };
    case "CAMPAIGN_WORLD_ASSET":
      return {
        ...base,
        source: {
          code: compatibility.record.campaignWorld.code,
          id: compatibility.record.campaignWorld.id,
          label: compatibility.record.campaignWorld.name
        },
        target: {
          code: compatibility.record.asset.code,
          id: compatibility.record.asset.id,
          label: compatibility.record.asset.title
        }
      };
  }
}

export function mapReleaseFragment(releaseFragment: ReleaseFragmentRecord) {
  return {
    active: releaseFragment.active,
    fragment: releaseFragment.fragment,
    id: releaseFragment.id,
    musicRelease: releaseFragment.musicRelease,
    placement: releaseFragment.placement,
    track: releaseFragment.track,
    weight: releaseFragment.weight
  };
}

export function mapChannelFragment(channelFragment: ChannelFragmentRecord) {
  return {
    active: channelFragment.active,
    campaignWorld: channelFragment.campaignWorld,
    channel: channelFragment.channel,
    fragment: channelFragment.fragment,
    id: channelFragment.id,
    moodReference: channelFragment.moodReference,
    placement: channelFragment.placement,
    weight: channelFragment.weight
  };
}

export function mapApprovalDecision(decision: ApprovalDecisionRecord) {
  return {
    createdAt: decision.createdAt.toISOString(),
    decidedBy: decision.decidedBy,
    id: decision.id,
    note: decision.note,
    reviewItemId: decision.reviewItemId,
    type: decision.type
  };
}

export function mapApprovalComment(comment: ApprovalCommentRecord) {
  return {
    author: comment.author,
    body: comment.body,
    createdAt: comment.createdAt.toISOString(),
    id: comment.id,
    reviewItemId: comment.reviewItemId
  };
}

export function mapRuleViolation(violation: RuleViolationRecord) {
  return {
    active: violation.active,
    createdAt: violation.createdAt.toISOString(),
    detail: violation.detail,
    id: violation.id,
    reviewItemId: violation.reviewItemId,
    ruleCode: violation.ruleCode,
    severity: violation.severity,
    source: violation.source,
    title: violation.title
  };
}

export function mapReviewItem(reviewItem: ReviewItemRecord) {
  return {
    asset: reviewItem.asset,
    campaignWorld: reviewItem.campaignWorld,
    channelFragment: reviewItem.channelFragment,
    comments: reviewItem.comments.map(mapApprovalComment),
    createdAt: reviewItem.createdAt.toISOString(),
    decisions: reviewItem.decisions.map(mapApprovalDecision),
    id: reviewItem.id,
    musicRelease: reviewItem.musicRelease,
    releaseFragment: reviewItem.releaseFragment,
    reviewKey: reviewItem.reviewKey,
    stage: reviewItem.stage,
    status: reviewItem.status,
    subjectKey: reviewItem.subjectKey,
    subjectType: reviewItem.subjectType,
    summary: reviewItem.summary,
    title: reviewItem.title,
    track: reviewItem.track,
    updatedAt: reviewItem.updatedAt.toISOString(),
    violations: reviewItem.violations.map(mapRuleViolation)
  };
}
