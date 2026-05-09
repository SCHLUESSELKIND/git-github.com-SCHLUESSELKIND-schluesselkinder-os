import {
  ArtistStatus,
  Channel,
  FragmentType,
  PrismaClient,
  ReleaseStatus,
  RuleCategory,
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
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
