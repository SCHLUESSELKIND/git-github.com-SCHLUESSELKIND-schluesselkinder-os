import Link from "next/link";
import { SoundsystemShell } from "../../_components/SoundsystemShell";
import {
  getArtifact,
  getArtifactDownloadLink,
  InferenceClientError
} from "../../_lib/inference";
import type {
  ArtifactRecord,
  ArtifactSignedUrl
} from "../../_lib/inference-types";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ artifact_id: string }>;
};

/**
 * Artifact Detail — inspect a single artifact record (S30).
 *
 * Shows all metadata fields, honest state for every status, and a download
 * action via signed URL when the artifact is stored. Never exposes raw
 * filesystem paths or secret tokens.
 */
export default async function ArtifactDetailPage({ params }: Props) {
  const { artifact_id } = await params;
  let artifact: ArtifactRecord | null = null;
  let downloadLink: ArtifactSignedUrl | null = null;
  let errorMessage: string | null = null;

  try {
    artifact = await getArtifact(artifact_id);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage =
        error.status === 404
          ? "Artifact not found."
          : `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  // Fetch download link only for stored artifacts
  if (artifact && artifact.status === "stored") {
    try {
      downloadLink = await getArtifactDownloadLink(artifact_id);
    } catch {
      // Non-critical — download link generation may fail
    }
  }

  if (errorMessage || !artifact) {
    return (
      <SoundsystemShell title="Artifact not found." status="STORAGE INSPECTOR">
        <p
          className="border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {errorMessage || "Artifact not found."}
        </p>
        <Link
          href="/admin/soundsystem/artifacts"
          className="mt-4 inline-block font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          &larr; Back to Artifacts
        </Link>
      </SoundsystemShell>
    );
  }

  const isStored = artifact.status === "stored";
  const isPlanned = artifact.status === "planned";
  const isFailed = artifact.status === "failed" || artifact.status === "missing";
  const isJson = artifact.content_type === "application/json";

  return (
    <SoundsystemShell
      title={artifact.kind.replace(/_/g, " ") + "."}
      status="ARTIFACT DETAIL"
    >
      {/* Back link */}
      <Link
        href="/admin/soundsystem/artifacts"
        className="mb-6 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
      >
        &larr; Artifacts
      </Link>

      {/* Status banner */}
      {isPlanned ? (
        <div
          className="mb-8 border px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{
            borderColor: "var(--ss-border-strong)",
            color: "var(--ss-text-secondary)"
          }}
        >
          Planned only &mdash; no bytes stored yet.
        </div>
      ) : null}

      {isFailed ? (
        <div
          className="mb-8 border px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{
            borderColor: "var(--ss-warning-dim)",
            color: "var(--ss-warning)"
          }}
        >
          {artifact.status === "failed"
            ? "Artifact storage failed."
            : "Artifact missing from storage."}
        </div>
      ) : null}

      {/* Metadata grid */}
      <section className="mb-10 grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4">
        <MetaCell label="Kind" value={artifact.kind.replace(/_/g, " ")} />
        <MetaCell
          label="Status"
          value={artifact.status.toUpperCase()}
          accent={isStored}
          warn={isFailed}
        />
        <MetaCell label="Storage mode" value={artifact.storage_mode} />
        <MetaCell label="Content type" value={artifact.content_type || "—"} />
        <MetaCell
          label="Size"
          value={
            artifact.size_bytes != null && artifact.size_bytes > 0
              ? formatBytes(artifact.size_bytes)
              : "—"
          }
        />
        <MetaCell label="Operator" value={artifact.operator_id || "—"} />
        <MetaCell
          label="Created"
          value={
            new Date(artifact.created_at)
              .toISOString()
              .slice(0, 16)
              .replace("T", " ")
          }
        />
        <MetaCell
          label="Updated"
          value={
            new Date(artifact.updated_at)
              .toISOString()
              .slice(0, 16)
              .replace("T", " ")
          }
        />
      </section>

      {/* Logical path */}
      <section className="mb-8">
        <header className="mb-3 border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            LOGICAL PATH
          </h2>
        </header>
        <p className="break-all font-mono text-[0.7rem] leading-5 text-[color:var(--ss-text-secondary)]">
          {artifact.logical_path}
        </p>
      </section>

      {/* Source lineage */}
      <section className="mb-8">
        <header className="mb-3 border-b border-[color:var(--ss-border)] pb-3">
          <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
            SOURCE LINEAGE
          </h2>
        </header>
        <div className="grid gap-2 font-mono text-[0.65rem] uppercase tracking-widest">
          <LineageRow label="Source entity type" value={artifact.source_entity_type} />
          <LineageRow label="Source entity ID" value={artifact.source_entity_id} />
          <LineageRow label="Provenance ID" value={artifact.provenance_id} />
        </div>
      </section>

      {/* Checksum */}
      {artifact.checksum_sha256 ? (
        <section className="mb-8">
          <header className="mb-3 border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              INTEGRITY
            </h2>
          </header>
          <p className="break-all font-mono text-[0.6rem] leading-5 text-[color:var(--ss-text-secondary)]">
            SHA-256: {artifact.checksum_sha256}
          </p>
        </section>
      ) : null}

      {/* Download action */}
      {isStored && downloadLink ? (
        <section className="mb-8">
          <header className="mb-3 border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              DOWNLOAD
            </h2>
          </header>
          <a
            href={downloadLink.url}
            className="inline-block border px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)]"
            style={{
              borderColor: "var(--ss-border-accent)",
              color: "var(--ss-accent)"
            }}
            download
          >
            Download stored artifact
          </a>
          {downloadLink.access_mode === "signed" && downloadLink.expires_at ? (
            <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Signed link expires{" "}
              {new Date(downloadLink.expires_at)
                .toISOString()
                .slice(0, 16)
                .replace("T", " ")}
            </p>
          ) : null}
          {isJson ? (
            <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Content type: application/json &mdash; open in browser to inspect.
            </p>
          ) : null}
        </section>
      ) : null}

      {/* Debug / internal (collapsed) */}
      <section className="mt-8">
        <details className="border border-[color:var(--ss-border)]">
          <summary className="cursor-pointer px-4 py-3 font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:text-[color:var(--ss-text-secondary)]">
            DEBUG / INTERNAL
          </summary>
          <div
            className="grid gap-2 px-4 py-3 font-mono text-[0.6rem] leading-5"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <DebugRow label="artifact_id" value={artifact.artifact_id} />
            <DebugRow label="storage_key" value={artifact.storage_key} />
            <DebugRow label="storage_mode" value={artifact.storage_mode} />
          </div>
        </details>
      </section>

      {/* Footer ID */}
      <p className="mt-6 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        ARTIFACT &middot; {artifact.artifact_id}
      </p>
    </SoundsystemShell>
  );
}

function MetaCell({
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
      <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="text-lg font-black uppercase leading-none"
        style={{ color: textColor }}
      >
        {value}
      </span>
    </div>
  );
}

function LineageRow({
  label,
  value
}: Readonly<{ label: string; value: string | null }>) {
  return (
    <div className="flex items-center justify-between border-b border-[color:var(--ss-border)] py-2">
      <span className="text-[color:var(--ss-text-muted)]">{label}</span>
      {value ? (
        <span className="text-[color:var(--ss-accent)]">{value}</span>
      ) : (
        <span className="text-[color:var(--ss-text-muted)]">&mdash;</span>
      )}
    </div>
  );
}

function DebugRow({
  label,
  value
}: Readonly<{ label: string; value: string | null }>) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[color:var(--ss-text-muted)]">{label}</span>
      <span className="break-all text-[color:var(--ss-text-secondary)]">
        {value || "—"}
      </span>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  const value = bytes / Math.pow(1024, i);
  return `${value < 10 ? value.toFixed(1) : Math.round(value)} ${units[i]}`;
}
