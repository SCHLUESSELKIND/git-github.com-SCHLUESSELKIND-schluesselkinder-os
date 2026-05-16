export type OperatorMode = "blackout" | "mint-signal" | "redline";

export const DEFAULT_OPERATOR_MODE: OperatorMode = "blackout";

export const OPERATOR_MODE_STORAGE_KEY = "snuffraga.operator-mode";

export type OperatorModeDescriptor = {
  readonly value: OperatorMode;
  readonly label: string;
  readonly hint: string;
};

export const OPERATOR_MODES: readonly OperatorModeDescriptor[] = [
  { value: "blackout", label: "BLACKOUT", hint: "default · steady" },
  { value: "mint-signal", label: "MINT SIGNAL", hint: "active monitor" },
  { value: "redline", label: "REDLINE", hint: "halt review" }
] as const;

export function isOperatorMode(value: unknown): value is OperatorMode {
  return value === "blackout" || value === "mint-signal" || value === "redline";
}

export type CommandIntent = {
  readonly code: string;
  readonly title: string;
  readonly slug: string;
  readonly summary: string;
  readonly engineHint: string;
};

export const COMMAND_INTENTS: readonly CommandIntent[] = [
  {
    code: "CREATE_TRACK",
    title: "Create Track",
    slug: "create",
    summary: "Compile prompt, queue full-mix generation, stage stems.",
    engineHint: "ACE-Step primary · YuE secondary"
  },
  {
    code: "BUILD_RIDDIM",
    title: "Build Riddim",
    slug: "build-riddim",
    summary: "Loop-first drum and bass bed for later vocal overlay.",
    engineHint: "ACE-Step primary · Stable Audio Open layers"
  },
  {
    code: "GENERATE_HOOK",
    title: "Generate Hook",
    slug: "generate-hook",
    summary: "Short repeatable mantra fragment for ritual anchor.",
    engineHint: "ACE-Step primary · YuE secondary"
  },
  {
    code: "STEM_REMIX",
    title: "Stem Remix",
    slug: "stems",
    summary: "Repaint or recompose existing stems with controlled drift.",
    engineHint: "ACE-Step cover · Demucs separation"
  },
  {
    code: "DUB_FX_LAB",
    title: "Dub FX Lab",
    slug: "dub-fx-lab",
    summary: "Delay trails, tape echoes, empty-room haze.",
    engineHint: "Stable Audio Open primary · ACE-Step lego"
  },
  {
    code: "STYLE_DNA_SYSTEM",
    title: "Style DNA",
    slug: "style-dna",
    summary: "Adapter and embedding profile management.",
    engineHint: "ACE-Step LoRA · embedding profile"
  }
] as const;

export function isInternalConsoleEnabled(): boolean {
  return process.env.NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED === "true";
}
