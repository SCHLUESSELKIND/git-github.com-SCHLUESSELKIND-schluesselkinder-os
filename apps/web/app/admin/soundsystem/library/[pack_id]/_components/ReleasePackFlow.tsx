"use client";

import { useState, useTransition } from "react";
import {
  createReleasePack,
  getReleaseByPack,
  updateReleaseChecklist,
  markReleaseReady,
  InferenceClientError
} from "../../../_lib/inference";
import type {
  ReleasePack,
  ComplianceChecklistItem,
  ReleaseAssetPlaceholder
} from "../../../_lib/generated-inference-types";

type Props = Readonly<{
  packId: string;
}>;

type FlowStage = "idle" | "created" | "ready" | "error";

export function ReleasePackFlow({ packId }: Props) {
  const [stage, setStage] = useState<FlowStage>("idle");
  const [release, setRelease] = useState<ReleasePack | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleCreate = (): void => {
    setError(null);
    startTransition(async () => {
      try {
        let fetched: ReleasePack;
        try {
          fetched = await getReleaseByPack(packId);
        } catch {
          fetched = await createReleasePack({
            pack_id: packId,
            artist: "SNUFFRAGA",
            genre: "Electronic"
          });
        }
        setRelease(fetched);
        setStage(fetched.status === "ready" ? "ready" : "created");
      } catch (e) {
        setError(formatError(e));
        setStage("error");
      }
    });
  };

  const handleToggleChecklist = (code: string, currentPassed: boolean): void => {
    if (!release) return;
    setError(null);
    startTransition(async () => {
      try {
        const updated = await updateReleaseChecklist(
          release.release_id,
          code,
          !currentPassed
        );
        setRelease(updated);
      } catch (e) {
        setError(formatError(e));
      }
    });
  };

  const handleMarkReady = (): void => {
    if (!release) return;
    setError(null);
    startTransition(async () => {
      try {
        const updated = await markReleaseReady(release.release_id);
        setRelease(updated);
        setStage("ready");
      } catch (e) {
        setError(formatError(e));
      }
    });
  };

  return (
    <section className="mt-8">
      <header className="mb-4 flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
        <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          RELEASE PACK
        </h2>
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {stage === "idle" && "READY"}
          {stage === "created" && "DRAFT"}
          {stage === "ready" && "RELEASE READY"}
          {stage === "error" && "ERROR"}
        </span>
      </header>

      {/* Stage: idle */}
      {stage === "idle" && (
        <div className="grid gap-3">
          <p className="font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
            Convert this pack into a release-ready package with social copy,
            compliance checklist, and asset placeholders.
          </p>
          <button
            type="button"
            onClick={handleCreate}
            disabled={isPending}
            className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
            style={{ minHeight: "var(--ss-tap-target)" }}
          >
            {isPending ? "CREATING…" : "CREATE RELEASE PACK"}
          </button>
        </div>
      )}

      {/* Stage: created or ready */}
      {(stage === "created" || stage === "ready") && release && (
        <div className="grid gap-4">
          {/* Release meta */}
          <ReleaseMetaView release={release} />

          {/* Social Copy */}
          <SocialCopyView release={release} />

          {/* Compliance Checklist */}
          <ComplianceChecklistView
            items={release.compliance_checklist}
            allPassed={release.compliance_passed}
            onToggle={handleToggleChecklist}
            disabled={isPending || stage === "ready"}
          />

          {/* Asset Placeholders */}
          <AssetListView assets={release.assets} />

          {/* Dropbox Target */}
          {release.dropbox_target && (
            <div
              className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
              style={{ backgroundColor: "var(--ss-panel-elevated)" }}
            >
              <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                DROPBOX TARGET
              </span>
              <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                {release.dropbox_target}
              </span>
            </div>
          )}

          {/* Mark Ready button */}
          {stage === "created" && release.compliance_passed && (
            <button
              type="button"
              onClick={handleMarkReady}
              disabled={isPending}
              className="w-full border border-[color:var(--ss-border-accent)] px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] disabled:opacity-50"
              style={{ minHeight: "var(--ss-tap-target)" }}
            >
              {isPending ? "MARKING…" : "MARK RELEASE READY"}
            </button>
          )}

          {/* Ready confirmation */}
          {stage === "ready" && (
            <div
              className="border px-4 py-3 text-center font-mono text-[0.7rem] font-black uppercase tracking-widest"
              style={{
                borderColor: "var(--ss-accent)",
                color: "var(--ss-accent)",
                backgroundColor: "var(--ss-accent-faint)"
              }}
            >
              RELEASE PACK READY FOR DISTRIBUTION
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error !== null && (
        <p
          className="mt-2 border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {error}
        </p>
      )}
    </section>
  );
}

function ReleaseMetaView({ release }: Readonly<{ release: ReleasePack }>) {
  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      <MetaPill label="ARTIST" value={release.artist} />
      <MetaPill label="STATUS" value={release.status.toUpperCase()} accent={release.status === "ready"} />
      <MetaPill label="GENRE" value={release.genre || "—"} />
      <MetaPill
        label="DURATION"
        value={
          release.duration_seconds
            ? `${Math.floor(release.duration_seconds / 60)}:${String(Math.floor(release.duration_seconds % 60)).padStart(2, "0")}`
            : "—"
        }
      />
    </div>
  );
}

function SocialCopyView({ release }: Readonly<{ release: ReleasePack }>) {
  return (
    <div className="grid gap-2">
      <h3 className="font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        SOCIAL COPY
      </h3>
      <div className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
        <CopyBlock label="SOUNDCLOUD" text={release.social_copy.soundcloud_description} />
        <CopyBlock label="TIKTOK" text={release.social_copy.tiktok_caption} />
        <CopyBlock label="INSTAGRAM" text={release.social_copy.instagram_caption} />
        {release.social_copy.hashtags.length > 0 && (
          <div className="px-3 py-2" style={{ backgroundColor: "var(--ss-panel)" }}>
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              TAGS
            </span>
            <p className="mt-1 font-mono text-[0.6rem] text-[color:var(--ss-accent)]">
              {release.social_copy.hashtags.join(" ")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function CopyBlock({ label, text }: Readonly<{ label: string; text: string }>) {
  return (
    <div className="px-3 py-2" style={{ backgroundColor: "var(--ss-panel)" }}>
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <p className="mt-1 whitespace-pre-wrap font-mono text-[0.6rem] leading-4 text-[color:var(--ss-text-secondary)]">
        {text || "—"}
      </p>
    </div>
  );
}

function ComplianceChecklistView({
  items,
  allPassed,
  onToggle,
  disabled
}: Readonly<{
  items: ReadonlyArray<ComplianceChecklistItem>;
  allPassed: boolean;
  onToggle: (code: string, passed: boolean) => void;
  disabled: boolean;
}>) {
  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between">
        <h3 className="font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          COMPLIANCE CHECKLIST
        </h3>
        <span
          className="font-mono text-[0.55rem] font-black uppercase tracking-widest"
          style={{ color: allPassed ? "var(--ss-accent)" : "var(--ss-warning)" }}
        >
          {allPassed ? "ALL PASSED" : `${items.filter((i) => i.passed).length}/${items.length}`}
        </span>
      </div>
      <div className="grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
        {items.map((item) => (
          <button
            key={item.code}
            type="button"
            onClick={() => onToggle(item.code, item.passed)}
            disabled={disabled}
            className="flex items-center gap-3 px-3 py-2 text-left disabled:opacity-60"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <span
              className="flex h-4 w-4 shrink-0 items-center justify-center border font-mono text-[0.5rem]"
              style={{
                borderColor: item.passed ? "var(--ss-accent)" : "var(--ss-border-strong)",
                backgroundColor: item.passed ? "var(--ss-accent-faint)" : "transparent",
                color: item.passed ? "var(--ss-accent)" : "var(--ss-text-muted)"
              }}
            >
              {item.passed ? "Y" : ""}
            </span>
            <div className="grid gap-0.5">
              <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                {item.label}
              </span>
              {item.notes && (
                <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                  {item.notes}
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function AssetListView({ assets }: Readonly<{ assets: ReadonlyArray<ReleaseAssetPlaceholder> }>) {
  return (
    <div className="grid gap-2">
      <h3 className="font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        ASSETS
      </h3>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {assets.map((asset) => (
          <div
            key={asset.asset_type}
            className="flex flex-col gap-1 border border-[color:var(--ss-border)] px-2 py-1.5"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {asset.label}
            </span>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.55rem] uppercase text-[color:var(--ss-text-secondary)]">
                .{asset.expected_format}
              </span>
              <span
                className="font-mono text-[0.5rem] font-black uppercase"
                style={{ color: asset.ready ? "var(--ss-accent)" : "var(--ss-warning)" }}
              >
                {asset.ready ? "READY" : "PENDING"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetaPill({
  label,
  value,
  accent = false
}: Readonly<{ label: string; value: string; accent?: boolean }>) {
  return (
    <div
      className="flex items-center justify-between border border-[color:var(--ss-border)] px-2 py-1.5"
      style={{ backgroundColor: "var(--ss-panel-elevated)" }}
    >
      <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        {label}
      </span>
      <span
        className="font-mono text-[0.7rem] font-black text-[color:var(--ss-text-primary)]"
        style={accent ? { color: "var(--ss-accent)" } : undefined}
      >
        {value}
      </span>
    </div>
  );
}

function formatError(error: unknown): string {
  if (error instanceof InferenceClientError) {
    return error.status ? `${error.status} · ${error.message}` : error.message;
  }
  if (error instanceof Error) return error.message;
  return "release_pack_error";
}
