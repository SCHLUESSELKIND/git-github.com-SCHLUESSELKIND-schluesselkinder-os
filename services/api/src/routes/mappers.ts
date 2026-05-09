import type {
  AudiencePersonaRecord,
  ArtistRecord,
  BrandRuleRecord,
  ChannelRuleRecord,
  ForbiddenEnergyRecord,
  FragmentRecord,
  LanguageRuleRecord,
  MusicReleaseRecord,
  ObjectReleaseRecord,
  SignalScoringRuleRecord,
  VisualRuleRecord,
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
