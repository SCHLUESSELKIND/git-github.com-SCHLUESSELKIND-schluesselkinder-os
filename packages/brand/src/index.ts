export const masterbrand = "SCHLUESSELKINDER" as const;

export const firstArtist = {
  name: "SHIBARI KAWAII",
  tracks: ["PICK ME UP", "TUESDAY MORNING COMEDOWN", "ROPEMASTER"]
} as const;

export const platformPlan = {
  backendHost: "Hetzner later",
  dns: "IONOS DNS",
  fulfillment: "Printful later",
  payments: "Stripe later",
  shopify: false
} as const;

export const seedCopy = {
  shortDescription:
    "A direct home for SCHLUESSELKINDER releases, artist commerce, and operations."
} as const;

export type TrackTitle = (typeof firstArtist.tracks)[number];
