"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";
import {
  applySelectionRewrite,
  editLyrics,
  exportLyricsVersion,
  InferenceClientError,
  manualUpdateLyrics,
  rewriteLyricsSelection,
  toggleLyricsSectionLock,
  type LyricsExportManifest,
  type LyricsRewriteVariant,
  type LyricsSection,
  type LyricsSectionType,
  type LyricsVersion
} from "../../../../_lib/inference";
import { SoundGraphFlow } from "./SoundGraphFlow";

type Props = Readonly<{
  projectKey: string;
  version: LyricsVersion;
  allVersions: ReadonlyArray<LyricsVersion>;
}>;

const SECTION_TYPES: ReadonlyArray<LyricsSectionType> = [
  "instrumental_opening",
  "verse",
  "pre_chorus",
  "chorus",
  "bridge",
  "dub_breakdown",
  "outro"
];

export function LyricsEditor({ projectKey, version, allVersions }: Props) {
  const router = useRouter();
  const [editPrompt, setEditPrompt] = useState("");
  const [targetSection, setTargetSection] = useState<LyricsSectionType | "">("");
  const [targetSectionIndex, setTargetSectionIndex] = useState<string>("");
  const [preserveRhyme, setPreserveRhyme] = useState(true);
  const [exportManifest, setExportManifest] = useState<LyricsExportManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const [editingSection, setEditingSection] = useState<number | null>(null);
  const [draftLines, setDraftLines] = useState<string>("");

  const [rewriteTargetIndex, setRewriteTargetIndex] = useState<number | null>(null);
  const [rewritePrompt, setRewritePrompt] = useState<string>("");
  const [rewriteVariants, setRewriteVariants] = useState<ReadonlyArray<LyricsRewriteVariant>>([]);

  const sectionsByIndex = useMemo(() => {
    const map = new Map<number, LyricsSection>();
    for (const section of version.structure.sections) {
      map.set(section.index, section);
    }
    return map;
  }, [version]);

  const selectedSection =
    rewriteTargetIndex !== null ? sectionsByIndex.get(rewriteTargetIndex) ?? null : null;

  function navigateToVersion(versionNumber: number): void {
    router.push(
      `/admin/soundsystem/lyrics/${encodeURIComponent(projectKey)}/${versionNumber}`
    );
    router.refresh();
  }

  function refreshAfterMutation(next: LyricsVersion): void {
    navigateToVersion(next.version);
  }

  function handleEditSubmit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    setError(null);
    const trimmed = editPrompt.trim();
    if (trimmed.length < 2) {
      setError("edit_prompt must be at least 2 characters");
      return;
    }
    startTransition(async () => {
      try {
        const next = await editLyrics({
          version_id: version.id,
          edit_prompt: trimmed,
          target_section: targetSection !== "" ? targetSection : undefined,
          target_section_index:
            targetSectionIndex !== "" ? Number(targetSectionIndex) : undefined,
          preserve_rhyme: preserveRhyme
        });
        setEditPrompt("");
        setTargetSection("");
        setTargetSectionIndex("");
        refreshAfterMutation(next);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleLockToggle(sectionIndex: number, current: boolean): void {
    setError(null);
    startTransition(async () => {
      try {
        const next = await toggleLyricsSectionLock(
          version.id,
          sectionIndex,
          !current
        );
        refreshAfterMutation(next);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function beginManualEdit(section: LyricsSection): void {
    setEditingSection(section.index);
    setDraftLines(section.lines.map((line) => line.text).join("\n"));
  }

  function cancelManualEdit(): void {
    setEditingSection(null);
    setDraftLines("");
  }

  function handleManualSave(sectionIndex: number, lock: boolean): void {
    setError(null);
    const lines = draftLines
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    if (lines.length === 0) {
      setError("at least one non-empty line required");
      return;
    }
    startTransition(async () => {
      try {
        const next = await manualUpdateLyrics({
          version_id: version.id,
          section_index: sectionIndex,
          lines,
          lock
        });
        cancelManualEdit();
        refreshAfterMutation(next);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function useSectionAsSelection(section: LyricsSection): void {
    setRewriteTargetIndex(section.index);
    setRewritePrompt("");
    setRewriteVariants([]);
    setError(null);
  }

  function clearSelection(): void {
    setRewriteTargetIndex(null);
    setRewritePrompt("");
    setRewriteVariants([]);
  }

  function handleBuildVariants(): void {
    setError(null);
    if (selectedSection === null) {
      setError("No section selected. Use 'USE SECTION TEXT' beside a section.");
      return;
    }
    if (selectedSection.locked) {
      setError(`Section ${selectedSection.label} is locked. Unlock to rewrite.`);
      return;
    }
    if (selectedSection.lines.length === 0) {
      setError(`Section ${selectedSection.label} has no lines to rewrite.`);
      return;
    }
    const trimmed = rewritePrompt.trim();
    if (trimmed.length < 2) {
      setError("rewrite_prompt must be at least 2 characters");
      return;
    }
    startTransition(async () => {
      try {
        const response = await rewriteLyricsSelection({
          version_id: version.id,
          section_index: selectedSection.index,
          line_start_index: 0,
          line_end_index: selectedSection.lines.length - 1,
          rewrite_prompt: trimmed,
          variant_count: 5
        });
        setRewriteVariants(response.variants);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleApplyVariant(variant: LyricsRewriteVariant, lock: boolean): void {
    setError(null);
    if (selectedSection === null) {
      setError("No section selected.");
      return;
    }
    if (selectedSection.locked) {
      setError(`Section ${selectedSection.label} is locked. Unlock to rewrite.`);
      return;
    }
    const lines = variant.lines.map((line) => line.text);
    startTransition(async () => {
      try {
        const next = await applySelectionRewrite(version.id, {
          section_index: selectedSection.index,
          lines,
          lock,
          summary:
            variant.summary !== null
              ? `apply rewrite · ${variant.summary}`
              : `apply rewrite section ${selectedSection.index}`
        });
        clearSelection();
        refreshAfterMutation(next);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  function handleExport(): void {
    setError(null);
    startTransition(async () => {
      try {
        const manifest = await exportLyricsVersion(version.id);
        setExportManifest(manifest);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }

  return (
    <div className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] lg:grid-cols-[0.95fr_1.4fr_0.95fr]">
      <PromptColumn
        editPrompt={editPrompt}
        setEditPrompt={setEditPrompt}
        targetSection={targetSection}
        setTargetSection={setTargetSection}
        targetSectionIndex={targetSectionIndex}
        setTargetSectionIndex={setTargetSectionIndex}
        preserveRhyme={preserveRhyme}
        setPreserveRhyme={setPreserveRhyme}
        sections={version.structure.sections}
        onSubmit={handleEditSubmit}
        isPending={isPending}
        error={error}
        version={version}
        selectedSection={selectedSection}
        rewritePrompt={rewritePrompt}
        setRewritePrompt={setRewritePrompt}
        rewriteVariants={rewriteVariants}
        onBuildVariants={handleBuildVariants}
        onClearSelection={clearSelection}
        onApplyVariant={handleApplyVariant}
      />
      <SectionsColumn
        sections={version.structure.sections}
        editingSection={editingSection}
        draftLines={draftLines}
        setDraftLines={setDraftLines}
        onLockToggle={handleLockToggle}
        onBeginManual={beginManualEdit}
        onCancelManual={cancelManualEdit}
        onSaveManual={handleManualSave}
        rewriteTargetIndex={rewriteTargetIndex}
        onUseSectionAsSelection={useSectionAsSelection}
        isPending={isPending}
      />
      <VersionsColumn
        version={version}
        allVersions={allVersions}
        projectKey={projectKey}
        onSelectVersion={navigateToVersion}
        onExport={handleExport}
        exportManifest={exportManifest}
        isPending={isPending}
      />
    </div>
  );
}

function PromptColumn({
  editPrompt,
  setEditPrompt,
  targetSection,
  setTargetSection,
  targetSectionIndex,
  setTargetSectionIndex,
  preserveRhyme,
  setPreserveRhyme,
  sections,
  onSubmit,
  isPending,
  error,
  version,
  selectedSection,
  rewritePrompt,
  setRewritePrompt,
  rewriteVariants,
  onBuildVariants,
  onClearSelection,
  onApplyVariant
}: Readonly<{
  editPrompt: string;
  setEditPrompt: (value: string) => void;
  targetSection: LyricsSectionType | "";
  setTargetSection: (value: LyricsSectionType | "") => void;
  targetSectionIndex: string;
  setTargetSectionIndex: (value: string) => void;
  preserveRhyme: boolean;
  setPreserveRhyme: (value: boolean) => void;
  sections: ReadonlyArray<LyricsSection>;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  isPending: boolean;
  error: string | null;
  version: LyricsVersion;
  selectedSection: LyricsSection | null;
  rewritePrompt: string;
  setRewritePrompt: (value: string) => void;
  rewriteVariants: ReadonlyArray<LyricsRewriteVariant>;
  onBuildVariants: () => void;
  onClearSelection: () => void;
  onApplyVariant: (variant: LyricsRewriteVariant, lock: boolean) => void;
}>) {
  return (
    <div
      className="grid gap-6 p-5"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <form onSubmit={onSubmit} className="grid gap-4">
        <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          EDIT COMMAND
        </p>
        <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-secondary)]">
          Submit appends a new version. Locked sections are preserved byte-for-byte.
          Parent: v{version.version}.
        </p>
        <label className="grid gap-2">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            PROMPT
          </span>
          <textarea
            required
            minLength={2}
            maxLength={4000}
            rows={4}
            value={editPrompt}
            onChange={(event) => setEditPrompt(event.target.value)}
            disabled={isPending}
            className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            placeholder="Make the verse harder, more dub pressure."
          />
        </label>
        <label className="grid gap-2">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TARGET SECTION TYPE (optional)
          </span>
          <select
            value={targetSection}
            onChange={(event) => setTargetSection(event.target.value as LyricsSectionType | "")}
            disabled={isPending}
            className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm uppercase text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            <option value="">— any (mock regenerates everything not locked) —</option>
            {SECTION_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-2">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TARGET SECTION INDEX (optional)
          </span>
          <select
            value={targetSectionIndex}
            onChange={(event) => setTargetSectionIndex(event.target.value)}
            disabled={isPending}
            className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm uppercase text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            <option value="">— skip —</option>
            {sections.map((section) => (
              <option key={section.index} value={section.index}>
                [{section.index}] {section.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          <input
            type="checkbox"
            checked={preserveRhyme}
            onChange={(event) => setPreserveRhyme(event.target.checked)}
            disabled={isPending}
            className="h-4 w-4 accent-[color:var(--ss-accent)]"
          />
          <span>preserve rhyme</span>
        </label>
        <button
          type="submit"
          disabled={isPending}
          className="border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          {isPending ? "EDITING…" : "APPLY EDIT"}
        </button>
      </form>

      <SelectionRewritePanel
        selectedSection={selectedSection}
        rewritePrompt={rewritePrompt}
        setRewritePrompt={setRewritePrompt}
        rewriteVariants={rewriteVariants}
        onBuildVariants={onBuildVariants}
        onClearSelection={onClearSelection}
        onApplyVariant={onApplyVariant}
        isPending={isPending}
      />

      {error !== null ? (
        <p
          className="border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

function SelectionRewritePanel({
  selectedSection,
  rewritePrompt,
  setRewritePrompt,
  rewriteVariants,
  onBuildVariants,
  onClearSelection,
  onApplyVariant,
  isPending
}: Readonly<{
  selectedSection: LyricsSection | null;
  rewritePrompt: string;
  setRewritePrompt: (value: string) => void;
  rewriteVariants: ReadonlyArray<LyricsRewriteVariant>;
  onBuildVariants: () => void;
  onClearSelection: () => void;
  onApplyVariant: (variant: LyricsRewriteVariant, lock: boolean) => void;
  isPending: boolean;
}>) {
  return (
    <section
      aria-labelledby="selection-rewrite-heading"
      className="border border-[color:var(--ss-border-strong)]"
      style={{ backgroundColor: "var(--ss-panel-elevated)" }}
    >
      <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] px-4 py-3">
        <h2
          id="selection-rewrite-heading"
          className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]"
        >
          SELECTION REWRITE
        </h2>
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          MOCK · 5 VARIANTS
        </span>
      </header>
      <p className="border-b border-[color:var(--ss-border)] px-4 py-2 font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
        Variants are rotations of current lines (mock provider). Apply commits a new version.
      </p>
      <div className="grid gap-4 p-4">
        {selectedSection === null ? (
          <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
            No section selected. Click <strong className="text-[color:var(--ss-accent)]">USE SECTION TEXT</strong> beside a section in the center column.
          </p>
        ) : selectedSection.locked ? (
          <div className="grid gap-3">
            <p
              className="font-mono text-[0.62rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              [{selectedSection.index}] {selectedSection.label} · LOCKED
            </p>
            <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
              Locked sections cannot be rewritten. Unlock the section in the center
              column to continue.
            </p>
            <button
              type="button"
              onClick={onClearSelection}
              disabled={isPending}
              className="w-fit border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
              style={{ minHeight: "var(--ss-tap-target)" }}
            >
              CLEAR SELECTION
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-accent)]">
              SELECTED · [{selectedSection.index}] {selectedSection.label} · {selectedSection.lines.length} LINES
            </p>
            <ol
              className="grid gap-0.5 border border-[color:var(--ss-border)] p-2 font-mono text-[0.7rem] leading-5 text-[color:var(--ss-text-primary)]"
              style={{ backgroundColor: "var(--ss-panel)" }}
            >
              {selectedSection.lines.map((line) => (
                <li key={line.index} className="grid grid-cols-[1.6rem_1fr] gap-2">
                  <span className="text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                    {String(line.index).padStart(2, "0")}
                  </span>
                  <span className="break-words">{line.text}</span>
                </li>
              ))}
            </ol>
            <label className="grid gap-2">
              <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                REWRITE PROMPT
              </span>
              <input
                type="text"
                value={rewritePrompt}
                onChange={(event) => setRewritePrompt(event.target.value)}
                disabled={isPending}
                className="border border-[color:var(--ss-border-strong)] bg-transparent px-3 py-2 font-mono text-sm text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
                placeholder="Tighter phrasing, more pressure"
                style={{ minHeight: "var(--ss-tap-target)" }}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={onBuildVariants}
                disabled={isPending}
                className="border border-[color:var(--ss-border-accent)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
                style={{ minHeight: "var(--ss-tap-target)" }}
              >
                BUILD VARIANTS
              </button>
              <button
                type="button"
                onClick={onClearSelection}
                disabled={isPending}
                className="border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
                style={{ minHeight: "var(--ss-tap-target)" }}
              >
                CLEAR
              </button>
            </div>
            {rewriteVariants.length === 0 ? null : (
              <ul className="grid gap-3">
                {rewriteVariants.map((variant) => (
                  <li
                    key={variant.index}
                    className="grid gap-2 border border-[color:var(--ss-border-strong)] p-3"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <p className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      VARIANT {variant.index + 1}
                      {variant.summary !== null ? ` · ${variant.summary}` : " · rotation"}
                    </p>
                    <ol className="grid gap-0.5 font-mono text-[0.72rem] leading-5 text-[color:var(--ss-text-primary)]">
                      {variant.lines.map((line) => (
                        <li
                          key={line.index}
                          className="grid grid-cols-[1.6rem_1fr] gap-2"
                        >
                          <span className="text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                            {String(line.index).padStart(2, "0")}
                          </span>
                          <span className="break-words">{line.text}</span>
                        </li>
                      ))}
                    </ol>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => onApplyVariant(variant, false)}
                        disabled={isPending}
                        className="border border-[color:var(--ss-border-accent)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
                        style={{ minHeight: "var(--ss-tap-target)" }}
                      >
                        APPLY
                      </button>
                      <button
                        type="button"
                        onClick={() => onApplyVariant(variant, true)}
                        disabled={isPending}
                        className="border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.62rem] font-black uppercase tracking-widest hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
                        style={{
                          color: "var(--ss-warning)",
                          minHeight: "var(--ss-tap-target)"
                        }}
                      >
                        APPLY + LOCK
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function SectionsColumn({
  sections,
  editingSection,
  draftLines,
  setDraftLines,
  onLockToggle,
  onBeginManual,
  onCancelManual,
  onSaveManual,
  rewriteTargetIndex,
  onUseSectionAsSelection,
  isPending
}: Readonly<{
  sections: ReadonlyArray<LyricsSection>;
  editingSection: number | null;
  draftLines: string;
  setDraftLines: (value: string) => void;
  onLockToggle: (sectionIndex: number, current: boolean) => void;
  onBeginManual: (section: LyricsSection) => void;
  onCancelManual: () => void;
  onSaveManual: (sectionIndex: number, lock: boolean) => void;
  rewriteTargetIndex: number | null;
  onUseSectionAsSelection: (section: LyricsSection) => void;
  isPending: boolean;
}>) {
  return (
    <section
      className="grid gap-px overflow-y-auto"
      style={{ backgroundColor: "var(--ss-border)", maxHeight: "78vh" }}
      aria-label="Lyrics sections"
    >
      {sections.map((section) => {
        const isEditing = editingSection === section.index;
        const isSelectedForRewrite = rewriteTargetIndex === section.index;
        return (
          <article
            key={section.index}
            className="grid gap-3 p-5"
            style={{
              backgroundColor: isSelectedForRewrite
                ? "var(--ss-panel-elevated)"
                : "var(--ss-panel)",
              borderLeft: isSelectedForRewrite
                ? "2px solid var(--ss-accent)"
                : "2px solid transparent"
            }}
          >
            <header className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  [{section.index}]
                </span>
                <span className="font-mono text-[0.78rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                  {section.label}
                </span>
                <span
                  className="border px-2 py-0.5 font-mono text-[0.58rem] uppercase tracking-widest"
                  style={{
                    borderColor: "var(--ss-border-strong)",
                    color: "var(--ss-text-muted)"
                  }}
                >
                  {section.section_type}
                </span>
                <span
                  className="border px-2 py-0.5 font-mono text-[0.58rem] uppercase tracking-widest"
                  style={{
                    borderColor: "var(--ss-border-strong)",
                    color:
                      section.source === "user"
                        ? "var(--ss-accent)"
                        : "var(--ss-text-muted)"
                  }}
                >
                  source · {section.source}
                </span>
                {section.manually_edited ? (
                  <span
                    className="border px-2 py-0.5 font-mono text-[0.58rem] uppercase tracking-widest"
                    style={{
                      borderColor: "var(--ss-border-accent)",
                      color: "var(--ss-accent)"
                    }}
                  >
                    manual edit
                  </span>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => onLockToggle(section.index, section.locked)}
                  disabled={isPending}
                  className="border px-2 py-1 font-mono text-[0.6rem] font-black uppercase tracking-widest hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
                  style={{
                    borderColor: section.locked
                      ? "var(--ss-warning-dim)"
                      : "var(--ss-border-strong)",
                    color: section.locked ? "var(--ss-warning)" : "var(--ss-text-secondary)",
                    minHeight: "var(--ss-tap-target)"
                  }}
                  aria-pressed={section.locked}
                >
                  {section.locked ? "LOCKED · UNLOCK" : "LOCK"}
                </button>
                <button
                  type="button"
                  onClick={() => onBeginManual(section)}
                  disabled={isPending || isEditing}
                  className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] hover:text-[color:var(--ss-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
                  style={{ minHeight: "var(--ss-tap-target)" }}
                >
                  EDIT LINES
                </button>
                <button
                  type="button"
                  onClick={() => onUseSectionAsSelection(section)}
                  disabled={
                    isPending ||
                    isEditing ||
                    section.locked ||
                    section.lines.length === 0 ||
                    isSelectedForRewrite
                  }
                  className="border px-2 py-1 font-mono text-[0.6rem] font-black uppercase tracking-widest hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
                  style={{
                    borderColor: isSelectedForRewrite
                      ? "var(--ss-border-accent)"
                      : "var(--ss-border-strong)",
                    color: isSelectedForRewrite
                      ? "var(--ss-accent)"
                      : "var(--ss-text-secondary)",
                    minHeight: "var(--ss-tap-target)"
                  }}
                  title={
                    section.locked
                      ? "Locked sections cannot be rewritten"
                      : section.lines.length === 0
                        ? "Section has no lines"
                        : "Use this section text in the Selection Rewrite panel"
                  }
                >
                  {isSelectedForRewrite ? "SELECTED" : "USE SECTION TEXT"}
                </button>
              </div>
            </header>
            {isEditing ? (
              <div className="grid gap-3">
                <textarea
                  rows={Math.max(section.lines.length, 3)}
                  value={draftLines}
                  onChange={(event) => setDraftLines(event.target.value)}
                  disabled={isPending}
                  className="border border-[color:var(--ss-border-accent)] bg-transparent px-3 py-2 font-mono text-sm leading-6 text-[color:var(--ss-text-primary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
                />
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => onSaveManual(section.index, section.locked)}
                    disabled={isPending}
                    className="border border-[color:var(--ss-border-accent)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
                    style={{ minHeight: "var(--ss-tap-target)" }}
                  >
                    SAVE
                  </button>
                  <button
                    type="button"
                    onClick={() => onSaveManual(section.index, true)}
                    disabled={isPending}
                    className="border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
                    style={{ color: "var(--ss-warning)", minHeight: "var(--ss-tap-target)" }}
                  >
                    SAVE + LOCK
                  </button>
                  <button
                    type="button"
                    onClick={onCancelManual}
                    disabled={isPending}
                    className="border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
                    style={{ minHeight: "var(--ss-tap-target)" }}
                  >
                    CANCEL
                  </button>
                </div>
              </div>
            ) : (
              <ol className="grid gap-1 font-mono text-sm leading-6 text-[color:var(--ss-text-primary)]">
                {section.lines.map((line) => (
                  <li
                    key={line.index}
                    className="grid grid-cols-[2.5rem_1fr_auto] items-baseline gap-2"
                  >
                    <span className="text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      {String(line.index).padStart(2, "0")}
                    </span>
                    <span>{line.text}</span>
                    <span className="text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      {line.syllables !== null ? `${line.syllables}s` : ""}
                      {line.rhyme_group !== null ? ` · ${line.rhyme_group}` : ""}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </article>
        );
      })}
    </section>
  );
}

function VersionsColumn({
  version,
  allVersions,
  projectKey,
  onSelectVersion,
  onExport,
  exportManifest,
  isPending
}: Readonly<{
  version: LyricsVersion;
  allVersions: ReadonlyArray<LyricsVersion>;
  projectKey: string;
  onSelectVersion: (versionNumber: number) => void;
  onExport: () => void;
  exportManifest: LyricsExportManifest | null;
  isPending: boolean;
}>) {
  return (
    <aside
      className="grid gap-5 p-5"
      style={{ backgroundColor: "var(--ss-panel)" }}
      aria-label="Versions and export"
    >
      <section>
        <header className="mb-3 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-2">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            VERSIONS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {allVersions.length} ENTRIES
          </span>
        </header>
        <ul className="grid gap-px" style={{ backgroundColor: "var(--ss-border)" }}>
          {allVersions
            .slice()
            .reverse()
            .map((entry) => {
              const active = entry.id === version.id;
              return (
                <li key={entry.id}>
                  <button
                    type="button"
                    onClick={() => onSelectVersion(entry.version)}
                    disabled={isPending || active}
                    className="grid w-full grid-cols-[3rem_1fr] items-baseline gap-2 px-3 py-2 text-left font-mono text-[0.7rem] uppercase tracking-widest hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:cursor-default disabled:opacity-100"
                    style={{
                      backgroundColor: active
                        ? "var(--ss-panel-elevated)"
                        : "var(--ss-panel)",
                      color: active ? "var(--ss-accent)" : "var(--ss-text-secondary)",
                      minHeight: "var(--ss-tap-target)"
                    }}
                  >
                    <span>v{entry.version}</span>
                    <span className="text-[0.6rem] leading-4 text-[color:var(--ss-text-muted)]">
                      {entry.edit_summary ?? "initial generation"}
                    </span>
                  </button>
                </li>
              );
            })}
        </ul>
      </section>

      <section>
        <header className="mb-3 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-2">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            LOCK MAP
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {version.structure.sections.filter((s) => s.locked).length} LOCKED
          </span>
        </header>
        <ul className="grid gap-1 font-mono text-[0.62rem] uppercase tracking-widest">
          {version.structure.sections.map((section) => (
            <li
              key={section.index}
              className="flex items-center justify-between border-b border-[color:var(--ss-border)] py-1"
              style={{
                color: section.locked ? "var(--ss-warning)" : "var(--ss-text-muted)"
              }}
            >
              <span>[{section.index}] {section.label}</span>
              <span>{section.locked ? "LOCKED" : "open"}</span>
            </li>
          ))}
        </ul>
      </section>

      <SoundGraphFlow versionId={version.id} projectKey={projectKey} />

      <ExportSection
        version={version}
        projectKey={projectKey}
        onExport={onExport}
        exportManifest={exportManifest}
        isPending={isPending}
      />

      <section>
        <header className="mb-3 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-2">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            COMPATIBILITY
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            STATIC SPEC
          </span>
        </header>
        <ul className="grid gap-3 font-mono text-[0.6rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-secondary)]">
          <li>
            <p className="text-[color:var(--ss-text-primary)]">SUNO EXPORT</p>
            <p className="normal-case tracking-normal text-[0.62rem] text-[color:var(--ss-text-muted)]">
              Sections render as uppercase bracket tags ([VERSE], [CHORUS]). Adlibs in
              parentheses (oh) map to vocals_adlibs on SoundGraph import. Negative prompt
              suppresses "oh oh oh" intros.
            </p>
          </li>
          <li>
            <p className="text-[color:var(--ss-text-primary)]">SOUNDGRAPH EXPORT</p>
            <p className="normal-case tracking-normal text-[0.62rem] text-[color:var(--ss-text-muted)]">
              Each section maps to an arrangement region. Sung sections route to vocals_main;
              instrumental_opening and dub_breakdown emit vocal_entry=false. Locked sections
              survive every regeneration byte-for-byte.
            </p>
          </li>
          <li>
            <p className="text-[color:var(--ss-text-primary)]">SAFETY</p>
            <p className="normal-case tracking-normal text-[0.62rem] text-[color:var(--ss-text-muted)]">
              No named-artist imitation, no copied lines, no voice likeness without explicit
              clearance. Filter is descriptive in this slice; enforcement lands with the real
              provider.
            </p>
          </li>
        </ul>
      </section>

      <footer className="mt-2 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        ← <a
          href={`/admin/soundsystem/lyrics/${encodeURIComponent(projectKey)}`}
          className="hover:text-[color:var(--ss-accent)]"
        >
          project view
        </a>
      </footer>
    </aside>
  );
}

function ExportSection({
  version,
  projectKey,
  onExport,
  exportManifest,
  isPending
}: Readonly<{
  version: LyricsVersion;
  projectKey: string;
  onExport: () => void;
  exportManifest: LyricsExportManifest | null;
  isPending: boolean;
}>) {
  const [downloadingManifest, setDownloadingManifest] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  function downloadLyricsTxt(): void {
    setDownloadError(null);
    const filename = `${projectKey}-v${version.version}-lyrics.txt`;
    triggerDownload(renderLyricsTxt(version), filename, "text/plain");
  }

  function downloadLyricsJson(): void {
    setDownloadError(null);
    const filename = `${projectKey}-v${version.version}-lyrics.json`;
    triggerDownload(
      JSON.stringify(version, null, 2),
      filename,
      "application/json"
    );
  }

  async function downloadSoundgraphManifest(): Promise<void> {
    setDownloadError(null);
    setDownloadingManifest(true);
    try {
      const manifest = await exportLyricsVersion(version.id);
      const filename = `${projectKey}-v${version.version}-soundgraph-lyrics.json`;
      triggerDownload(
        JSON.stringify(manifest, null, 2),
        filename,
        "application/json"
      );
    } catch (e) {
      setDownloadError(formatError(e));
    } finally {
      setDownloadingManifest(false);
    }
  }

  return (
    <section>
      <header className="mb-3 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-2">
        <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          EXPORT
        </h2>
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          CONTRACT ARTIFACT
        </span>
      </header>
      <p className="mb-3 font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
        Local browser download. No Dropbox sync. No persistent artifact store.
        Export is a contract artifact, not a release-ready distribution package.
      </p>
      <div className="grid gap-2">
        <button
          type="button"
          onClick={downloadLyricsTxt}
          disabled={isPending || downloadingManifest}
          className="w-full border border-[color:var(--ss-border-accent)] px-3 py-2 text-left font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          ↓ {projectKey}-v{version.version}-lyrics.txt
        </button>
        <button
          type="button"
          onClick={downloadLyricsJson}
          disabled={isPending || downloadingManifest}
          className="w-full border border-[color:var(--ss-border-accent)] px-3 py-2 text-left font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          ↓ {projectKey}-v{version.version}-lyrics.json
        </button>
        <button
          type="button"
          onClick={() => {
            void downloadSoundgraphManifest();
          }}
          disabled={isPending || downloadingManifest}
          className="w-full border border-[color:var(--ss-border-accent)] px-3 py-2 text-left font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          {downloadingManifest
            ? "FETCHING MANIFEST…"
            : `↓ ${projectKey}-v${version.version}-soundgraph-lyrics.json`}
        </button>
        <button
          type="button"
          onClick={onExport}
          disabled={isPending || downloadingManifest}
          className="w-full border border-[color:var(--ss-border-strong)] px-3 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          PREVIEW MANIFEST (NO DOWNLOAD)
        </button>
      </div>
      {downloadError !== null ? (
        <p
          className="mt-3 border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.62rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {downloadError}
        </p>
      ) : null}
      {exportManifest !== null ? (
        <div className="mt-3 grid gap-3 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
          <dl className="grid gap-2">
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">LYRICS TXT</dt>
              <dd className="break-all text-[color:var(--ss-text-primary)]">
                {exportManifest.lyrics_txt_path}
              </dd>
            </div>
            <div>
              <dt className="text-[color:var(--ss-text-muted)]">LYRICS JSON</dt>
              <dd className="break-all text-[color:var(--ss-text-primary)]">
                {exportManifest.lyrics_json_path}
              </dd>
            </div>
            {exportManifest.safety_report_json_path !== null ? (
              <div>
                <dt className="text-[color:var(--ss-text-muted)]">SAFETY REPORT</dt>
                <dd className="break-all text-[color:var(--ss-text-primary)]">
                  {exportManifest.safety_report_json_path}
                </dd>
              </div>
            ) : null}
          </dl>
          <div>
            <p className="text-[color:var(--ss-text-muted)]">
              VOCAL NOTES · {exportManifest.vocal_notes.length} entries
            </p>
            <ul className="mt-1 grid gap-1">
              {exportManifest.vocal_notes.map((note) => (
                <li
                  key={note.section_index}
                  className="grid grid-cols-[2.5rem_1fr] items-baseline gap-2 normal-case text-[0.6rem] tracking-normal"
                >
                  <span className="font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                    [{note.section_index}]
                  </span>
                  <span className="text-[color:var(--ss-text-primary)]">{note.note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function renderLyricsTxt(version: LyricsVersion): string {
  const blocks: string[] = [
    `# ${version.structure.target_language.toUpperCase()} · v${version.version}`,
    `# parent=${version.parent_version_id ?? "none"}  edit_summary=${version.edit_summary ?? "initial generation"}`,
    ""
  ];
  for (const section of version.structure.sections) {
    blocks.push(`[${section.label.toUpperCase()}]`);
    if (section.lines.length === 0) {
      blocks.push("[empty]");
    } else {
      for (const line of section.lines) {
        blocks.push(line.text);
      }
    }
    blocks.push("");
  }
  return blocks.join("\n");
}

function triggerDownload(content: string, filename: string, mimeType: string): void {
  if (typeof window === "undefined") {
    return;
  }
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  window.document.body.appendChild(anchor);
  anchor.click();
  window.document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

function formatError(error: unknown): string {
  if (error instanceof InferenceClientError) {
    return error.status ? `${error.status} · ${error.message}` : error.message;
  }
  if (error instanceof Error) return error.message;
  return "inference_error";
}
