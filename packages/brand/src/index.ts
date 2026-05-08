export const masterbrand = "SCHLUESSELKINDER" as const;

export const firstArtist = {
  name: "SHIBARI KAWAII",
  slug: "shibari-kawaii",
  role: "first artist",
  location: "Berlin afterhours",
  archiveCode: "SK-A001",
  fragments: {
    de: ["Kalte Nähe.", "Rope pressure.", "Nacht bleibt Material."],
    en: ["Cold intimacy.", "Body as signal.", "Sound after the room empties."]
  },
  tracks: [
    {
      title: "PICK ME UP",
      code: "SK-001",
      mood: "static pulse",
      fragment: {
        de: "Ein heller Griff im dunklen Raum.",
        en: "A bright hand in a dark room."
      }
    },
    {
      title: "TUESDAY MORNING COMEDOWN",
      code: "SK-002",
      mood: "concrete dawn",
      fragment: {
        de: "Beton, Kaffee, Restlicht.",
        en: "Concrete, coffee, remaining light."
      }
    },
    {
      title: "ROPEMASTER",
      code: "SK-003",
      mood: "ritual force",
      fragment: {
        de: "Kontrolle ohne Wärme.",
        en: "Control without warmth."
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
    de: "Keine helle Stunde.",
    en: "No bright room."
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
    de: "Drei Stücke. Kein Versprechen.",
    en: "Three tracks. No promise."
  },
  shopSignal: {
    de: "Kein Store. Ein Zeichen.",
    en: "Not a store. A signal."
  },
  shopArchive: {
    de: "Kalte Formen. Späte Materialien. Noch geschlossen.",
    en: "Cold forms. Late materials. Still closed."
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
      label: "drop study",
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

export const brandAssets = {
  campaignDungeonChair: "/brand/campaign-dungeon-chair.png",
  posterEin: "/brand/poster-ein.png",
  runeKeyMark: "/brand/rune-key-mark.png",
  shibariKawaiiRopeface: "/brand/shibari-kawaii-ropeface.png",
  shibariKawaiiSymbolCard: "/brand/shibari-kawaii-symbol-card.jpeg",
  symbolEyeKey: "/brand/symbol-eye-key.png"
} as const;

export type TrackTitle = (typeof firstArtist.tracks)[number]["title"];
