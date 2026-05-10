import type { EvaluationFinding, EvaluationTextInput, ForbiddenEnergyInput } from "./types.js";

export const forbiddenEnergyOperationalTerms: Record<string, string[]> = {
  AI_MOODBOARD: ["ai moodboard", "dreamcore", "midjourney", "moodboard collage", "prompt aesthetic"],
  CYBERPUNK_OVERLOAD: ["cyberpunk", "neon gradient", "neon glow", "glowing neon", "dystopia"],
  FAKE_LUXURY: ["luxury flex", "premium lifestyle", "exclusive lifestyle", "status symbol", "elevated luxury"],
  FETISH_DECORATION: ["fetish", "bdsm", "kink", "bondage spectacle"],
  HORROR: ["horror", "creepy", "doll", "voodoo", "blood", "dark-art", "slasher"],
  HYPE_LANGUAGE: ["hype", "insane drop", "must cop", "go viral", "next big thing"],
  ARCHIVE_INCOHERENCE: ["random capsule", "assorted vibes", "mixed aesthetic", "everything collection"],
  CREATOR_ECONOMY_LANGUAGE: ["creator", "content creator", "build your audience", "personal brand", "monetize"],
  EXCESSIVE_EXPLANATION: ["what this means is", "in other words", "let us explain", "this campaign is about"],
  LIFESTYLE_CLICHE: ["lifestyle", "must-have", "trend", "fit check", "elevate your"],
  MEME_IRONY: ["meme", "lol", "it's giving", "based", "vibes only"],
  MOTIVATIONAL_FASHION: ["be your best self", "empower your style", "dress for success", "confidence boost"],
  OVER_LOGOING: ["oversized logo", "logo wall", "repeat the logo", "logo everywhere", "all-over logo"],
  ROPEFACE_DOMINANCE: ["ropeface as masterbrand", "ropeface hero logo", "ropeface institutional mark"],
  SHOPIFY_MERCH: ["shop now", "buy now", "add to cart", "checkout", "stock", "merch drop", "limited drop"],
  STARTUP_SAAS: ["startup", "saas", "growth hack", "join us", "discover", "unlock", "community platform"],
  TIKTOK_BAIT: ["tiktok bait", "watch till the end", "wait for it", "pov:", "viral sound"],
  TREND_CHASING: ["trend alert", "trending now", "viral trend", "current trend", "algorithm trend"]
};

type DetectForbiddenEnergyInput = Readonly<{
  forbiddenEnergy: ForbiddenEnergyInput[];
  text: EvaluationTextInput;
}>;

export function detectForbiddenEnergy(input: DetectForbiddenEnergyInput): EvaluationFinding[] {
  const normalizedText = normalize(input.text.body.join(" "));

  return input.forbiddenEnergy.flatMap((energy) => {
    const terms = [...(forbiddenEnergyOperationalTerms[energy.code] ?? []), energy.label].map(normalize).filter(Boolean);
    const matchedTerm = terms.find((term) => normalizedText.includes(term));

    if (!matchedTerm) {
      return [];
    }

    return [
      {
        code: `FORBIDDEN_ENERGY_${energy.code}`,
        detail: `Matched forbidden term "${matchedTerm}" for ${energy.code}. ${energy.reason}`,
        ruleCode: energy.code,
        severity: "BLOCKER" as const,
        source: "FORBIDDEN_ENERGY" as const,
        title: `Forbidden energy detected: ${energy.label}`
      }
    ];
  });
}

function normalize(value: string): string {
  return value.toLowerCase().replace(/\s+/g, " ").trim();
}
