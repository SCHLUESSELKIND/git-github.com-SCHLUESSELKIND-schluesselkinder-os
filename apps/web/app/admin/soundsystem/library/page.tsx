import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getLibrarySummary,
  listLibraryEntries,
  InferenceClientError
} from "../_lib/inference";
import type {
  ProjectLibraryEntry,
  ProjectLibrarySummary
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Project Library — browse exported project packs (S18).
 *
 * Each pack bundles MusicJob + Artifacts + Lyrics + SoundGraph + Provenance.
 * This page shows the library summary and a list of all entries.
 */
export default async function LibraryPage() {
  let summary: ProjectLibrarySummary | null = null;
  let entries: ReadonlyArray<ProjectLibraryEntry> = [];
  let unreachable = false;

  try {
    [summary, entries] = await Promise.all([
      getLibrarySummary(),
      listLibraryEntries()
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Library." status="PROJECT PACKS">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Exported project packs. Each pack bundles a completed music job with its lyrics,
        arrangement, artifacts, and provenance chain into a single exportable unit.
      </p>

      {unreachable ? (
        <p
          className="mb-8 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          Inference unreachable. Start uvicorn app.main:app --port 8010 under
          services/soundsystem-inference.
        </p>
      ) : null}

      {/* Summary grid */}
      {summary ? (
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-5">
          <SummaryCell label="Total packs" value={String(summary.total_packs)} />
          <SummaryCell label="Library entries" value={String(summary.total_entries)} />
          <SummaryCell label="With lyrics" value={String(summary.entries_with_lyrics)} />
          <SummaryCell label="With arrangement" value={String(summary.entries_with_arrangements)} />
          <SummaryCell label="With provenance" value={String(summary.entries_with_provenance)} />
        </section>
      ) : null}

      {/* Entry list */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            PROJECT PACKS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {entries.length} ENTRIES
          </span>
        </header>

        {entries.length === 0 ? (
          <div className="mt-6 grid gap-3">
            <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No project packs yet.
            </p>
            <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Export a pack from the Lyrics → SoundGraph → Music Router flow, or POST
              to /v1/library/packs with a completed music_job_id.
            </p>
          </div>
        ) : (
          <div className="mt-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)]">
            {entries.map((entry) => (
              <LibraryEntryCard key={entry.entry_id} entry={entry} />
            ))}
          </div>
        )}
      </section>
    </SoundsystemShell>
  );
}

function LibraryEntryCard({
  entry
}: Readonly<{ entry: ProjectLibraryEntry }>) {
  return (
    <Link
      href={`/admin/soundsystem/library/${entry.pack_id}`}
      className="grid gap-3 p-5 hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      {/* Title row */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-lg font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
          {entry.title}
        </span>
        <StatusChip status={entry.status} />
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-3 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {entry.intent && (
          <span className="border border-[color:var(--ss-border-strong)] px-1.5 py-0.5 text-[color:var(--ss-text-secondary)]">
            {entry.intent.replace(/_/g, " ")}
          </span>
        )}
        {entry.bpm && (
          <span>{entry.bpm} BPM</span>
        )}
        {entry.key_signature && (
          <span>{entry.key_signature}</span>
        )}
        {entry.estimated_duration_seconds && (
          <span>{entry.estimated_duration_seconds.toFixed(1)}s</span>
        )}
        <span>{entry.component_count} components</span>
        <span>{entry.artifact_count} artifacts</span>
      </div>

      {/* Lineage badges */}
      <div className="flex items-center gap-2">
        <LineageBadge label="LYRICS" active={entry.has_lyrics} />
        <LineageBadge label="ARRANGEMENT" active={entry.has_arrangement} />
        <LineageBadge label="PROVENANCE" active={entry.has_provenance} />
      </div>

      {/* Slug + date */}
      <div className="flex items-center justify-between font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        <span>/{entry.slug}</span>
        <span>{new Date(entry.created_at).toISOString().slice(0, 16).replace("T", " ")}</span>
      </div>
    </Link>
  );
}

function StatusChip({ status }: Readonly<{ status: string }>) {
  const color =
    status === "complete"
      ? "var(--ss-accent)"
      : status === "failed"
        ? "var(--ss-warning)"
        : "var(--ss-text-muted)";
  const borderColor =
    status === "complete"
      ? "var(--ss-border-accent)"
      : status === "failed"
        ? "var(--ss-warning-dim)"
        : "var(--ss-border-strong)";
  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
      style={{ color, borderColor }}
    >
      {status}
    </span>
  );
}

function LineageBadge({
  label,
  active
}: Readonly<{ label: string; active: boolean }>) {
  return (
    <span
      className="border px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
      style={{
        borderColor: active ? "var(--ss-border-accent)" : "var(--ss-border)",
        color: active ? "var(--ss-accent)" : "var(--ss-text-muted)",
        opacity: active ? 1 : 0.5
      }}
    >
      {label}
    </span>
  );
}

function SummaryCell({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="flex flex-col gap-2 p-4" style={{ backgroundColor: "var(--ss-panel)" }}>
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span className="text-2xl font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
        {value}
      </span>
    </div>
  );
}
