"use client";

import { useState, useTransition, useCallback, useRef } from "react";
import Link from "next/link";
import {
  updateReleaseChecklist,
  markReleaseReady,
  uploadReleaseCover,
  uploadReleaseAudioMaster,
  uploadReleaseStemPack,
  buildReleaseExport,
  createSoundCloudPreview,
  createSoundCloudJob,
  publishMockSoundCloud,
  createMerchCapsule,
  lockMerchCapsule,
  exportMockMerchCapsule,
  getMerchProviderStatus,
  updateMerchProduct,
  createDistributionPack,
  updateDistributionPackStatus,
  toggleDistributionReadinessItem,
  createCampaign,
  getCampaignByRelease,
  updateCampaign,
  createVinylRelease,
  getVinylReleaseByRelease,
  updateVinylReleaseStatus,
  getVinylExport,
  InferenceClientError
} from "../../../_lib/inference";
import type {
  ReleasePack,
  ComplianceChecklistItem,
  CoverValidationWarning,
  AudioValidationWarning,
  StemPackValidationWarning,
  StemPackManifestEntry,
  ReleaseAssetPlaceholder,
  SocialCopy,
  ReleaseExportResult,
  ReleaseExportWarning,
  SoundCloudPublishPreview,
  SoundCloudPublishJob,
  SoundCloudPublishWarning,
  SoundCloudMetadata,
  MerchCapsule,
  MerchCapsuleWarning,
  MerchProduct,
  MerchExportPayload,
  MerchProviderExportNotes,
  MerchProviderAggregation,
  MerchProviderProductStatus,
  MerchProductUpdateResult,
  DistributionPack,
  DistributionReadinessItem,
  DistributionPackStatus,
  Campaign,
  CampaignTask,
  CampaignWarning,
  CampaignChannel,
  CampaignStatus,
  CampaignTaskStatus,
  VinylReleaseObject,
  VinylExportPayload,
  VinylReleaseStatus,
  VinylFormat,
  VinylEditionType,
  VinylReadinessItem
} from "../../../_lib/generated-inference-types";

type Props = Readonly<{
  initialRelease: ReleasePack;
}>;

/**
 * ReleaseDetailView — interactive client component for a single release (S24).
 *
 * Handles:
 * - Release metadata display
 * - Social copy display with copy-to-clipboard
 * - Compliance checklist editing (toggle items)
 * - Mark ready flow
 * - Asset placeholder display
 * - Dropbox target display
 */
export function ReleaseDetailView({ initialRelease }: Props) {
  const [release, setRelease] = useState<ReleasePack>(initialRelease);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const isReady = release.status === "ready";

  const handleToggleChecklist = useCallback(
    (code: string, currentPassed: boolean): void => {
      if (isReady) return;
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
    },
    [release.release_id, isReady]
  );

  const handleMarkReady = useCallback((): void => {
    if (!release.compliance_passed || isReady) return;
    setError(null);
    startTransition(async () => {
      try {
        const updated = await markReleaseReady(release.release_id);
        setRelease(updated);
      } catch (e) {
        setError(formatError(e));
      }
    });
  }, [release.release_id, release.compliance_passed, isReady]);

  return (
    <div className="grid gap-8">
      {/* Status banner */}
      {isReady && (
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

      {/* Overview grid */}
      <section className="grid gap-px border border-[color:var(--ss-border)] bg-[color:var(--ss-border)] md:grid-cols-4">
        <MetaCell label="Artist" value={release.artist} />
        <MetaCell
          label="Status"
          value={release.status.toUpperCase()}
          accent={isReady}
        />
        <MetaCell label="Genre" value={release.genre || "—"} />
        <MetaCell label="BPM" value={release.bpm ? String(release.bpm) : "—"} />
        <MetaCell label="Key" value={release.key_signature || "—"} />
        <MetaCell
          label="Duration"
          value={
            release.duration_seconds
              ? `${Math.floor(release.duration_seconds / 60)}:${String(Math.floor(release.duration_seconds % 60)).padStart(2, "0")}`
              : "—"
          }
        />
        <MetaCell label="Operator" value={release.operator_id || "—"} />
        <MetaCell
          label="Created"
          value={new Date(release.created_at)
            .toISOString()
            .slice(0, 16)
            .replace("T", " ")}
        />
      </section>

      {/* Description */}
      {release.description && (
        <section>
          <SectionHeader title="DESCRIPTION" />
          <p className="mt-3 font-mono text-[0.7rem] leading-5 text-[color:var(--ss-text-secondary)]">
            {release.description}
          </p>
        </section>
      )}

      {/* Social Copy */}
      <SocialCopySection socialCopy={release.social_copy} />

      {/* Compliance Checklist */}
      <ComplianceChecklistSection
        items={release.compliance_checklist}
        allPassed={release.compliance_passed}
        onToggle={handleToggleChecklist}
        disabled={isPending || isReady}
      />

      {/* Mark Ready */}
      {!isReady && release.compliance_passed && (
        <button
          type="button"
          onClick={handleMarkReady}
          disabled={isPending}
          className="w-full border border-[color:var(--ss-border-accent)] px-4 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent-faint)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--ss-accent)] disabled:opacity-50"
          style={{ minHeight: "var(--ss-tap-target)" }}
        >
          {isPending ? "MARKING READY…" : "MARK RELEASE READY"}
        </button>
      )}

      {/* Assets */}
      <AssetSection assets={release.assets} />

      {/* Cover Upload */}
      <CoverUploadSection
        release={release}
        onReleaseUpdate={setRelease}
      />

      {/* Audio Master Upload */}
      <AudioMasterUploadSection
        release={release}
        onReleaseUpdate={setRelease}
      />

      {/* Stem Pack Upload */}
      <StemPackUploadSection
        release={release}
        onReleaseUpdate={setRelease}
      />

      {/* Release Export */}
      <ReleaseExportSection release={release} />

      {/* SoundCloud Handoff */}
      <SoundCloudHandoffSection release={release} />

      {/* Merch Capsule */}
      <MerchCapsuleSection release={release} />

      {/* Provider Matrix (S43) */}
      <ProviderMatrixSection release={release} />

      {/* Ditto Distribution */}
      <DittoDistributionSection release={release} />

      {/* Campaign OS */}
      <CampaignSection release={release} />

      {/* Vinyl Release */}
      <VinylReleaseSection release={release} />

      {/* Dropbox Target */}
      {release.dropbox_target && (
        <section>
          <SectionHeader title="DROPBOX TARGET" />
          <div
            className="mt-3 flex items-center justify-between border border-[color:var(--ss-border)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.7rem] text-[color:var(--ss-text-primary)]">
              {release.dropbox_target}
            </span>
            <CopyButton text={release.dropbox_target} label="PATH" />
          </div>
        </section>
      )}

      {/* Pack reference */}
      <section>
        <SectionHeader title="SOURCE PACK" />
        <div className="mt-3">
          <Link
            href={`/admin/soundsystem/library/${release.pack_id}`}
            className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
          >
            VIEW EXPORT PACK → {release.pack_id}
          </Link>
        </div>
      </section>

      {/* Error */}
      {error !== null && (
        <p
          className="border border-[color:var(--ss-warning-dim)] px-3 py-2 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
          role="alert"
        >
          {error}
        </p>
      )}

      {/* Release ID footer */}
      <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
        RELEASE · {release.release_id}
      </p>
    </div>
  );
}

// ---------- Sub-components ----------

function SocialCopySection({
  socialCopy
}: Readonly<{ socialCopy: SocialCopy }>) {
  return (
    <section>
      <SectionHeader title="SOCIAL COPY" />
      <div className="mt-3 grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
        <CopyBlock
          label="SOUNDCLOUD"
          text={socialCopy.soundcloud_description}
        />
        <CopyBlock label="TIKTOK" text={socialCopy.tiktok_caption} />
        <CopyBlock label="INSTAGRAM" text={socialCopy.instagram_caption} />
        {socialCopy.hashtags.length > 0 && (
          <div
            className="flex items-center justify-between px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <div>
              <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                HASHTAGS
              </span>
              <p className="mt-1 font-mono text-[0.65rem] text-[color:var(--ss-accent)]">
                {socialCopy.hashtags.join(" ")}
              </p>
            </div>
            <CopyButton text={socialCopy.hashtags.join(" ")} label="TAGS" />
          </div>
        )}
      </div>
    </section>
  );
}

function CopyBlock({ label, text }: Readonly<{ label: string; text: string }>) {
  return (
    <div
      className="flex items-start justify-between gap-3 px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex-1">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {label}
        </span>
        <p className="mt-1 whitespace-pre-wrap font-mono text-[0.65rem] leading-5 text-[color:var(--ss-text-secondary)]">
          {text || "—"}
        </p>
      </div>
      {text && <CopyButton text={text} label={label} />}
    </div>
  );
}

function CopyButton({
  text,
  label
}: Readonly<{ text: string; label: string }>) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available — ignore silently
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="shrink-0 border border-[color:var(--ss-border-strong)] px-2 py-1 font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:border-[color:var(--ss-accent)] hover:text-[color:var(--ss-accent)]"
      title={`Copy ${label} to clipboard`}
    >
      {copied ? "COPIED" : "COPY"}
    </button>
  );
}

function ComplianceChecklistSection({
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
    <section>
      <div className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
        <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
          COMPLIANCE CHECKLIST
        </h2>
        <span
          className="font-mono text-[0.6rem] font-black uppercase tracking-widest"
          style={{ color: allPassed ? "var(--ss-accent)" : "var(--ss-warning)" }}
        >
          {allPassed
            ? "ALL PASSED"
            : `${items.filter((i) => i.passed).length}/${items.length}`}
        </span>
      </div>
      <div className="mt-3 grid gap-px border border-[color:var(--ss-border)]" style={{ backgroundColor: "var(--ss-border)" }}>
        {items.map((item) => (
          <button
            key={item.code}
            type="button"
            onClick={() => onToggle(item.code, item.passed)}
            disabled={disabled}
            className="flex items-center gap-4 px-4 py-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-60"
            style={{ backgroundColor: "var(--ss-panel)" }}
          >
            <span
              className="flex h-5 w-5 shrink-0 items-center justify-center border font-mono text-[0.55rem] font-black"
              style={{
                borderColor: item.passed
                  ? "var(--ss-accent)"
                  : "var(--ss-border-strong)",
                backgroundColor: item.passed
                  ? "var(--ss-accent-faint)"
                  : "transparent",
                color: item.passed ? "var(--ss-accent)" : "var(--ss-text-muted)"
              }}
            >
              {item.passed ? "Y" : ""}
            </span>
            <div className="grid gap-1">
              <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                {item.label}
              </span>
              {item.notes && (
                <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
                  {item.notes}
                </span>
              )}
            </div>
            <span className="ml-auto font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {item.code}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function CoverUploadSection({
  release,
  onReleaseUpdate
}: Readonly<{
  release: ReleasePack;
  onReleaseUpdate: (r: ReleasePack) => void;
}>) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<CoverValidationWarning[]>([]);
  const [uploadedArtifactId, setUploadedArtifactId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const coverAsset = release.assets.find((a) => a.asset_type === "cover_art");
  const isReady = coverAsset?.ready === true;

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Validate file type on client side
      if (!["image/png", "image/jpeg"].includes(file.type)) {
        setError("Only PNG and JPEG are accepted for cover art.");
        return;
      }

      // Validate file size on client side (20 MB)
      if (file.size > 20 * 1024 * 1024) {
        setError("Cover image must be under 20 MB.");
        return;
      }

      setError(null);
      setWarnings([]);

      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        if (!base64) {
          setError("Failed to read file.");
          return;
        }

        startTransition(async () => {
          try {
            const result = await uploadReleaseCover(release.release_id, {
              filename: file.name,
              content_type: file.type,
              content_base64: base64
            });
            onReleaseUpdate(result.release);
            setWarnings([...result.warnings]);
            setUploadedArtifactId(result.artifact.artifact_id);
            setError(null);
          } catch (err) {
            setError(formatError(err));
          }
        });
      };
      reader.readAsDataURL(file);
    },
    [release.release_id, onReleaseUpdate]
  );

  return (
    <section>
      <SectionHeader title="COVER ART" />
      <div className="mt-3 grid gap-3">
        {/* Current state */}
        {isReady ? (
          <div
            className="flex items-center justify-between border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-accent)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <div className="grid gap-1">
              <span
                className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
                style={{ color: "var(--ss-accent)" }}
              >
                COVER ART UPLOADED
              </span>
              {coverAsset?.artifact_id && (
                <Link
                  href={`/admin/soundsystem/artifacts/${coverAsset.artifact_id}`}
                  className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
                >
                  OPEN ARTIFACT &rarr; {coverAsset.artifact_id.slice(0, 8)}
                </Link>
              )}
            </div>
            <span
              className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase tracking-widest"
              style={{
                borderColor: "var(--ss-border-accent)",
                color: "var(--ss-accent)"
              }}
            >
              READY
            </span>
          </div>
        ) : (
          <div
            className="border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-strong)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No cover art uploaded yet.
            </span>
          </div>
        )}

        {/* Upload control */}
        <div className="grid gap-2">
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg"
              onChange={handleFileChange}
              disabled={isPending}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isPending}
              className="border px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-primary)"
              }}
            >
              {isPending
                ? "UPLOADING…"
                : isReady
                  ? "REPLACE COVER"
                  : "UPLOAD COVER ART"}
            </button>
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              PNG / JPEG &middot; MIN 1400&times;1400 PX &middot; SQUARE &middot; MAX 20 MB
            </span>
          </div>

          {/* Warnings */}
          {warnings.length > 0 &&
            warnings.map((w) => (
              <p
                key={w.code}
                className="font-mono text-[0.6rem] uppercase tracking-widest"
                style={{ color: "var(--ss-warning)" }}
              >
                {w.message}
              </p>
            ))}

          {/* Success artifact link */}
          {uploadedArtifactId && !error && (
            <Link
              href={`/admin/soundsystem/artifacts/${uploadedArtifactId}`}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
            >
              VIEW UPLOADED ARTIFACT &rarr;
            </Link>
          )}

          {/* Error */}
          {error && (
            <p
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {error}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function AudioMasterUploadSection({
  release,
  onReleaseUpdate
}: Readonly<{
  release: ReleasePack;
  onReleaseUpdate: (r: ReleasePack) => void;
}>) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<AudioValidationWarning[]>([]);
  const [uploadedArtifactId, setUploadedArtifactId] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    channels: number | null;
    sample_rate: number | null;
    sample_width_bytes: number | null;
    duration_seconds: number | null;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const audioAsset = release.assets.find((a) => a.asset_type === "audio_master");
  const isReady = audioAsset?.ready === true;

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Validate file type on client side
      if (
        !["audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave"].includes(
          file.type
        )
      ) {
        setError("Only WAV files are accepted for audio masters.");
        return;
      }

      // Validate file size on client side (120 MB)
      if (file.size > 120 * 1024 * 1024) {
        setError("Audio master must be under 120 MB.");
        return;
      }

      setError(null);
      setWarnings([]);
      setMetadata(null);

      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        if (!base64) {
          setError("Failed to read file.");
          return;
        }

        startTransition(async () => {
          try {
            const result = await uploadReleaseAudioMaster(release.release_id, {
              filename: file.name,
              content_type: file.type || "audio/wav",
              content_base64: base64
            });
            onReleaseUpdate(result.release);
            setWarnings([...result.warnings]);
            setUploadedArtifactId(result.artifact.artifact_id);
            setMetadata({
              channels: result.channels ?? null,
              sample_rate: result.sample_rate ?? null,
              sample_width_bytes: result.sample_width_bytes ?? null,
              duration_seconds: result.duration_seconds ?? null
            });
            setError(null);
          } catch (err) {
            setError(formatError(err));
          }
        });
      };
      reader.readAsDataURL(file);
    },
    [release.release_id, onReleaseUpdate]
  );

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <section>
      <SectionHeader title="AUDIO MASTER" />
      <div className="mt-3 grid gap-3">
        {/* Current state */}
        {isReady ? (
          <div
            className="flex items-center justify-between border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-accent)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <div className="grid gap-1">
              <span
                className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
                style={{ color: "var(--ss-accent)" }}
              >
                AUDIO MASTER UPLOADED
              </span>
              {audioAsset?.artifact_id && (
                <Link
                  href={`/admin/soundsystem/artifacts/${audioAsset.artifact_id}`}
                  className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
                >
                  OPEN ARTIFACT &rarr; {audioAsset.artifact_id.slice(0, 8)}
                </Link>
              )}
            </div>
            <span
              className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase"
              style={{
                borderColor: "var(--ss-border-accent)",
                color: "var(--ss-accent)"
              }}
            >
              READY
            </span>
          </div>
        ) : (
          <div
            className="border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-strong)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No audio master uploaded yet.
            </span>
          </div>
        )}

        {/* Metadata */}
        {metadata && (
          <div
            className="grid grid-cols-4 gap-2 border px-4 py-3"
            style={{
              borderColor: "var(--ss-border)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            {metadata.channels != null && (
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  CHANNELS
                </span>
                <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                  {metadata.channels === 1 ? "MONO" : "STEREO"}
                </span>
              </div>
            )}
            {metadata.sample_rate != null && (
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  SAMPLE RATE
                </span>
                <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                  {(metadata.sample_rate / 1000).toFixed(1)} KHZ
                </span>
              </div>
            )}
            {metadata.sample_width_bytes != null && (
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  BIT DEPTH
                </span>
                <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                  {metadata.sample_width_bytes * 8}-BIT
                </span>
              </div>
            )}
            {metadata.duration_seconds != null && (
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  DURATION
                </span>
                <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                  {formatDuration(metadata.duration_seconds)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Upload control */}
        <div className="grid gap-2">
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/wav,audio/x-wav,.wav"
              onChange={handleFileChange}
              disabled={isPending}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isPending}
              className="border px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-primary)"
              }}
            >
              {isPending
                ? "UPLOADING…"
                : isReady
                  ? "REPLACE AUDIO MASTER"
                  : "UPLOAD AUDIO MASTER"}
            </button>
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              WAV ONLY &middot; 48 KHZ+ &middot; 24-BIT+ &middot; STEREO &middot; MAX 120 MB
            </span>
          </div>

          {/* Warnings */}
          {warnings.length > 0 &&
            warnings.map((w) => (
              <p
                key={w.code}
                className="font-mono text-[0.6rem] uppercase tracking-widest"
                style={{ color: "var(--ss-warning)" }}
              >
                {w.message}
              </p>
            ))}

          {/* Success artifact link */}
          {uploadedArtifactId && !error && (
            <Link
              href={`/admin/soundsystem/artifacts/${uploadedArtifactId}`}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
            >
              VIEW UPLOADED ARTIFACT &rarr;
            </Link>
          )}

          {/* Error */}
          {error && (
            <p
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {error}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function StemPackUploadSection({
  release,
  onReleaseUpdate
}: Readonly<{
  release: ReleasePack;
  onReleaseUpdate: (r: ReleasePack) => void;
}>) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<StemPackValidationWarning[]>([]);
  const [uploadedArtifactId, setUploadedArtifactId] = useState<string | null>(null);
  const [entries, setEntries] = useState<StemPackManifestEntry[]>([]);
  const [totalFiles, setTotalFiles] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const stemsAsset = release.assets.find((a) => a.asset_type === "stems_archive");
  const isReady = stemsAsset?.ready === true;

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Validate file type on client side
      if (
        !["application/zip", "application/x-zip-compressed"].includes(file.type) &&
        !file.name.endsWith(".zip")
      ) {
        setError("Only ZIP archives are accepted for stem packs.");
        return;
      }

      // Validate file size on client side (250 MB)
      if (file.size > 250 * 1024 * 1024) {
        setError("Stem pack must be under 250 MB.");
        return;
      }

      setError(null);
      setWarnings([]);
      setEntries([]);
      setTotalFiles(0);

      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        if (!base64) {
          setError("Failed to read file.");
          return;
        }

        startTransition(async () => {
          try {
            const result = await uploadReleaseStemPack(release.release_id, {
              filename: file.name,
              content_type: file.type || "application/zip",
              content_base64: base64
            });
            onReleaseUpdate(result.release);
            setWarnings([...result.warnings]);
            setUploadedArtifactId(result.artifact.artifact_id);
            setEntries([...result.entries]);
            setTotalFiles(result.total_files);
            setError(null);
          } catch (err) {
            setError(formatError(err));
          }
        });
      };
      reader.readAsDataURL(file);
    },
    [release.release_id, onReleaseUpdate]
  );

  return (
    <section>
      <SectionHeader title="STEM PACK" />
      <div className="mt-3 grid gap-3">
        {/* Current state */}
        {isReady ? (
          <div
            className="flex items-center justify-between border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-accent)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <div className="grid gap-1">
              <span
                className="font-mono text-[0.65rem] font-black uppercase tracking-widest"
                style={{ color: "var(--ss-accent)" }}
              >
                STEM PACK UPLOADED
              </span>
              {stemsAsset?.artifact_id && (
                <Link
                  href={`/admin/soundsystem/artifacts/${stemsAsset.artifact_id}`}
                  className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
                >
                  OPEN ARTIFACT &rarr; {stemsAsset.artifact_id.slice(0, 8)}
                </Link>
              )}
            </div>
            <span
              className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase"
              style={{
                borderColor: "var(--ss-border-accent)",
                color: "var(--ss-accent)"
              }}
            >
              READY
            </span>
          </div>
        ) : (
          <div
            className="border px-4 py-3"
            style={{
              borderColor: "var(--ss-border-strong)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <span className="font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No stem pack uploaded yet.
            </span>
          </div>
        )}

        {/* Entry list preview */}
        {entries.length > 0 && (
          <div
            className="border px-4 py-3"
            style={{
              borderColor: "var(--ss-border)",
              backgroundColor: "var(--ss-panel-elevated)"
            }}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                {totalFiles} FILES
              </span>
              <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                {entries.filter((e) => e.is_audio).length} AUDIO
              </span>
            </div>
            <div className="grid gap-1">
              {entries.slice(0, 12).map((entry) => (
                <div
                  key={entry.filename}
                  className="flex items-center justify-between"
                >
                  <span
                    className="truncate font-mono text-[0.55rem] text-[color:var(--ss-text-secondary)]"
                    title={entry.filename}
                  >
                    {entry.filename}
                  </span>
                  <span className="ml-2 shrink-0 font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                    {entry.is_audio ? entry.extension.toUpperCase() : entry.extension}
                  </span>
                </div>
              ))}
              {entries.length > 12 && (
                <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                  +{entries.length - 12} more files
                </span>
              )}
            </div>
          </div>
        )}

        {/* Upload control */}
        <div className="grid gap-2">
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="application/zip,.zip"
              onChange={handleFileChange}
              disabled={isPending}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isPending}
              className="border px-4 py-2 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-primary)"
              }}
            >
              {isPending
                ? "UPLOADING…"
                : isReady
                  ? "REPLACE STEM PACK"
                  : "UPLOAD STEM PACK"}
            </button>
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              ZIP ONLY &middot; MAX 250 MB &middot; SMALL/MEDIUM PACKS
            </span>
          </div>

          {/* Size warning */}
          <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            BASE64 JSON UPLOAD. LARGE STEM PACKS REQUIRE FUTURE CHUNKED UPLOADER.
          </p>

          {/* Warnings */}
          {warnings.length > 0 &&
            warnings.map((w) => (
              <p
                key={w.code}
                className="font-mono text-[0.6rem] uppercase tracking-widest"
                style={{ color: "var(--ss-warning)" }}
              >
                {w.message}
              </p>
            ))}

          {/* Success artifact link */}
          {uploadedArtifactId && !error && (
            <Link
              href={`/admin/soundsystem/artifacts/${uploadedArtifactId}`}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
            >
              VIEW UPLOADED ARTIFACT &rarr;
            </Link>
          )}

          {/* Error */}
          {error && (
            <p
              className="font-mono text-[0.6rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              {error}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function AssetSection({
  assets
}: Readonly<{ assets: ReadonlyArray<ReleaseAssetPlaceholder> }>) {
  return (
    <section>
      <SectionHeader title="ASSETS" />
      <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-4">
        {assets.map((asset) => (
          <div
            key={asset.asset_type}
            className="flex flex-col gap-2 border border-[color:var(--ss-border)] px-3 py-2"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {asset.label}
            </span>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.6rem] uppercase text-[color:var(--ss-text-secondary)]">
                .{asset.expected_format}
              </span>
              <span
                className="font-mono text-[0.55rem] font-black uppercase"
                style={{
                  color: asset.ready ? "var(--ss-accent)" : "var(--ss-warning)"
                }}
              >
                {asset.ready ? "READY" : "PENDING"}
              </span>
            </div>
            {asset.artifact_id && (
              <Link
                href={`/admin/soundsystem/artifacts/${asset.artifact_id}`}
                className="font-mono text-[0.5rem] text-[color:var(--ss-accent)] hover:underline"
              >
                {asset.artifact_id.slice(0, 8)}
              </Link>
            )}
            {asset.path && !asset.artifact_id && (
              <span className="break-all font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                {asset.path}
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Release Export (S34)
// ---------------------------------------------------------------------------

function ReleaseExportSection({
  release
}: Readonly<{ release: ReleasePack }>) {
  const [exporting, setExporting] = useState(false);
  const [result, setResult] = useState<ReleaseExportResult | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const hasAnyAsset = release.assets.some(
    (a: ReleaseAssetPlaceholder) => a.ready && a.artifact_id
  );

  const handleExport = useCallback(async () => {
    setExporting(true);
    setExportError(null);
    setResult(null);
    try {
      const res = await buildReleaseExport(release.release_id);
      setResult(res);
    } catch (err) {
      setExportError(formatError(err));
    } finally {
      setExporting(false);
    }
  }, [release.release_id]);

  return (
    <section>
      <SectionHeader title="RELEASE EXPORT" />
      <div className="mt-4 space-y-3">
        <button
          type="button"
          disabled={exporting || !hasAnyAsset}
          onClick={handleExport}
          className="w-full border border-[color:var(--ss-accent)] px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            backgroundColor: exporting ? "var(--ss-panel)" : "var(--ss-accent)",
            color: exporting ? "var(--ss-text-muted)" : "var(--ss-bg)"
          }}
        >
          {exporting ? "BUILDING EXPORT ZIP…" : "BUILD EXPORT ZIP"}
        </button>

        {!hasAnyAsset && (
          <p className="font-mono text-[0.6rem] text-[color:var(--ss-text-muted)]">
            Upload at least one asset (cover, audio master, or stem pack) before exporting.
          </p>
        )}

        {exportError && (
          <div
            className="border border-[color:var(--ss-error)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.65rem] text-[color:var(--ss-error)]">
              {exportError}
            </span>
          </div>
        )}

        {result && (
          <div
            className="space-y-3 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.6rem] font-bold uppercase tracking-widest text-[color:var(--ss-accent)]">
                {result.status}
              </span>
              <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
                {result.total_files} files &middot; {(result.total_size_bytes / 1024).toFixed(1)} KB
              </span>
            </div>

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="space-y-1">
                {result.warnings.map((w: ReleaseExportWarning, i: number) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 font-mono text-[0.6rem] text-[color:var(--ss-warning)]"
                  >
                    <span className="shrink-0">⚠</span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Entries */}
            <div className="space-y-1">
              {result.entries.map((e, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between font-mono text-[0.55rem]"
                >
                  <span className="text-[color:var(--ss-text-primary)]">{e.path}</span>
                  <span className="text-[color:var(--ss-text-muted)]">
                    {(e.size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
              ))}
            </div>

            {/* Artifact link */}
            <Link
              href={`/admin/soundsystem/artifacts/${result.artifact.artifact_id}`}
              className="inline-block font-mono text-[0.6rem] text-[color:var(--ss-accent)] hover:underline"
            >
              View export artifact &rarr; {result.artifact.artifact_id.slice(0, 8)}
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// SoundCloud Handoff (S36)
// ---------------------------------------------------------------------------

function SoundCloudHandoffSection({
  release
}: Readonly<{ release: ReleasePack }>) {
  const [preview, setPreview] = useState<SoundCloudPublishPreview | null>(null);
  const [job, setJob] = useState<SoundCloudPublishJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [scError, setScError] = useState<string | null>(null);

  const handlePreview = useCallback(async () => {
    setLoading(true);
    setScError(null);
    try {
      const p = await createSoundCloudPreview(release);
      setPreview(p);
    } catch (err) {
      setScError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [release]);

  const handleCreateJob = useCallback(async () => {
    setLoading(true);
    setScError(null);
    try {
      const j = await createSoundCloudJob({ release_id: release.release_id });
      setJob(j);
    } catch (err) {
      setScError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [release.release_id]);

  const handlePublishMock = useCallback(async () => {
    if (!job) return;
    setLoading(true);
    setScError(null);
    try {
      const updated = await publishMockSoundCloud(job.job_id);
      setJob(updated);
    } catch (err) {
      setScError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [job]);

  return (
    <section>
      <SectionHeader title="SOUNDCLOUD HANDOFF" />
      <div className="mt-4 space-y-3">
        {/* Step 1: Preview */}
        {!preview && !job && (
          <button
            type="button"
            disabled={loading}
            onClick={handlePreview}
            className="w-full border px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
            style={{
              borderColor: "var(--ss-border-strong)",
              color: "var(--ss-text-primary)"
            }}
          >
            {loading ? "BUILDING PREVIEW…" : "CREATE SOUNDCLOUD PREVIEW"}
          </button>
        )}

        {/* Preview card */}
        {preview && !job && (
          <div
            className="space-y-3 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <SoundCloudMetadataDisplay metadata={preview.metadata} />

            {/* Warnings */}
            {preview.warnings.length > 0 && (
              <div className="space-y-1">
                {preview.warnings.map((w: SoundCloudPublishWarning, i: number) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 font-mono text-[0.6rem] text-[color:var(--ss-warning)]"
                  >
                    <span className="shrink-0">!</span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Can publish / Blocked */}
            <div className="flex items-center justify-between">
              <span
                className="font-mono text-[0.6rem] font-bold uppercase tracking-widest"
                style={{
                  color: preview.can_publish
                    ? "var(--ss-accent)"
                    : "var(--ss-warning)"
                }}
              >
                {preview.can_publish ? "READY FOR PUBLISH" : "BLOCKED"}
              </span>
              {preview.blocked_reason && (
                <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
                  {preview.blocked_reason}
                </span>
              )}
            </div>

            {/* Create Job button */}
            <button
              type="button"
              disabled={loading}
              onClick={handleCreateJob}
              className="w-full border px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
              style={{
                borderColor: preview.can_publish
                  ? "var(--ss-accent)"
                  : "var(--ss-border-strong)",
                backgroundColor: preview.can_publish
                  ? "var(--ss-accent)"
                  : "transparent",
                color: preview.can_publish
                  ? "var(--ss-bg)"
                  : "var(--ss-text-primary)"
              }}
            >
              {loading ? "CREATING JOB…" : "CREATE PUBLISH JOB"}
            </button>
          </div>
        )}

        {/* Job card */}
        {job && (
          <div
            className="space-y-3 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                JOB {job.job_id.slice(0, 8)}
              </span>
              <StatusChip status={job.status} />
            </div>

            <SoundCloudMetadataDisplay metadata={job.metadata} />

            {/* Warnings */}
            {job.warnings.length > 0 && (
              <div className="space-y-1">
                {job.warnings.map((w: SoundCloudPublishWarning, i: number) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 font-mono text-[0.6rem] text-[color:var(--ss-warning)]"
                  >
                    <span className="shrink-0">!</span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Error */}
            {job.error && (
              <p
                className="font-mono text-[0.6rem] uppercase tracking-widest"
                style={{ color: "var(--ss-warning)" }}
              >
                {job.error}
              </p>
            )}

            {/* Mock Publish button — only for ready jobs */}
            {job.status === "ready" && (
              <button
                type="button"
                disabled={loading}
                onClick={handlePublishMock}
                className="w-full border border-[color:var(--ss-accent)] px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
                style={{
                  backgroundColor: "var(--ss-accent)",
                  color: "var(--ss-bg)"
                }}
              >
                {loading ? "PUBLISHING…" : "EXECUTE MOCK PUBLISH"}
              </button>
            )}

            {/* Provider mode */}
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              PROVIDER: {job.provider_mode}
            </span>
          </div>
        )}

        {/* Error */}
        {scError && (
          <div
            className="border border-[color:var(--ss-error)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.65rem] text-[color:var(--ss-error)]">
              {scError}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}

function SoundCloudMetadataDisplay({
  metadata
}: Readonly<{ metadata: SoundCloudMetadata }>) {
  return (
    <div className="grid gap-2">
      <div className="grid grid-cols-2 gap-2">
        <div className="grid gap-0.5">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TITLE
          </span>
          <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
            {metadata.title}
          </span>
        </div>
        <div className="grid gap-0.5">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            ARTIST
          </span>
          <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
            {metadata.artist}
          </span>
        </div>
      </div>
      {metadata.genre && (
        <div className="grid gap-0.5">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            GENRE
          </span>
          <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
            {metadata.genre}
          </span>
        </div>
      )}
      {metadata.tags.length > 0 && (
        <div className="grid gap-0.5">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            TAGS
          </span>
          <span className="font-mono text-[0.6rem] text-[color:var(--ss-accent)]">
            {metadata.tags.join(", ")}
          </span>
        </div>
      )}
      {metadata.description && (
        <div className="grid gap-0.5">
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            DESCRIPTION
          </span>
          <p className="line-clamp-3 font-mono text-[0.55rem] leading-4 text-[color:var(--ss-text-secondary)]">
            {metadata.description}
          </p>
        </div>
      )}
      <div className="flex gap-4">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
          {metadata.is_private ? "PRIVATE" : "PUBLIC"}
        </span>
        {metadata.audio_artifact_id && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-accent)]">
            AUDIO LINKED
          </span>
        )}
        {metadata.cover_artifact_id && (
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-accent)]">
            COVER LINKED
          </span>
        )}
      </div>
    </div>
  );
}

function StatusChip({ status }: Readonly<{ status: string }>) {
  const color =
    status === "published_mock"
      ? "var(--ss-accent)"
      : status === "blocked" || status === "failed"
        ? "var(--ss-warning)"
        : "var(--ss-text-muted)";

  return (
    <span
      className="border px-2 py-0.5 font-mono text-[0.55rem] font-black uppercase tracking-widest"
      style={{ borderColor: color, color }}
    >
      {status.replace("_", " ")}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Merch Capsule (S37)
// ---------------------------------------------------------------------------

function MerchCapsuleSection({
  release
}: Readonly<{ release: ReleasePack }>) {
  const [capsule, setCapsule] = useState<MerchCapsule | null>(null);
  const [exportPayload, setExportPayload] = useState<MerchExportPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [merchError, setMerchError] = useState<string | null>(null);

  const handleBuildCapsule = useCallback(async () => {
    setLoading(true);
    setMerchError(null);
    try {
      const c = await createMerchCapsule({ release_id: release.release_id });
      setCapsule(c);
    } catch (err) {
      setMerchError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [release.release_id]);

  const handleLock = useCallback(async () => {
    if (!capsule) return;
    setLoading(true);
    setMerchError(null);
    try {
      const locked = await lockMerchCapsule(capsule.capsule_id);
      setCapsule(locked);
    } catch (err) {
      setMerchError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [capsule]);

  const handleExportMock = useCallback(async () => {
    if (!capsule) return;
    setLoading(true);
    setMerchError(null);
    try {
      const payload = await exportMockMerchCapsule(capsule.capsule_id);
      setExportPayload(payload);
      setCapsule((prev) =>
        prev
          ? { ...prev, status: "exported_mock" as MerchCapsule["status"] }
          : prev
      );
    } catch (err) {
      setMerchError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [capsule]);

  return (
    <section>
      <SectionHeader title="MERCH CAPSULE" />
      <div className="mt-4 space-y-3">
        {/* Build button */}
        {!capsule && (
          <button
            type="button"
            disabled={loading}
            onClick={handleBuildCapsule}
            className="w-full border px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
            style={{
              borderColor: "var(--ss-border-strong)",
              color: "var(--ss-text-primary)"
            }}
          >
            {loading ? "BUILDING…" : "BUILD MERCH CAPSULE"}
          </button>
        )}

        {/* Capsule card */}
        {capsule && (
          <div
            className="space-y-3 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                {capsule.title}
              </span>
              <StatusChip status={capsule.status} />
            </div>

            {/* Product list with inline editing (S44) */}
            <div className="space-y-1">
              <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                PRODUCTS ({capsule.products.filter((p: MerchProduct) => p.active).length} ACTIVE / {capsule.max_active_products} MAX)
              </span>
              {capsule.products.map((p: MerchProduct) => (
                <MerchProductRow
                  key={p.product_id}
                  product={p}
                  capsuleId={capsule.capsule_id}
                  locked={capsule.status === "locked" || capsule.status === "archived" || capsule.status === "exported_mock"}
                  onUpdated={(result: MerchProductUpdateResult) => {
                    setCapsule(result.capsule);
                  }}
                />
              ))}
            </div>
            {capsule.status === "draft" && (
              <p className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                PROVIDER PAYLOADS ARE NOT AUTOMATICALLY REBUILT. REBUILD SHOPIFY/PRINTFUL/TIKTOK AFTER EDITING.
              </p>
            )}

            {/* Provider group chips */}
            <div className="flex flex-wrap gap-1">
              {capsule.provider_groups.map((g: string) => (
                <span
                  key={g}
                  className="border px-2 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
                  style={{
                    borderColor: "var(--ss-border-strong)",
                    color: "var(--ss-text-muted)"
                  }}
                >
                  {g.replace("_provider", "")}
                </span>
              ))}
            </div>

            {/* Warnings */}
            {capsule.warnings.length > 0 && (
              <div className="space-y-1">
                {capsule.warnings.map((w: MerchCapsuleWarning, i: number) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 font-mono text-[0.6rem] text-[color:var(--ss-warning)]"
                  >
                    <span className="shrink-0">!</span>
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              {capsule.status === "draft" && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleLock}
                  className="flex-1 border px-4 py-2 font-mono text-[0.65rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
                  style={{
                    borderColor: "var(--ss-border-strong)",
                    color: "var(--ss-text-primary)"
                  }}
                >
                  {loading ? "LOCKING…" : "LOCK CAPSULE"}
                </button>
              )}
              {(capsule.status === "draft" || capsule.status === "locked") && (
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleExportMock}
                  className="flex-1 border px-4 py-2 font-mono text-[0.65rem] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
                  style={{
                    borderColor: "var(--ss-accent)",
                    backgroundColor: "var(--ss-accent)",
                    color: "var(--ss-bg)"
                  }}
                >
                  {loading ? "EXPORTING…" : "EXPORT MOCK PAYLOAD"}
                </button>
              )}
            </div>

            {/* Mock notice */}
            <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              NO REAL SHOP SYNC. MOCK PROVIDER EXPORT ONLY.
            </p>
          </div>
        )}

        {/* Export payload */}
        {exportPayload && (
          <div
            className="space-y-3 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)]">
              MOCK EXPORT PAYLOAD
            </span>

            {/* Provider exports */}
            {exportPayload.provider_exports.map(
              (e: MerchProviderExportNotes, i: number) => (
                <div key={i} className="grid gap-0.5">
                  <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                    {e.provider_group.replace("_provider", "").toUpperCase()} ({e.product_count})
                  </span>
                  <p className="font-mono text-[0.55rem] leading-4 text-[color:var(--ss-text-secondary)]">
                    {e.notes}
                  </p>
                </div>
              )
            )}

            {/* Platform notes */}
            <div className="grid gap-1 border-t border-[color:var(--ss-border)] pt-2">
              <p className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                {exportPayload.tiktok_shop_notes}
              </p>
              <p className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                {exportPayload.printful_notes}
              </p>
              <p className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                {exportPayload.shopify_draft_notes}
              </p>
            </div>

            {/* Export warnings */}
            {exportPayload.warnings.length > 0 && (
              <div className="space-y-1">
                {exportPayload.warnings.map(
                  (w: MerchCapsuleWarning, i: number) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 font-mono text-[0.55rem] text-[color:var(--ss-warning)]"
                    >
                      <span className="shrink-0">!</span>
                      <span>{w.message}</span>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {merchError && (
          <div
            className="border border-[color:var(--ss-error)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.65rem] text-[color:var(--ss-error)]">
              {merchError}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Merch Product Row (S44)
// ---------------------------------------------------------------------------

function MerchProductRow({
  product,
  capsuleId,
  locked,
  onUpdated
}: Readonly<{
  product: MerchProduct;
  capsuleId: string;
  locked: boolean;
  onUpdated: (result: MerchProductUpdateResult) => void;
}>) {
  const [expanded, setExpanded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editTitle, setEditTitle] = useState(product.title);
  const [editActive, setEditActive] = useState(product.active);
  const [editAvailability, setEditAvailability] = useState(product.availability);
  const [editPricing, setEditPricing] = useState(product.price_positioning);
  const [editError, setEditError] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setEditError(null);
    try {
      const body: Record<string, unknown> = {};
      if (editTitle !== product.title) body.title = editTitle;
      if (editActive !== product.active) body.active = editActive;
      if (editAvailability !== product.availability) body.availability = editAvailability;
      if (editPricing !== product.price_positioning) body.price_positioning = editPricing;
      if (Object.keys(body).length === 0) {
        setExpanded(false);
        return;
      }
      const result = await updateMerchProduct(capsuleId, product.product_id, body);
      onUpdated(result);
      setExpanded(false);
    } catch (err) {
      setEditError(formatError(err));
    } finally {
      setSaving(false);
    }
  }, [capsuleId, product, editTitle, editActive, editAvailability, editPricing, onUpdated]);

  return (
    <div className="border-b border-[color:var(--ss-border)]">
      <div
        className="flex cursor-pointer items-center justify-between py-1.5 font-mono text-[0.55rem]"
        onClick={() => { if (!locked) setExpanded(!expanded); }}
      >
        <div className="flex items-center gap-2">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{
              backgroundColor: product.active
                ? "var(--ss-accent)"
                : "var(--ss-text-muted)"
            }}
          />
          <span className="text-[color:var(--ss-text-primary)]">
            {product.title}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[color:var(--ss-text-muted)]">
            {product.availability.replace("_", " ")}
          </span>
          {!locked && (
            <span className="text-[color:var(--ss-text-muted)]">
              {expanded ? "▴" : "▾"}
            </span>
          )}
          {locked && (
            <span className="text-[0.45rem] text-[color:var(--ss-text-muted)]">
              LOCKED
            </span>
          )}
        </div>
      </div>

      {expanded && !locked && (
        <div className="grid gap-2 pb-3 pl-4">
          {/* Title */}
          <label className="grid gap-0.5">
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              TITLE
            </span>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="border bg-transparent px-2 py-1 font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]"
              style={{ borderColor: "var(--ss-border-strong)" }}
            />
          </label>

          {/* Availability */}
          <label className="grid gap-0.5">
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              AVAILABILITY
            </span>
            <select
              value={editAvailability}
              onChange={(e) => setEditAvailability(e.target.value as MerchProduct["availability"])}
              className="border bg-transparent px-2 py-1 font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]"
              style={{ borderColor: "var(--ss-border-strong)" }}
            >
              <option value="limited">limited</option>
              <option value="always_on">always on</option>
              <option value="unavailable">unavailable</option>
            </select>
          </label>

          {/* Price positioning */}
          <label className="grid gap-0.5">
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              PRICE POSITIONING
            </span>
            <select
              value={editPricing}
              onChange={(e) => setEditPricing(e.target.value)}
              className="border bg-transparent px-2 py-1 font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]"
              style={{ borderColor: "var(--ss-border-strong)" }}
            >
              <option value="entry">entry</option>
              <option value="mid">mid</option>
              <option value="premium">premium</option>
              <option value="cult">cult</option>
            </select>
          </label>

          {/* Active toggle */}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={editActive}
              onChange={(e) => setEditActive(e.target.checked)}
              className="accent-[var(--ss-accent)]"
            />
            <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              ACTIVE
            </span>
          </label>

          {/* Save / Cancel */}
          <div className="flex gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={handleSave}
              className="border px-3 py-1 font-mono text-[0.55rem] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
              style={{
                borderColor: "var(--ss-accent)",
                backgroundColor: "var(--ss-accent)",
                color: "var(--ss-bg)"
              }}
            >
              {saving ? "SAVING…" : "SAVE"}
            </button>
            <button
              type="button"
              onClick={() => {
                setEditTitle(product.title);
                setEditActive(product.active);
                setEditAvailability(product.availability);
                setEditPricing(product.price_positioning);
                setExpanded(false);
                setEditError(null);
              }}
              className="border px-3 py-1 font-mono text-[0.55rem] uppercase tracking-widest"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-muted)"
              }}
            >
              CANCEL
            </button>
          </div>

          {editError && (
            <span className="font-mono text-[0.55rem] text-[color:var(--ss-error)]">
              {editError}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Provider Matrix (S43)
// ---------------------------------------------------------------------------

function ProviderMatrixSection({
  release
}: Readonly<{ release: ReleasePack }>) {
  const [aggregation, setAggregation] = useState<MerchProviderAggregation | null>(null);
  const [loading, setLoading] = useState(false);
  const [matrixError, setMatrixError] = useState<string | null>(null);

  const handleLoad = useCallback(async () => {
    setLoading(true);
    setMatrixError(null);
    try {
      // Find capsule for this release — we need capsule_id
      // The aggregation endpoint uses capsule_id, so we try to load via
      // the merch capsule list for this release. For now, we attempt to
      // fetch aggregation for each capsule. The simplest approach is to
      // let the user load after building a capsule.
      const capsules = await import("../../../_lib/inference").then(
        (m) => m.listMerchCapsules()
      );
      const capsule = capsules.find(
        (c: MerchCapsule) => c.release_id === release.release_id
      );
      if (!capsule) {
        setMatrixError("No merch capsule found for this release. Build one first.");
        return;
      }
      const agg = await getMerchProviderStatus(capsule.capsule_id);
      setAggregation(agg);
    } catch (err) {
      setMatrixError(formatError(err));
    } finally {
      setLoading(false);
    }
  }, [release.release_id]);

  return (
    <section>
      <SectionHeader title="PROVIDER MATRIX" />
      <div className="mt-4 space-y-3">
        {!aggregation && (
          <div className="space-y-2">
            <button
              type="button"
              disabled={loading}
              onClick={handleLoad}
              className="w-full border px-6 py-3 font-mono text-[0.7rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-primary)"
              }}
            >
              {loading ? "LOADING…" : "LOAD PROVIDER STATUS"}
            </button>
            <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              OPERATIONAL PREVIEW ONLY. NO PRODUCTS CREATED.
            </p>
          </div>
        )}

        {aggregation && (
          <div
            className="space-y-4 border border-[color:var(--ss-border)] p-4"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            {/* Capsule info */}
            <div className="flex items-center justify-between">
              <span className="font-mono text-[0.65rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                {aggregation.capsule_title}
              </span>
              <StatusChip status={aggregation.capsule_status} />
            </div>

            {/* Summary counters */}
            <div className="grid grid-cols-4 gap-2">
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  PRODUCTS
                </span>
                <span className="font-mono text-[0.65rem] text-[color:var(--ss-text-primary)]">
                  {aggregation.active_product_count} / {aggregation.product_count}
                </span>
              </div>
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  EXPORTED
                </span>
                <span
                  className="font-mono text-[0.65rem]"
                  style={{ color: "var(--ss-accent)" }}
                >
                  {aggregation.summary.exported_mock_count}
                </span>
              </div>
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  BLOCKED
                </span>
                <span
                  className="font-mono text-[0.65rem]"
                  style={{ color: aggregation.summary.blocked_count > 0 ? "var(--ss-warning)" : "var(--ss-text-muted)" }}
                >
                  {aggregation.summary.blocked_count}
                </span>
              </div>
              <div className="grid gap-0.5">
                <span className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  WARNINGS
                </span>
                <span
                  className="font-mono text-[0.65rem]"
                  style={{ color: aggregation.summary.total_warnings > 0 ? "var(--ss-warning)" : "var(--ss-text-muted)" }}
                >
                  {aggregation.summary.total_warnings}
                </span>
              </div>
            </div>

            {/* Provider modes */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(aggregation.providers).map(([key, provider]) => (
                <span
                  key={key}
                  className="border px-2 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest"
                  style={{
                    borderColor: "var(--ss-border-strong)",
                    color: "var(--ss-text-muted)"
                  }}
                >
                  {key.replace("_", " ")}: {provider.mode}
                </span>
              ))}
            </div>

            {/* Product × Provider matrix */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border-b border-[color:var(--ss-border)] px-2 py-2 text-left font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      PRODUCT
                    </th>
                    <th className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      SHOPIFY
                    </th>
                    <th className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      PRINTFUL
                    </th>
                    <th className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      TIKTOK
                    </th>
                    <th className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                      WARN
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {aggregation.products.map((ps: MerchProviderProductStatus) => (
                    <tr key={ps.product_id}>
                      <td className="border-b border-[color:var(--ss-border)] px-2 py-2">
                        <div className="grid gap-0.5">
                          <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]">
                            {ps.title}
                          </span>
                          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                            {ps.product_type.replace("_", " ")} · {ps.availability.replace("_", " ")}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center">
                        <ProviderStatusChip status={ps.shopify_status} />
                      </td>
                      <td className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center">
                        <ProviderStatusChip status={ps.printful_status} />
                      </td>
                      <td className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center">
                        <ProviderStatusChip status={ps.tiktok_status} />
                      </td>
                      <td className="border-b border-[color:var(--ss-border)] px-2 py-2 text-center">
                        {ps.total_warnings > 0 ? (
                          <span
                            className="font-mono text-[0.55rem] font-black"
                            style={{ color: "var(--ss-warning)" }}
                          >
                            {ps.total_warnings}
                          </span>
                        ) : (
                          <span className="font-mono text-[0.55rem] text-[color:var(--ss-text-muted)]">
                            0
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Operational notice */}
            <p className="font-mono text-[0.5rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              OPERATIONAL PREVIEW ONLY. NO PRODUCTS CREATED. NO REAL API CALLS.
            </p>

            {/* Reload button */}
            <button
              type="button"
              disabled={loading}
              onClick={handleLoad}
              className="border px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest transition-colors hover:bg-[color:var(--ss-panel)] disabled:opacity-50"
              style={{
                borderColor: "var(--ss-border-strong)",
                color: "var(--ss-text-muted)"
              }}
            >
              {loading ? "RELOADING…" : "RELOAD STATUS"}
            </button>
          </div>
        )}

        {matrixError && (
          <div
            className="border border-[color:var(--ss-error)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <span className="font-mono text-[0.65rem] text-[color:var(--ss-error)]">
              {matrixError}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}

function ProviderStatusChip({ status }: Readonly<{ status: string }>) {
  const color =
    status === "exported_mock"
      ? "var(--ss-accent)"
      : status === "blocked"
        ? "var(--ss-warning)"
        : status === "not_created"
          ? "var(--ss-text-muted)"
          : status === "draft"
            ? "var(--ss-text-secondary)"
            : "var(--ss-text-muted)";

  return (
    <span
      className="inline-block border px-1.5 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
      style={{ borderColor: color, color }}
    >
      {status.replace("_", " ")}
    </span>
  );
}

// Ditto Distribution (S37)
// ---------------------------------------------------------------------------

function DittoDistributionSection({
  release,
}: Readonly<{ release: ReleasePack }>) {
  const [pack, setPack] = useState<DistributionPack | null>(null);
  const [distError, setDistError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    setDistError(null);
    setLoading(true);
    try {
      const p = await createDistributionPack({ release_id: release.release_id });
      setPack(p);
    } catch (err) {
      setDistError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: DistributionPackStatus) => {
    if (!pack) return;
    setDistError(null);
    try {
      const updated = await updateDistributionPackStatus(pack.distribution_id, {
        status,
      });
      setPack(updated);
    } catch (err) {
      setDistError(formatError(err));
    }
  };

  const handleToggleReadiness = async (code: string) => {
    if (!pack) return;
    setDistError(null);
    try {
      const updated = await toggleDistributionReadinessItem(
        pack.distribution_id,
        code
      );
      setPack(updated);
    } catch (err) {
      setDistError(formatError(err));
    }
  };

  return (
    <section>
      <SectionHeader title="DITTO DISTRIBUTION" />

      {distError && (
        <div
          className="mt-3 border px-4 py-3 font-mono text-xs"
          style={{
            borderColor: "var(--ss-error)",
            color: "var(--ss-error)",
            backgroundColor: "var(--ss-panel)",
          }}
        >
          {distError}
        </div>
      )}

      {!pack ? (
        <div className="mt-4 flex items-center gap-4">
          <button
            onClick={handleCreate}
            disabled={loading}
            className="border px-5 py-2 font-mono text-[0.65rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80 disabled:opacity-40"
            style={{
              borderColor: "var(--ss-accent)",
              color: "var(--ss-accent)",
              backgroundColor: "transparent",
            }}
          >
            {loading ? "CREATING…" : "CREATE DISTRIBUTION PACK"}
          </button>
          <span className="font-mono text-[0.6rem] text-[color:var(--ss-text-muted)]">
            No real Ditto API calls — metadata export only
          </span>
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {/* Status + Provider */}
          <div className="flex items-center gap-4">
            <StatusChip status={pack.status} />
            <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              Provider: {pack.provider}
            </span>
            {pack.readiness_passed && (
              <span
                className="font-mono text-[0.55rem] font-bold uppercase"
                style={{ color: "var(--ss-success, #16a34a)" }}
              >
                ✓ READY
              </span>
            )}
          </div>

          {/* Metadata */}
          <div
            className="space-y-2 border p-4"
            style={{
              borderColor: "var(--ss-border)",
              backgroundColor: "var(--ss-panel)",
            }}
          >
            <h3 className="font-mono text-[0.6rem] font-bold uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              DITTO METADATA
            </h3>
            <div className="grid grid-cols-2 gap-2 font-mono text-xs">
              <span className="text-[color:var(--ss-text-muted)]">Artist</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.artist}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">Title</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.title}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">Genre</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.genre ?? "—"}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">Language</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.language}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">Explicit</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.explicit ? "YES" : "NO"}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">ISRC</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.isrc ?? "—"}
              </span>
              <span className="text-[color:var(--ss-text-muted)]">UPC</span>
              <span className="text-[color:var(--ss-text-primary)]">
                {pack.metadata.upc ?? "—"}
              </span>
            </div>
          </div>

          {/* Store Targets */}
          <div
            className="space-y-2 border p-4"
            style={{
              borderColor: "var(--ss-border)",
              backgroundColor: "var(--ss-panel)",
            }}
          >
            <h3 className="font-mono text-[0.6rem] font-bold uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              STORE TARGETS ({pack.store_targets.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {pack.store_targets.map((store: string) => (
                <span
                  key={store}
                  className="border px-2 py-1 font-mono text-[0.55rem] uppercase"
                  style={{
                    borderColor: "var(--ss-border)",
                    color: "var(--ss-text-primary)",
                  }}
                >
                  {store.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>

          {/* Readiness Checklist */}
          <div
            className="space-y-2 border p-4"
            style={{
              borderColor: "var(--ss-border)",
              backgroundColor: "var(--ss-panel)",
            }}
          >
            <h3 className="font-mono text-[0.6rem] font-bold uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              READINESS CHECKLIST
            </h3>
            <div className="space-y-1">
              {pack.readiness_checklist.map(
                (item: DistributionReadinessItem) => (
                  <button
                    key={item.code}
                    onClick={() => handleToggleReadiness(item.code)}
                    className="flex w-full items-center gap-3 px-2 py-1.5 text-left font-mono text-xs transition-colors hover:opacity-80"
                  >
                    <span
                      style={{
                        color: item.passed
                          ? "var(--ss-success, #16a34a)"
                          : "var(--ss-text-muted)",
                      }}
                    >
                      {item.passed ? "✓" : "○"}
                    </span>
                    <span className="text-[color:var(--ss-text-primary)]">
                      {item.label}
                    </span>
                    {item.notes && (
                      <span className="text-[0.55rem] text-[color:var(--ss-text-muted)]">
                        — {item.notes}
                      </span>
                    )}
                  </button>
                )
              )}
            </div>
          </div>

          {/* Status Actions */}
          <div className="flex flex-wrap gap-3">
            {pack.status === "draft" && (
              <button
                onClick={() => handleStatusUpdate("ready" as DistributionPackStatus)}
                className="border px-4 py-2 font-mono text-[0.6rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80"
                style={{
                  borderColor: "var(--ss-accent)",
                  color: "var(--ss-accent)",
                  backgroundColor: "transparent",
                }}
              >
                MARK READY
              </button>
            )}
            {pack.status === "ready" && (
              <button
                onClick={() =>
                  handleStatusUpdate("submitted" as DistributionPackStatus)
                }
                className="border px-4 py-2 font-mono text-[0.6rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80"
                style={{
                  borderColor: "var(--ss-accent)",
                  color: "var(--ss-accent)",
                  backgroundColor: "transparent",
                }}
              >
                MARK SUBMITTED
              </button>
            )}
            {pack.status === "submitted" && (
              <>
                <button
                  onClick={() =>
                    handleStatusUpdate("live" as DistributionPackStatus)
                  }
                  className="border px-4 py-2 font-mono text-[0.6rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80"
                  style={{
                    borderColor: "var(--ss-success, #16a34a)",
                    color: "var(--ss-success, #16a34a)",
                    backgroundColor: "transparent",
                  }}
                >
                  MARK LIVE
                </button>
                <button
                  onClick={() =>
                    handleStatusUpdate("rejected" as DistributionPackStatus)
                  }
                  className="border px-4 py-2 font-mono text-[0.6rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80"
                  style={{
                    borderColor: "var(--ss-error)",
                    color: "var(--ss-error)",
                    backgroundColor: "transparent",
                  }}
                >
                  MARK REJECTED
                </button>
              </>
            )}
            {pack.status === "live" && (
              <button
                onClick={() =>
                  handleStatusUpdate("takedown" as DistributionPackStatus)
                }
                className="border px-4 py-2 font-mono text-[0.6rem] font-bold uppercase tracking-widest transition-colors hover:opacity-80"
                style={{
                  borderColor: "var(--ss-error)",
                  color: "var(--ss-error)",
                  backgroundColor: "transparent",
                }}
              >
                REQUEST TAKEDOWN
              </button>
            )}
          </div>

          {/* Operator Notes */}
          {pack.operator_notes && (
            <div
              className="border p-3 font-mono text-xs"
              style={{
                borderColor: "var(--ss-border)",
                backgroundColor: "var(--ss-panel-elevated)",
                color: "var(--ss-text-muted)",
              }}
            >
              {pack.operator_notes}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function SectionHeader({ title }: Readonly<{ title: string }>) {
  return (
    <h2 className="border-b border-[color:var(--ss-border)] pb-3 font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
      {title}
    </h2>
  );
}

function MetaCell({
  label,
  value,
  accent = false
}: Readonly<{ label: string; value: string; accent?: boolean }>) {
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
        style={{ color: accent ? "var(--ss-accent)" : "var(--ss-text-primary)" }}
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
  return "release_detail_error";
}

// Campaign OS (S45)
// ---------------------------------------------------------------------------

const CHANNEL_LABELS: Record<string, string> = {
  soundcloud: "SoundCloud",
  distribution: "Distribution",
  merch: "Merch",
  tiktok: "TikTok",
  instagram: "Instagram",
  discord: "Discord",
};

const TASK_STATUS_COLORS: Record<string, string> = {
  pending: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  blocked: "#f97316",
  completed: "#22c55e",
};

const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  planning: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  active: "#22c55e",
  completed: "#3b82f6",
  archived: "#6b7280",
};

function CampaignSection({
  release,
}: Readonly<{ release: ReleasePack }>) {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [campaignError, setCampaignError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);

  const handleLoad = async () => {
    setCampaignError(null);
    try {
      const c = await getCampaignByRelease(release.release_id);
      setCampaign(c);
    } catch {
      // 404 means no campaign yet — that's fine
      setCampaign(null);
    }
    setChecked(true);
  };

  const handleCreate = async () => {
    setCampaignError(null);
    setLoading(true);
    try {
      const c = await createCampaign({ release_id: release.release_id });
      setCampaign(c);
    } catch (err) {
      setCampaignError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: CampaignStatus) => {
    if (!campaign) return;
    setCampaignError(null);
    try {
      const updated = await updateCampaign(campaign.campaign_id, { status });
      setCampaign(updated);
    } catch (err) {
      setCampaignError(formatError(err));
    }
  };

  // Group tasks by channel
  const tasksByChannel: Record<string, CampaignTask[]> = {};
  if (campaign) {
    for (const task of campaign.tasks) {
      const ch = task.channel;
      if (!tasksByChannel[ch]) tasksByChannel[ch] = [];
      tasksByChannel[ch].push(task);
    }
  }

  return (
    <section>
      <SectionHeader title="CAMPAIGN OS" />

      {campaignError && (
        <p className="mt-2 font-mono text-[0.65rem] text-red-400">
          {campaignError}
        </p>
      )}

      {!checked && !campaign && (
        <div className="mt-3">
          <button
            className="border border-[color:var(--ss-border)] px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)]"
            onClick={handleLoad}
          >
            LOAD CAMPAIGN
          </button>
        </div>
      )}

      {checked && !campaign && (
        <div className="mt-3">
          <p className="mb-3 font-mono text-[0.6rem] text-[color:var(--ss-text-muted)]">
            No campaign exists for this release.
          </p>
          <button
            className="border border-[color:var(--ss-accent)] px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent)] hover:text-black disabled:opacity-40"
            onClick={handleCreate}
            disabled={loading}
          >
            {loading ? "BUILDING…" : "BUILD CAMPAIGN"}
          </button>
        </div>
      )}

      {campaign && (
        <div className="mt-3 space-y-4">
          {/* Campaign header */}
          <div
            className="flex items-center justify-between border border-[color:var(--ss-border)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-[0.7rem] font-black uppercase text-[color:var(--ss-text-primary)]">
                {campaign.title}
              </span>
              <span
                className="inline-block border px-1.5 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
                style={{
                  borderColor: CAMPAIGN_STATUS_COLORS[campaign.status] ?? "var(--ss-text-muted)",
                  color: CAMPAIGN_STATUS_COLORS[campaign.status] ?? "var(--ss-text-muted)",
                }}
              >
                {campaign.status}
              </span>
            </div>

            {/* Status actions */}
            <div className="flex gap-2">
              {campaign.status === "planning" && (
                <button
                  className="border border-[color:var(--ss-accent)] px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent)] hover:text-black"
                  onClick={() => handleStatusUpdate("ready" as CampaignStatus)}
                >
                  MARK READY
                </button>
              )}
              {campaign.status === "ready" && (
                <button
                  className="border border-green-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-green-500 hover:bg-green-500 hover:text-black"
                  onClick={() => handleStatusUpdate("active" as CampaignStatus)}
                >
                  ACTIVATE
                </button>
              )}
              {campaign.status === "active" && (
                <button
                  className="border border-blue-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-blue-500 hover:bg-blue-500 hover:text-black"
                  onClick={() => handleStatusUpdate("completed" as CampaignStatus)}
                >
                  COMPLETE
                </button>
              )}
              {campaign.status !== "archived" && campaign.status !== "planning" && (
                <button
                  className="border border-[color:var(--ss-border)] px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:border-[color:var(--ss-text-muted)]"
                  onClick={() => handleStatusUpdate("archived" as CampaignStatus)}
                >
                  ARCHIVE
                </button>
              )}
            </div>
          </div>

          {/* Channels */}
          <div className="flex flex-wrap gap-2">
            {campaign.channels.map((ch) => (
              <span
                key={ch}
                className="border border-[color:var(--ss-border)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]"
              >
                {CHANNEL_LABELS[ch] ?? ch}
              </span>
            ))}
          </div>

          {/* Warnings */}
          {campaign.warnings.length > 0 && (
            <div className="space-y-1">
              {campaign.warnings.map((w, i) => (
                <div
                  key={i}
                  className="border-l-2 border-orange-500 bg-orange-500/5 px-3 py-2 font-mono text-[0.6rem] text-orange-400"
                >
                  <span className="font-black uppercase">{w.code}</span>{" "}
                  {w.message}
                </div>
              ))}
            </div>
          )}

          {/* Tasks grouped by channel */}
          {Object.entries(tasksByChannel).map(([channel, tasks]) => (
            <div key={channel}>
              <h4 className="mb-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                {CHANNEL_LABELS[channel] ?? channel}
              </h4>
              <div className="space-y-1">
                {tasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="font-mono text-[0.6rem] font-bold text-[color:var(--ss-text-primary)]">
                        {task.title}
                      </span>
                      {task.description && (
                        <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                          {task.description}
                        </span>
                      )}
                      {task.warnings.length > 0 && (
                        <span className="font-mono text-[0.5rem] text-orange-400">
                          {task.warnings.join(" · ")}
                        </span>
                      )}
                    </div>
                    <span
                      className="inline-block border px-1.5 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
                      style={{
                        borderColor: TASK_STATUS_COLORS[task.status] ?? "var(--ss-text-muted)",
                        color: TASK_STATUS_COLORS[task.status] ?? "var(--ss-text-muted)",
                      }}
                    >
                      {task.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Timeline */}
          {campaign.timeline.length > 0 && (
            <div>
              <h4 className="mb-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                TIMELINE
              </h4>
              <div className="space-y-1">
                {campaign.timeline.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-baseline gap-3 border-l border-[color:var(--ss-border)] pl-3 font-mono text-[0.55rem]"
                  >
                    <span className="text-[color:var(--ss-text-muted)]">
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                    <span className="font-bold text-[color:var(--ss-text-primary)]">
                      {item.event}
                    </span>
                    {item.notes && (
                      <span className="text-[color:var(--ss-text-muted)]">
                        {item.notes}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// Vinyl Release Object (S46)
// ---------------------------------------------------------------------------

const VINYL_STATUS_COLORS: Record<string, string> = {
  draft: "var(--ss-text-muted)",
  ready: "var(--ss-accent)",
  submitted: "#f59e0b",
  test_pressing: "#f97316",
  approved: "#22c55e",
  live: "#3b82f6",
  archived: "#6b7280",
  blocked: "#ef4444",
};

const FORMAT_LABELS: Record<string, string> = {
  seven_inch: '7"',
  ten_inch: '10"',
  twelve_inch: '12"',
  dubplate: "Dubplate",
  lathe_cut: "Lathe Cut",
};

const EDITION_LABELS: Record<string, string> = {
  vinyl_on_demand: "Vinyl on Demand",
  limited_numbered: "Limited Numbered",
  white_label: "White Label",
  collector_box: "Collector Box",
};

function VinylReleaseSection({
  release,
}: Readonly<{ release: ReleasePack }>) {
  const [vinyl, setVinyl] = useState<VinylReleaseObject | null>(null);
  const [exportPayload, setExportPayload] = useState<VinylExportPayload | null>(null);
  const [vinylError, setVinylError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<VinylFormat>("twelve_inch" as VinylFormat);
  const [selectedEdition, setSelectedEdition] = useState<VinylEditionType>("vinyl_on_demand" as VinylEditionType);

  const handleLoad = async () => {
    setVinylError(null);
    try {
      const v = await getVinylReleaseByRelease(release.release_id);
      setVinyl(v);
    } catch {
      setVinyl(null);
    }
    setChecked(true);
  };

  const handleCreate = async () => {
    setVinylError(null);
    setLoading(true);
    try {
      const v = await createVinylRelease({
        release_id: release.release_id,
        format: selectedFormat,
        edition_type: selectedEdition,
      });
      setVinyl(v);
    } catch (err) {
      setVinylError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: VinylReleaseStatus) => {
    if (!vinyl) return;
    setVinylError(null);
    try {
      const updated = await updateVinylReleaseStatus(vinyl.vinyl_id, { status });
      setVinyl(updated);
    } catch (err) {
      setVinylError(formatError(err));
    }
  };

  const handleExport = async () => {
    if (!vinyl) return;
    setVinylError(null);
    try {
      const payload = await getVinylExport(vinyl.vinyl_id);
      setExportPayload(payload);
    } catch (err) {
      setVinylError(formatError(err));
    }
  };

  return (
    <section>
      <SectionHeader title="VINYL RELEASE" />

      {vinylError && (
        <p className="mt-2 font-mono text-[0.65rem] text-red-400">
          {vinylError}
        </p>
      )}

      {!checked && !vinyl && (
        <div className="mt-3">
          <button
            className="border border-[color:var(--ss-border)] px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)]"
            onClick={handleLoad}
          >
            LOAD VINYL
          </button>
        </div>
      )}

      {checked && !vinyl && (
        <div className="mt-3 space-y-3">
          <p className="font-mono text-[0.6rem] text-[color:var(--ss-text-muted)]">
            No vinyl release exists for this release.
          </p>
          <div className="flex gap-3">
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value as VinylFormat)}
              className="border border-[color:var(--ss-border)] bg-[color:var(--ss-panel)] px-2 py-1 font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]"
            >
              <option value="twelve_inch">12&quot;</option>
              <option value="ten_inch">10&quot;</option>
              <option value="seven_inch">7&quot;</option>
              <option value="dubplate">Dubplate</option>
              <option value="lathe_cut">Lathe Cut</option>
            </select>
            <select
              value={selectedEdition}
              onChange={(e) => setSelectedEdition(e.target.value as VinylEditionType)}
              className="border border-[color:var(--ss-border)] bg-[color:var(--ss-panel)] px-2 py-1 font-mono text-[0.55rem] text-[color:var(--ss-text-primary)]"
            >
              <option value="vinyl_on_demand">Vinyl on Demand</option>
              <option value="limited_numbered">Limited Numbered</option>
              <option value="white_label">White Label</option>
              <option value="collector_box">Collector Box</option>
            </select>
          </div>
          <button
            className="border border-[color:var(--ss-accent)] px-4 py-2 font-mono text-[0.6rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent)] hover:text-black disabled:opacity-40"
            onClick={handleCreate}
            disabled={loading}
          >
            {loading ? "BUILDING…" : "BUILD VINYL RELEASE"}
          </button>
          <p className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
            Manual vinyl handoff. No manufacturing order placed.
          </p>
        </div>
      )}

      {vinyl && (
        <div className="mt-3 space-y-4">
          {/* Vinyl header */}
          <div
            className="flex items-center justify-between border border-[color:var(--ss-border)] px-4 py-3"
            style={{ backgroundColor: "var(--ss-panel-elevated)" }}
          >
            <div className="flex items-center gap-3">
              <span className="font-mono text-[0.7rem] font-black uppercase text-[color:var(--ss-text-primary)]">
                {vinyl.title}
              </span>
              <span
                className="inline-block border px-1.5 py-0.5 font-mono text-[0.45rem] font-black uppercase tracking-widest"
                style={{
                  borderColor: VINYL_STATUS_COLORS[vinyl.status] ?? "var(--ss-text-muted)",
                  color: VINYL_STATUS_COLORS[vinyl.status] ?? "var(--ss-text-muted)",
                }}
              >
                {vinyl.status.replace("_", " ")}
              </span>
            </div>
            <div className="flex gap-2">
              {vinyl.status === "draft" && (
                <button
                  className="border border-[color:var(--ss-accent)] px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-accent)] hover:text-black"
                  onClick={() => handleStatusUpdate("ready" as VinylReleaseStatus)}
                >
                  MARK READY
                </button>
              )}
              {vinyl.status === "ready" && (
                <button
                  className="border border-yellow-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-yellow-500 hover:bg-yellow-500 hover:text-black"
                  onClick={() => handleStatusUpdate("submitted" as VinylReleaseStatus)}
                >
                  SUBMIT
                </button>
              )}
              {vinyl.status === "submitted" && (
                <button
                  className="border border-orange-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-orange-500 hover:bg-orange-500 hover:text-black"
                  onClick={() => handleStatusUpdate("test_pressing" as VinylReleaseStatus)}
                >
                  TEST PRESSING
                </button>
              )}
              {vinyl.status === "test_pressing" && (
                <button
                  className="border border-green-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-green-500 hover:bg-green-500 hover:text-black"
                  onClick={() => handleStatusUpdate("approved" as VinylReleaseStatus)}
                >
                  APPROVE
                </button>
              )}
              {vinyl.status === "approved" && (
                <button
                  className="border border-blue-500 px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-blue-500 hover:bg-blue-500 hover:text-black"
                  onClick={() => handleStatusUpdate("live" as VinylReleaseStatus)}
                >
                  GO LIVE
                </button>
              )}
              {vinyl.status !== "archived" && (
                <button
                  className="border border-[color:var(--ss-border)] px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)] hover:border-[color:var(--ss-text-muted)]"
                  onClick={() => handleStatusUpdate("archived" as VinylReleaseStatus)}
                >
                  ARCHIVE
                </button>
              )}
            </div>
          </div>

          {/* Format / Edition / Provider */}
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: "FORMAT", value: FORMAT_LABELS[vinyl.format] ?? vinyl.format },
              { label: "EDITION", value: EDITION_LABELS[vinyl.edition_type] ?? vinyl.edition_type },
              { label: "PROVIDER", value: vinyl.provider_group.replace("_", " ") },
              { label: "QUANTITY", value: vinyl.pressing_quantity?.toString() ?? "—" },
            ].map((m) => (
              <div
                key={m.label}
                className="flex flex-col gap-2 p-4"
                style={{ backgroundColor: "var(--ss-panel)" }}
              >
                <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  {m.label}
                </span>
                <span className="text-lg font-black uppercase leading-none text-[color:var(--ss-text-primary)]">
                  {m.value}
                </span>
              </div>
            ))}
          </div>

          {/* Readiness checklist */}
          {vinyl.readiness_items.length > 0 && (
            <div>
              <h4 className="mb-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                READINESS
              </h4>
              <div className="space-y-1">
                {vinyl.readiness_items.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ backgroundColor: item.passed ? "#22c55e" : "#f97316" }}
                      />
                      <span className="font-mono text-[0.6rem] text-[color:var(--ss-text-primary)]">
                        {item.label}
                      </span>
                    </div>
                    {!item.passed && item.warning && (
                      <span className="font-mono text-[0.5rem] text-orange-400">
                        {item.warning}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {vinyl.warnings.length > 0 && (
            <div className="space-y-1">
              {vinyl.warnings.map((w, i) => (
                <div
                  key={i}
                  className="border-l-2 border-orange-500 bg-orange-500/5 px-3 py-2 font-mono text-[0.6rem] text-orange-400"
                >
                  {w}
                </div>
              ))}
            </div>
          )}

          {/* Track listing */}
          {vinyl.side_a_tracks.length > 0 && (
            <div>
              <h4 className="mb-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                SIDE A
              </h4>
              <div className="space-y-1">
                {vinyl.side_a_tracks.map((t, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <span className="font-mono text-[0.6rem] text-[color:var(--ss-text-primary)]">
                      {t.position}. {t.title}
                    </span>
                    {t.duration_seconds != null && (
                      <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                        {Math.floor(t.duration_seconds / 60)}:{String(Math.floor(t.duration_seconds % 60)).padStart(2, "0")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {vinyl.side_b_tracks.length > 0 && (
            <div>
              <h4 className="mb-2 font-mono text-[0.55rem] font-black uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                SIDE B
              </h4>
              <div className="space-y-1">
                {vinyl.side_b_tracks.map((t, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between border border-[color:var(--ss-border)] px-3 py-2"
                    style={{ backgroundColor: "var(--ss-panel)" }}
                  >
                    <span className="font-mono text-[0.6rem] text-[color:var(--ss-text-primary)]">
                      {t.position}. {t.title}
                    </span>
                    {t.duration_seconds != null && (
                      <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
                        {Math.floor(t.duration_seconds / 60)}:{String(Math.floor(t.duration_seconds % 60)).padStart(2, "0")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Export */}
          <div className="flex items-center gap-3">
            <button
              className="border border-[color:var(--ss-border)] px-3 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)] hover:bg-[color:var(--ss-panel-elevated)]"
              onClick={handleExport}
            >
              VIEW EXPORT PAYLOAD
            </button>
            <span className="font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]">
              Manual vinyl handoff. No manufacturing order placed.
            </span>
          </div>

          {exportPayload && (
            <pre
              className="overflow-x-auto border border-[color:var(--ss-border)] p-3 font-mono text-[0.5rem] text-[color:var(--ss-text-muted)]"
              style={{ backgroundColor: "var(--ss-panel)" }}
            >
              {JSON.stringify(exportPayload, null, 2)}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}
