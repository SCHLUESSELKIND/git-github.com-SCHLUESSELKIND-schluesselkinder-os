import Link from "next/link";
import { SoundsystemShell } from "../../_components/SoundsystemShell";
import { getExportPack, InferenceClientError } from "../../_lib/inference";
import type {
  ExportPack,
  ExportPackComponent
} from "../../_lib/inference-types";
import { DropboxExportFlow } from "./_components/DropboxExportFlow";
import { ReleasePackFlow } from "./_components/ReleasePackFlow";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ pack_id: string }>;
};

/**
 * Pack Detail View — inspect a single export pack (S18).
 *
 * Shows all components, artifact paths, provenance chain reference,
 * and the raw JSON for debugging.
 */
export default async function PackDetailPage({ params }: Props) {
  const { pack_id } = await params;
  let pack: ExportPack | null = null;
  let errorMessage: string | null = null;

  try {
    pack = await getExportPack(pack_id);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage =
        error.status === 404
          ? "Export pack not found."
          : `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  if (errorMessage || !pack) {
    return (
      <SoundsystemShell title="Pack not found." status="LIBRARY">
        <p
          className="border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {errorMessage || "Export pack not found."}
        </p>
        <Link
          href="/admin/soundsystem/library"
          className="mt-4 inline-block font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          ← Back to Library
        </Link>
      </SoundsystemShell>
    );
  }

  return (
    <SoundsystemShell title={pack.title} status="PACK DETAIL">
      {/* Back link */}
      <Link
        href="/admin/soundsystem/library"
        className="mb-6 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
      >
        ← Library
      </Link>

      {/* Pack overview */}
      <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4">
        <MetaCell label="Status" value={pack.status.toUpperCase()} accent={pack.status === "complete"} />
        <MetaCell label="Components" value={String(pack.total_components)} />
        <MetaCell label="BPM" value={pack.bpm ? String(pack.bpm) : "—"} />
        <MetaCell label="Key" value={pack.key_signature || "—"} />
        <MetaCell label="Intent" value={pack.intent ? pack.intent.replace(/_/g, " ") : "—"} />
        <MetaCell
          label="Duration"
          value={pack.estimated_duration_seconds ? `${pack.estimated_duration_seconds.toFixed(1)}s` : "—"}
        />
        <MetaCell label="Operator" value={pack.operator_id || "—"} />
        <MetaCell
          label="Created"
          value={new Date(pack.created_at).toISOString().slice(0, 16).replace("T", " ")}
        />
      </section>

      {/* Lineage links */}
      <section className="mb-10">
        <header className="mb-4 border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            LINEAGE
          </h2>
        </header>
        <div className="grid gap-2 font-mono text-[0.65rem] uppercase tracking-widest">
          <LineageRow label="Music Job" id={pack.music_job_id} />
          <LineageRow label="Lyrics Version" id={pack.lyrics_version_id} />
          <LineageRow label="Arrangement" id={pack.arrangement_id} />
          <LineageRow label="Provenance" id={pack.provenance_id} />
        </div>
      </section>

      {/* Components table */}
      <section className="mb-10">
        <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            COMPONENTS
          </h2>
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {pack.components.length}
          </span>
        </header>
        <div className="mt-4 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)]">
          {pack.components.map((component, i) => (
            <ComponentRow key={i} component={component} index={i} />
          ))}
        </div>
      </section>

      {/* Notes */}
      {pack.notes && (
        <section className="mb-10">
          <header className="mb-3 border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              NOTES
            </h2>
          </header>
          <p className="font-mono text-[0.7rem] leading-5 text-[color:var(--ss-text-secondary)]">
            {pack.notes}
          </p>
        </section>
      )}

      {/* Release Pack */}
      <ReleasePackFlow packId={pack_id} />

      {/* Dropbox Export */}
      <DropboxExportFlow packId={pack_id} />

      {/* Inspect JSON */}
      <section className="mt-8">
        <details className="border border-[color:var(--ss-border)]">
          <summary className="cursor-pointer px-4 py-3 font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:text-[color:var(--ss-text-secondary)]">
            INSPECT JSON
          </summary>
          <pre
            className="overflow-x-auto whitespace-pre-wrap px-4 py-3 font-mono text-[0.6rem] leading-4 text-[color:var(--ss-text-secondary)]"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            {JSON.stringify(pack, null, 2)}
          </pre>
        </details>
      </section>

      {/* Pack ID footer */}
      <p className="mt-6 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        PACK · {pack.pack_id}
      </p>
    </SoundsystemShell>
  );
}

function MetaCell({
  label,
  value,
  accent = false
}: Readonly<{ label: string; value: string; accent?: boolean }>) {
  return (
    <div className="flex flex-col gap-2 p-4" style={{ backgroundColor: "var(--ss-panel)" }}>
      <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="text-lg font-black uppercase leading-none"
        style={{ color: accent ? "var(--ss-accent)" : "var(--ss-text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}

function LineageRow({
  label,
  id
}: Readonly<{ label: string; id: string | null }>) {
  return (
    <div className="flex items-center justify-between border-b border-[color:var(--ss-border)] py-2">
      <span className="text-[color:var(--ss-text-muted)]">{label}</span>
      {id ? (
        <span className="text-[color:var(--ss-accent)]">{id}</span>
      ) : (
        <span className="text-[color:var(--ss-text-muted)]">—</span>
      )}
    </div>
  );
}

function ComponentRow({
  component,
  index
}: Readonly<{ component: ExportPackComponent; index: number }>) {
  return (
    <div
      className="grid grid-cols-[2rem_auto_1fr] items-center gap-3 px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {String(index).padStart(2, "0")}
      </span>
      <span
        className="border px-2 py-0.5 font-mono text-[0.55rem] uppercase tracking-widest"
        style={{
          borderColor: "var(--ss-border-strong)",
          color: componentColor(component.component_type)
        }}
      >
        {component.component_type}
      </span>
      <div className="grid gap-0.5">
        <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          {component.label}
        </span>
        {component.path && (
          <span className="break-all font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
            {component.path}
          </span>
        )}
      </div>
    </div>
  );
}

function componentColor(type: string): string {
  if (type === "music_job") return "var(--ss-text-primary)";
  if (type.startsWith("artifact_")) return "var(--ss-accent)";
  if (type === "lyrics_version") return "var(--ss-text-secondary)";
  if (type === "soundgraph_arrangement") return "var(--ss-text-secondary)";
  if (type === "output_provenance") return "var(--ss-warning)";
  return "var(--ss-text-muted)";
}
