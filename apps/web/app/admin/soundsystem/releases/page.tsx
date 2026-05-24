import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getReleaseSummary,
  listReleases,
  InferenceClientError
} from "../_lib/inference";
import type {
  ReleasePack,
  ReleasePackSummary
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Release Center — browse and inspect release packs (S24).
 *
 * Each release wraps an ExportPack with social copy, compliance checklist,
 * asset placeholders, and a Dropbox release target. Operators verify the
 * checklist and mark the release READY for distribution.
 */
export default async function ReleasesPage() {
  let summary: ReleasePackSummary | null = null;
  let releases: ReleasePack[] = [];
  let unreachable = false;

  try {
    [summary, releases] = await Promise.all([
      getReleaseSummary(),
      listReleases()
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  return (
    <SoundsystemShell title="Releases." status="RELEASE CENTER">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Release packs ready for distribution. Each release bundles social copy,
        compliance checklist, asset placeholders, and a Dropbox release target.
        Verify the checklist and mark ready.
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
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4">
          <SummaryCell label="Total releases" value={String(summary.total_releases)} />
          <SummaryCell label="Drafts" value={String(summary.drafts)} />
          <SummaryCell
            label="Ready"
            value={String(summary.ready)}
            accent={summary.ready > 0}
          />
          <SummaryCell
            label="Compliance passed"
            value={String(summary.compliance_passed)}
            accent={summary.compliance_passed > 0}
          />
        </section>
      ) : null}

      {/* Release list */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            RELEASE PACKS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {releases.length} RELEASES
          </span>
        </header>

        {releases.length === 0 ? (
          <div className="mt-6 grid gap-3">
            <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No release packs yet.
            </p>
            <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Create a release from a Library pack detail view, or POST to
              /v1/releases with a pack_id and artist.
            </p>
          </div>
        ) : (
          <div className="mt-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)]">
            {releases.map((release) => (
              <ReleaseCard key={release.release_id} release={release} />
            ))}
          </div>
        )}
      </section>
    </SoundsystemShell>
  );
}

function ReleaseCard({ release }: Readonly<{ release: ReleasePack }>) {
  const checklistProgress = release.compliance_checklist.filter(
    (i) => i.passed
  ).length;
  const checklistTotal = release.compliance_checklist.length;

  return (
    <Link
      href={`/admin/soundsystem/releases/${release.release_id}`}
      className="grid gap-3 p-5 hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      {/* Title row */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-lg font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
          {release.title}
        </span>
        <ReleaseStatusChip status={release.status} />
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-3 font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        <span className="text-[color:var(--ss-text-secondary)]">
          {release.artist}
        </span>
        {release.genre && (
          <span className="border border-[color:var(--ss-border-strong)] px-1.5 py-0.5 text-[color:var(--ss-text-secondary)]">
            {release.genre}
          </span>
        )}
        {release.bpm && <span>{release.bpm} BPM</span>}
        {release.key_signature && <span>{release.key_signature}</span>}
        {release.duration_seconds && (
          <span>
            {Math.floor(release.duration_seconds / 60)}:
            {String(Math.floor(release.duration_seconds % 60)).padStart(2, "0")}
          </span>
        )}
      </div>

      {/* Bottom row: compliance + date */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ComplianceBadge
            passed={release.compliance_passed}
            progress={checklistProgress}
            total={checklistTotal}
          />
          {release.dropbox_target && (
            <span className="border border-[color:var(--ss-border)] px-1.5 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              DROPBOX
            </span>
          )}
        </div>
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {new Date(release.created_at)
            .toISOString()
            .slice(0, 16)
            .replace("T", " ")}
        </span>
      </div>
    </Link>
  );
}

function ReleaseStatusChip({
  status
}: Readonly<{ status: string }>) {
  const isDraft = status === "draft";
  const isReady = status === "ready";
  const color = isReady
    ? "var(--ss-accent)"
    : isDraft
      ? "var(--ss-text-secondary)"
      : "var(--ss-text-muted)";
  const borderColor = isReady
    ? "var(--ss-border-accent)"
    : isDraft
      ? "var(--ss-border-strong)"
      : "var(--ss-border)";

  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.58rem] font-black uppercase tracking-widest"
      style={{ color, borderColor }}
    >
      {status}
    </span>
  );
}

function ComplianceBadge({
  passed,
  progress,
  total
}: Readonly<{ passed: boolean; progress: number; total: number }>) {
  return (
    <span
      className="border px-1.5 py-0.5 font-mono text-[0.5rem] font-black uppercase tracking-widest"
      style={{
        borderColor: passed
          ? "var(--ss-border-accent)"
          : "var(--ss-border-strong)",
        color: passed ? "var(--ss-accent)" : "var(--ss-warning)"
      }}
    >
      {passed ? "COMPLIANCE PASSED" : `${progress}/${total} CHECKED`}
    </span>
  );
}

function SummaryCell({
  label,
  value,
  accent = false
}: Readonly<{ label: string; value: string; accent?: boolean }>) {
  return (
    <div
      className="flex flex-col gap-2 p-4"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="text-2xl font-black uppercase leading-none"
        style={{
          color: accent ? "var(--ss-accent)" : "var(--ss-text-primary)"
        }}
      >
        {value}
      </span>
    </div>
  );
}
