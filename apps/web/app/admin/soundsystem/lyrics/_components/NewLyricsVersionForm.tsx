"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { createLyrics, type LyricsSectionType } from "../../_lib/inference";

type Props = Readonly<{
  defaultProjectKey?: string;
  projectKeyLocked?: boolean;
}>;

export function NewLyricsVersionForm({
  defaultProjectKey = "",
  projectKeyLocked = false
}: Props) {
  const router = useRouter();
  const [projectKey, setProjectKey] = useState(defaultProjectKey);
  const [prompt, setPrompt] = useState("");
  const [characterCode, setCharacterCode] = useState("SHIBARI_KAWAII");
  const [avoidIntroSinging, setAvoidIntroSinging] = useState(false);
  const [preserveRhyme, setPreserveRhyme] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const trimmedKey = projectKey.trim();
    const trimmedPrompt = prompt.trim();
    if (trimmedKey.length < 3) {
      setError("project_key must be at least 3 characters");
      return;
    }
    if (trimmedPrompt.length < 4) {
      setError("prompt must be at least 4 characters");
      return;
    }
    startTransition(async () => {
      try {
        const version = await createLyrics({
          project_key: trimmedKey,
          prompt: trimmedPrompt,
          character_code: characterCode.trim() || "SHIBARI_KAWAII",
          avoid_intro_singing: avoidIntroSinging,
          preserve_rhyme: preserveRhyme
        });
        router.push(
          `/admin/soundsystem/lyrics/${encodeURIComponent(trimmedKey)}/${version.version}`
        );
        router.refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : "inference_error");
      }
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="grid gap-4 border border-[color:var(--ss-border)] p-5"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        NEW LYRICS VERSION
      </p>
      <label className="grid gap-2">
        <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          PROJECT KEY
        </span>
        <input
          required
          minLength={3}
          maxLength={120}
          disabled={projectKeyLocked || isPending}
          value={projectKey}
          onChange={(event) => setProjectKey(event.target.value)}
          className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
          placeholder="snuffraga-warehouse-001"
        />
      </label>
      <label className="grid gap-2">
        <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          BRIEF (PROMPT)
        </span>
        <textarea
          required
          minLength={4}
          maxLength={4000}
          rows={5}
          disabled={isPending}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          placeholder="Cold afterhours signal. No bright room. Hold the pressure."
        />
      </label>
      <label className="grid gap-2">
        <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          CHARACTER CODE
        </span>
        <input
          maxLength={80}
          disabled={isPending}
          value={characterCode}
          onChange={(event) => setCharacterCode(event.target.value)}
          className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        />
      </label>
      <div className="flex flex-wrap items-center gap-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={avoidIntroSinging}
            onChange={(event) => setAvoidIntroSinging(event.target.checked)}
            disabled={isPending}
            className="h-4 w-4 accent-[color:var(--ss-accent)]"
          />
          <span>avoid intro singing</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={preserveRhyme}
            onChange={(event) => setPreserveRhyme(event.target.checked)}
            disabled={isPending}
            className="h-4 w-4 accent-[color:var(--ss-accent)]"
          />
          <span>preserve rhyme</span>
        </label>
      </div>
      {error !== null ? (
        <p
          className="border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={isPending}
        className="border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
        style={{ minHeight: "var(--ss-tap-target)" }}
      >
        {isPending ? "QUEUEING…" : "GENERATE"}
      </button>
    </form>
  );
}
