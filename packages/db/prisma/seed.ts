import {
  AssetSourceType,
  AssetType,
  ArtistStatus,
  Channel,
  CompatibilityVerdict,
  DecisionType,
  FragmentPlacement,
  FragmentType,
  PrismaClient,
  ReleaseStatus,
  ReviewStage,
  ReviewStatus,
  ReviewSubjectType,
  RuleCategory,
  RuleViolationSource,
  RuleSeverity
} from "@prisma/client";

const prisma = new PrismaClient();

async function seedArtist() {
  return prisma.artist.upsert({
    where: { slug: "shibari-kawaii" },
    update: {
      bioFragment: "Kalte Nähe.",
      name: "SHIBARI KAWAII",
      status: ArtistStatus.ACTIVE,
      symbol: "ROPEFACE"
    },
    create: {
      bioFragment: "Kalte Nähe.",
      name: "SHIBARI KAWAII",
      slug: "shibari-kawaii",
      status: ArtistStatus.ACTIVE,
      symbol: "ROPEFACE"
    }
  });
}

async function seedMusicReleases(artistId: string) {
  const releases = [
    {
      moodFragment: "static pulse",
      releaseCode: "SKM-001",
      title: "PICK ME UP"
    },
    {
      moodFragment: "concrete dawn",
      releaseCode: "SKM-002",
      title: "TUESDAY MORNING COMEDOWN"
    },
    {
      moodFragment: "ritual force",
      releaseCode: "SKM-003",
      title: "ROPEMASTER"
    }
  ] as const;

  for (const release of releases) {
    const musicRelease = await prisma.musicRelease.upsert({
      where: { releaseCode: release.releaseCode },
      update: {
        artistId,
        status: ReleaseStatus.ACTIVE,
        title: release.title
      },
      create: {
        artistId,
        releaseCode: release.releaseCode,
        status: ReleaseStatus.ACTIVE,
        title: release.title
      }
    });

    await prisma.track.deleteMany({
      where: { releaseId: musicRelease.id }
    });

    await prisma.track.create({
      data: {
        moodFragment: release.moodFragment,
        releaseId: musicRelease.id,
        title: release.title
      }
    });
  }
}

async function seedObjectReleases(artistId: string) {
  const objects = [
    {
      archiveFragment: "Archiv offen. Store geschlossen.",
      materialNote: "Black cotton study. Key mark.",
      mark: "KEY",
      releaseId: "SK-001",
      title: "BLACK HOODIE / KEY",
      type: "GARMENT_STUDY"
    },
    {
      archiveFragment: "SIGNAL ZUERST. WARE SPÄTER.",
      materialNote: "Black sweat study. Rune mark.",
      mark: "RUNE",
      releaseId: "SK-002",
      title: "BLACK SWEAT / RUNE",
      type: "GARMENT_STUDY"
    },
    {
      archiveFragment: "No soft biography.",
      materialNote: "Oversized tee study. Ropeface artist stamp.",
      mark: "ROPEFACE",
      releaseId: "SK-A001",
      title: "OVERSIZED TEE / ROPEFACE",
      type: "ARTIST_STUDY"
    }
  ] as const;

  for (const object of objects) {
    await prisma.objectRelease.upsert({
      where: { releaseId: object.releaseId },
      update: {
        archiveFragment: object.archiveFragment,
        artistId,
        mark: object.mark,
        materialNote: object.materialNote,
        status: ReleaseStatus.CLOSED,
        title: object.title,
        type: object.type
      },
      create: {
        archiveFragment: object.archiveFragment,
        artistId,
        mark: object.mark,
        materialNote: object.materialNote,
        releaseId: object.releaseId,
        status: ReleaseStatus.CLOSED,
        title: object.title,
        type: object.type
      }
    });
  }
}

async function seedFragments() {
  const fragments = [
    { content: "NACHT BLEIBT MATERIAL.", language: "de", type: FragmentType.HERO, weight: 100 },
    { content: "DER RAUM IST LEER. DER TON BLEIBT.", language: "de", type: FragmentType.MANIFEST, weight: 90 },
    { content: "SIGNAL ZUERST. WARE SPÄTER.", language: "de", type: FragmentType.OBJECT, weight: 80 },
    { content: "NO BRIGHT ROOM.", language: "en", type: FragmentType.HERO, weight: 70 },
    { content: "Archiv offen. Store geschlossen.", language: "de", type: FragmentType.OBJECT, weight: 60 },
    { content: "Afterhours is a method.", language: "en", type: FragmentType.MANIFEST, weight: 50 },
    { content: "No soft biography.", language: "en", type: FragmentType.ARTIST, weight: 40 },
    { content: "Evidence, not lifestyle.", language: "en", type: FragmentType.MANIFEST, weight: 30 }
  ] as const;

  await prisma.fragment.deleteMany({
    where: {
      content: {
        in: fragments.map((fragment) => fragment.content)
      }
    }
  });

  await prisma.fragment.createMany({
    data: fragments.map((fragment) => ({
      active: true,
      content: fragment.content,
      language: fragment.language,
      type: fragment.type,
      weight: fragment.weight
    }))
  });
}

async function seedBrandRules() {
  const rules = [
    {
      category: RuleCategory.CORE,
      code: "CORE_NOT_MOODBOARD",
      statement: "SCHLUESSELKINDER is not horror, not cyberpunk, not fetish decoration, and not an AI moodboard.",
      title: "Not moodboard energy",
      weight: 100
    },
    {
      category: RuleCategory.CORE,
      code: "CORE_LABEL_SYSTEM",
      statement: "The brand is a cold underground music and streetwear label system.",
      title: "Cold label system",
      weight: 95
    },
    {
      category: RuleCategory.CORE,
      code: "CORE_RADICAL_REDUCTION",
      statement: "Use radical reduction. Do not add motifs just because they are available.",
      title: "Radical reduction",
      weight: 90
    },
    {
      category: RuleCategory.CORE,
      code: "CORE_BERLIN_FILTER",
      statement: "Every public output should pass this filter: would an obscure Berlin underground label publish this?",
      title: "Berlin label filter",
      weight: 85
    }
  ] as const;

  for (const rule of rules) {
    await prisma.brandRule.upsert({
      where: { code: rule.code },
      update: {
        category: rule.category,
        statement: rule.statement,
        title: rule.title,
        weight: rule.weight
      },
      create: {
        category: rule.category,
        code: rule.code,
        severity: RuleSeverity.REQUIRED,
        statement: rule.statement,
        title: rule.title,
        weight: rule.weight
      }
    });
  }
}

async function seedVisualRules() {
  const rules = [
    {
      code: "VISUAL_CHAIR_PRIMARY",
      rule: "The dungeon/chair image is the primary recurring campaign environment.",
      title: "Chair environment leads",
      weight: 100
    },
    {
      code: "VISUAL_RUNE_SYSTEM",
      rule: "The rune/key mark is the institutional identity language.",
      title: "Rune/key system",
      weight: 95
    },
    {
      code: "VISUAL_ROPEFACE_SECONDARY",
      rule: "Ropeface is artist-specific secondary identity, used as a stamp or artifact mark.",
      title: "Ropeface restraint",
      weight: 80
    },
    {
      code: "VISUAL_NO_COLLAGE",
      rule: "Avoid poster collage, internet occult aesthetics, horror props, and overdesigned cyberpunk.",
      title: "No collage drift",
      weight: 90
    }
  ] as const;

  for (const rule of rules) {
    await prisma.visualRule.upsert({
      where: { code: rule.code },
      update: {
        rule: rule.rule,
        title: rule.title,
        weight: rule.weight
      },
      create: {
        code: rule.code,
        rule: rule.rule,
        severity: RuleSeverity.REQUIRED,
        title: rule.title,
        weight: rule.weight
      }
    });
  }
}

async function seedLanguageRules() {
  const rules = [
    {
      code: "LANG_GERMAN_FIRST",
      rule: "German first. English appears as cold fragments, not translation filler.",
      title: "German-first fragments",
      weight: 100
    },
    {
      code: "LANG_METADATA_OVER_EXPLANATION",
      rule: "Use metadata, short lines, and institutional fragments over explanation.",
      title: "Metadata over explanation",
      weight: 95
    },
    {
      code: "LANG_ONE_DOMINANT_STATEMENT",
      rule: "Use one dominant statement per public view.",
      title: "One dominant statement",
      weight: 90
    },
    {
      code: "LANG_NO_CONVERSION",
      rule: "Avoid startup language, community marketing, fake hype, discover, join us, and shop now.",
      title: "No conversion language",
      weight: 100
    }
  ] as const;

  for (const rule of rules) {
    await prisma.languageRule.upsert({
      where: { code: rule.code },
      update: {
        rule: rule.rule,
        title: rule.title,
        weight: rule.weight
      },
      create: {
        code: rule.code,
        rule: rule.rule,
        severity: RuleSeverity.REQUIRED,
        title: rule.title,
        weight: rule.weight
      }
    });
  }
}

async function seedForbiddenEnergy() {
  const energies = [
    ["HORROR", "Horror", "Pushes the label toward props, fear tropes, and dark-art culture."],
    ["CYBERPUNK_OVERLOAD", "Cyberpunk overload", "Adds generic neon dystopia instead of controlled techno-industrial emptiness."],
    ["FETISH_DECORATION", "Fetish decoration", "Turns rope and pressure into spectacle instead of restraint."],
    ["AI_MOODBOARD", "AI moodboard", "Feels assembled from available motifs rather than authored as a label system."],
    ["STARTUP_SAAS", "Startup SaaS", "Breaks the institutional underground label tone."],
    ["SHOPIFY_MERCH", "Shopify merch language", "Makes the object archive feel like a generic store."],
    ["MEME_IRONY", "Meme irony", "Collapses emotional pressure into internet tone."],
    ["LIFESTYLE_CLICHE", "Lifestyle cliche", "Turns the system into shallow taste performance."]
  ] as const;

  for (const [code, label, reason] of energies) {
    await prisma.forbiddenEnergy.upsert({
      where: { code },
      update: {
        label,
        reason
      },
      create: {
        code,
        label,
        reason,
        severity: RuleSeverity.REQUIRED,
        weight: 100
      }
    });
  }
}

async function seedVoiceProfiles() {
  const profiles = [
    {
      code: "MASTERBRAND",
      description: "Institutional SCHLUESSELKINDER voice: cold, sparse, archival, German-first.",
      name: "Masterbrand"
    },
    {
      code: "FIRST_ARTIST",
      description: "SHIBARI KAWAII dossier voice: intimate, controlled, no soft biography.",
      name: "First artist"
    },
    {
      code: "OBJECT_ARCHIVE",
      description: "Object archive voice: future-facing, closed, material, no commerce pressure.",
      name: "Object archive"
    }
  ] as const;

  for (const profile of profiles) {
    await prisma.voiceProfile.upsert({
      where: { code: profile.code },
      update: {
        description: profile.description,
        name: profile.name
      },
      create: profile
    });
  }
}

async function seedAudiencePersonas() {
  const personas = [
    {
      aestheticAttraction: "Concrete, restraint, hard typography, black garments, sparse symbols.",
      behavioralPattern: "Saves references, listens repeatedly, studies archive details before acting.",
      code: "POST_CLUB_ISOLATION",
      emotionalState: "Afterhours distance, fatigue, intimacy without warmth.",
      name: "Post-club isolation",
      rejectionPattern: "Rejects hype, friendliness, lifestyle optimism, and obvious trend language.",
      resonanceReason: "The system gives form to the hour after the room empties."
    },
    {
      aestheticAttraction: "Label archives, release codes, metadata, controlled visual systems.",
      behavioralPattern: "Reads credits, follows release systems, notices consistency and restraint.",
      code: "ARCHIVE_MINDED_UNDERGROUND_OBSERVER",
      emotionalState: "Detached attention and cultural pattern recognition.",
      name: "Archive-minded underground observer",
      rejectionPattern: "Rejects messy collage, explainers, and broad community marketing.",
      resonanceReason: "The archive structure feels deliberate and credible."
    },
    {
      aestheticAttraction: "Sparse tracks, cold fragments, pressure, repetition, static.",
      behavioralPattern: "Loops individual tracks and attaches to fragments rather than campaigns.",
      code: "EMOTIONALLY_RESTRAINED_MUSIC_OBSESSIVE",
      emotionalState: "High feeling, low expression.",
      name: "Emotionally restrained music obsessive",
      rejectionPattern: "Rejects over-emotional storytelling and artist-brand theater.",
      resonanceReason: "The music language gives pressure without confession."
    },
    {
      aestheticAttraction: "Brutalist fashion, object studies, black forms, material seriousness.",
      behavioralPattern: "Treats garments as artifacts and reads clothing through cultural context.",
      code: "BRUTALIST_FASHION_MINIMALIST",
      emotionalState: "Controlled desire, visual severity, object focus.",
      name: "Brutalist fashion minimalist",
      rejectionPattern: "Rejects merch language, lifestyle styling, and fake scarcity.",
      resonanceReason: "The object archive makes clothing feel like evidence, not product."
    },
    {
      aestheticAttraction: "Berlin melancholy, late rooms, cinematic darkness, no sentimentality.",
      behavioralPattern: "Follows atmosphere and signals before explicit offers.",
      code: "AFTERHOURS_ROMANTICISM_WITHOUT_SOFTNESS",
      emotionalState: "Romantic charge held under discipline.",
      name: "Afterhours romanticism without softness",
      rejectionPattern: "Rejects softness, nostalgia, fantasy, and obvious seduction.",
      resonanceReason: "The brand allows intimacy without warmth or explanation."
    }
  ] as const;

  for (const persona of personas) {
    await prisma.audiencePersona.upsert({
      where: { code: persona.code },
      update: persona,
      create: persona
    });
  }
}

async function seedChannelRules() {
  const rules = [
    {
      channel: Channel.WEBSITE,
      code: "CHANNEL_WEBSITE_INSTITUTIONAL",
      rule: "Website language stays institutional, sparse, and archive-led.",
      title: "Website as label system",
      weight: 100
    },
    {
      channel: Channel.INSTAGRAM,
      code: "CHANNEL_INSTAGRAM_FRAGMENTS",
      rule: "Instagram uses fragments, release signals, and controlled image evidence. No fake hype.",
      title: "Instagram fragment discipline",
      weight: 80
    },
    {
      channel: Channel.TIKTOK,
      code: "CHANNEL_TIKTOK_NO_TREND_CHASING",
      rule: "TikTok output must not chase trends at the cost of brand restraint.",
      title: "TikTok restraint",
      weight: 80
    },
    {
      channel: Channel.SOUNDCLOUD,
      code: "CHANNEL_SOUNDCLOUD_RELEASE_METADATA",
      rule: "SoundCloud copy uses clean release metadata and track fragments.",
      title: "SoundCloud metadata",
      weight: 70
    },
    {
      channel: Channel.SPOTIFY,
      code: "CHANNEL_SPOTIFY_CLEAN_RELEASE",
      rule: "Spotify presence stays clean, direct, and release-led.",
      title: "Spotify release clarity",
      weight: 70
    }
  ] as const;

  for (const rule of rules) {
    await prisma.channelRule.upsert({
      where: { code: rule.code },
      update: {
        channel: rule.channel,
        rule: rule.rule,
        title: rule.title,
        weight: rule.weight
      },
      create: {
        channel: rule.channel,
        code: rule.code,
        rule: rule.rule,
        severity: RuleSeverity.REQUIRED,
        title: rule.title,
        weight: rule.weight
      }
    });
  }
}

async function seedSignalScoringRules() {
  const rules = [
    ["SCORE_ICONIC_RESTRAINT", "Iconic restraint", "Rewards outputs that become more iconic by removing noise.", 10, 3],
    ["SCORE_CHAIR_RUNE_PROTECTION", "Chair and rune protection", "Rewards outputs that protect the chair environment and rune/key system.", 10, 3],
    ["SCORE_LANGUAGE_SPARSITY", "Language sparsity", "Rewards sparse, German-first, metadata-driven language.", 10, 2],
    ["SCORE_FORBIDDEN_ENERGY_AVOIDANCE", "Forbidden energy avoidance", "Penalizes horror, cyberpunk overload, fetish decoration, AI moodboard, hype, and merch language.", 10, 4],
    ["SCORE_CULTURAL_CREDIBILITY", "Cultural credibility", "Rewards outputs that feel publishable by an obscure Berlin underground label.", 10, 3],
    ["SCORE_TENSION_WITHOUT_NOISE", "Tension without noise", "Rewards pressure, asymmetry, and restraint without collage or gimmicks.", 10, 2]
  ] as const;

  for (const [code, title, description, maxScore, weight] of rules) {
    await prisma.signalScoringRule.upsert({
      where: { code },
      update: {
        description,
        maxScore,
        title,
        weight
      },
      create: {
        code,
        description,
        maxScore,
        title,
        weight
      }
    });
  }
}

async function seedCampaignWorlds() {
  const worlds = [
    {
      code: "ROOM_AFTER_LIGHT",
      description: "Primary campaign world for chair, concrete, low light, and after-room pressure.",
      name: "Room after light",
      weight: 100
    },
    {
      code: "COLD_ARCHIVE",
      description: "Object and release archive world built from restraint, metadata, and closed-system language.",
      name: "Cold archive",
      weight: 90
    },
    {
      code: "CONCRETE_SIGNAL",
      description: "Infrastructure world for hard surfaces, institutional marks, and signal-first composition.",
      name: "Concrete signal",
      weight: 80
    },
    {
      code: "POST_CLUB_SILENCE",
      description: "Music world for empty-room timing, late pressure, and minimal afterhours fragments.",
      name: "Post-club silence",
      weight: 70
    }
  ] as const;

  for (const world of worlds) {
    await prisma.campaignWorld.upsert({
      where: { code: world.code },
      update: world,
      create: world
    });
  }
}

async function seedVisualEnvironments() {
  const environments = [
    {
      code: "DUNGEON_CHAIR_PRIMARY",
      description: "Primary recurring campaign environment. Concrete room, chair, rope, low light.",
      name: "Dungeon chair primary",
      weight: 100
    },
    {
      code: "BLACK_FABRIC_VOID",
      description: "Black material field for object archive restraint. No horror prop usage.",
      name: "Black fabric void",
      weight: 70
    },
    {
      code: "CONCRETE_WALL_LOW_LIGHT",
      description: "Concrete texture and low-light surface environment for institutional signal work.",
      name: "Concrete wall low light",
      weight: 85
    },
    {
      code: "ARCHIVE_OBJECT_TABLE",
      description: "Controlled object-study environment for future archive references.",
      name: "Archive object table",
      weight: 60
    }
  ] as const;

  for (const environment of environments) {
    await prisma.visualEnvironment.upsert({
      where: { code: environment.code },
      update: environment,
      create: environment
    });
  }
}

async function seedMoodReferences() {
  const moods = [
    {
      code: "TENSION_LOW_LIGHT",
      description: "Low-light pressure with restrained contrast and no theatrical horror.",
      name: "Tension low light",
      weight: 90
    },
    {
      code: "INSTITUTIONAL_COLDNESS",
      description: "Cold system tone, technical distance, and label-level restraint.",
      name: "Institutional coldness",
      weight: 100
    },
    {
      code: "EMPTY_ROOM_PRESSURE",
      description: "After-room pressure, silence, and spatial absence.",
      name: "Empty room pressure",
      weight: 95
    },
    {
      code: "BLACKOUT_SILENCE",
      description: "Reduced signal state, blackout field, and minimal channel energy.",
      name: "Blackout silence",
      weight: 75
    },
    {
      code: "POST_CLUB_MELANCHOLY",
      description: "Controlled late-hour melancholy without soft nostalgia.",
      name: "Post-club melancholy",
      weight: 80
    }
  ] as const;

  for (const mood of moods) {
    await prisma.moodReference.upsert({
      where: { code: mood.code },
      update: mood,
      create: mood
    });
  }
}

async function seedAssets() {
  const assets = [
    {
      code: "CHAIR_CAMPAIGN_ENVIRONMENT",
      description: "Dungeon/chair campaign environment used as primary visual world.",
      referenceKey: "brand/chair-campaign-environment",
      sourceType: AssetSourceType.LOCAL_REFERENCE,
      title: "Chair campaign environment",
      type: AssetType.IMAGE,
      weight: 100
    },
    {
      code: "RUNE_KEY_SYMBOL",
      description: "Institutional rune/key mark. System language, not decoration.",
      referenceKey: "brand/rune-key-symbol",
      sourceType: AssetSourceType.SYMBOLIC_REFERENCE,
      title: "Rune/key symbol",
      type: AssetType.SYMBOL,
      weight: 100
    },
    {
      code: "ROPEFACE_ARTIST_STAMP",
      description: "SHIBARI KAWAII secondary artist stamp. Not masterbrand hero identity.",
      referenceKey: "brand/ropeface-artist-stamp",
      sourceType: AssetSourceType.SYMBOLIC_REFERENCE,
      title: "Ropeface artist stamp",
      type: AssetType.SYMBOL,
      weight: 60
    },
    {
      code: "SHIBARI_KAWAII_WORDMARK",
      description: "Artist wordmark reference for dossier contexts only.",
      referenceKey: "brand/shibari-kawaii-wordmark",
      sourceType: AssetSourceType.SYMBOLIC_REFERENCE,
      title: "SHIBARI KAWAII wordmark",
      type: AssetType.SYMBOL,
      weight: 40
    },
    {
      code: "EIN_POSTER_TEXTURE",
      description: "Supporting poster texture. Influence only, not primary system.",
      referenceKey: "brand/ein-poster-texture",
      sourceType: AssetSourceType.LOCAL_REFERENCE,
      title: "EIN poster texture",
      type: AssetType.IMAGE,
      weight: 30
    }
  ] as const;

  for (const asset of assets) {
    await prisma.asset.upsert({
      where: { code: asset.code },
      update: asset,
      create: asset
    });
  }
}

async function seedAssetTags() {
  const tags = [
    ["RUNE_KEY", "Rune/key"],
    ["CHAIR", "Chair"],
    ["CONCRETE", "Concrete"],
    ["LOW_LIGHT", "Low light"],
    ["BLACK_MATERIAL", "Black material"],
    ["ARTIST_STAMP", "Artist stamp"],
    ["ARCHIVE_SIGNAL", "Archive signal"]
  ] as const;

  for (const [code, label] of tags) {
    await prisma.assetTag.upsert({
      where: { code },
      update: { label },
      create: { code, label }
    });
  }
}

async function seedAssetTagAssignments() {
  const assignments = [
    ["CHAIR_CAMPAIGN_ENVIRONMENT", "CHAIR", 100],
    ["CHAIR_CAMPAIGN_ENVIRONMENT", "CONCRETE", 90],
    ["CHAIR_CAMPAIGN_ENVIRONMENT", "LOW_LIGHT", 90],
    ["RUNE_KEY_SYMBOL", "RUNE_KEY", 100],
    ["RUNE_KEY_SYMBOL", "ARCHIVE_SIGNAL", 90],
    ["ROPEFACE_ARTIST_STAMP", "ARTIST_STAMP", 70],
    ["SHIBARI_KAWAII_WORDMARK", "ARTIST_STAMP", 50],
    ["EIN_POSTER_TEXTURE", "ARCHIVE_SIGNAL", 30],
    ["EIN_POSTER_TEXTURE", "BLACK_MATERIAL", 20]
  ] as const;

  for (const [assetCode, tagCode, weight] of assignments) {
    const asset = await prisma.asset.findUniqueOrThrow({ where: { code: assetCode } });
    const tag = await prisma.assetTag.findUniqueOrThrow({ where: { code: tagCode } });

    await prisma.assetTagAssignment.upsert({
      where: {
        assetId_tagId: {
          assetId: asset.id,
          tagId: tag.id
        }
      },
      update: { weight },
      create: {
        assetId: asset.id,
        tagId: tag.id,
        weight
      }
    });
  }
}

async function seedCompatibilityGraph(artistId: string) {
  const campaignWorldIds = await getIdMap("campaignWorld");
  const visualEnvironmentIds = await getIdMap("visualEnvironment");
  const moodReferenceIds = await getIdMap("moodReference");
  const assetIds = await getIdMap("asset");

  await upsertArtistCampaignWorld(
    artistId,
    campaignWorldIds.ROOM_AFTER_LIGHT,
    CompatibilityVerdict.REQUIRED,
    "SHIBARI KAWAII is anchored in the primary chair campaign world.",
    100
  );
  await upsertArtistCampaignWorld(
    artistId,
    campaignWorldIds.COLD_ARCHIVE,
    CompatibilityVerdict.ALLOWED,
    "Artist dossier can inherit archive restraint.",
    70
  );

  const releases = await prisma.musicRelease.findMany({
    include: { tracks: true },
    where: {
      releaseCode: {
        in: ["SKM-001", "SKM-002", "SKM-003"]
      }
    }
  });

  for (const release of releases) {
    const releaseWorld =
      release.releaseCode === "SKM-002" ? "CONCRETE_SIGNAL" : release.releaseCode === "SKM-001" ? "POST_CLUB_SILENCE" : "ROOM_AFTER_LIGHT";

    await upsertMusicReleaseCampaignWorld(
      release.id,
      campaignWorldIds[releaseWorld],
      release.releaseCode === "SKM-003" ? CompatibilityVerdict.REQUIRED : CompatibilityVerdict.ALLOWED,
      `${release.releaseCode} belongs to ${releaseWorld}.`,
      release.releaseCode === "SKM-003" ? 100 : 80
    );

    for (const track of release.tracks) {
      const moodCode =
        release.releaseCode === "SKM-001"
          ? "POST_CLUB_MELANCHOLY"
          : release.releaseCode === "SKM-002"
            ? "EMPTY_ROOM_PRESSURE"
            : "TENSION_LOW_LIGHT";

      await upsertTrackMoodReference(
        track.id,
        moodReferenceIds[moodCode],
        CompatibilityVerdict.REQUIRED,
        `${track.title} uses ${moodCode} as its core mood reference.`,
        100
      );
    }
  }

  await upsertCampaignWorldVisualEnvironment(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    visualEnvironmentIds.DUNGEON_CHAIR_PRIMARY,
    CompatibilityVerdict.REQUIRED,
    "The chair image is the primary recurring campaign environment.",
    100
  );
  await upsertCampaignWorldVisualEnvironment(
    campaignWorldIds.CONCRETE_SIGNAL,
    visualEnvironmentIds.CONCRETE_WALL_LOW_LIGHT,
    CompatibilityVerdict.REQUIRED,
    "Concrete signal requires concrete, low-light environment logic.",
    90
  );
  await upsertCampaignWorldVisualEnvironment(
    campaignWorldIds.COLD_ARCHIVE,
    visualEnvironmentIds.ARCHIVE_OBJECT_TABLE,
    CompatibilityVerdict.ALLOWED,
    "The object archive may use controlled artifact-study framing.",
    70
  );
  await upsertCampaignWorldVisualEnvironment(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    visualEnvironmentIds.BLACK_FABRIC_VOID,
    CompatibilityVerdict.DISCOURAGED,
    "Black fabric can flatten the chair-led world if it becomes generic dark merch staging.",
    20
  );

  await upsertCampaignWorldMoodReference(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    moodReferenceIds.EMPTY_ROOM_PRESSURE,
    CompatibilityVerdict.REQUIRED,
    "Room-after-light must preserve empty-room pressure.",
    100
  );
  await upsertCampaignWorldMoodReference(
    campaignWorldIds.COLD_ARCHIVE,
    moodReferenceIds.INSTITUTIONAL_COLDNESS,
    CompatibilityVerdict.REQUIRED,
    "The archive requires institutional coldness.",
    100
  );
  await upsertCampaignWorldMoodReference(
    campaignWorldIds.POST_CLUB_SILENCE,
    moodReferenceIds.POST_CLUB_MELANCHOLY,
    CompatibilityVerdict.ALLOWED,
    "Post-club silence may carry controlled melancholy.",
    80
  );

  await upsertCampaignWorldAsset(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    assetIds.CHAIR_CAMPAIGN_ENVIRONMENT,
    CompatibilityVerdict.REQUIRED,
    "Chair environment is required for the primary campaign world.",
    100
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    assetIds.RUNE_KEY_SYMBOL,
    CompatibilityVerdict.REQUIRED,
    "Rune/key remains the institutional punctuation mark.",
    95
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.ROOM_AFTER_LIGHT,
    assetIds.ROPEFACE_ARTIST_STAMP,
    CompatibilityVerdict.DISCOURAGED,
    "Ropeface must stay secondary and archival, not hero-dominant.",
    30
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.COLD_ARCHIVE,
    assetIds.RUNE_KEY_SYMBOL,
    CompatibilityVerdict.REQUIRED,
    "The archive is rune/key-led.",
    100
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.COLD_ARCHIVE,
    assetIds.ROPEFACE_ARTIST_STAMP,
    CompatibilityVerdict.FORBIDDEN,
    "Ropeface cannot replace the rune/key as institutional archive language.",
    100
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.CONCRETE_SIGNAL,
    assetIds.SHIBARI_KAWAII_WORDMARK,
    CompatibilityVerdict.FORBIDDEN,
    "Artist wordmarks cannot lead institutional concrete signal contexts.",
    95
  );
  await upsertCampaignWorldAsset(
    campaignWorldIds.COLD_ARCHIVE,
    assetIds.EIN_POSTER_TEXTURE,
    CompatibilityVerdict.DISCOURAGED,
    "Poster texture is influence only and should not become collage energy.",
    20
  );
}

async function seedReleaseFragments() {
  const releaseFragmentData = [
    ["SKM-001", null, "NACHT BLEIBT MATERIAL.", FragmentPlacement.RELEASE_NOTE, 90],
    ["SKM-002", null, "DER RAUM IST LEER. DER TON BLEIBT.", FragmentPlacement.RELEASE_NOTE, 90],
    ["SKM-003", null, "No soft biography.", FragmentPlacement.METADATA, 80],
    [null, "PICK ME UP", "Afterhours is a method.", FragmentPlacement.METADATA, 70],
    [null, "TUESDAY MORNING COMEDOWN", "DER RAUM IST LEER. DER TON BLEIBT.", FragmentPlacement.METADATA, 90],
    [null, "ROPEMASTER", "No soft biography.", FragmentPlacement.METADATA, 80]
  ] as const;

  await prisma.releaseFragment.deleteMany({});

  for (const [releaseCode, trackTitle, fragmentContent, placement, weight] of releaseFragmentData) {
    const fragment = await prisma.fragment.findFirstOrThrow({ where: { content: fragmentContent } });
    const musicRelease = releaseCode
      ? await prisma.musicRelease.findUniqueOrThrow({ where: { releaseCode } })
      : null;
    const track = trackTitle ? await prisma.track.findFirstOrThrow({ where: { title: trackTitle } }) : null;

    await prisma.releaseFragment.create({
      data: {
        active: true,
        fragmentId: fragment.id,
        musicReleaseId: musicRelease?.id,
        placement,
        trackId: track?.id,
        weight
      }
    });
  }
}

async function seedChannelFragments() {
  const campaignWorldIds = await getIdMap("campaignWorld");
  const moodReferenceIds = await getIdMap("moodReference");
  const channelFragmentData = [
    ["NACHT BLEIBT MATERIAL.", Channel.WEBSITE, "ROOM_AFTER_LIGHT", null, FragmentPlacement.HERO, 100],
    ["DER RAUM IST LEER. DER TON BLEIBT.", Channel.INSTAGRAM, "ROOM_AFTER_LIGHT", "EMPTY_ROOM_PRESSURE", FragmentPlacement.CAPTION, 80],
    ["SIGNAL ZUERST. WARE SPÄTER.", Channel.WEBSITE, "COLD_ARCHIVE", "INSTITUTIONAL_COLDNESS", FragmentPlacement.OBJECT_ARCHIVE, 90],
    ["Archiv offen. Store geschlossen.", Channel.INSTAGRAM, "COLD_ARCHIVE", null, FragmentPlacement.CAPTION, 70],
    ["NO BRIGHT ROOM.", Channel.TIKTOK, "POST_CLUB_SILENCE", "BLACKOUT_SILENCE", FragmentPlacement.CHANNEL_COPY, 60],
    ["Evidence, not lifestyle.", Channel.SOUNDCLOUD, null, "INSTITUTIONAL_COLDNESS", FragmentPlacement.METADATA, 60]
  ] as const;

  await prisma.channelFragment.deleteMany({});

  for (const [fragmentContent, channel, campaignWorldCode, moodReferenceCode, placement, weight] of channelFragmentData) {
    const fragment = await prisma.fragment.findFirstOrThrow({ where: { content: fragmentContent } });

    await prisma.channelFragment.create({
      data: {
        active: true,
        campaignWorldId: campaignWorldCode ? campaignWorldIds[campaignWorldCode] : null,
        channel,
        fragmentId: fragment.id,
        moodReferenceId: moodReferenceCode ? moodReferenceIds[moodReferenceCode] : null,
        placement,
        weight
      }
    });
  }
}

type IdMapModel = "campaignWorld" | "visualEnvironment" | "moodReference" | "asset";

async function getIdMap(model: IdMapModel) {
  const records =
    model === "campaignWorld"
      ? await prisma.campaignWorld.findMany()
      : model === "visualEnvironment"
        ? await prisma.visualEnvironment.findMany()
        : model === "moodReference"
          ? await prisma.moodReference.findMany()
          : await prisma.asset.findMany();

  return Object.fromEntries(records.map((record) => [record.code, record.id]));
}

async function upsertArtistCampaignWorld(
  artistId: string,
  campaignWorldId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.artistCampaignWorld.upsert({
    where: { artistId_campaignWorldId: { artistId, campaignWorldId } },
    update: { reason, verdict, weight },
    create: { artistId, campaignWorldId, reason, verdict, weight }
  });
}

async function upsertMusicReleaseCampaignWorld(
  musicReleaseId: string,
  campaignWorldId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.musicReleaseCampaignWorld.upsert({
    where: { musicReleaseId_campaignWorldId: { campaignWorldId, musicReleaseId } },
    update: { reason, verdict, weight },
    create: { campaignWorldId, musicReleaseId, reason, verdict, weight }
  });
}

async function upsertTrackMoodReference(
  trackId: string,
  moodReferenceId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.trackMoodReference.upsert({
    where: { trackId_moodReferenceId: { moodReferenceId, trackId } },
    update: { reason, verdict, weight },
    create: { moodReferenceId, reason, trackId, verdict, weight }
  });
}

async function upsertCampaignWorldVisualEnvironment(
  campaignWorldId: string,
  visualEnvironmentId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.campaignWorldVisualEnvironment.upsert({
    where: { campaignWorldId_visualEnvironmentId: { campaignWorldId, visualEnvironmentId } },
    update: { reason, verdict, weight },
    create: { campaignWorldId, reason, verdict, visualEnvironmentId, weight }
  });
}

async function upsertCampaignWorldMoodReference(
  campaignWorldId: string,
  moodReferenceId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.campaignWorldMoodReference.upsert({
    where: { campaignWorldId_moodReferenceId: { campaignWorldId, moodReferenceId } },
    update: { reason, verdict, weight },
    create: { campaignWorldId, moodReferenceId, reason, verdict, weight }
  });
}

async function upsertCampaignWorldAsset(
  campaignWorldId: string,
  assetId: string,
  verdict: CompatibilityVerdict,
  reason: string,
  weight: number
) {
  await prisma.campaignWorldAsset.upsert({
    where: { campaignWorldId_assetId: { assetId, campaignWorldId } },
    update: { reason, verdict, weight },
    create: { assetId, campaignWorldId, reason, verdict, weight }
  });
}

async function seedReviewItems() {
  const ropemaster = await prisma.musicRelease.findUniqueOrThrow({
    where: { releaseCode: "SKM-003" }
  });
  const coldArchive = await prisma.campaignWorld.findUniqueOrThrow({
    where: { code: "COLD_ARCHIVE" }
  });

  const moodboardReview = await prisma.reviewItem.upsert({
    where: { reviewKey: "SKR-MOODBOARD-SKM-003" },
    update: {
      musicReleaseId: ropemaster.id,
      stage: ReviewStage.MOODBOARD_REVIEW,
      status: ReviewStatus.PENDING,
      subjectKey: ropemaster.releaseCode,
      subjectType: ReviewSubjectType.MUSIC_RELEASE,
      summary: "Moodboard review shell for ROPEMASTER. No generation or approval execution exists yet.",
      title: "ROPEMASTER moodboard review"
    },
    create: {
      musicReleaseId: ropemaster.id,
      reviewKey: "SKR-MOODBOARD-SKM-003",
      stage: ReviewStage.MOODBOARD_REVIEW,
      status: ReviewStatus.PENDING,
      subjectKey: ropemaster.releaseCode,
      subjectType: ReviewSubjectType.MUSIC_RELEASE,
      summary: "Moodboard review shell for ROPEMASTER. No generation or approval execution exists yet.",
      title: "ROPEMASTER moodboard review"
    }
  });

  await ensureRuleViolation({
    detail: "Ropeface must remain an archival artist stamp and cannot become the hero identity for this review.",
    reviewItemId: moodboardReview.id,
    ruleCode: "VISUAL_ROPEFACE_SECONDARY",
    severity: RuleSeverity.WARNING,
    source: RuleViolationSource.VISUAL_RULE,
    title: "Ropeface hierarchy check"
  });
  await ensureApprovalComment(
    moodboardReview.id,
    "Seed review item only. Human approval will be added by a future authenticated workflow.",
    "SYSTEM_SEED"
  );

  const contentReview = await prisma.reviewItem.upsert({
    where: { reviewKey: "SKR-CONTENT-COLD-ARCHIVE" },
    update: {
      campaignWorldId: coldArchive.id,
      stage: ReviewStage.CONTENT_REVIEW,
      status: ReviewStatus.NEEDS_REVISION,
      subjectKey: coldArchive.code,
      subjectType: ReviewSubjectType.CAMPAIGN_WORLD,
      summary: "Content review shell for COLD_ARCHIVE. Stores review intent only.",
      title: "COLD_ARCHIVE content review"
    },
    create: {
      campaignWorldId: coldArchive.id,
      reviewKey: "SKR-CONTENT-COLD-ARCHIVE",
      stage: ReviewStage.CONTENT_REVIEW,
      status: ReviewStatus.NEEDS_REVISION,
      subjectKey: coldArchive.code,
      subjectType: ReviewSubjectType.CAMPAIGN_WORLD,
      summary: "Content review shell for COLD_ARCHIVE. Stores review intent only.",
      title: "COLD_ARCHIVE content review"
    }
  });

  await ensureRuleViolation({
    detail: "Archive content must keep radical reduction and avoid adding motifs just because they are available.",
    reviewItemId: contentReview.id,
    ruleCode: "CORE_RADICAL_REDUCTION",
    severity: RuleSeverity.REQUIRED,
    source: RuleViolationSource.BRAND_RULE,
    title: "Radical reduction required"
  });
  await ensureApprovalComment(
    contentReview.id,
    "Needs revision is represented as current materialized status; decision history remains append-only.",
    "SYSTEM_SEED"
  );
  await ensureApprovalDecision({
    decidedBy: "SYSTEM_SEED",
    note: "Seeded historical decision to demonstrate append-only review history.",
    reviewItemId: contentReview.id,
    type: DecisionType.REQUEST_REVISION
  });
}

type RuleViolationSeed = Readonly<{
  detail: string;
  reviewItemId: string;
  ruleCode: string;
  severity: RuleSeverity;
  source: RuleViolationSource;
  title: string;
}>;

async function ensureRuleViolation(seed: RuleViolationSeed) {
  const existing = await prisma.ruleViolation.findFirst({
    where: {
      reviewItemId: seed.reviewItemId,
      ruleCode: seed.ruleCode,
      source: seed.source,
      title: seed.title
    }
  });

  if (existing) {
    await prisma.ruleViolation.update({
      where: { id: existing.id },
      data: {
        active: true,
        detail: seed.detail,
        severity: seed.severity
      }
    });
    return;
  }

  await prisma.ruleViolation.create({
    data: {
      active: true,
      detail: seed.detail,
      reviewItemId: seed.reviewItemId,
      ruleCode: seed.ruleCode,
      severity: seed.severity,
      source: seed.source,
      title: seed.title
    }
  });
}

async function ensureApprovalComment(reviewItemId: string, body: string, author: string) {
  const existing = await prisma.approvalComment.findFirst({
    where: {
      author,
      body,
      reviewItemId
    }
  });

  if (existing) {
    return;
  }

  await prisma.approvalComment.create({
    data: {
      author,
      body,
      reviewItemId
    }
  });
}

type ApprovalDecisionSeed = Readonly<{
  decidedBy: string;
  note: string;
  reviewItemId: string;
  type: DecisionType;
}>;

async function ensureApprovalDecision(seed: ApprovalDecisionSeed) {
  const existing = await prisma.approvalDecision.findFirst({
    where: {
      decidedBy: seed.decidedBy,
      note: seed.note,
      reviewItemId: seed.reviewItemId,
      type: seed.type
    }
  });

  if (existing) {
    return;
  }

  await prisma.approvalDecision.create({
    data: seed
  });
}

async function main() {
  const artist = await seedArtist();

  await seedMusicReleases(artist.id);
  await seedObjectReleases(artist.id);
  await seedFragments();
  await seedBrandRules();
  await seedVisualRules();
  await seedLanguageRules();
  await seedForbiddenEnergy();
  await seedVoiceProfiles();
  await seedAudiencePersonas();
  await seedChannelRules();
  await seedSignalScoringRules();
  await seedCampaignWorlds();
  await seedVisualEnvironments();
  await seedMoodReferences();
  await seedAssets();
  await seedAssetTags();
  await seedAssetTagAssignments();
  await seedCompatibilityGraph(artist.id);
  await seedReleaseFragments();
  await seedChannelFragments();
  await seedReviewItems();
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
