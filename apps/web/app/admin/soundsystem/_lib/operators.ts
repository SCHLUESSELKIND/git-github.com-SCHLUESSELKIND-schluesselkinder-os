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

export type CommandIntentState = "awaiting_wire" | "ready";

export type CommandIntent = {
  readonly code: string;
  readonly title: string;
  readonly slug: string;
  readonly summary: string;
  readonly engineHint: string;
  readonly state: CommandIntentState;
  readonly targetPath?: string;
};

export const COMMAND_INTENTS: readonly CommandIntent[] = [
  {
    code: "CREATE_TRACK",
    title: "Create Track",
    slug: "music-router",
    summary: "Intent-driven music generation via auto router. All six music intents route through the mock provider.",
    engineHint: "AUTO ROUTER · mock adapters",
    state: "ready",
    targetPath: "/admin/soundsystem/music-router"
  },
  {
    code: "BUILD_RIDDIM",
    title: "Build Riddim",
    slug: "build-riddim",
    summary: "Loop-first drum and bass bed for later vocal overlay.",
    engineHint: "ACE-Step primary · Stable Audio Open layers",
    state: "awaiting_wire"
  },
  {
    code: "GENERATE_HOOK",
    title: "Generate Hook",
    slug: "generate-hook",
    summary: "Short repeatable mantra fragment for ritual anchor.",
    engineHint: "ACE-Step primary · YuE secondary",
    state: "awaiting_wire"
  },
  {
    code: "STEM_REMIX",
    title: "Stem Remix",
    slug: "stems",
    summary: "Repaint or recompose existing stems with controlled drift.",
    engineHint: "ACE-Step cover · Demucs separation",
    state: "awaiting_wire"
  },
  {
    code: "DUB_FX_LAB",
    title: "Dub FX Lab",
    slug: "dub-fx-lab",
    summary: "Delay trails, tape echoes, empty-room haze.",
    engineHint: "Stable Audio Open primary · ACE-Step lego",
    state: "awaiting_wire"
  },
  {
    code: "STYLE_DNA_SYSTEM",
    title: "Style DNA",
    slug: "style-dna",
    summary: "Adapter and embedding profile management.",
    engineHint: "ACE-Step LoRA · embedding profile",
    state: "awaiting_wire"
  },
  {
    code: "WRITE_LYRICS",
    title: "Write Lyrics",
    slug: "lyrics",
    summary: "Generate, edit, lock, and version SoundGraph-ready lyrics. Mock provider · GPT-5.5 boundary reserved.",
    engineHint: "MOCK provider · session-scoped store",
    state: "ready",
    targetPath: "/admin/soundsystem/lyrics"
  },
  {
    code: "CHARACTER_VOICE",
    title: "Voice Lab",
    slug: "voice-lab",
    summary: "Create voice tags, spoken vocals, voice converts. Consent-gated — every job must cite a non-revoked consent record.",
    engineHint: "MOCK provider · consent preflight",
    state: "ready",
    targetPath: "/admin/soundsystem/voice-lab"
  },
  {
    code: "PROJECT_LIBRARY",
    title: "Library",
    slug: "library",
    summary: "Browse exported project packs. Each pack bundles a music job with its lyrics, arrangement, artifacts, and provenance chain.",
    engineHint: "IN-MEMORY · export packs",
    state: "ready",
    targetPath: "/admin/soundsystem/library"
  },
  {
    code: "RELEASE_CENTER",
    title: "Releases",
    slug: "releases",
    summary: "Release center. Inspect, verify, and mark release packs ready for distribution. Compliance checklist, social copy, assets, Dropbox target.",
    engineHint: "DUAL-MODE · in_memory / postgres",
    state: "ready",
    targetPath: "/admin/soundsystem/releases"
  },
  {
    code: "ARTIFACT_LIBRARY",
    title: "Artifacts",
    slug: "artifacts",
    summary: "Artifact storage inspector. Browse, inspect, and download stored artifacts. Metadata registry with signed URL policy.",
    engineHint: "DUAL-MODE · in_memory / postgres",
    state: "ready",
    targetPath: "/admin/soundsystem/artifacts"
  },
  {
    code: "CAMPAIGNS",
    title: "Campaigns",
    slug: "campaigns",
    summary: "Campaign timeline. View release operations by channel and status. Task lanes, warnings, and timeline feed. Calendar view only — no automation executed.",
    engineHint: "IN-MEMORY · read-model",
    state: "ready",
    targetPath: "/admin/soundsystem/campaigns"
  },
  {
    code: "COMMAND_CENTER",
    title: "Command Center",
    slug: "command-center",
    summary: "Release-to-Campaign orchestration. Aggregates readiness across release, campaign, automation, merch, distribution, vinyl. Bootstraps campaign + recommended templates in one action. No execution.",
    engineHint: "IN-MEMORY · orchestration surface",
    state: "ready",
    targetPath: "/admin/soundsystem/command-center"
  },
  {
    code: "COMMERCE_SYNC",
    title: "Commerce Sync",
    slug: "commerce-sync",
    summary: "Unified Shopify + Printful operator dashboard. One capsule, one screen — provider mode badges, sync state, draft/sync IDs, Sync Shopify / Sync Printful / Sync Both. Draft/sync products only — no publishing.",
    engineHint: "OPERATOR-TRIGGERED · draft/sync products only",
    state: "ready",
    targetPath: "/admin/soundsystem/commerce-sync"
  },
  {
    code: "INTELLIGENCE",
    title: "Intelligence",
    slug: "intelligence",
    summary: "Analytics event graph. Unified internal metrics across streaming, social, commerce, and campaigns. No provider API calls — internal schema only.",
    engineHint: "IN-MEMORY · event graph",
    state: "ready",
    targetPath: "/admin/soundsystem/intelligence"
  },
  {
    code: "CONNECTORS",
    title: "Connectors",
    slug: "connectors",
    summary: "Provider connector framework. Unified adapter registry for all provider boundaries. Health, capabilities, sync preview. No real API calls — contract layer only.",
    engineHint: "IN-MEMORY · adapter registry",
    state: "ready",
    targetPath: "/admin/soundsystem/connectors"
  }
] as const;

export function intentHref(intent: CommandIntent): string {
  return intent.targetPath ?? `/admin/soundsystem/${intent.slug}`;
}

// Re-exported for compatibility with existing imports. The single source of
// truth for the admin gate lives in `app/admin/_lib/admin-gate.ts`.
export { isInternalConsoleEnabled } from "../../_lib/admin-gate";
