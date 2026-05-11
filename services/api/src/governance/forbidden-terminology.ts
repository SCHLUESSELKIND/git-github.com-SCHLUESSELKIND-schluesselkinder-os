export const protectedRuntimeRoots = [
  "services/api/src/contracts",
  "services/api/src/routes",
  "services/api/src/drafts",
  "services/api/src/exports"
] as const;

export const protectedRuntimeExclusions = [
  ".test.ts",
  "services/api/src/routes/mappers.ts"
] as const;

export const allowedNegativeControls = [
  "approvalAuthority: false",
  "approvalAuthority: z.literal(false)",
  "automationAllowed: false",
  "automationAllowed: z.literal(false)",
  "distributionAuthority: false",
  "distributionAuthority: z.literal(false)",
  "externalDelivery: false",
  "externalDelivery: z.literal(false)",
  "publishAuthority: false",
  "publishAuthority: z.literal(false)",
  "publishReady: false",
  "publishReady: z.literal(false)",
  "reviewRequired: true",
  "reviewRequired: z.literal(true)",
  "usableWithoutReview: false"
] as const;

export const frozenRuntimeTerms = [
  join("pub", "lish"),
  join("de", "ploy"),
  join("la", "unch"),
  join("auto", "pilot"),
  join("growth", " engine"),
  join("engagement", " optimization"),
  join("campaign", " execution"),
  join("ready", "ToPost"),
  join("ready", "ToPublish"),
  join("sched", "uled"),
  join("distrib", "uted"),
  join("deliver", "able"),
  join("up", "loaded"),
  join("qu", "eued")
] as const;

export const hiddenDeliveryFieldTerms = [
  join("upload", "Target"),
  join("cdn", "Url"),
  join("storage", "Provider"),
  join("delivery", "Destination"),
  join("queue", "Id"),
  join("retry", "State"),
  join("platform", "Action"),
  join("file", "Path")
] as const;

export const providerDependencyTerms = [
  join("open", "ai"),
  join("anth", "ropic"),
  "replicate",
  "stability",
  "stripe",
  "printful",
  "tiktok",
  "instagram",
  "spotify",
  "soundcloud",
  "facebook"
] as const;

export const workerDependencyTerms = [
  "bullmq",
  "bull",
  "agenda",
  join("node", "-cron"),
  "inngest",
  "temporal",
  "qstash"
] as const;

export const storageDependencyTerms = [
  join("@aws", "-sdk"),
  join("aws", "-sdk"),
  "cloudinary",
  join("vercel", "/blob"),
  join("fire", "base")
] as const;

function join(left: string, right: string): string {
  return `${left}${right}`;
}
