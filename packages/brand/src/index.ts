export const masterbrand = "SCHLUESSELKINDER" as const;

export const firstArtist = {
  name: "SHIBARI KAWAII",
  slug: "shibari-kawaii",
  role: "first artist",
  location: "Berlin afterhours",
  archiveCode: "SK-A001",
  fragments: {
    de: ["Kalte Nähe.", "Keine Biografie. Nur Druck.", "Nacht bleibt Material."],
    en: ["Cold intimacy.", "Body as signal.", "Sound after the room empties."]
  },
  tracks: [
    {
      title: "D-DATE",
      code: "SND-001",
      mood: "static pulse",
      duration: "3:28",
      platform: "SoundCloud",
      status: "ARCHIVE SIGNAL",
      soundCloudUrl: "https://soundcloud.com/thomas-frerich-681624781/d-date-shibari-kawaii",
      fragment: {
        de: "Datum ohne Morgen.",
        en: "Date without morning."
      }
    },
    {
      title: "ROPEMASTER",
      code: "SND-002",
      mood: "concrete dawn",
      duration: "4:08",
      platform: "SoundCloud",
      status: "ARCHIVE SIGNAL",
      soundCloudUrl: "https://soundcloud.com/thomas-frerich-681624781/ropemaster-shibari-kawaii-1",
      fragment: {
        de: "Kontrolle ohne Wärme.",
        en: "Control without warmth."
      }
    },
    {
      title: "PICK ME",
      code: "SND-003",
      mood: "ritual force",
      duration: "3:57",
      platform: "SoundCloud",
      status: "ARCHIVE SIGNAL",
      soundCloudUrl: "https://soundcloud.com/thomas-frerich-681624781/pick-me-shibari-kawaii",
      fragment: {
        de: "Ein heller Griff im dunklen Raum.",
        en: "A bright hand in a dark room."
      }
    }
  ]
} as const;

export const platformPlan = {
  backendHost: "Hetzner later",
  dns: "IONOS DNS",
  fulfillment: "Printful later",
  payments: "Stripe later",
  shopify: false
} as const;

export const seedCopy = {
  shortDescription: "Music, garments, residue.",
  hero: {
    de: "NACHT BLEIBT MATERIAL.",
    en: "NO BRIGHT ROOM."
  },
  systemFragments: {
    afterhours: "Afterhours is a method.",
    evidence: "Evidence, not lifestyle.",
    noSoftBiography: "No soft biography.",
    roomTone: "Der Raum ist leer. Der Ton bleibt."
  },
  campaign: {
    de: "Beton hält den Ton.",
    en: "Concrete keeps the sound."
  },
  collective: [
    {
      de: "Ein Label für die Nacht nach der Nacht.",
      en: "A label for the night after the night."
    },
    {
      de: "Songs zuerst. Objekte später.",
      en: "Songs first. Objects later."
    },
    {
      de: "Berlin concrete. Rope memory. Red light held back.",
      en: "Berlin concrete. Rope memory. Red light held back."
    }
  ],
  musicSignal: {
    de: "Drei Signale im Raum.",
    en: "Three signals in the room."
  },
  shopSignal: {
    de: "Archiv offen. Store geschlossen.",
    en: "SIGNAL ZUERST. WARE SPÄTER."
  },
  shopArchive: {
    de: "Kalte Formen. Späte Materialien.",
    en: "Future object system."
  },
  about: [
    {
      de: "SCHLUESSELKINDER ist ein kalter Raum für Musik, Kleidung und Restspuren.",
      en: "SCHLUESSELKINDER is a cold room for music, clothing, and residue."
    },
    {
      de: "Nicht laut. Nicht sauber. Nicht für Tageslicht gebaut.",
      en: "Not loud. Not clean. Not built for daylight."
    },
    {
      de: "Wir behandeln Releases wie Rituale und Kleidung wie Beweise.",
      en: "We treat releases like rituals and garments like evidence."
    }
  ],
  shopPreview: [
    {
      label: "garment study",
      de: "Schwarz. Schwer. Spät.",
      en: "Black. Heavy. Late."
    },
    {
      label: "object study",
      de: "Metall, Papier, Druck.",
      en: "Metal, paper, pressure."
    },
    {
      label: "signal study",
      de: "Erst Signal. Dann Ware.",
      en: "Signal first. Product later."
    }
  ],
  commerceBoundary: ["NO CART.", "NO STOCK.", "NO TRANSACTION."],
  manifesto: [
    "NO BRIGHT ROOM.",
    "NACHT BLEIBT MATERIAL.",
    "MUSIC, GARMENTS, RESIDUE.",
    "AFTERHOURS IS A METHOD."
  ]
} as const;

export const theKeyTool = {
  name: "THE KEY",
  code: "SK-T001",
  role: "system tool",
  platform: "iOS",
  status: "APP REVIEW",
  surfaceUrl: "https://antisobersoberclub.de",
  surfaceLabel: "ANTISOBERSOBERCLUB",
  toggle: "CLUB AN. / CLUB AUS.",
  lines: [
    {
      de: "Ein Werkzeug für sichere Nächte.",
      en: "A tool for safer raves."
    },
    {
      de: "Wasser. Pausen. Crew. Heimweg.",
      en: "Water. Breaks. Crew. The way home."
    },
    {
      de: "Kein Lifestyle. Ein Protokoll.",
      en: "Not a lifestyle. A protocol."
    }
  ],
  signals: [
    {
      code: "KEY-01",
      title: "PLAN",
      de: "Die Nacht beginnt vor der Tür.",
      en: "The night starts before the door."
    },
    {
      code: "KEY-02",
      title: "LIVE",
      de: "Der Raum hält den Takt.",
      en: "The room keeps the pulse."
    },
    {
      code: "KEY-03",
      title: "CREW",
      de: "Niemand geht allein.",
      en: "No one walks alone."
    },
    {
      code: "KEY-04",
      title: "HEIMWEG",
      de: "Die Nacht endet erst zuhause.",
      en: "The night ends at home."
    }
  ]
} as const;

export const brandAssets = {
  campaignDungeonChair: "/brand/campaign-dungeon-chair.png",
  posterEin: "/brand/poster-ein.png",
  runeKeyMark: "/brand/rune-key-mark.png",
  shibariKawaiiRopeface: "/brand/shibari-kawaii-ropeface.png",
  shibariKawaiiSymbolCard: "/brand/shibari-kawaii-symbol-card.jpeg",
  symbolEyeKey: "/brand/symbol-eye-key.png"
} as const;

export type TrackTitle = (typeof firstArtist.tracks)[number]["title"];
