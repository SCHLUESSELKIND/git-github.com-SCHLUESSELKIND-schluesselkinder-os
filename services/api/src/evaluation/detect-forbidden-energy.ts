import type { EvaluationFinding, EvaluationTextInput, ForbiddenEnergyInput } from "./types.js";

const operationalTerms: Record<string, string[]> = {
  AI_MOODBOARD: ["ai moodboard", "dreamcore", "midjourney", "moodboard collage", "prompt aesthetic"],
  CYBERPUNK_OVERLOAD: ["cyberpunk", "neon gradient", "neon glow", "glowing neon", "dystopia"],
  FETISH_DECORATION: ["fetish", "bdsm", "kink", "bondage spectacle"],
  HORROR: ["horror", "creepy", "doll", "voodoo", "blood", "dark-art", "slasher"],
  LIFESTYLE_CLICHE: ["lifestyle", "must-have", "trend", "fit check", "elevate your"],
  MEME_IRONY: ["meme", "lol", "it's giving", "based", "vibes only"],
  SHOPIFY_MERCH: ["shop now", "buy now", "add to cart", "checkout", "stock", "merch drop", "limited drop"],
  STARTUP_SAAS: ["startup", "saas", "growth hack", "join us", "discover", "unlock", "community platform"]
};

type DetectForbiddenEnergyInput = Readonly<{
  forbiddenEnergy: ForbiddenEnergyInput[];
  text: EvaluationTextInput;
}>;

export function detectForbiddenEnergy(input: DetectForbiddenEnergyInput): EvaluationFinding[] {
  const normalizedText = normalize(input.text.body.join(" "));

  return input.forbiddenEnergy.flatMap((energy) => {
    const terms = [...(operationalTerms[energy.code] ?? []), energy.label].map(normalize).filter(Boolean);
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
