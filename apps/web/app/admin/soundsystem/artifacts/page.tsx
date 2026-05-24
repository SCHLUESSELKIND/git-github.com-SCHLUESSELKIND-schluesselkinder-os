import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getArtifactStorageSummary,
  listArtifacts,
  InferenceClientError
} from "../_lib/inference";
import type {
  ArtifactRecord,
  ArtifactStorageSummary
} from "../_lib/inference-types";

export const dynamic = "force-dynamic";

/**
 * Artifact Storage Inspector — browse all artifact records (S30).
 *
 * Shows the storage summary and a read-only table of all artifacts.
 * Each row links to the artifact detail page. No destructive actions.
 */
export default async function ArtifactsPage() {
  let summary: ArtifactStorageSummary | null = null;
  let artifacts: ArtifactRecord[] = [];
  let unreachable = false;

  try {
    [summary, artifacts] = await Promise.all([
      getArtifactStorageSummary(),
      listArtifacts()
    ]);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }

  // Group counts by kind
  const kindCounts = new Map<string, number>();
  for (const a of artifacts) {
    kindCounts.set(a.kind, (kindCounts.get(a.kind) ?? 0) + 1);
  }

  return (
    <SoundsystemShell title="Artifacts." status="STORAGE INSPECTOR">
      <p className="mb-8 max-w-3xl font-mono text-xs uppercase leading-6 tracking-widest text-[color:var(--ss-text-secondary)]">
        Artifact storage registry. Browse metadata records for all stored and
        planned artifacts — audio mixes, stem packs, manifests, provenance
        chains, and export bundles.
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
        <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4 lg:grid-cols-7">
          <SummaryCell label="Total" value={String(summary.total)} />
          <SummaryCell
            label="Stored"
            value={String(summary.stored)}
            accent={summary.stored > 0}
          />
          <SummaryCell label="Planned" value={String(summary.planned)} />
          <SummaryCell label="Missing" value={String(summary.missing)} warn={summary.missing > 0} />
          <SummaryCell label="Failed" value={String(summary.failed)} warn={summary.failed > 0} />
          <SummaryCell label="Deleted" value={String(summary.deleted)} />
          <SummaryCell
            label="Total size"
            value={formatBytes(summary.total_size_bytes)}
          />
        </section>
      ) : null}

      {/* Kind breakdown */}
      {kindCounts.size > 0 ? (
        <section className="mb-10">
          <header className="mb-4 border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              BY KIND
            </h2>
          </header>
          <div className="flex flex-wrap gap-2">
            {Array.from(kindCounts.entries())
              .sort((a, b) => b[1] - a[1])
              .map(([kind, count]) => (
                <span
                  key={kind}
                  className="border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.58rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]"
                >
                  {kind.replace(/_/g, " ")} · {count}
                </span>
              ))}
          </div>
        </section>
      ) : null}

      {/* Artifact list */}
      <section>
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            ARTIFACT RECORDS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {artifacts.length} RECORDS
          </span>
        </header>

        {artifacts.length === 0 ? (
          <div className="mt-6 grid gap-3">
            <p className="font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No artifacts yet.
            </p>
            <p className="max-w-xl font-mono text-[0.62rem] leading-5 uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Artifacts are created when producers (SoundGraph, Music Router,
              Export Pack, Release Pack) register outputs. POST to /v1/artifacts
              or trigger a generation flow.
            </p>
          </div>
        ) : (
          <div className="mt-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)]">
            {artifacts.map((artifact) => (
              <ArtifactRow key={artifact.artifact_id} artifact={artifact} />
            ))}
          </div>
        )}
      </section>
    </SoundsystemShell>
  );
}

function ArtifactRow({
  artifact
}: Readonly<{ artifact: ArtifactRecord }>) {
  return (
    <Link
      href={`/admin/soundsystem/artifacts/${artifact.artifact_id}`}
      className="grid gap-2 p-4 hover:bg-[color:var(--ss-panel-elevated)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      {/* Top row: kind + status */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <KindChip kind={artifact.kind} />
          <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            {artifact.logical_path}
          </span>
        </div>
        <StatusChip status={artifact.status} />
      </div>

      {/* Bottom row: metadata */}
      <div className="flex flex-wrap items-center gap-3 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {artifact.content_type && (
          <span>{artifact.content_type}</span>
        )}
        {artifact.size_bytes != null && artifact.size_bytes > 0 && (
          <span>{formatBytes(artifact.size_bytes)}</span>
        )}
        {artifact.checksum_sha256 && (
          <span
            className="border border-[color:var(--ss-border)] px-1 py-0.5"
            title={artifact.checksum_sha256}
          >
            SHA256
          </span>
        )}
        {artifact.source_entity_type && (
          <span className="text-[color:var(--ss-text-secondary)]">
            {artifact.source_entity_type}
          </span>
        )}
        <span className="border border-[color:var(--ss-border)] px-1 py-0.5">
          {artifact.storage_mode}
        </span>
        <span>
          {new Date(artifact.created_at)
            .toISOString()
            .slice(0, 16)
            .replace("T", " ")}
        </span>
      </div>
    </Link>
  );
}

function KindChip({ kind }: Readonly<{ kind: string }>) {
  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase tracking-widest"
      style={{
        borderColor: kindBorderColor(kind),
        color: kindColor(kind)
      }}
    >
      {kind.replace(/_/g, " ")}
    </span>
  );
}

function StatusChip({ status }: Readonly<{ status: string }>) {
  const color =
    status === "stored"
      ? "var(--ss-accent)"
      : status === "planned"
        ? "var(--ss-text-secondary)"
        : status === "failed" || status === "missing"
          ? "var(--ss-warning)"
          : "var(--ss-text-muted)";
  const borderColor =
    status === "stored"
      ? "var(--ss-border-accent)"
      : status === "failed" || status === "missing"
        ? "var(--ss-warning-dim)"
        : "var(--ss-border-strong)";
  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase tracking-widest"
      style={{ color, borderColor }}
    >
      {status}
    </span>
  );
}

function SummaryCell({
  label,
  value,
  accent = false,
  warn = false
}: Readonly<{
  label: string;
  value: string;
  accent?: boolean;
  warn?: boolean;
}>) {
  const textColor = warn
    ? "var(--ss-warning)"
    : accent
      ? "var(--ss-accent)"
      : "var(--ss-text-primary)";
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
        style={{ color: textColor }}
      >
        {value}
      </span>
    </div>
  );
}

function kindColor(kind: string): string {
  if (kind === "audio_mix" || kind === "stem_pack") return "var(--ss-accent)";
  if (kind === "manifest" || kind === "soundgraph") return "var(--ss-text-secondary)";
  if (kind === "provenance") return "var(--ss-warning)";
  if (kind === "lyrics") return "var(--ss-text-secondary)";
  return "var(--ss-text-muted)";
}

function kindBorderColor(kind: string): string {
  if (kind === "audio_mix" || kind === "stem_pack") return "var(--ss-border-accent)";
  if (kind === "provenance") return "var(--ss-warning-dim)";
  return "var(--ss-border-strong)";
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value < 10 ? value.toFixed(1) : Math.round(value)} ${units[i]}`;
}
